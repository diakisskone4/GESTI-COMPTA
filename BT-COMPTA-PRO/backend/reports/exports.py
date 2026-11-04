"""Génération des documents PDF (ReportLab) et Excel (OpenPyXL).

Format d'entrée commun (« document ») :
{
  'title': str, 'subtitle': str,
  'sections': [ {'title': str, 'lines': [str]} | {'title': str, 'columns': [...], 'rows': [[...]], 'footer': [...]} ]
}
"""
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

BRAND_DARK = '#102B55'
BRAND_BLUE = '#1683D8'
BRAND_GREEN = '#16A36A'
LIGHT = '#F3F5F8'


def calculation_document(meta: dict, inputs: list[tuple[str, str]], output: dict) -> dict:
    sections = []
    if inputs:
        sections.append({'title': 'Données utilisées', 'columns': ['Donnée', 'Valeur'], 'rows': [list(i) for i in inputs]})
    if output.get('formulas'):
        sections.append({'title': 'Formules', 'lines': output['formulas']})
    if output.get('steps'):
        sections.append({'title': 'Étapes de calcul', 'columns': ['Étape', 'Calcul', 'Résultat'],
                         'rows': [[s['label'], s['detail'], s['value']] for s in output['steps']]})
    if output.get('results'):
        sections.append({'title': 'Résultats', 'columns': ['Indicateur', 'Valeur'],
                         'rows': [[x['label'], x['value']] for x in output['results']]})
    for t in output.get('tables', []):
        sections.append({'title': t['title'], 'columns': t['columns'], 'rows': t['rows'], 'footer': t.get('footer')})
    if output.get('entries'):
        sections.append({'title': 'Écritures comptables', 'columns': ['Opération', 'Compte', 'Libellé', 'Débit', 'Crédit'],
                         'rows': [[e['group'], e['account'], e['label'], e['debit'], e['credit']] for e in output['entries']]})
    if output.get('interpretation'):
        sections.append({'title': 'Interprétation', 'lines': output['interpretation']})
    if output.get('warnings'):
        sections.append({'title': 'Points d\'attention', 'lines': output['warnings']})
    return {'title': meta['title'], 'subtitle': f'{meta["level"]} — {meta["category"]}', 'sections': sections}


def build_pdf(doc: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    wide = any(len(s.get('columns', [])) > 6 for s in doc['sections'])
    pagesize = landscape(A4) if wide else A4
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=pagesize, leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm, title=doc['title'], author='BT COMPTA PRO')
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle('h1', parent=styles['Title'], textColor=colors.HexColor(BRAND_DARK), alignment=TA_LEFT, fontSize=18, spaceAfter=2)
    sub = ParagraphStyle('sub', parent=styles['Normal'], textColor=colors.HexColor(BRAND_BLUE), fontSize=10, spaceAfter=10)
    h2 = ParagraphStyle('h2', parent=styles['Heading3'], textColor=colors.HexColor(BRAND_DARK), spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle('body', parent=styles['Normal'], fontSize=9, leading=12)
    cell = ParagraphStyle('cell', parent=body, fontSize=8, leading=10)
    head = ParagraphStyle('head', parent=cell, textColor=colors.white, fontName='Helvetica-Bold')

    story = [Paragraph('BT COMPTA PRO', sub), Paragraph(escape(doc['title']), h1)]
    if doc.get('subtitle'):
        story.append(Paragraph(escape(doc['subtitle']), sub))
    width = pagesize[0] - 28 * mm
    for section in doc['sections']:
        story.append(Paragraph(escape(section['title']), h2))
        if 'columns' in section:
            data = [[Paragraph(escape(str(c)), head) for c in section['columns']]]
            data += [[Paragraph(escape(str(v)), cell) for v in row] for row in section['rows']]
            if section.get('footer'):
                data.append([Paragraph('<b>%s</b>' % escape(str(v)), cell) for v in section['footer']])
            n = len(section['columns'])
            table = Table(data, colWidths=[width / n] * n, repeatRows=1)
            style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BRAND_DARK)),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(LIGHT)]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]
            if section.get('footer'):
                style.append(('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#DCEBFA')))
            table.setStyle(TableStyle(style))
            story.append(table)
        else:
            for line in section.get('lines', []):
                story.append(Paragraph('• ' + escape(str(line)), body))
        story.append(Spacer(1, 4))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f'Document généré le {datetime.now():%d/%m/%Y à %H:%M} — BT COMPTA PRO. '
                           'Usage pédagogique : vérifier les règles fiscales en vigueur au Mali.', cell))
    pdf.build(story)
    return buffer.getvalue()


def _to_number(value):
    """Convertit « 1 234,50 » en nombre pour Excel ; renvoie la valeur d'origine sinon."""
    if not isinstance(value, str):
        return value
    text = value.replace(' ', '').replace('\xa0', '').replace(' ', '').replace(',', '.')
    try:
        if text and text.lstrip('-').replace('.', '', 1).isdigit():
            return float(text)
    except ValueError:
        pass
    return value


def build_xlsx(doc: dict) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = 'BT COMPTA PRO'
    ws.append(['BT COMPTA PRO'])
    ws['A1'].font = Font(bold=True, color=BRAND_BLUE[1:], size=11)
    ws.append([doc['title']])
    ws['A2'].font = Font(bold=True, color=BRAND_DARK[1:], size=15)
    if doc.get('subtitle'):
        ws.append([doc['subtitle']])
    header_fill = PatternFill('solid', fgColor=BRAND_DARK[1:])
    widths: dict[int, int] = {}
    for section in doc['sections']:
        ws.append([])
        ws.append([section['title']])
        ws.cell(ws.max_row, 1).font = Font(bold=True, color=BRAND_DARK[1:], size=12)
        if 'columns' in section:
            ws.append(section['columns'])
            for i in range(1, len(section['columns']) + 1):
                c = ws.cell(ws.max_row, i)
                c.font = Font(bold=True, color='FFFFFF')
                c.fill = header_fill
                c.alignment = Alignment(wrap_text=True, vertical='center')
            for row in section['rows']:
                ws.append([_to_number(v) for v in row])
            if section.get('footer'):
                ws.append([_to_number(v) for v in section['footer']])
                for i in range(1, len(section['footer']) + 1):
                    ws.cell(ws.max_row, i).font = Font(bold=True)
            for row in [section['columns'], *section['rows']]:
                for i, v in enumerate(row, start=1):
                    widths[i] = max(widths.get(i, 10), min(60, len(str(v)) + 2))
        else:
            for line in section.get('lines', []):
                ws.append([line])
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, float):
                c.number_format = '#,##0.00'
    for i, w in widths.items():
        ws.column_dimensions[get_column_letter(i)].width = w
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
