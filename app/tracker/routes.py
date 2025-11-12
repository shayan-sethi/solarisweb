from __future__ import annotations

from datetime import date

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import TrackerEntryForm
from ..models import EnergyLog
from ..utils.energy import build_energy_context

tracker_bp = Blueprint("tracker", __name__, url_prefix="/tracker")


@tracker_bp.before_request
def require_journey():
    if not current_user.is_authenticated:
        return
    if not current_user.journey_completed:
        return redirect(url_for("subsidy.eligibility"))


@tracker_bp.route("/", methods=["GET"])
@login_required
def index():
    energy_context = build_energy_context(current_user.id)

    return render_template(
        "tracker/index.html",
        title="Energy Tracker",
        logs=energy_context["logs"],
        total_generation=energy_context["totals"]["generation"],
        total_export=energy_context["totals"]["export"],
        total_revenue=energy_context["totals"]["revenue"],
        chart_daily_series=energy_context["daily_series"],
        simulated_data=not energy_context["has_real_logs"],
        automation_insights=energy_context["insights"],
    )


@tracker_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_entry():
    form = TrackerEntryForm()
    if not form.date.data:
        form.date.data = date.today()
    if form.validate_on_submit():
        log = EnergyLog(
            user_id=current_user.id,
            entry_type=form.entry_type.data,
            kwh=form.kwh.data,
            revenue=form.revenue.data,
            panel_id=form.panel_id.data or None,
            date=form.date.data,
            note=form.note.data,
        )
        db.session.add(log)
        db.session.commit()
        flash("Tracker entry saved!", "success")
        return redirect(url_for("tracker.index"))
    return render_template(
        "tracker/add.html",
        title="Add Tracker Entry",
        form=form,
    )
