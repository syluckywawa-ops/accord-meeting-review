#!/usr/bin/env python3
"""Create readable, evidence-addressable transcripts from AMI NXT XML.

The script intentionally does not read or export AMI abstractive summaries. Gold
labels must be created from transcripts before the official ACTIONS audit.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


NITE = "http://nite.sourceforge.net/"
NITE_ID = f"{{{NITE}}}id"
NITE_HREF = f"{{{NITE}}}href"
HREF_RANGE = re.compile(r"id\(([^)]+)\)(?:\.\.id\(([^)]+)\))?")

ROLE_NAMES = {
    "PM": "Project Manager",
    "ME": "Marketing Expert",
    "ID": "Industrial Designer",
    "UI": "User Interface Designer",
}


@dataclass(frozen=True)
class Segment:
    speaker: str
    role: str
    start: float
    end: float
    text: str
    source_ids: tuple[str, ...]


def normalise_ami_date(raw_date: str) -> str | None:
    """AMI metadata mixes two- and four-digit years."""
    cleaned = raw_date.strip()
    if not cleaned:
        return None
    for date_format in ("%d-%m-%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(cleaned, date_format).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Unsupported AMI date format: {raw_date!r}")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def detokenize(elements: Iterable[ET.Element]) -> str:
    """Join AMI word elements while preserving ordinary punctuation."""
    result = ""
    for element in elements:
        if local_name(element.tag) != "w" or not element.text:
            continue
        token = element.text.strip()
        if not token:
            continue
        is_punctuation = element.get("punc") == "true"
        attach_left = is_punctuation or token.startswith(("'", "’"))
        if result and not attach_left:
            result += " "
        result += token
    return result.strip()


def parse_meeting_metadata(meetings_xml: Path, meeting_id: str) -> dict:
    root = ET.parse(meetings_xml).getroot()
    for meeting in root.iter():
        if local_name(meeting.tag) != "meeting":
            continue
        if meeting.get("observation") != meeting_id:
            continue

        raw_date = meeting.get("dateOnly", "").strip()
        meeting_date = normalise_ami_date(raw_date)

        speakers = {}
        for speaker in meeting:
            if local_name(speaker.tag) != "speaker":
                continue
            agent = speaker.get("nxt_agent", "")
            role_code = speaker.get("role", "")
            speakers[agent] = {
                "agent": agent,
                "role_code": role_code,
                "role": ROLE_NAMES.get(role_code, role_code or "Unknown role"),
                "participant_id": speaker.get("global_name"),
                "channel": speaker.get("channel"),
            }

        return {
            "meeting_id": meeting_id,
            "date": meeting_date,
            "start_time": meeting.get("startTime") or None,
            "duration_seconds": float(meeting.get("duration", "0") or 0),
            "visibility": meeting.get("visibility"),
            "speakers": speakers,
        }
    raise ValueError(f"Meeting {meeting_id!r} not found in {meetings_xml}")


def load_speaker_segments(source_root: Path, meeting_id: str, speaker: str, role: str) -> tuple[list[Segment], int]:
    words_path = source_root / "words" / f"{meeting_id}.{speaker}.words.xml"
    segments_path = source_root / "segments" / f"{meeting_id}.{speaker}.segments.xml"
    if not words_path.exists() or not segments_path.exists():
        raise FileNotFoundError(f"Missing words or segments for {meeting_id}.{speaker}")

    word_root = ET.parse(words_path).getroot()
    word_elements = list(word_root)
    id_to_position = {
        element.get(NITE_ID): index
        for index, element in enumerate(word_elements)
        if element.get(NITE_ID)
    }
    word_count = sum(local_name(element.tag) == "w" for element in word_elements)

    segments: list[Segment] = []
    segment_root = ET.parse(segments_path).getroot()
    for element in segment_root:
        if local_name(element.tag) != "segment":
            continue
        selected: list[ET.Element] = []
        for child in element:
            # AMI uses a namespaced child element but a plain `href` attribute.
            # The fallback also supports NXT variants that namespace the attribute.
            href = child.get("href") or child.get(NITE_HREF, "")
            match = HREF_RANGE.search(href)
            if not match:
                continue
            first_id, last_id = match.group(1), match.group(2) or match.group(1)
            if first_id not in id_to_position or last_id not in id_to_position:
                raise ValueError(f"Unresolved word range in {meeting_id}: {href}")
            first, last = id_to_position[first_id], id_to_position[last_id]
            selected.extend(word_elements[first : last + 1])

        text = detokenize(selected)
        if not text:
            continue
        segments.append(
            Segment(
                speaker=speaker,
                role=role,
                start=float(element.get("transcriber_start", "0") or 0),
                end=float(element.get("transcriber_end", "0") or 0),
                text=text,
                source_ids=(element.get(NITE_ID, ""),),
            )
        )
    return segments, word_count


def merge_adjacent_segments(segments: list[Segment], max_gap_seconds: float = 1.5) -> list[Segment]:
    """Merge only consecutive same-speaker segments after chronological sort."""
    ordered = sorted(segments, key=lambda item: (item.start, item.end, item.speaker))
    merged: list[Segment] = []
    for segment in ordered:
        if (
            merged
            and merged[-1].speaker == segment.speaker
            and segment.start - merged[-1].end <= max_gap_seconds
        ):
            previous = merged[-1]
            merged[-1] = Segment(
                speaker=previous.speaker,
                role=previous.role,
                start=previous.start,
                end=max(previous.end, segment.end),
                text=f"{previous.text} {segment.text}".strip(),
                source_ids=previous.source_ids + segment.source_ids,
            )
        else:
            merged.append(segment)
    return merged


def timestamp(seconds: float) -> str:
    minutes, remainder = divmod(max(seconds, 0.0), 60)
    return f"{int(minutes):02d}:{remainder:05.2f}"


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("Manifest is empty")
    return rows


def prepare_meeting(source_root: Path, output_root: Path, manifest_row: dict[str, str]) -> dict:
    meeting_id = manifest_row["meeting_id"]
    metadata = parse_meeting_metadata(
        source_root / "corpusResources" / "meetings.xml", meeting_id
    )

    all_segments: list[Segment] = []
    word_count = 0
    for speaker, speaker_meta in metadata["speakers"].items():
        speaker_segments, speaker_words = load_speaker_segments(
            source_root, meeting_id, speaker, speaker_meta["role"]
        )
        all_segments.extend(speaker_segments)
        word_count += speaker_words

    expected_words = int(manifest_row["transcribed_word_elements"])
    if word_count != expected_words:
        raise ValueError(
            f"Word-count mismatch for {meeting_id}: manifest={expected_words}, parsed={word_count}"
        )

    turns = merge_adjacent_segments(all_segments)
    transcript_dir = output_root / "transcripts"
    metadata_dir = output_root / "metadata"
    transcript_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    turn_records = []
    text_lines = [
        f"Meeting: {meeting_id}",
        f"Split: {manifest_row['split']}",
        f"Meeting date: {metadata['date'] or 'unknown'}",
        f"AMI duration (seconds): {metadata['duration_seconds']:.0f}",
        f"Transcribed word elements: {word_count}",
        "",
    ]
    for index, turn in enumerate(turns, start=1):
        turn_id = f"{meeting_id}-T{index:04d}"
        text_lines.append(
            f"[{timestamp(turn.start)}-{timestamp(turn.end)}] {turn_id} | "
            f"{turn.role} ({turn.speaker}): {turn.text}"
        )
        turn_records.append(
            {
                "turn_id": turn_id,
                "speaker": turn.speaker,
                "role": turn.role,
                "start_seconds": round(turn.start, 3),
                "end_seconds": round(turn.end, 3),
                "text": turn.text,
                "source_segment_ids": list(turn.source_ids),
            }
        )

    (transcript_dir / f"{meeting_id}.txt").write_text(
        "\n".join(text_lines) + "\n", encoding="utf-8"
    )
    payload = {
        **metadata,
        "split": manifest_row["split"],
        "official_partition": manifest_row["official_partition"],
        "transcribed_word_elements": word_count,
        "turn_count": len(turn_records),
        "turns": turn_records,
    }
    (metadata_dir / f"{meeting_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "meeting_id": meeting_id,
        "split": manifest_row["split"],
        "word_count": word_count,
        "turn_count": len(turn_records),
        "duration_seconds": metadata["duration_seconds"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Extracted AMI manual annotation root")
    parser.add_argument("--manifest", type=Path, required=True, help="Locked data manifest CSV")
    parser.add_argument("--output", type=Path, required=True, help="Derived-data output directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = read_manifest(args.manifest)
    summaries = [prepare_meeting(args.source, args.output, row) for row in rows]
    summary_path = args.output / "preparation_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    total_words = sum(item["word_count"] for item in summaries)
    print(f"Prepared {len(summaries)} meetings and {total_words} transcribed word elements.")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
