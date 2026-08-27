from flask import flash, redirect, render_template, url_for
from flask_babel import gettext as _
from flask_login import login_required

from app.blueprints.customers import bp
from app.blueprints.customers.forms import CustomerForm
from app.models.customer import Customer
from app.permissions import editor_required
from app.repositories.customer_repository import CustomerRepository


@bp.route("/")
@login_required
def index():
    customers = CustomerRepository().get_all()
    return render_template("customers/index.html", customers=customers)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@editor_required
def new_customer():
    form = CustomerForm()

    if form.validate_on_submit():
        customer = Customer(
            name=form.name.data,
            rut=form.rut.data,
            email=form.email.data or None,
            phone=form.phone.data or None,
            shipping_address=form.shipping_address.data or None,
            segment_id=form.segment_id.data,
            instagram_handle=form.instagram_handle.data or None,
            notes=form.notes.data or None,
        )
        CustomerRepository().add(customer)
        CustomerRepository().commit()
        flash(_("Customer '%(name)s' created.", name=customer.name), "success")
        return redirect(url_for("customers.index"))

    return render_template("customers/customer_form.html", form=form, mode="new")


@bp.route("/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
@editor_required
def edit_customer(customer_id):
    customer = CustomerRepository().get(customer_id)
    if customer is None:
        flash(_("Customer not found."), "danger")
        return redirect(url_for("customers.index"))

    form = CustomerForm(obj=customer)

    if form.validate_on_submit():
        customer.name = form.name.data
        customer.rut = form.rut.data
        customer.email = form.email.data or None
        customer.phone = form.phone.data or None
        customer.shipping_address = form.shipping_address.data or None
        customer.segment_id = form.segment_id.data
        customer.instagram_handle = form.instagram_handle.data or None
        customer.notes = form.notes.data or None
        CustomerRepository().commit()
        flash(_("Customer '%(name)s' updated.", name=customer.name), "success")
        return redirect(url_for("customers.index"))

    return render_template(
        "customers/customer_form.html", form=form, mode="edit", customer=customer
    )
