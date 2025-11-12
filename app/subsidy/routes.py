from __future__ import annotations

from datetime import datetime

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import SubsidyNumbersForm, SubsidySiteForm
from ..utils import (
    estimate_subsidy,
    estimate_system_size_kw,
    match_subsidy_schemes,
    estimate_monthly_units_from_bill,
    get_provider_label,
    get_provider_tariff,
    get_scheme_filter_options,
)
from ..utils.vendors import get_recommended_vendors

subsidy_bp = Blueprint("subsidy", __name__, url_prefix="/subsidy")


def _reset_journey() -> None:
    session.pop("subsidy_journey", None)


def _ensure_session() -> dict:
    data = session.get("subsidy_journey")
    if not data:
        data = {}
        session["subsidy_journey"] = data
    return data


@subsidy_bp.route("/", methods=["GET", "POST"])
@login_required
def eligibility():
    _reset_journey()
    form = SubsidyNumbersForm()

    if form.validate_on_submit():
        journey = _ensure_session()
        roof_area = float(form.roof_area.data or 0)
        monthly_bill = float(form.monthly_bill.data or 0)
        provider = form.provider.data or ""

        journey.update(
            {
                "roof_area": roof_area,
                "monthly_bill": monthly_bill,
                "provider": provider,
            }
        )
        session.modified = True
        return redirect(url_for("subsidy.site"))

    return render_template(
        "subsidy/step1_numbers.html",
        title="Subsidy Journey — Step 1",
        form=form,
        step=1,
    )


@subsidy_bp.route("/site", methods=["GET", "POST"])
@login_required
def site():
    journey = _ensure_session()
    if "roof_area" not in journey:
        flash("Start with your rooftop numbers first.", "error")
        return redirect(url_for("subsidy.eligibility"))

    form = SubsidySiteForm()
    if form.validate_on_submit():
        journey.update(
            {
                "state": form.state.data,
                "consumer_segment": form.consumer_segment.data,
                "grid_connection": form.grid_connection.data,
                "roof_type": form.roof_type.data or "",
            }
        )
        session.modified = True
        return redirect(url_for("subsidy.results"))

    return render_template(
        "subsidy/step3_site.html",
        title="Subsidy Journey — Step 2",
        form=form,
        step=2,
    )


@subsidy_bp.route("/results", methods=["GET"])
@login_required
def results():
    journey = _ensure_session()
    required_keys = {
        "roof_area",
        "state",
        "consumer_segment",
        "grid_connection",
        "provider",
        "monthly_bill",
    }
    if not required_keys.issubset(journey.keys()):
        flash("Complete the subsidy journey before viewing matches.", "error")
        return redirect(url_for("subsidy.eligibility"))

    roof_area = journey.get("roof_area", 0.0)
    monthly_bill = journey.get("monthly_bill", 0.0)
    provider_key = journey.get("provider")

    estimated_monthly_units = estimate_monthly_units_from_bill(monthly_bill, provider_key)
    annual_consumption = estimated_monthly_units * 12 if estimated_monthly_units else None

    recommended_kw = estimate_system_size_kw(
        roof_area=roof_area or None,
        annual_consumption_kwh=annual_consumption or None,
    )

    result = estimate_subsidy(recommended_kw)
    matches = match_subsidy_schemes(
        state=journey.get("state") or "",
        consumer_segment=journey.get("consumer_segment") or "residential",
        owns_property=journey.get("ownership") if "ownership" in journey else None,
        is_grid_connected=journey.get("grid_connection") == "grid",
        roof_area=roof_area or None,
        annual_consumption=annual_consumption or None,
    )

    coverage_filter = request.args.get("coverage", "all")
    ownership_filter = request.args.get("ownership", "all")
    grid_filter = request.args.get("grid", "all")
    current_filters = {
        "coverage": coverage_filter,
        "ownership": ownership_filter,
        "grid": grid_filter,
    }

    filter_options = get_scheme_filter_options(matches)

    def build_filter_links(name: str, options: list[str], label_map: dict[str, str]):
        links = []
        for value in options:
            params = current_filters.copy()
            params[name] = value
            label = label_map.get(value, value.title())
            links.append(
                {
                    "value": value,
                    "label": label,
                    "url": url_for("subsidy.results", **params),
                    "active": params[name] == value,
                }
            )
        return links

    coverage_labels = {
        "all": "All",
        "national": "National",
        "state": "State",
        "csr": "CSR / NGO",
    }
    ownership_labels = {
        "all": "All",
        "owner": "Owner required",
        "tenant": "Tenant-friendly",
    }
    grid_labels = {
        "all": "All",
        "grid": "Grid-connected",
        "off-grid": "Off-grid / hybrid",
    }

    coverage_links = build_filter_links(
        "coverage",
        ["all"] + filter_options.get("coverage", []),
        coverage_labels,
    )
    ownership_links = build_filter_links(
        "ownership",
        ["all", "owner", "tenant"],
        ownership_labels,
    )
    grid_links = build_filter_links(
        "grid",
        ["all", "grid", "off-grid"],
        grid_labels,
    )

    def passes_filters(scheme):
        if coverage_filter != "all" and scheme.coverage != coverage_filter:
            return False
        if ownership_filter == "owner" and scheme.requires_ownership is False:
            return False
        if ownership_filter == "tenant" and scheme.requires_ownership is True:
            return False
        if grid_filter == "grid" and scheme.requires_grid_connection is False:
            return False
        if grid_filter == "off-grid" and scheme.requires_grid_connection is not False:
            return False
        return True

    filtered_matches = [scheme for scheme in matches if passes_filters(scheme)]

    estimated_annual_output = recommended_kw * 1100
    if annual_consumption:
        tariff = get_provider_tariff(provider_key)
        offset_kwh = min(annual_consumption, estimated_annual_output)
        estimated_annual_savings = offset_kwh * tariff
    elif monthly_bill:
        estimated_annual_savings = monthly_bill * 12 * 0.6
    else:
        estimated_annual_savings = estimated_annual_output * 6

    current_user.last_system_kw = recommended_kw
    current_user.last_net_cost_inr = result.net_cost
    current_user.last_estimated_savings_inr = estimated_annual_savings
    current_user.last_estimate_updated_at = datetime.utcnow()
    if not current_user.journey_completed:
        current_user.journey_completed = True
    db.session.commit()

    state_label = journey.get("state") or ""
    consumer_segment = journey.get("consumer_segment") or "residential"
    segment_labels = {
        "residential": "Residential",
        "agricultural": "Agricultural",
        "community": "Community / cooperative",
    }
    provider_label = get_provider_label(provider_key)
    profile_tags = []
    if state_label:
        profile_tags.append(state_label.title())
    profile_tags.append(segment_labels.get(consumer_segment, consumer_segment.title()))
    profile_tags.append(
        "Grid-connected site" if journey.get("grid_connection") == "grid" else "Off-grid / unreliable grid"
    )
    if provider_label:
        profile_tags.append(provider_label)
    if estimated_monthly_units:
        profile_tags.append(f"{round(estimated_monthly_units):,} units / month")

    return render_template(
        "subsidy/step4_results.html",
        title="Subsidy Journey — Results",
        step=3,
        recommended_kw=recommended_kw,
        roof_area=roof_area,
        annual_consumption=annual_consumption,
        monthly_bill=monthly_bill,
        estimated_monthly_units=estimated_monthly_units,
        provider_label=provider_label,
        result=result,
        matches=filtered_matches,
        total_matches=len(matches),
        profile_tags=profile_tags,
        estimated_annual_savings=estimated_annual_savings,
        coverage_links=coverage_links,
        ownership_links=ownership_links,
        grid_links=grid_links,
        current_filters=current_filters,
        show_tracker_cta=True,
    )


@subsidy_bp.route("/vendors", methods=["GET"])
@login_required
def vendors():
    journey = _ensure_session()
    roof_area = journey.get("roof_area")
    monthly_bill = journey.get("monthly_bill")
    provider_key = journey.get("provider")
    estimated_monthly_units = estimate_monthly_units_from_bill(monthly_bill, provider_key)
    annual_consumption = estimated_monthly_units * 12 if estimated_monthly_units else None

    recommended_kw = None
    estimated_annual_savings = None
    provider_label = get_provider_label(provider_key)

    if roof_area or annual_consumption:
        recommended_kw = estimate_system_size_kw(
            roof_area=roof_area or None,
            annual_consumption_kwh=annual_consumption or None,
        )
        estimated_annual_output = recommended_kw * 1100
        if annual_consumption:
            tariff = get_provider_tariff(provider_key)
            offset_kwh = min(annual_consumption, estimated_annual_output)
            estimated_annual_savings = offset_kwh * tariff
        elif monthly_bill:
            estimated_annual_savings = monthly_bill * 12 * 0.6
        else:
            estimated_annual_savings = estimated_annual_output * 6

    recommended_vendors = get_recommended_vendors(recommended_kw)
    
    top_recommended = [v for v in recommended_vendors if v.get("is_recommended", False)]
    other_vendors = [v for v in recommended_vendors if not v.get("is_recommended", False)]
    
    return render_template(
        "subsidy/vendors.html",
        title="Installer Marketplace",
        recommended_vendors=top_recommended,
        other_vendors=other_vendors,
        recommended_kw=recommended_kw,
        estimated_annual_savings=estimated_annual_savings,
        estimated_monthly_units=estimated_monthly_units,
        provider_label=provider_label,
    )


@subsidy_bp.route("/restart", methods=["POST"])
@login_required
def restart():
    if current_user.journey_completed:
        current_user.journey_completed = False
        db.session.commit()
    _reset_journey()
    return redirect(url_for("subsidy.eligibility"))

