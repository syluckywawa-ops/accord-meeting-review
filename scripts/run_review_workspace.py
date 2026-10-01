"""Run the offline demonstration: python3 scripts/run_review_workspace.py."""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import secrets
import re
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from actionai.review_workspace import new_session, apply_review, approved_items, export_csv, task_tracking, review_hints
from actionai.imported_meetings import prepare_import, extract_rules, extract_llm
from actionai.document_import import decode_file, extract_document

PATHS = {
    "few_shot": "outputs/llm-evaluation/few-shot-v1.0-frozen/test.json",
    "zero_shot": "outputs/llm-evaluation/zero-shot-v1.0-frozen/test.json",
    "rule_baseline": "outputs/rule-baseline/rule-baseline-v1.0-frozen/test.json",
}
LOCK = threading.Lock()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def optional_log(result):
    """Raw provider logs are private audit artifacts, not demo dependencies."""
    relative = result.get("raw_log_path")
    if not relative:
        return {}
    path = ROOT / relative
    return read(path) if path.is_file() else {}


class Handler(BaseHTTPRequestHandler):
    def visitor(self):
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get("Cookie", ""))
        except Exception:
            pass
        token = cookies.get("actionai_visitor")
        value = token.value if token else ""
        if not re.fullmatch(r"[a-f0-9]{64}", value):
            value = secrets.token_hex(32)
        return value

    def reply(self, data, status=200, content_type="application/json; charset=utf-8"):
        body = data.encode("utf-8") if isinstance(data, str) else json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if hasattr(self, "visitor_id"):
            self.send_header("Set-Cookie", f"actionai_visitor={self.visitor_id}; Path=/; HttpOnly; SameSite=Strict")
        self.end_headers()
        self.wfile.write(body)

    def context(self, query):
        condition = query.get("condition", ["few_shot"])[0]
        meeting = query.get("meeting", ["TS3003c"])[0]
        if meeting.startswith("import-"):
            if not re.fullmatch(r"import-[a-f0-9]{32}", meeting) or condition not in {"local_rules", "live_ai"}:
                raise ValueError("Unknown imported meeting or method")
            folder = ROOT / f"outputs/review-workspace/{self.visitor_id}/imports/{meeting}"
            if not folder.exists():
                raise ValueError("Imported meeting not available in this browser session")
            metadata = read(folder / "metadata.json")
            result = read(folder / "extraction.json")
            destination = folder / "review.json"
            state = read(destination) if destination.exists() else new_session(meeting, condition, result)
            if state["condition"] != condition:
                raise ValueError("Method does not match this imported meeting")
            return result, metadata, destination, state
        if condition not in PATHS:
            raise ValueError("Unknown method")
        payload = read(ROOT / PATHS[condition])
        result = next((x for x in payload["results"] if x["transcript_id"] == meeting), None)
        if result is None:
            raise ValueError("Unknown meeting")
        if condition == "rule_baseline":
            result = dict(result, run_status="valid")
        metadata = read(ROOT / f"data/derived/metadata/{meeting}.json")
        destination = ROOT / f"outputs/review-workspace/{self.visitor_id}/{condition}/{meeting}.json"
        state = read(destination) if destination.exists() else new_session(meeting, condition, result)
        return result, metadata, destination, state

    def do_GET(self):
        self.visitor_id = self.visitor()
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                self.reply((ROOT / "web/review.html").read_text(encoding="utf-8"), content_type="text/html; charset=utf-8")
            elif parsed.path == "/api/catalog":
                folder = ROOT / f"outputs/review-workspace/{self.visitor_id}/imports"
                imports = []
                if folder.exists():
                    for entry in sorted(folder.glob("*/review.json")):
                        session = read(entry)
                        imports.append({"meeting": session["meeting_id"], "condition": session["condition"],
                                        "title": read(entry.parent / "metadata.json")["title"]})
                self.reply({"methods": list(PATHS), "meetings": [x["transcript_id"] for x in read(ROOT / PATHS["few_shot"])["results"]],
                            "imports": imports, "live_available": bool(os.environ.get("OPENROUTER_API_KEY"))})
            elif parsed.path in {"/api/session", "/api/export"}:
                query = parse_qs(parsed.query)
                result, metadata, destination, state = self.context(query)
                if parsed.path == "/api/session":
                    log = optional_log(result)
                    self.reply({"state": state, "turns": metadata["turns"], "review_hints": review_hints(state),
                                "usage": result.get("usage", log.get("usage_total", {})),
                                "title": metadata.get("title", state["meeting_id"]),
                                "issues": result.get("issues", log.get("attempts", [{}])[-1].get("validation_issues", []))})
                else:
                    items = approved_items(state, metadata)
                    if query.get("format", ["json"])[0] == "csv":
                        self.reply(export_csv(items, task_tracking(state)), content_type="text/csv; charset=utf-8")
                    else:
                        self.reply({"meeting_id": state["meeting_id"], "condition": state["condition"],
                                    "review_revision": state["revision"], "source_status": state["source_status"],
                                    "human_reviewed": True, "action_items": items,
                                    "task_tracking": task_tracking(state), "audit_history": state["history"]})
            else:
                self.reply({"error": "Not found"}, 404)
        except (ValueError, KeyError) as error:
            self.reply({"error": str(error)}, 400)

    def do_POST(self):
        self.visitor_id = self.visitor()
        # Restrict mutation to the same local origin; no external page may write sessions.
        origin = self.headers.get("Origin")
        if origin and urlparse(origin).netloc != self.headers.get("Host", ""):
            self.reply({"error": "Origin rejected"}, 403)
            return
        if self.path not in {"/api/review", "/api/import", "/api/parse-document"}:
            self.reply({"error": "Not found"}, 404)
            return
        try:
            size = int(self.headers.get("Content-Length", 0))
            limit = 12000000 if self.path == '/api/parse-document' else 1000000
            if not 0 < size <= limit:
                raise ValueError("Invalid request size")
            request = json.loads(self.rfile.read(size))
            if self.path == '/api/parse-document':
                self.reply(extract_document(request.get('name'), decode_file(request.get('base64'))))
                return
            if self.path == "/api/import":
                method = request.get("method", "local_rules")
                if method not in {"local_rules", "live_ai"}:
                    raise ValueError("Unknown extraction method")
                metadata = prepare_import(request.get("text"), request.get("title"))
                result = extract_rules(metadata) if method == "local_rules" else extract_llm(metadata, method, ROOT)
                session = new_session(metadata["meeting_id"], method, result)
                folder = ROOT / f"outputs/review-workspace/{self.visitor_id}/imports/{metadata['meeting_id']}"
                folder.mkdir(parents=True, exist_ok=False)
                for name, value in (("metadata", metadata), ("extraction", result), ("review", session)):
                    (folder / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
                self.reply({"meeting": metadata["meeting_id"], "condition": method})
                return
            query = {"meeting": [request["meeting"]], "condition": [request["condition"]]}
            with LOCK:
                _, metadata, destination, state = self.context(query)
                if request.get("revision") != state["revision"]:
                    self.reply({"error": "Session changed. Reload before editing."}, 409)
                    return
                updated = apply_review(state, request["operation"], metadata)
                destination.parent.mkdir(parents=True, exist_ok=True)
                temporary = destination.with_suffix(".tmp")
                temporary.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
                os.replace(temporary, destination)
            self.reply(updated)
        except (ValueError, KeyError) as error:
            self.reply({"error": str(error)}, 400)
        except Exception:
            self.reply({"error": "Extraction could not complete. Check server dependencies and provider availability; no reviewed list was created."}, 502)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"ActionAI review workspace: http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()
