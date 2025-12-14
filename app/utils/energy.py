from __future__ import annotations

import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from typing import Any, Dict, List

from ..models import EnergyLog


def build_energy_context(user_id: int) -> Dict[str, Any]:
    logs: List[EnergyLog] = (
        EnergyLog.query.filter_by(user_id=user_id)
        .order_by(EnergyLog.date.desc(), EnergyLog.created_at.desc())
        .all()
    )
    has_real_logs = bool(logs)

    daily_totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {"generation": 0.0, "consumption": 0.0, "export": 0.0, "revenue": 0.0}
    )

    if has_real_logs:
        for log in logs:
            date_key = log.date.strftime("%Y-%m-%d")
            day_totals = daily_totals[date_key]
            kwh_value = float(log.kwh or 0)
            entry_type = (log.entry_type or "").lower()
            if entry_type == "generation":
                day_totals["generation"] += kwh_value
            elif entry_type == "export":
                day_totals["export"] += kwh_value
            else:
                day_totals["consumption"] += kwh_value
            if log.revenue is not None:
                day_totals["revenue"] += float(log.revenue or 0)
    
    # Remove dummy data generation
    sample_logs: List[Any] = []

    daily_series = [
        {
            "date": date_key,
            "generation": round(values["generation"], 2),
            "consumption": round(values["consumption"], 2),
            "export": round(values["export"], 2),
            "revenue": round(values["revenue"], 2),
        }
        for date_key, values in sorted(daily_totals.items())
    ]

    total_generation = round(sum(item["generation"] for item in daily_series), 2)
    total_export = round(sum(item["export"] for item in daily_series), 2)
    total_revenue = round(sum(item["revenue"] for item in daily_series), 2)
    total_consumption = round(sum(item["consumption"] for item in daily_series), 2)

    insights: list[str] = []

    if daily_series:
        def friendly_date(value: str) -> str:
            return datetime.strptime(value, "%Y-%m-%d").strftime("%d %b %Y")

        average_generation = sum(item["generation"] for item in daily_series) / len(daily_series)
        insights.append(f"Average daily generation sits at {average_generation:.1f} kWh over the observed window.")

        latest = daily_series[-1]
        insights.append(
            f"Latest reading logged on {friendly_date(latest['date'])} produced {latest['generation']:.1f} kWh."
        )

        if total_generation:
            export_ratio = (total_export / total_generation) * 100
            insights.append(
                f"Export ratio is {export_ratio:.0f}% of total generation, highlighting grid contribution potential."
            )

        peak_generation_day = max(daily_series, key=lambda item: item["generation"])
        insights.append(
            f"Peak generation observed on {friendly_date(peak_generation_day['date'])} at {peak_generation_day['generation']:.1f} kWh."
        )

        if len(daily_series) >= 14:
            recent_week = daily_series[-7:]
            previous_week = daily_series[-14:-7]
            recent_total = sum(item["generation"] for item in recent_week)
            previous_total = sum(item["generation"] for item in previous_week)
            if previous_total:
                change = recent_total - previous_total
                direction = "up" if change >= 0 else "down"
                percent_change = abs(change) / previous_total * 100
                insights.append(f"Generation is {direction} {percent_change:.1f}% compared to the prior week.")
        if total_revenue:
            average_revenue = total_revenue / len(daily_series)
            insights.append(
                f"Revenue averages ₹{average_revenue:,.0f} per day with a cumulative ₹{total_revenue:,.0f}."
            )

    totals = {
        "generation": total_generation,
        "export": total_export,
        "revenue": total_revenue,
        "consumption": total_consumption,
    }

    return {
        "logs": logs if has_real_logs else sample_logs,
        "has_real_logs": has_real_logs,
        "daily_series": daily_series,
        "totals": totals,
        "insights": insights,
    }

