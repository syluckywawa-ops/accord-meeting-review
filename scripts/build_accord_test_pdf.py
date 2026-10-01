"""Build a fictional product smoke-test document, not formal experiment data."""
from pathlib import Path
import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'output/pdf/Accord_Test_Meeting.pdf'
TURNS = [
    ('Sam', 'Welcome to our digital onboarding planning meeting.'),
    ('Alex', 'The draft checklist was reviewed yesterday.'),
    ('Sam', 'Today we need to agree on next steps for the onboarding pilot.'),
    ('Alex', 'I will send the revised onboarding checklist by Friday.'),
    ('Priya', 'I will review the checklist and share comments by Monday.'),
    ('Mia', 'I will update the help page text before the next meeting.'),
    ('Sam', 'Noah, please check the FAQ links before the next meeting.'),
    ('Noah', 'Agreed. I can take that task.'),
    ('Mia', 'Maybe we could add a chatbot later. This is only a suggestion.'),
    ('Priya', 'We have not agreed to build a chatbot or assign that work.'),
    ('Sam', 'The pilot must use fictional accounts, not real customer data.'),
    ('Alex', 'Understood. There are no additional commitments today.'),
]


def build():
    fonts = Path(reportlab.__file__).resolve().parent / 'fonts'
    pdfmetrics.registerFont(TTFont('AccordSans', str(fonts / 'Vera.ttf')))
    pdfmetrics.registerFont(TTFont('AccordBold', str(fonts / 'VeraBd.ttf')))
    pdfmetrics.registerFont(TTFont('AccordSerif', str(fonts / 'Vera.ttf')))
    pdfmetrics.registerFontFamily('AccordSans', normal='AccordSans', bold='AccordBold')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=48,
                            leftMargin=48, topMargin=46, bottomMargin=45,
                            title='Accord - Fictional Test Meeting', author='Accord project')
    heading = ParagraphStyle('heading', fontName='AccordSerif', fontSize=25,
                             leading=32, textColor=colors.HexColor('#305638'))
    sub = ParagraphStyle('sub', fontName='AccordSans', fontSize=9, leading=15,
                         textColor=colors.HexColor('#667A58'))
    body = ParagraphStyle('turn', fontName='AccordSans', fontSize=9.5, leading=17,
                          spaceAfter=14, textColor=colors.HexColor('#34493B'))
    blocks = [Paragraph('Accord test meeting', heading), Spacer(1, 8),
              Paragraph('Digital onboarding pilot | Fictional transcript', sub),
              Spacer(1, 5), Paragraph('Product smoke test only. Not formal evaluation data.', sub),
              Spacer(1, 18), HRFlowable(width='100%', color=colors.HexColor('#DAE4D0')),
              Spacer(1, 22)]
    for speaker, text in TURNS:
        blocks.append(Paragraph(f'<b>{speaker}:</b> {text}', body))

    def footer(canvas, document):
        canvas.setFont('AccordSans', 7)
        canvas.setFillColor(colors.HexColor('#738568'))
        canvas.drawString(48, 27, 'FICTIONAL MEETING - NO REAL CUSTOMER INFORMATION')
        canvas.drawRightString(A4[0] - 48, 27, str(document.page))

    doc.build(blocks, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == '__main__':
    build()
