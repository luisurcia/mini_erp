from collections import defaultdict
from datetime import UTC, datetime

from flask import render_template, request
from flask_babel import gettext as _
from flask_babel import ngettext
from flask_login import login_required

from app.blueprints.dashboard import bp
from app.repositories.sales_repository import SalesRepository
from app.services.inventory_service import InventoryService
from app.services.sales_service import SalesService

# One colour per period in comparison mode; cycles if there are more
# periods than colours.
PERIOD_COLORS = [
    "#e27ca6", "#2e8c93", "#e3b23c", "#e0762e", "#a34a63", "#9a968c",
    "#c9648d", "#1a1816",
]


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


def _period_stats(sales_service: SalesService, sales: list) -> dict:
    """The 6 Excel metrics for one set of sales (#91)."""
    return {
        "total_paid": sales_service.total_revenue(sales),
        "total_bottles": sales_service.total_bottles(sales),
        "ticket_count": len(sales),
        "invoice_count": sales_service.taxed_sales_count(sales),
        "average_bottles_per_sale": sales_service.average_bottles_per_sale(sales),
        "average_unit_price": sales_service.average_unit_price(sales),
    }


def _pct_change(old, new) -> float | None:
    old, new = float(old), float(new)
    if old == 0:
        return None
    return (new - old) / old * 100.0


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

    # Comparison mode (#83, phase B): one period per selected year (each
    # scoped to the selected months), shown side by side. Needs 2+ years.
    compare_requested = request.args.get("compare") == "1"
    compare = compare_requested and len(selected_years) >= 2

    sales_scope = sales_repo.completed_in_years(selected_years)
    sales_this_period = [
        s
        for s in sales_scope
        if not selected_months or s.sale_date.month in selected_months
    ]

    metric_defs = [
        ("total_paid", _("Total paid value"), "money"),
        ("total_bottles", _("Total bottles"), "int"),
        ("ticket_count", _("Number of tickets"), "int"),
        ("invoice_count", _("Number of invoices"), "int"),
        ("average_bottles_per_sale", _("Average bottles per sale"), "float1"),
        ("average_unit_price", _("Average net unit price"), "money"),
    ]

    stats = _period_stats(sales_service, sales_this_period)
    low_stock_items = inventory_service.low_stock_report()

    # The per-month charts show only the selected months (all 12 when none
    # is picked); non-compare mode sums them across the selected years.
    chart_months = selected_months or list(range(1, 13))
    chart_month_labels = [month_names[m - 1] for m in chart_months]

    periods: list[dict] = []
    deltas: dict | None = None
    compare_charts: dict | None = None
    charts: dict | None = None

    if compare:
        by_year: dict[int, list] = defaultdict(list)
        for sale in sales_scope:
            by_year[sale.sale_date.year].append(sale)

        for year in sorted(selected_years):  # chronological, so Δ reads left→right
            period_sales = [
                s
                for s in by_year.get(year, [])
                if not selected_months or s.sale_date.month in selected_months
            ]
            if len(selected_months) == 1:
                label = f"{month_names[selected_months[0] - 1]} {year}"
            else:
                label = str(year)
            periods.append(
                {
                    "year": year,
                    "label": label,
                    "stats": _period_stats(sales_service, period_sales),
                    "_sales": period_sales,
                }
            )

        if len(periods) == 2:
            first, last = periods[0]["stats"], periods[1]["stats"]
            deltas = {key: _pct_change(first[key], last[key]) for key, _l, _f in metric_defs}

        colors = [PERIOD_COLORS[i % len(PERIOD_COLORS)] for i in range(len(periods))]

        tickets_ds, bottles_ds = [], []
        for period, color in zip(periods, colors, strict=True):
            monthly_counts = sales_service.monthly_sales_counts(period["_sales"])
            monthly_bottles = sales_service.monthly_bottles_sold(period["_sales"])
            tickets_ds.append(
                {
                    "label": period["label"],
                    "data": [monthly_counts[m - 1] for m in chart_months],
                    "backgroundColor": color,
                }
            )
            bottles_ds.append(
                {
                    "label": period["label"],
                    "data": [monthly_bottles[m - 1] for m in chart_months],
                    "backgroundColor": color,
                }
            )

        # Grouped product bar: products on the x-axis (union, ordered by
        # total across every period), one bar per period.
        product_totals: dict[str, float] = defaultdict(float)
        short_by_name: dict[str, str] = {}
        per_period_products: list[dict[str, float]] = []
        for period in periods:
            by_product: dict[str, float] = {}
            for row in sales_service.sales_by_product(period["_sales"]):
                by_product[row["product"]] = row["amount"]
                short_by_name[row["product"]] = row["product_short"]
                product_totals[row["product"]] += row["amount"]
            per_period_products.append(by_product)
        product_names = [
            name for name, _total in sorted(
                product_totals.items(), key=lambda kv: kv[1], reverse=True
            )
        ]
        product_ds = [
            {
                "label": period["label"],
                "data": [per_period_products[i].get(name, 0) for name in product_names],
                "backgroundColor": color,
            }
            for i, (period, color) in enumerate(zip(periods, colors, strict=True))
        ]

        compare_charts = {
            "month_labels": chart_month_labels,
            "tickets": tickets_ds,
            "bottles": bottles_ds,
            "products": [short_by_name.get(name, name) for name in product_names],
            "product_sales": product_ds,
        }
        # Don't leak Sale objects into the template context.
        for period in periods:
            del period["_sales"]
    else:
        monthly_counts = sales_service.monthly_sales_counts(sales_this_period)
        monthly_bottles = sales_service.monthly_bottles_sold(sales_this_period)
        charts = {
            "product_sales": sales_service.sales_by_product(sales_this_period),
            "monthly_counts": [monthly_counts[m - 1] for m in chart_months],
            "monthly_bottles": [monthly_bottles[m - 1] for m in chart_months],
        }

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
        compare=compare,
        compare_requested=compare_requested,
        stats=stats,
        metric_defs=metric_defs,
        periods=periods,
        deltas=deltas,
        compare_charts=compare_charts,
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
