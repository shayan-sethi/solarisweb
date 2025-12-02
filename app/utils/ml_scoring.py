"""
ML-based scoring models for Solaris
Includes subsidy matching, vendor scoring, and financial predictions
"""
from __future__ import annotations

import math
from typing import Optional


def calculate_subsidy_match_score(
    *,
    scheme: dict,
    user_system_size_kw: float,
    user_annual_consumption_kwh: Optional[float],
    user_state: str,
    user_consumer_segment: str,
    gross_cost_inr: float,
    subsidy_amount_inr: float,
    ease_of_claim: float = 0.5,  # 0-1 scale, manually encoded
) -> float:
    """
    ML-based scoring model for subsidy matching.
    
    Uses weighted features to calculate match score (0-100):
    - System size compatibility
    - Subsidy benefit ratio
    - State match bonus
    - Consumer segment match
    - Ease of claim
    - Payback period optimization
    
    Args:
        scheme: Scheme data dict with match_score, benefit, etc.
        user_system_size_kw: User's recommended system size
        user_annual_consumption_kwh: Estimated annual consumption
        user_state: User's state
        user_consumer_segment: User's consumer segment
        gross_cost_inr: Total system cost before subsidy
        subsidy_amount_inr: Subsidy amount from this scheme
        ease_of_claim: Manual encoding of application difficulty (0-1)
    
    Returns:
        Match score from 0-100
    """
    score = 0.0
    
    # Base score from rule-based matching (already filtered)
    base_score = scheme.get('match_score', 7.5) * 10  # Convert 0-10 to 0-100
    
    # Feature 1: Subsidy benefit ratio (0-30 points)
    if gross_cost_inr > 0:
        subsidy_ratio = min(subsidy_amount_inr / gross_cost_inr, 1.0)
        benefit_score = subsidy_ratio * 30
        score += benefit_score
    
    # Feature 2: State match bonus (0-15 points)
    scheme_states = scheme.get('states', [])
    scheme_coverage = scheme.get('coverage', 'national')
    if scheme_coverage == 'state' and user_state.lower() in [s.lower() for s in scheme_states]:
        score += 15
    elif scheme_coverage == 'national':
        score += 10  # National schemes get moderate bonus
    
    # Feature 3: Consumer segment match (0-10 points)
    scheme_segments = scheme.get('consumer_segments', [])
    if user_consumer_segment.lower() in [s.lower() for s in scheme_segments]:
        score += 10
    
    # Feature 4: System size compatibility (0-20 points)
    # Prefer schemes that match typical residential sizes (1-10 kW)
    if 1.0 <= user_system_size_kw <= 10.0:
        size_score = 20 * (1 - abs(user_system_size_kw - 5.0) / 5.0)  # Peak at 5kW
        score += max(0, size_score)
    else:
        score += 10  # Still give some points for other sizes
    
    # Feature 5: Ease of claim (0-10 points)
    score += ease_of_claim * 10
    
    # Feature 6: Payback period optimization (0-15 points)
    # Shorter payback = better score
    if gross_cost_inr > 0 and user_annual_consumption_kwh:
        # Estimate annual savings (assuming 80% self-consumption)
        tariff_rate = 6.0  # Average Indian tariff
        annual_savings = user_annual_consumption_kwh * 0.8 * tariff_rate
        net_cost = gross_cost_inr - subsidy_amount_inr
        if annual_savings > 0:
            payback_years = net_cost / annual_savings
            # Score inversely proportional to payback period
            # 5 years = 15 points, 10 years = 7.5 points, 20 years = 0 points
            payback_score = max(0, 15 * (1 - (payback_years - 5) / 15))
            score += payback_score
    
    # Normalize to 0-100 range
    final_score = min(100, max(0, score))
    
    # Round to 1 decimal place
    return round(final_score, 1)


def calculate_vendor_score(
    *,
    rating: float,
    mnre_verified: bool,
    sentiment_score: float,  # From NLP sentiment analysis (0-1)
    price_fairness: float,  # 0-1 scale
    completion_rate: float,  # 0-1 scale
    warranty_years: float,
    years_experience: int,
) -> float:
    """
    ML-based vendor scoring using weighted formula.
    
    VendorScore = 0.4 × SentimentScore + 0.2 × MNRE_Verified + 
                  0.15 × PriceFairness + 0.15 × CompletionRate + 
                  0.1 × WarrantyScore
    
    Args:
        rating: Average user rating (0-5)
        mnre_verified: Whether vendor is MNRE verified
        sentiment_score: Sentiment analysis score from reviews (0-1)
        price_fairness: Price competitiveness score (0-1)
        completion_rate: Project completion rate (0-1)
        warranty_years: Warranty period in years
        years_experience: Years of experience
    
    Returns:
        Vendor score from 0-100
    """
    # Sentiment score (0-40 points)
    sentiment_component = sentiment_score * 40
    
    # MNRE verification (0-20 points)
    mnre_component = 20 if mnre_verified else 0
    
    # Price fairness (0-15 points)
    price_component = price_fairness * 15
    
    # Completion rate (0-15 points)
    completion_component = completion_rate * 15
    
    # Warranty score (0-10 points)
    # Normalize warranty: 5 years = 10 points, 1 year = 2 points
    warranty_component = min(10, max(2, warranty_years * 2))
    
    # Total score
    total_score = (
        sentiment_component +
        mnre_component +
        price_component +
        completion_component +
        warranty_component
    )
    
    # Bonus for experience (up to +5 points)
    experience_bonus = min(5, years_experience / 2)
    total_score += experience_bonus
    
    # Normalize rating to contribute to sentiment if not already included
    rating_component = (rating / 5.0) * 10  # Up to 10 points
    total_score = (total_score * 0.9) + rating_component
    
    return min(100, max(0, round(total_score, 1)))


def calculate_financial_predictions(
    *,
    system_size_kw: float,
    annual_generation_kwh: float,
    tariff_rate_inr_per_kwh: float,
    gross_cost_inr: float,
    subsidy_amount_inr: float,
    self_consumption_ratio: float = 0.8,  # 80% self-consumption
) -> dict:
    """
    Financial and CO₂ savings prediction model.
    
    Uses regression-based calculations for:
    - Monthly/annual savings
    - Payback period
    - CO₂ emissions avoided
    
    Formula: 1 kWh = ~0.82 kg CO₂ in India
    
    Args:
        system_size_kw: System size in kW
        annual_generation_kwh: Estimated annual generation
        tariff_rate_inr_per_kwh: Local electricity tariff
        gross_cost_inr: Total system cost
        subsidy_amount_inr: Subsidy amount
        self_consumption_ratio: Ratio of generation self-consumed (0-1)
    
    Returns:
        Dict with predictions:
        - monthly_savings_inr
        - annual_savings_inr
        - payback_period_years
        - co2_avoided_kg_per_year
        - net_cost_inr
    """
    # Net cost after subsidy
    net_cost_inr = gross_cost_inr - subsidy_amount_inr
    
    # Annual savings calculation
    # Self-consumed energy saves at retail tariff
    self_consumed_kwh = annual_generation_kwh * self_consumption_ratio
    annual_savings_inr = self_consumed_kwh * tariff_rate_inr_per_kwh
    
    # Monthly savings
    monthly_savings_inr = annual_savings_inr / 12.0
    
    # Payback period
    if annual_savings_inr > 0:
        payback_period_years = net_cost_inr / annual_savings_inr
    else:
        payback_period_years = float('inf')
    
    # CO₂ emissions avoided
    # Formula: 1 kWh = ~0.82 kg CO₂ in India (grid average)
    co2_avoided_kg_per_year = annual_generation_kwh * 0.82
    
    return {
        'monthly_savings_inr': round(monthly_savings_inr, 2),
        'annual_savings_inr': round(annual_savings_inr, 2),
        'payback_period_years': round(payback_period_years, 2) if payback_period_years != float('inf') else None,
        'co2_avoided_kg_per_year': round(co2_avoided_kg_per_year, 2),
        'net_cost_inr': round(net_cost_inr, 2),
        'self_consumed_kwh': round(self_consumed_kwh, 2),
    }


def analyze_sentiment_simple(text: str) -> float:
    """
    Simple sentiment analysis for vendor reviews.
    Uses keyword-based approach (can be replaced with VADER or other NLP models).
    
    Returns sentiment score from 0-1 (1 = most positive)
    """
    if not text:
        return 0.5
    
    text_lower = text.lower()
    
    # Positive keywords
    positive_words = [
        'excellent', 'great', 'good', 'amazing', 'wonderful', 'perfect',
        'satisfied', 'happy', 'recommend', 'professional', 'quality',
        'reliable', 'trustworthy', 'efficient', 'fast', 'quick'
    ]
    
    # Negative keywords
    negative_words = [
        'bad', 'poor', 'terrible', 'awful', 'disappointed', 'worst',
        'slow', 'delayed', 'broken', 'failed', 'complaint', 'issue',
        'problem', 'unreliable', 'expensive', 'overpriced'
    ]
    
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    total_sentiment_words = positive_count + negative_count
    if total_sentiment_words == 0:
        return 0.5  # Neutral
    
    # Calculate sentiment ratio
    sentiment_ratio = positive_count / total_sentiment_words
    
    # Normalize to 0-1 scale with slight bias toward positive
    return min(1.0, max(0.0, sentiment_ratio * 1.2))

