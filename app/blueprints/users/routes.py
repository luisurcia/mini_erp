from flask import flash, redirect, render_template, url_for
from flask_babel import gettext as _
from flask_login import current_user, login_required

from app.blueprints.users import bp
from app.blueprints.users.forms import UserForm
from app.exceptions import MiniErpError
from app.permissions import admin_required
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


@bp.route("/")
@login_required
@admin_required
def index():
    users = UserRepository().get_all()
    return render_template("users/index.html", users=users)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_user():
    form = UserForm()
    if form.validate_on_submit():
        if not form.password.data:
            flash(_("Password is required for a new user."), "danger")
        else:
            try:
                user = UserService().create_user(
                    username=form.username.data,
                    password=form.password.data,
                    role=form.role.data,
                )
                flash(_("User '%(name)s' created.", name=user.username), "success")
                return redirect(url_for("users.index"))
            except MiniErpError as exc:
                flash(str(exc), "danger")

    return render_template("users/user_form.html", form=form, mode="new")


@bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    user = UserRepository().get(user_id)
    if user is None:
        flash(_("User not found."), "danger")
        return redirect(url_for("users.index"))

    form = UserForm(obj=user)
    if not form.is_submitted():
        form.password.data = ""
        form.confirm_password.data = ""

    if form.validate_on_submit():
        try:
            UserService().update_user(
                user,
                username=form.username.data,
                role=form.role.data,
                password=form.password.data or None,
            )
            flash(_("User '%(name)s' updated.", name=form.username.data), "success")
            return redirect(url_for("users.index"))
        except MiniErpError as exc:
            flash(str(exc), "danger")

    return render_template("users/user_form.html", form=form, mode="edit", user=user)


@bp.route("/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = UserRepository().get(user_id)
    if user is None:
        flash(_("User not found."), "danger")
    elif user.id == current_user.id:
        flash(_("You cannot delete your own account."), "danger")
    else:
        try:
            UserService().delete_user(user)
            flash(_("User '%(name)s' deleted.", name=user.username), "success")
        except MiniErpError as exc:
            flash(str(exc), "danger")
    return redirect(url_for("users.index"))
