from datetime import datetime, timezone

from flask import render_template, request
from flask_babel import gettext as _
from flask_login import login_required

from app.blueprints.dashboard import bp
from app.repositories.product_repository import ProductRepository
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
    product_repo = ProductRepository()
    sales_repo = SalesRepository()
    inventory_service = InventoryService()
    opportunity_service = OpportunityService()
    sales_service = SalesService()

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    sales_this_month = sales_repo.completed_between(month_start, now)

    available_years = sales_repo.distinct_years() or [now.year]
    selected_year = request.args.get("year", type=int, default=available_years[0])
    if selected_year not in available_years:
        available_years = sorted({*available_years, selected_year}, reverse=True)
    selected_month = request.args.get("month", type=int)

    sales_this_year = sales_repo.completed_in_year(selected_year)
    product_sales_source = (
        [s for s in sales_this_year if s.sale_date.month == selected_month]
        if selected_month
        else sales_this_year
    )

    stats = {
        "active_products": len(product_repo.get_active()),
        "low_stock_count": len(inventory_service.low_stock_report()),
        "open_opportunities": len(opportunity_service.open_opportunities()),
        "revenue_this_month": sales_service.total_revenue(sales_this_month),
        "invoice_count": sales_service.invoice_count(sales_this_year),
        "average_sale_total": sales_service.average_sale_total(sales_this_year),
        "total_sold_year": sales_service.total_revenue(sales_this_year),
    }
    low_stock_items = inventory_service.low_stock_report()
    recent_opportunities = opportunity_service.open_opportunities()[:5]

    charts = {
        "product_sales": sales_service.sales_by_product(product_sales_source),
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
