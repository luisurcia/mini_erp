from flask import flash, redirect, render_template, url_for
from flask_babel import gettext as _
from flask_login import login_required

from app.blueprints.company import bp
from app.blueprints.company.forms import CompanySettingsForm, CustomerSegmentForm
from app.extensions import db
from app.models.company import Company
from app.models.customer_segment import CustomerSegment
from app.permissions import admin_required


@bp.route("/", methods=["GET", "POST"])
@login_required
@admin_required
def settings():
    company = Company.get_settings()
    form = CompanySettingsForm(obj=company)

    if form.validate_on_submit():
        company.tax_rate = form.tax_rate.data
        company.tax_enabled_default = form.tax_enabled_default.data
        company.product_short_name_enabled = form.product_short_name_enabled.data
        company.product_size_enabled = form.product_size_enabled.data
        company.product_sku_enabled = form.product_sku_enabled.data
        company.language = form.language.data
        company.currency_code = form.currency_code.data
        company.currency_symbol = form.currency_symbol.data
        company.currency_decimals = form.currency_decimals.data
        db.session.commit()
        flash(_("Company settings updated."), "success")
        return redirect(url_for("company.settings"))

    return render_template("company/settings.html", form=form)


@bp.route("/segments")
@login_required
@admin_required
def segments():
    customer_segments = CustomerSegment.query.order_by(CustomerSegment.id).all()
    return render_template("company/segments_list.html", segments=customer_segments)


@bp.route("/segments/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_segment():
    form = CustomerSegmentForm()

    if form.validate_on_submit():
        db.session.add(CustomerSegment(name=form.name.data, is_active=form.is_active.data))
        db.session.commit()
        flash(_("Segment '%(name)s' created.", name=form.name.data), "success")
        return redirect(url_for("company.segments"))

    return render_template("company/segment_form.html", form=form, mode="new")


@bp.route("/segments/<int:segment_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_segment(segment_id):
    segment = db.session.get(CustomerSegment, segment_id)
    if segment is None:
        flash(_("Segment not found."), "danger")
        return redirect(url_for("company.segments"))

    form = CustomerSegmentForm(obj=segment)

    if form.validate_on_submit():
        segment.name = form.name.data
        segment.is_active = form.is_active.data
        db.session.commit()
        flash(_("Segment '%(name)s' updated.", name=segment.name), "success")
        return redirect(url_for("company.segments"))

    return render_template(
        "company/segment_form.html", form=form, mode="edit", segment=segment
    )
