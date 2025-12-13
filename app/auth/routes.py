from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..forms import LoginForm, RegisterForm
from ..models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if not current_user.journey_completed:
            return redirect(url_for("subsidy.eligibility"))
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(form.password.data):
            flash("Invalid email or password.", "error")
        else:
            login_user(user, remember=form.remember.data)
            flash("Welcome back to Solaris!", "success")
            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            if user.journey_completed:
                return redirect(url_for("dashboard.index"))
            return redirect(url_for("subsidy.eligibility"))

    return render_template("auth/login.html", form=form, title="Sign in")


@auth_bp.route("/register/", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        if not current_user.journey_completed:
            return redirect(url_for("subsidy.eligibility"))
        return redirect(url_for("dashboard.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
        else:
            user = User(email=email, name=form.name.data.strip() if form.name.data else None)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Account created successfully.", "success")
            return redirect(url_for("subsidy.eligibility"))

    return render_template("auth/register.html", form=form, title="Create account")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("main.home"))

