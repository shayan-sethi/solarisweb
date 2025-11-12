from __future__ import annotations

from typing import Any, Dict, List


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
    Calculate a recommendation score for a vendor based on multiple factors.
    Higher score = better recommendation.
    """
    score = 0.0
    
    rating = vendor.get("rating", 0.0)
    base_price = vendor.get("base_price_per_kw_inr", 80000)
    years_exp = vendor.get("years_experience", 0)
    num_locations = len(vendor.get("locations", []))
    num_highlights = len(vendor.get("highlights", []))
    
    max_price = max(v.get("base_price_per_kw_inr", 80000) for v in solar_vendors)
    min_price = min(v.get("base_price_per_kw_inr", 50000) for v in solar_vendors)
    price_range = max_price - min_price if max_price > min_price else 1
    
    rating_score = rating * 20
    price_score = ((max_price - base_price) / price_range) * 25 if price_range > 0 else 0
    experience_score = min(years_exp * 1.5, 20)
    locations_score = min(num_locations * 2, 15)
    highlights_score = min(num_highlights * 2, 20)
    
    score = rating_score + price_score + experience_score + locations_score + highlights_score
    
    return round(score, 2)


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
