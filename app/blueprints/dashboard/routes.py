from datetime import UTC, datetime

from flask import render_template, request
from flask_babel import gettext as _
from flask_login import login_required

from app.blueprints.dashboard import bp
from app.repositories.sales_repository import SalesRepository
from app.services.inventory_service import InventoryService
from app.services.opportunity_service import OpportunityService
from app.services.sales_service import SalesService


def _month_names() -> list[str]:
    return [
        _("Jan"), _("Feb"), _("Mar"), _("Apr"), _("May"), _("Jun"),
        _("Jul"), _("Aug"), _("Sep"), _("Oct"), _("Nov"), _("Dec"),
    ]


@bp.route("/")
@login_required
def index():
    sales_repo = SalesRepository()
    inventory_service = InventoryService()
    opportunity_service = OpportunityService()
    sales_service = SalesService()

    now = datetime.now(UTC)
    available_years = sales_repo.distinct_years() or [now.year]
    selected_year = request.args.get("year", type=int, default=available_years[0])
    if selected_year not in available_years:
        available_years = sorted({*available_years, selected_year}, reverse=True)
    selected_month = request.args.get("month", type=int)

    # Everything on this page is scoped to this same year (+ month, if one
    # is picked) — no metric or chart falls back to all-time data. See #30.
    sales_this_year = sales_repo.completed_in_year(selected_year)
    sales_this_period = (
        [s for s in sales_this_year if s.sale_date.month == selected_month]
        if selected_month
        else sales_this_year
    )

    stats = {
        "net_sales": sales_service.total_revenue(sales_this_period),
        "average_sale_total": sales_service.average_sale_total(sales_this_period),
        "average_bottles_per_sale": sales_service.average_bottles_per_sale(sales_this_period),
    }
    low_stock_items = inventory_service.low_stock_report()
    recent_opportunities = opportunity_service.open_opportunities()[:5]

    charts = {
        "product_sales": sales_service.sales_by_product(sales_this_period),
        "monthly_counts": sales_service.monthly_sales_counts(sales_this_year),
        "monthly_bottles": sales_service.monthly_bottles_sold(sales_this_year),
    }

    return render_template(
        "dashboard/index.html",
        stats=stats,
        low_stock_items=low_stock_items,
        recent_opportunities=recent_opportunities,
        charts=charts,
        available_years=available_years,
        selected_year=selected_year,
        selected_month=selected_month,
        month_names=_month_names(),
    )
