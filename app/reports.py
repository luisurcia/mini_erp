"""PDF report generation. Kept out of any blueprint so it can be called
from a route and tested on its own. See #81."""

from datetime import date
from decimal import Decimal
from io import BytesIO

from flask_babel import gettext as _
from flask_babel import ngettext
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
_GROUP_BG = colors.HexColor("#f1eadd")
_HAIRLINE = colors.HexColor("#c9c4b8")


def build_unpaid_sales_pdf(sales, generated_on: date | None = None) -> bytes:
    """Render the unpaid sales as a one-page PDF the partners use for
    weekly collections (#81). Sales are grouped by customer (#88), each
    group oldest first, groups ordered by the customer's oldest debt.
    Text follows the current request's locale."""
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

    ordered_sales = sorted(sales, key=lambda sale: sale.sale_date)
    groups: dict[int, list] = {}
    for sale in ordered_sales:
        groups.setdefault(sale.customer_id, []).append(sale)
    ordered_groups = sorted(groups.values(), key=lambda g: g[0].sale_date)

    def _overdue(sale) -> int:
        return max((generated_on - sale.sale_date.date()).days, 0)

    def _sale_count(n: int) -> str:
        return ngettext("%(num)s sale", "%(num)s sales", n)

    rows = [
        [
            _("Date"),
            _("Invoice #"),
            _("Tax"),
            _("Days overdue"),
            _("Total"),
        ]
    ]
    customer_header_rows: list[int] = []
    subtotal_rows: list[int] = []
    grand_total = Decimal("0")

    for group in ordered_groups:
        customer_header_rows.append(len(rows))
        rows.append([Paragraph(group[0].customer.name, cell), "", "", "", ""])
        group_total = Decimal("0")
        for sale in group:
            group_total += sale.total_amount
            rows.append(
                [
                    sale.sale_date.strftime("%Y-%m-%d"),
                    sale.invoice_number or "—",
                    _("Yes") if sale.tax_applied else _("No"),
                    str(_overdue(sale)),
                    format_money(sale.total_amount),
                ]
            )
        grand_total += group_total
        subtotal_rows.append(len(rows))
        rows.append(
            [
                _sale_count(len(group)),
                "",
                "",
                _("Subtotal"),
                format_money(group_total),
            ]
        )

    last = len(rows)
    rows.append(
        [
            _sale_count(len(ordered_sales)),
            "",
            "",
            _("Total to collect"),
            format_money(grand_total),
        ]
    )

    table = Table(
        rows,
        colWidths=[28 * mm, 46 * mm, 18 * mm, 30 * mm, 32 * mm],
        repeatRows=1,
    )
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, -1), _INK),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (3, -1), "CENTER"),
        ("ALIGN", (4, 0), (4, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, _INK),
        ("LINEABOVE", (0, last), (-1, last), 0.75, _INK),
        ("FONTNAME", (3, last), (-1, last), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for r in customer_header_rows:
        style.append(("SPAN", (0, r), (-1, r)))
        style.append(("BACKGROUND", (0, r), (-1, r), _GROUP_BG))
        style.append(("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"))
    for r in subtotal_rows:
        style.append(("FONTNAME", (3, r), (-1, r), "Helvetica-Bold"))
        style.append(("LINEABOVE", (0, r), (-1, r), 0.25, _HAIRLINE))
    table.setStyle(TableStyle(style))
    story.append(table)

    if not ordered_sales:
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(_("No unpaid sales."), styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()
