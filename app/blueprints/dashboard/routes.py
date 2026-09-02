from datetime import UTC, datetime

from flask import render_template, request
from flask_babel import gettext as _
from flask_babel import ngettext
from flask_login import login_required

from app.blueprints.dashboard import bp
from app.repositories.sales_repository import SalesRepository
from app.services.inventory_service import InventoryService
from app.services.sales_service import SalesService


def _month_names() -> list[str]:
    return [
        _("Jan"), _("Feb"), _("Mar"), _("Apr"), _("May"), _("Jun"),
        _("Jul"), _("Aug"), _("Sep"), _("Oct"), _("Nov"), _("Dec"),
    ]


def _filter_label(selected: list, total: int, all_text: str, some_text) -> str:
    """Text on a multi-select dropdown's toggle: 'all', the single value,
    or 'N selected'."""
    if not selected or len(selected) == total:
        return all_text
    if len(selected) == 1:
        return str(selected[0])
    return some_text(len(selected))


@bp.route("/")
@login_required
def index():
    sales_repo = SalesRepository()
    inventory_service = InventoryService()
    sales_service = SalesService()

    now = datetime.now(UTC)
    available_years = sales_repo.distinct_years() or [now.year]
    month_names = _month_names()

    # Multi-select filters (#83, phase A): pick any set of years and any
    # set of months; everything aggregates over the union. Empty = all.
    selected_years = sorted(
        (y for y in request.args.getlist("year", type=int) if y in available_years),
        reverse=True,
    )
    selected_months = sorted(
        m for m in request.args.getlist("month", type=int) if 1 <= m <= 12
    )

    sales_scope = sales_repo.completed_in_years(selected_years)
    sales_this_period = [
        s
        for s in sales_scope
        if not selected_months or s.sale_date.month in selected_months
    ]

    # The 6 metrics Scoby tracks in their Excel (#91), in that order.
    stats = {
        "total_paid": sales_service.total_revenue(sales_this_period),
        "total_bottles": sales_service.total_bottles(sales_this_period),
        "ticket_count": len(sales_this_period),
        "invoice_count": sales_service.taxed_sales_count(sales_this_period),
        "average_bottles_per_sale": sales_service.average_bottles_per_sale(sales_this_period),
        "average_unit_price": sales_service.average_unit_price(sales_this_period),
    }
    low_stock_items = inventory_service.low_stock_report()

    # Every chart honours both filters: the per-month charts show only the
    # selected months (all 12 when none is picked), summed across the
    # selected years (phase B turns them into one series per year).
    chart_months = selected_months or list(range(1, 13))
    monthly_counts = sales_service.monthly_sales_counts(sales_this_period)
    monthly_bottles = sales_service.monthly_bottles_sold(sales_this_period)
    charts = {
        "product_sales": sales_service.sales_by_product(sales_this_period),
        "monthly_counts": [monthly_counts[m - 1] for m in chart_months],
        "monthly_bottles": [monthly_bottles[m - 1] for m in chart_months],
    }
    chart_month_labels = [month_names[m - 1] for m in chart_months]

    year_label = _filter_label(
        selected_years,
        len(available_years),
        _("All years"),
        lambda n: ngettext("%(num)s year", "%(num)s years", n),
    )
    if len(selected_months) == 1:
        month_label = month_names[selected_months[0] - 1]
    else:
        month_label = _filter_label(
            selected_months,
            12,
            _("All months"),
            lambda n: ngettext("%(num)s month", "%(num)s months", n),
        )
    charts_years_label = (
        ", ".join(str(y) for y in selected_years) if selected_years else _("all years")
    )

    return render_template(
        "dashboard/index.html",
        stats=stats,
        low_stock_items=low_stock_items,
        charts=charts,
        month_names=month_names,
        chart_month_labels=chart_month_labels,
        year_options=[(y, str(y), y in selected_years) for y in available_years],
        month_options=[
            (i, name, i in selected_months)
            for i, name in enumerate(month_names, start=1)
        ],
        year_label=year_label,
        month_label=month_label,
        charts_years_label=charts_years_label,
    )
