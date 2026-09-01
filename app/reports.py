"""PDF report generation. Kept out of any blueprint so it can be called
from a route and tested on its own. See #81."""

from datetime import date
from decimal import Decimal
from io import BytesIO

from flask_babel import gettext as _
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.display import format_money
from app.models.company import Company

_INK = colors.HexColor("#1a1816")
_HEADER_BG = colors.HexColor("#e7decf")


def build_unpaid_sales_pdf(sales, generated_on: date | None = None) -> bytes:
    """Render the list of unpaid sales as a one-page PDF the partners use
    for weekly collections. `sales` should already be in the order to
    print (oldest first). Text follows the current request's locale."""
    generated_on = generated_on or date.today()
    company = Company.get_settings()
    styles = getSampleStyleSheet()
    cell = styles["BodyText"]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=_("Unpaid sales"),
    )

    title_style = styles["Title"]
    title_style.textColor = _INK
    story = [
        Paragraph(f"{company.name} — {_('Unpaid sales')}", title_style),
        Paragraph(
            _("Generated on %(date)s", date=generated_on.isoformat()),
            styles["Normal"],
        ),
        Spacer(1, 8 * mm),
    ]

    header = [
        "#",
        _("Date"),
        _("Customer"),
        _("Invoice #"),
        _("Tax"),
        _("Days overdue"),
        _("Total"),
    ]
    rows = [header]
    total = Decimal("0")
    for sale in sales:
        total += sale.total_amount
        overdue = max((generated_on - sale.sale_date.date()).days, 0)
        rows.append(
            [
                str(sale.id),
                sale.sale_date.strftime("%Y-%m-%d"),
                Paragraph(sale.customer.name, cell),
                sale.invoice_number or "—",
                _("Yes") if sale.tax_applied else _("No"),
                str(overdue),
                format_money(sale.total_amount),
            ]
        )

    rows.append(
        [
            "",
            "",
            Paragraph(
                _("%(count)s sales", count=len(sales)), cell
            ),
            "",
            "",
            _("Total to collect"),
            format_money(total),
        ]
    )

    table = Table(
        rows,
        colWidths=[12 * mm, 24 * mm, 52 * mm, 26 * mm, 14 * mm, 20 * mm, 26 * mm],
        repeatRows=1,
    )
    last = len(rows) - 1
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, -1), _INK),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (3, 0), (5, -1), "CENTER"),
                ("ALIGN", (6, 0), (6, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, 0), 0.75, _INK),
                ("LINEBELOW", (0, 1), (-1, last - 1), 0.25, colors.HexColor("#c9c4b8")),
                ("LINEABOVE", (0, last), (-1, last), 0.75, _INK),
                ("FONTNAME", (5, last), (-1, last), "Helvetica-Bold"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)

    if not sales:
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(_("No unpaid sales."), styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()
