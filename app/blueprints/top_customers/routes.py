from flask import render_template, request
from flask_babel import gettext as _
from flask_login import login_required

from app.blueprints.top_customers import bp
from app.models.customer_segment import CustomerSegment
from app.models.user import User
from app.permissions import module_required
from app.repositories.sales_repository import SalesRepository
from app.services.sales_service import SalesService

ALL_TIME = "all"


def _month_names() -> list[str]:
    return [
        _("Jan"), _("Feb"), _("Mar"), _("Apr"), _("May"), _("Jun"),
        _("Jul"), _("Aug"), _("Sep"), _("Oct"), _("Nov"), _("Dec"),
    ]


@bp.route("/")
@login_required
@module_required(User.MODULE_TOP_CUSTOMERS)
def index():
    sales_repo = SalesRepository()
    sales_service = SalesService()

    available_years = sales_repo.distinct_years()
    default_year = str(available_years[0]) if available_years else ALL_TIME
    selected_year = request.args.get("year", default=default_year)
    selected_month = None

    if selected_year == ALL_TIME:
        sales = sales_repo.completed_all()
    else:
        selected_year = int(selected_year)
        if selected_year not in available_years:
            available_years = sorted({*available_years, selected_year}, reverse=True)
        sales_this_year = sales_repo.completed_in_year(selected_year)
        selected_month = request.args.get("month", type=int)
        sales = (
            [s for s in sales_this_year if s.sale_date.month == selected_month]
            if selected_month
            else sales_this_year
        )

    # Segment filter — independent of the year/month scope, so it also
    # applies to the All-time view (unlike month). See #40.
    segments = (
        CustomerSegment.query.filter_by(is_active=True).order_by(CustomerSegment.id).all()
    )
    selected_segment = request.args.get("segment", type=int)
    if selected_segment:
        sales = [s for s in sales if s.customer.segment_id == selected_segment]

    top_customers = sales_service.top_customers_by_consumption(
        sales,
        limit=10,
        last_purchase_by_customer=sales_repo.last_purchase_by_customer(),
    )

    return render_template(
        "top_customers/index.html",
        top_customers=top_customers,
        available_years=available_years,
        selected_year=selected_year,
        selected_month=selected_month,
        month_names=_month_names(),
        all_time_value=ALL_TIME,
        segments=segments,
        selected_segment=selected_segment,
    )
