"""Generate disposable synthetic documents for browser import checks."""
import io
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject, DictionaryObject
import zipfile

folder = Path(__file__).resolve().parents[1] / 'outputs/import-smoke-test'
folder.mkdir(parents=True, exist_ok=True)
writer = PdfWriter()
page = writer.add_blank_page(width=600, height=800)
font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
stream = DecodedStreamObject()
stream.set_data(b'BT /F1 12 Tf 50 750 Td (Alex: I will send the proposal tomorrow.) Tj 0 -20 Td (Jamie: I will review the figures by Friday.) Tj ET')
page[NameObject('/Contents')] = writer._add_object(stream)
writer.write(folder / 'synthetic_meeting.pdf')
xml = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Alex: I will send the proposal tomorrow.</w:t></w:r></w:p><w:p><w:r><w:t>Jamie: I will review the figures by Friday.</w:t></w:r></w:p></w:body></w:document>'
with zipfile.ZipFile(folder / 'synthetic_meeting.docx', 'w') as archive:
    archive.writestr('word/document.xml', xml)
print(folder)
