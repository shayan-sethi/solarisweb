from __future__ import annotations

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

from ..utils.energy import build_energy_context
from ..utils.projects import build_projects_context

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.before_request
def require_journey():
    if not current_user.is_authenticated:
        return
    if not current_user.journey_completed:
        return redirect(url_for("subsidy.eligibility"))


@dashboard_bp.route("/", methods=["GET"])
@login_required
def index():
    projects_context = build_projects_context(current_user.id)
    recent_projects = projects_context["projects"][:3]
    projects_simulated = not projects_context["has_real_projects"]

    energy_context = build_energy_context(current_user.id)
    total_generation = energy_context["totals"]["generation"]
    recent_energy = energy_context["logs"][:3]

    estimate_summary = {
        "system_kw": current_user.last_system_kw,
        "net_cost": current_user.last_net_cost_inr,
        "savings": current_user.last_estimated_savings_inr,
        "updated_at": current_user.last_estimate_updated_at,
    }
    estimate_stats = None
    if estimate_summary["system_kw"]:
        estimate_stats = {
            "monthly_savings": 8200,
            "lifetime_savings": 152000,
            "co2_offset": 1.8,
        }

    return render_template(
        "dashboard/index.html",
        title="Dashboard",
        recent_projects=recent_projects,
        projects_simulated=projects_simulated,
        total_generation=total_generation,
        recent_energy=recent_energy,
        estimate_summary=estimate_summary,
        estimate_stats=estimate_stats,
        show_tracker_cta=True,
        energy_chart_series=energy_context["daily_series"],
        energy_insights=energy_context["insights"],
        energy_simulated=not energy_context["has_real_logs"],
        energy_totals=energy_context["totals"],
    )

