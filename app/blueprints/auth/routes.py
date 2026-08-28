from flask import flash, redirect, render_template, url_for
from flask_babel import gettext as _
from flask_login import current_user, login_required, login_user, logout_user

from app.blueprints.auth import bp
from app.blueprints.auth.forms import ChangeLanguageForm, ChangePasswordForm, LoginForm
from app.extensions import db
from app.models.company import Company
from app.models.user import User


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("dashboard.index"))
        flash(_("Invalid username or password."), "danger")

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash(_("Current password is incorrect."), "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash(_("Password changed."), "success")
            return redirect(url_for("dashboard.index"))

    return render_template("auth/change_password.html", form=form)


@bp.route("/language", methods=["GET", "POST"])
@login_required
def change_language():
    form = ChangeLanguageForm()
    if not form.is_submitted():
        form.language.data = current_user.language or Company.get_settings().language

    if form.validate_on_submit():
        current_user.language = form.language.data
        db.session.commit()
        # Rendered on the next request, so it already shows in the new language.
        flash(_("Language updated."), "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/change_language.html", form=form)
