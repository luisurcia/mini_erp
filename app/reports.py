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

from app.display import format_money, product_label
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


def dispatch_line_items(sale) -> list[tuple[int, str]]:
    """The sale's lines as they appear on the dispatch ticket: one entry
    per product with the quantities summed across warehouses (#114),
    ordered by product label. Warehouse and price are dropped — they don't
    belong on a picking/delivery slip."""
    quantities: dict[int, int] = {}
    labels: dict[int, str] = {}
    for item in sale.items:
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity
        labels.setdefault(item.product_id, product_label(item.product))
    return [
        (quantities[pid], labels[pid])
        for pid in sorted(labels, key=lambda pid: labels[pid].lower())
    ]


def build_dispatch_ticket_pdf(sale, generated_on: date | None = None) -> bytes:
    """Render one sale's dispatch ticket as an A4 PDF (#111): who and where
    to deliver, and what — quantities and product names, no prices. Handed
    to the courier or attached to the box. Text follows the request locale.
    """
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
        title=_("Dispatch ticket"),
    )

    title_style = styles["Title"]
    title_style.textColor = _INK
    label_style = styles["Normal"]

    story = [
        Paragraph(f"{company.name} — {_('Dispatch ticket')}", title_style),
        Paragraph(
            _("Generated on %(date)s", date=generated_on.isoformat()),
            label_style,
        ),
        Spacer(1, 6 * mm),
    ]

    sale_ref = _("Sale #%(id)s", id=sale.id)
    if sale.invoice_number:
        sale_ref += f" · {_('Invoice #')} {sale.invoice_number}"
    story.append(Paragraph(sale_ref, styles["Heading3"]))
    story.append(
        Paragraph(
            f"{_('Date:')} {sale.sale_date.strftime('%Y-%m-%d')}", label_style
        )
    )
    story.append(Spacer(1, 4 * mm))

    customer = sale.customer
    story.append(Paragraph(_("Delivery"), styles["Heading4"]))
    for label, value in (
        (_("Customer:"), customer.name),
        (_("RUT:"), customer.rut or "—"),
        (_("Email:"), customer.email or "—"),
        (_("Phone:"), customer.phone or "—"),
        (_("Address:"), customer.shipping_address_line or "—"),
    ):
        story.append(Paragraph(f"<b>{label}</b> {value}", label_style))
    story.append(Spacer(1, 6 * mm))

    line_items = dispatch_line_items(sale)
    rows = [[_("Units"), _("Product")]]
    for quantity, label in line_items:
        rows.append([str(quantity), Paragraph(label, cell)])
    rows.append([str(sum(q for q, _label in line_items)), _("Total units")])

    last = len(rows) - 1
    table = Table(rows, colWidths=[24 * mm, 150 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, -1), _INK),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, 0), 0.75, _INK),
                ("LINEABOVE", (0, last), (-1, last), 0.75, _INK),
                ("FONTNAME", (0, last), (-1, last), "Helvetica-Bold"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(table)

    if sale.notes:
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(f"<b>{_('Notes:')}</b> {sale.notes}", label_style))

    doc.build(story)
    return buffer.getvalue()
