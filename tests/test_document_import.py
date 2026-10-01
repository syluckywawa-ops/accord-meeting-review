import base64
import io
import unittest
import zipfile
from pathlib import Path
from actionai.document_import import decode_file, extract_document
from actionai.imported_meetings import prepare_import, extract_rules


def word_bytes(xml):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        archive.writestr('word/document.xml', xml)
    return output.getvalue()


class DocumentImportTests(unittest.TestCase):
    def test_fictional_demo_pdf_reads_expected_commitments(self):
        path = Path(__file__).resolve().parents[1] / 'output/pdf/Accord_Test_Meeting.pdf'
        result = extract_document(path.name, path.read_bytes())
        self.assertEqual(result['format'], 'pdf')
        self.assertIn('Noah: Agreed. I can take that task.', result['text'])
        draft = extract_rules(prepare_import(result['text'], 'PDF smoke test'))
        self.assertEqual([i['owners'] for i in draft['action_items']], [['Alex'], ['Priya'], ['Mia']])
        self.assertTrue(all(i['deadline_text'] is None for i in draft['action_items']))

    def test_txt_and_encoding(self):
        data = 'Alex: I will send it.\n小林：我会核对数据。'.encode('utf-8-sig')
        result = extract_document('meeting.txt', data)
        self.assertIn('小林', result['text'])
        self.assertEqual(decode_file(base64.b64encode(data).decode()), data)

    def test_docx_paragraphs_and_table_cells(self):
        xml = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Alex: I will send the proposal.</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Jamie: I will review it.</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>'
        result = extract_document('meeting.docx', word_bytes(xml))
        self.assertEqual(result['text'], 'Alex: I will send the proposal.\nJamie: I will review it.')
        self.assertTrue(result['warnings'])

    def test_bad_inputs_are_rejected(self):
        for name, content in [('meeting.doc', b'old document'), ('meeting.docx', b'broken'), ('meeting.txt', b'\xff'), ('audio.mp3', b'audio')]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                extract_document(name, content)
        with self.assertRaises(ValueError):
            decode_file('not base64!')

    def test_xml_declarations_rejected(self):
        with self.assertRaises(ValueError):
            extract_document('meeting.docx', word_bytes('<!DOCTYPE x><x/>'))

    def test_empty_and_oversize_text(self):
        for content in [b' ', b'a' * 150001]:
            with self.assertRaises(ValueError):
                extract_document('meeting.txt', content)

    def test_real_pdf_text_and_blank_page(self):
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject, NameObject, DictionaryObject
        writer = PdfWriter()
        page = writer.add_blank_page(width=600, height=800)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        stream = DecodedStreamObject()
        stream.set_data(b'BT /F1 12 Tf 50 750 Td (Alex: I will send the proposal tomorrow.) Tj ET')
        page[NameObject('/Contents')] = writer._add_object(stream)
        writer.add_blank_page(width=600, height=800)
        output = io.BytesIO()
        writer.write(output)
        result = extract_document('meeting.pdf', output.getvalue())
        self.assertIn('Alex: I will send the proposal tomorrow.', result['text'])
        self.assertTrue(any('page(s) 2' in x for x in result['warnings']))


if __name__ == '__main__':
    unittest.main()
