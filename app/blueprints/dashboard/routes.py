from datetime import datetime, timezone

from flask_login import login_required

from app.blueprints.dashboard import bp
from app.repositories.product_repository import ProductRepository
from app.repositories.sales_repository import SalesRepository
from app.services.inventory_service import InventoryService
from app.services.opportunity_service import OpportunityService
from app.services.sales_service import SalesService
from flask import render_template


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

    stats = {
        "active_products": len(product_repo.get_active()),
        "low_stock_count": len(inventory_service.low_stock_report()),
        "open_opportunities": len(opportunity_service.open_opportunities()),
        "revenue_this_month": sales_service.total_revenue(sales_this_month),
    }
    low_stock_items = inventory_service.low_stock_report()
    recent_opportunities = opportunity_service.open_opportunities()[:5]

    return render_template(
        "dashboard/index.html",
        stats=stats,
        low_stock_items=low_stock_items,
        recent_opportunities=recent_opportunities,
    )
