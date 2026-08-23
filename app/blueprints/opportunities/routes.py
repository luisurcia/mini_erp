from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.blueprints.opportunities import bp
from app.blueprints.opportunities.forms import OpportunityForm, StageForm
from app.exceptions import MiniErpError
from app.models.opportunity import Opportunity
from app.permissions import editor_required
from app.repositories.customer_repository import CustomerRepository
from app.repositories.opportunity_repository import OpportunityRepository
from app.repositories.product_repository import ProductRepository
from app.services.opportunity_service import OpportunityService


@bp.route("/")
@login_required
def index():
    stage_filter = request.args.get("stage")
    repo = OpportunityRepository()
    opportunities = repo.by_stage(stage_filter) if stage_filter else repo.get_all()
    return render_template(
        "opportunities/index.html",
        opportunities=opportunities,
        stages=Opportunity.STAGES,
        stage_filter=stage_filter,
        stage_form=StageForm(),
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
@editor_required
def new_opportunity():
    form = OpportunityForm()
    form.customer_id.choices = _customer_choices()
    form.product_id.choices = _product_choices()

    if form.validate_on_submit():
        OpportunityService().create(
            customer_id=form.customer_id.data,
            product_id=form.product_id.data,
            quantity_requested=form.quantity_requested.data,
            source=form.source.data,
            notes=form.notes.data,
        )
        flash("Opportunity created.", "success")
        return redirect(url_for("opportunities.index"))

    return render_template("opportunities/opportunity_form.html", form=form)


@bp.route("/<int:opportunity_id>/stage", methods=["POST"])
@login_required
@editor_required
def update_stage(opportunity_id):
    form = StageForm()
    if form.validate_on_submit():
        try:
            OpportunityService().update_stage(opportunity_id, form.stage.data)
            flash("Stage updated.", "success")
        except MiniErpError as exc:
            flash(str(exc), "danger")
    return redirect(url_for("opportunities.index"))


@bp.route("/<int:opportunity_id>/convert", methods=["POST"])
@login_required
@editor_required
def convert(opportunity_id):
    try:
        sale = OpportunityService().convert_to_sale(opportunity_id)
        flash(f"Converted to Sale #{sale.id}.", "success")
        return redirect(url_for("sales.detail", sale_id=sale.id))
    except MiniErpError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("opportunities.index"))


def _customer_choices():
    return [(c.id, c.name) for c in CustomerRepository().get_all()]


def _product_choices():
    return [(p.id, p.display_name) for p in ProductRepository().get_active()]
