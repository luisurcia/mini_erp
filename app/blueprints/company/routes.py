from flask import flash, redirect, render_template, url_for
from flask_login import login_required

from app.blueprints.company import bp
from app.blueprints.company.forms import CompanySettingsForm
from app.extensions import db
from app.models.company import Company
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
        db.session.commit()
        flash("Company settings updated.", "success")
        return redirect(url_for("company.settings"))

    return render_template("company/settings.html", form=form)
