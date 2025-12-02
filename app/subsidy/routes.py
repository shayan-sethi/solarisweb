from __future__ import annotations

from datetime import datetime
import json

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
    current_app,
)
from flask_login import current_user, login_required

from ..extensions import db, csrf
from ..forms import SubsidyNumbersForm, SubsidySiteForm
from ..models import SubsidySubmission
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
    
    # Apply ML-based scoring to matches
    from app.utils.ml_scoring import calculate_subsidy_match_score
    
    for match in matches:
        # Calculate ML match score
        ml_score = calculate_subsidy_match_score(
            scheme={
                'match_score': match.match_score,
                'benefit': match.benefit,
                'states': match.states,
                'coverage': match.coverage,
                'consumer_segments': match.consumer_segments,
            },
            user_system_size_kw=recommended_kw,
            user_annual_consumption_kwh=annual_consumption,
            user_state=journey.get("state") or "",
            user_consumer_segment=journey.get("consumer_segment") or "residential",
            gross_cost_inr=result.gross_cost,
            subsidy_amount_inr=result.central + result.state_subsidy,
            ease_of_claim=0.7 if match.application_url else 0.5,  # Higher if online portal available
        )
        # Update match score with ML score
        match.match_score = ml_score / 10.0  # Convert back to 0-10 scale for compatibility

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
    
    # Sort matches by ML score (highest first)
    filtered_matches.sort(key=lambda x: x.match_score, reverse=True)

    # Calculate financial and CO₂ predictions using ML model
    from app.utils.ml_scoring import calculate_financial_predictions
    
    estimated_annual_output = recommended_kw * 1100
    tariff = get_provider_tariff(provider_key)
    
    financial_predictions = calculate_financial_predictions(
        system_size_kw=recommended_kw,
        annual_generation_kwh=estimated_annual_output,
        tariff_rate_inr_per_kwh=tariff,
        gross_cost_inr=result.gross_cost,
        subsidy_amount_inr=result.central + result.state_subsidy,
        self_consumption_ratio=0.8,
    )
    
    if annual_consumption:
        offset_kwh = min(annual_consumption, estimated_annual_output)
        estimated_annual_savings = offset_kwh * tariff
    elif monthly_bill:
        estimated_annual_savings = monthly_bill * 12 * 0.6
    else:
        estimated_annual_savings = financial_predictions['annual_savings_inr']

    current_user.last_system_kw = recommended_kw
    current_user.last_net_cost_inr = result.net_cost
    current_user.last_estimated_savings_inr = estimated_annual_savings
    current_user.last_estimate_updated_at = datetime.utcnow()
    if not current_user.journey_completed:
        current_user.journey_completed = True
    
    # Save subsidy submission data
    submission = SubsidySubmission(
        user_id=current_user.id,
        roof_area=float(journey.get("roof_area", 0)) if journey.get("roof_area") else None,
        monthly_bill=float(journey.get("monthly_bill", 0)) if journey.get("monthly_bill") else None,
        provider=journey.get("provider"),
        state=journey.get("state"),
        consumer_segment=journey.get("consumer_segment"),
        grid_connection=journey.get("grid_connection"),
        roof_type=journey.get("roof_type"),
    )
    db.session.add(submission)
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


@subsidy_bp.route("/ai-chat", methods=["POST"])
@csrf.exempt
@login_required
def ai_chat():
    """Handle AI chat requests for subsidy form guidance using Google Gemini"""
    try:
        import google.generativeai as genai
        
        api_key = current_app.config.get("GEMINI_API_KEY")
        if not api_key:
            current_app.logger.error("GEMINI_API_KEY not found in config")
            return jsonify({"error": "Gemini API key not configured. Please set GEMINI_API_KEY environment variable."}), 500
        
        current_app.logger.info(f"Using Gemini API key (length: {len(api_key)})")
        
        data = request.get_json()
        user_message = data.get("message", "")
        step = data.get("step", 1)
        form_data = data.get("form_data", {})
        
        if not user_message:
            return jsonify({"error": "Message is required"}), 400
        
        # Build context-aware system prompt based on the step
        system_prompts = {
            1: """You are a helpful AI assistant guiding users through the Indian solar subsidy application form (Step 1: Basic Numbers).

You help users understand:
- Rooftop area: How to measure usable roof space, excluding tanks, shading, setbacks
- Monthly electricity bill: Average of recent bills, used to estimate consumption
- Electricity provider/DISCOM: Their local distribution company

Be friendly, clear, and provide practical advice. Answer questions about requirements, calculations, and what information they need to provide.

You can use markdown formatting to make your responses clearer:
- Use **bold** for emphasis
- Use headings (## Heading) to organize information
- Use bullet points (- item) for lists
- Use `code` for technical terms or values""",
            2: """You are a helpful AI assistant guiding users through the Indian solar subsidy application form (Step 2: Site Information).

You help users understand:
- State: Their location for state-specific subsidies
- Consumer segment: Residential, Agricultural, or Community/Cooperative
- Grid connection: Whether they're connected to the grid or off-grid
- Roof type: Concrete (RCC), Tin/Metal, Tiles, Asbestos, Flat roof, Sloped roof, or Other

Be friendly, clear, and provide practical advice about regional requirements and eligibility.

You can use markdown formatting to make your responses clearer:
- Use **bold** for emphasis
- Use headings (## Heading) to organize information
- Use bullet points (- item) for lists
- Use `code` for technical terms or values""",
            3: """You are a helpful AI assistant guiding users through applying for Indian solar subsidies after they've completed the eligibility form.

You help users with:
- How to apply for the recommended subsidy schemes
- Required documents for subsidy applications
- Step-by-step application process for different schemes
- Timeline expectations for subsidy approval
- How to contact DISCOM or relevant authorities
- Understanding subsidy benefits and net costs
- Next steps after receiving subsidy approval
- Vendor selection and installation process
- Net metering application process

Be friendly, clear, and provide actionable, step-by-step guidance. Help them understand the application process, required documents, timelines, and what to expect at each stage. Reference specific schemes when relevant and provide practical next steps.

You can use markdown formatting to make your responses clearer and more organized:
- Use **bold** for important terms or emphasis
- Use headings (## Heading, ### Subheading) to structure your response
- Use bullet points (- item) for lists of documents, steps, or requirements
- Use `code` for technical terms, amounts, or specific values
- Organize longer responses with clear sections using headings"""
        }
        
        system_prompt = system_prompts.get(step, system_prompts[1])
        
        # Add form context if available
        context = ""
        if form_data:
            context = f"\n\nCurrent form data:\n{json.dumps(form_data, indent=2)}"
        
        # If on results page (step 3), add results context from session
        if step == 3:
            journey = _ensure_session()
            if journey:
                results_context = f"""
                
User's subsidy eligibility results:
- State: {journey.get('state', 'Not specified')}
- Consumer segment: {journey.get('consumer_segment', 'Not specified')}
- Grid connection: {journey.get('grid_connection', 'Not specified')}
- Roof area: {journey.get('roof_area', 'Not specified')} m²
- Monthly bill: ₹{journey.get('monthly_bill', 'Not specified')}
- Provider: {journey.get('provider', 'Not specified')}

The user has completed the eligibility form and is now viewing their recommended subsidy schemes. Help them understand how to apply for these schemes, what documents they need, application timelines, and next steps."""
                context += results_context
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Use gemini-2.0-flash which is available and fast
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        # Create the full prompt
        full_prompt = f"{system_prompt}{context}\n\nUser question: {user_message}"
        
        # Generate response
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=500,
            )
        )
        
        ai_response = response.text
        
        return jsonify({"response": ai_response})
    
    except ImportError:
        return jsonify({"error": "Google Generative AI library not installed. Run: pip install google-generativeai"}), 500
    except Exception as e:
        import traceback
        error_details = str(e)
        # Log the full error for debugging
        current_app.logger.error(f"Gemini API error: {error_details}\n{traceback.format_exc()}")
        # Return error with details
        error_msg = f"AI service error: {error_details}"
        if current_app.debug:
            error_msg += f"\n\nTraceback:\n{traceback.format_exc()}"
        return jsonify({"error": error_msg}), 500


@subsidy_bp.route("/view", methods=["GET"])
@login_required
def view_data():
    journey = _ensure_session()
    if not journey:
        flash("No subsidy form data found. Please complete the subsidy journey first.", "error")
        return redirect(url_for("subsidy.eligibility"))
    
    # Get provider label for display
    provider_key = journey.get("provider")
    provider_label = get_provider_label(provider_key) if provider_key else None
    
    # Format the data for display
    form_data = {
        "roof_area": journey.get("roof_area"),
        "monthly_bill": journey.get("monthly_bill"),
        "provider": provider_label or provider_key or "Not specified",
        "state": journey.get("state"),
        "consumer_segment": journey.get("consumer_segment"),
        "grid_connection": journey.get("grid_connection"),
        "roof_type": journey.get("roof_type"),
    }
    
    # Calculate estimates if possible
    estimated_monthly_units = None
    if form_data["monthly_bill"] and provider_key:
        estimated_monthly_units = estimate_monthly_units_from_bill(form_data["monthly_bill"], provider_key)
    
    annual_consumption = estimated_monthly_units * 12 if estimated_monthly_units else None
    
    recommended_kw = None
    if form_data["roof_area"] or annual_consumption:
        recommended_kw = estimate_system_size_kw(
            roof_area=form_data["roof_area"] or None,
            annual_consumption_kwh=annual_consumption or None,
        )
    
    return render_template(
        "subsidy/view_data.html",
        title="View Subsidy Form Data",
        form_data=form_data,
        estimated_monthly_units=estimated_monthly_units,
        annual_consumption=annual_consumption,
        recommended_kw=recommended_kw,
    )
