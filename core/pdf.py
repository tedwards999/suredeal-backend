from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _build_document_pdf(title, doc_id, customer, date_issued, secondary_date_label, secondary_date, notes, line_items):
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f'{title} #{doc_id}', styles['Title']),
        Spacer(1, 12),
        Paragraph(f'Customer: {customer.name} {customer.surname} ({customer.company.company_name})', styles['Normal']),
        Paragraph(f'Date issued: {date_issued}', styles['Normal']),
        Paragraph(f'{secondary_date_label}: {secondary_date}', styles['Normal']),
        Spacer(1, 12),
    ]
    if notes:
        elements.append(Paragraph(f'Notes: {notes}', styles['Normal']))
        elements.append(Spacer(1, 12))

    table_data = [['Product', 'Quantity', 'Price', 'Discount', 'Line total']]
    total = Decimal('0')
    for item in line_items:
        table_data.append([item.product.name, str(item.quantity), str(item.price), str(item.discount), str(item.line_total)])
        total += item.line_total
    table_data.append(['', '', '', 'Total', str(total)])

    table = Table(table_data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
    ]))
    elements.append(table)

    pdf.build(elements)
    buffer.seek(0)
    return buffer


def build_quote_pdf(quote):
    return _build_document_pdf(
        title='Quotation',
        doc_id=quote.pk,
        customer=quote.customer,
        date_issued=quote.date_issued,
        secondary_date_label='Expiry date',
        secondary_date=quote.expiry_date,
        notes=quote.notes,
        line_items=quote.quotelineitem_set.select_related('product').all(),
    )


def build_invoice_pdf(invoice):
    return _build_document_pdf(
        title='Invoice',
        doc_id=invoice.pk,
        customer=invoice.customer,
        date_issued=invoice.date_issued,
        secondary_date_label='Due date',
        secondary_date=invoice.due_date,
        notes=invoice.notes,
        line_items=invoice.invoicelineitem_set.select_related('product').all(),
    )
