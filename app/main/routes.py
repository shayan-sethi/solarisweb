from __future__ import annotations

from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from flask_babel import gettext as _

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("home.html", title="Solaris — Smart Rooftop Solar Estimator", show_tracker_cta=True)


@main_bp.route("/map/", endpoint="map")
def solar_map():
    return render_template("health/index.html", title="Helio Map")


@main_bp.route("/set_language/<lang_code>")
def set_language(lang_code):
    from flask import current_app
    from flask_babel import get_locale, force_locale
    if lang_code in current_app.config['LANGUAGES']:
        session['language'] = lang_code
        session.permanent = True
        # Force locale refresh
        with force_locale(lang_code):
            flash(_('Language changed successfully.'), 'success')
    else:
        flash(_('Invalid language selected.'), 'error')
    return redirect(request.referrer or url_for('main.home'))

