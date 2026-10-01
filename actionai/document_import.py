"""Local, bounded text extraction; preview before creating a meeting."""
import base64
import binascii
import io
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TEXT = 150000
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def decode_file(encoded):
    if not isinstance(encoded, str) or len(encoded) > MAX_FILE_BYTES * 4 // 3 + 8:
        raise ValueError('Use a document smaller than 8 MB.')
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError('The uploaded file could not be decoded.')
    if not data or len(data) > MAX_FILE_BYTES:
        raise ValueError('Use a non-empty document smaller than 8 MB.')
    return data


def extract_document(name, data):
    suffix = Path(str(name)).suffix.lower()
    warnings = []
    if len(data) > MAX_FILE_BYTES or not data:
        raise ValueError('Use a non-empty document smaller than 8 MB.')
    if suffix == '.txt':
        try:
            text = data.decode('utf-8-sig')
        except UnicodeDecodeError:
            raise ValueError('Save the TXT file using UTF-8 encoding.')
    elif suffix == '.docx':
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                entries = archive.infolist()
                if len(entries) > 2000 or sum(x.file_size for x in entries) > 32 * 1024 * 1024:
                    raise ValueError('The Word document exceeds the safe extraction limit.')
                xml = archive.read('word/document.xml')
            if b'<!DOCTYPE' in xml.upper() or b'<!ENTITY' in xml.upper():
                raise ValueError('Unsupported XML declarations in Word document.')
            root = ET.fromstring(xml)
            paragraphs = []
            # Paragraph order includes table cells; formatting is not interpreted.
            for paragraph in root.iter(W + 'p'):
                parts = []
                for node in paragraph.iter():
                    if node.tag == W + 't':
                        parts.append(node.text or '')
                    elif node.tag == W + 'tab':
                        parts.append(' ')
                    elif node.tag in {W + 'br', W + 'cr'}:
                        parts.append('\n')
                if ''.join(parts).strip():
                    paragraphs.append(''.join(parts))
            text = '\n'.join(paragraphs)
        except (zipfile.BadZipFile, KeyError, ET.ParseError):
            raise ValueError('This is not a readable DOCX document. Resave it as .docx or TXT.')
        warnings.append('Only main-document text is extracted. Check tables, tracked edits, headers and speaker labels against the original.')
    elif suffix == '.pdf':
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ValueError('PDF extraction is not installed on this server.')
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise ValueError('Password-protected PDFs are not supported. Export an unlocked copy.')
            if len(reader.pages) > 100:
                raise ValueError('Use a PDF with no more than 100 pages.')
            pages, empty = [], []
            for index, page in enumerate(reader.pages):
                content = page.get_contents()
                if content and len(content.get_data()) > 5 * 1024 * 1024:
                    raise ValueError('A PDF page exceeds the safe extraction limit.')
                value = page.extract_text() or ''
                pages.append(value)
                if not value.strip():
                    empty.append(str(index + 1))
                if sum(len(x) for x in pages) > MAX_TEXT:
                    raise ValueError('Extracted text exceeds 150,000 characters. Split the meeting document.')
            text = '\n'.join(pages)
            if empty:
                warnings.append('No selectable text on page(s) ' + ', '.join(empty) + '. Image-only pages need OCR and are not imported.')
        except ValueError:
            raise
        except Exception:
            raise ValueError('This PDF could not be read. Export a text-based PDF or TXT copy.')
        warnings.append('PDF reading order and line breaks can differ from the original. Review and repair the preview before extraction.')
    elif suffix == '.doc':
        raise ValueError('Legacy .doc is not supported. Open it in Word and save as .docx.')
    else:
        raise ValueError('Supported documents: TXT, text-based PDF and DOCX. Audio transcription is not configured yet.')
    text = text.strip()
    if not text:
        raise ValueError('No readable text found. A scanned PDF needs OCR; an empty document cannot be imported.')
    if len(text) > MAX_TEXT:
        raise ValueError('Extracted text exceeds 150,000 characters. Split the meeting document.')
    return {'text': text, 'warnings': warnings, 'characters': len(text), 'format': suffix[1:]}
