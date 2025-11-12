from __future__ import annotations

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("home.html", title="Solaris — Smart Rooftop Solar Estimator", show_tracker_cta=True)


@main_bp.route("/map", endpoint="map")
def solar_map():
    return render_template("health/index.html", title="Solar Shadow Map")

