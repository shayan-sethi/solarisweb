from __future__ import annotations

from typing import Any, Dict, List
from app.utils.ml_scoring import calculate_vendor_score as ml_calculate_vendor_score, analyze_sentiment_simple


solar_vendors = [
    {
        "id": "sunrise-energy",
        "name": "Sunrise Energy Solutions",
        "rating": 4.6,
        "price_range_inr": "₹65k – ₹75k / kW (turnkey)",
        "base_price_per_kw_inr": 68000,
        "locations": ["Delhi", "Noida", "Gurugram"],
        "years_experience": 9,
        "highlights": ["MNRE empanelled", "Net-meter support", "24x7 monitoring"],
        "contact": "+91-98765-43210",
        "website": "https://sunriseenergy.example.com",
    },
    {
        "id": "surya-grid",
        "name": "SuryaGrid EPC",
        "rating": 4.3,
        "price_range_inr": "₹58k – ₹70k / kW",
        "base_price_per_kw_inr": 61000,
        "locations": ["Mumbai", "Pune", "Nashik"],
        "years_experience": 12,
        "highlights": ["Hybrid inverter experts", "O&M packages", "Battery integration"],
        "contact": "+91-99887-77665",
        "website": "https://suryagrid.example.com",
    },
    {
        "id": "greenbeam",
        "name": "GreenBeam Solar",
        "rating": 4.8,
        "price_range_inr": "₹62k – ₹80k / kW",
        "base_price_per_kw_inr": 67000,
        "locations": ["Ahmedabad", "Vadodara", "Surat"],
        "years_experience": 7,
        "highlights": ["5-year O&M included", "Real-time app", "EMI options"],
        "contact": "care@greenbeam.example.com",
        "website": "https://greenbeam.example.com",
    },
    {
        "id": "agripower",
        "name": "AgriPower Pumps",
        "rating": 4.2,
        "price_range_inr": "₹3.2L – ₹4.5L per 5HP pump",
        "base_price_per_kw_inr": 64000,
        "locations": ["Jaipur", "Udaipur", "Indore"],
        "years_experience": 11,
        "highlights": ["PM-KUSUM specialists", "RBI/NABARD loan support", "On-field service"],
        "contact": "+91-90909-80807",
        "website": "https://agripower.example.com",
    },
    {
        "id": "urban-spark",
        "name": "UrbanSpark Rooftech",
        "rating": 4.5,
        "price_range_inr": "₹55k – ₹68k / kW",
        "base_price_per_kw_inr": 59000,
        "locations": ["Bengaluru", "Mysuru", "Hyderabad"],
        "years_experience": 8,
        "highlights": ["Remote diagnostics", "Smart EV-ready", "Rapid installation"],
        "contact": "hello@urbanspark.example.com",
        "website": "https://urbanspark.example.com",
    },
]


def calculate_vendor_score(vendor: Dict[str, Any]) -> float:
    """
    Calculate a recommendation score for a vendor using ML-based scoring.
    Uses sentiment analysis and weighted formula.
    """
    # Extract vendor data
    rating = vendor.get("rating", 0.0)
    highlights = vendor.get("highlights", [])
    mnre_verified = any("MNRE" in h.upper() or "empanelled" in h.lower() for h in highlights)
    
    # Simulate review text for sentiment analysis (in real app, use actual reviews)
    review_text = " ".join(highlights)
    sentiment_score = analyze_sentiment_simple(review_text)
    
    # Calculate price fairness (0-1 scale)
    max_price = max(v.get("base_price_per_kw_inr", 80000) for v in solar_vendors)
    min_price = min(v.get("base_price_per_kw_inr", 50000) for v in solar_vendors)
    base_price = vendor.get("base_price_per_kw_inr", 70000)
    price_range = max_price - min_price if max_price > min_price else 1
    price_fairness = 1.0 - ((base_price - min_price) / price_range) if price_range > 0 else 0.5
    
    # Estimate completion rate (0-1 scale) - higher rating = higher completion
    completion_rate = min(1.0, rating / 5.0)
    
    # Warranty years (extract from highlights or default)
    warranty_years = 5.0  # Default
    for h in highlights:
        if "year" in h.lower() and any(c.isdigit() for c in h):
            try:
                warranty_years = float([c for c in h.split() if c.isdigit()][0])
                break
            except:
                pass
    
    # Use ML scoring model
    ml_score = ml_calculate_vendor_score(
        rating=rating,
        mnre_verified=mnre_verified,
        sentiment_score=sentiment_score,
        price_fairness=price_fairness,
        completion_rate=completion_rate,
        warranty_years=warranty_years,
        years_experience=vendor.get("years_experience", 0),
    )
    
    return ml_score


def get_vendor_recommendation_reasons(vendor: Dict[str, Any], all_vendors: List[Dict[str, Any]]) -> List[str]:
    """Generate recommendation reasons for a vendor based on their stats."""
    reasons = []
    
    rating = vendor.get("rating", 0.0)
    base_price = vendor.get("base_price_per_kw_inr", 80000)
    years_exp = vendor.get("years_experience", 0)
    num_locations = len(vendor.get("locations", []))
    
    avg_rating = sum(v.get("rating", 0.0) for v in all_vendors) / len(all_vendors) if all_vendors else 0
    avg_price = sum(v.get("base_price_per_kw_inr", 70000) for v in all_vendors) / len(all_vendors) if all_vendors else 70000
    max_years = max((v.get("years_experience", 0) for v in all_vendors), default=0)
    max_locations = max((len(v.get("locations", [])) for v in all_vendors), default=0)
    
    if rating >= 4.6:
        reasons.append("Top-rated service")
    elif rating > avg_rating + 0.2:
        reasons.append("Above-average rating")
    
    if base_price <= avg_price * 0.9:
        reasons.append("Competitive pricing")
    elif base_price <= min(v.get("base_price_per_kw_inr", 80000) for v in all_vendors) * 1.1:
        reasons.append("Best value pricing")
    
    if years_exp >= max_years * 0.9:
        reasons.append("Highly experienced")
    elif years_exp >= 10:
        reasons.append("Proven track record")
    
    if num_locations >= max_locations * 0.8:
        reasons.append("Wide service coverage")
    
    if "MNRE empanelled" in vendor.get("highlights", []):
        reasons.append("MNRE certified")
    
    if "O&M" in " ".join(vendor.get("highlights", [])):
        reasons.append("Maintenance included")
    
    return reasons[:3]


def get_recommended_vendors(recommended_kw: float | None = None) -> List[Dict[str, Any]]:
    """
    Get vendors sorted by recommendation score, with top vendors marked as recommended.
    """
    vendors_with_scores = []
    
    for vendor in solar_vendors:
        score = calculate_vendor_score(vendor)
        reasons = get_vendor_recommendation_reasons(vendor, solar_vendors)
        vendor_copy = vendor.copy()
        vendor_copy["recommendation_score"] = score
        vendor_copy["recommendation_reasons"] = reasons
        vendors_with_scores.append(vendor_copy)
    
    vendors_with_scores.sort(key=lambda v: v["recommendation_score"], reverse=True)
    
    top_score = vendors_with_scores[0]["recommendation_score"] if vendors_with_scores else 0
    
    for vendor in vendors_with_scores:
        vendor["is_recommended"] = vendor["recommendation_score"] >= top_score * 0.85
    
    return vendors_with_scores
