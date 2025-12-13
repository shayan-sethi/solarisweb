from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import ProfileForm
from ..models import SubsidySubmission

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.before_request
def require_journey():
    if not current_user.is_authenticated:
        return
    if not current_user.journey_completed:
        return redirect(url_for("subsidy.eligibility"))


@profile_bp.route("/", methods=["GET"])
@login_required
def view_profile():
    subsidy_submissions = (
        SubsidySubmission.query.filter_by(user_id=current_user.id)
        .order_by(SubsidySubmission.created_at.desc())
        .all()
    )
    return render_template(
        "profile/view.html",
        title="Profile",
        subsidy_submissions=subsidy_submissions,
    )


@profile_bp.route("/edit/", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.email = form.email.data.lower().strip()
        current_user.phone = form.phone.data
        current_user.dob = form.dob.data
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile.view_profile"))

    return render_template("profile/edit.html", title="Edit Profile", form=form)



