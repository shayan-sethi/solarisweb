from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace
from typing import Any, List

from ..models import Project


def build_projects_context(user_id: int) -> dict[str, Any]:
    projects: List[Project] = (
        Project.query.filter_by(user_id=user_id)
        .order_by(Project.created_at.desc())
        .all()
    )
    has_real_projects = bool(projects)

    if has_real_projects:
        return {
            "projects": projects,
            "has_real_projects": True,
        }

    sample_projects = [
        SimpleNamespace(
            id=idx + 1,
            name=name,
            installer=installer,
            detail=detail,
            system_type=system_type,
            installation_date=installation_date,
            image_filename=None,
            created_at=created_at,
        )
        for idx, (name, installer, detail, system_type, installation_date, created_at) in enumerate([
            (
                "Residential Rooftop - Main Building",
                "GreenEnergy Solutions",
                "5 kW on-grid system installed on concrete rooftop. Net metering enabled with local DISCOM.",
                "on-grid",
                date.today() - timedelta(days=120),
                datetime.now() - timedelta(days=120),
            ),
            (
                "Garage Solar Installation",
                "SolarTech India",
                "3 kW hybrid system with battery backup for garage and workshop area.",
                "hybrid",
                date.today() - timedelta(days=85),
                datetime.now() - timedelta(days=85),
            ),
            (
                "Community Solar Project",
                "UrbanSpark Rooftech",
                "Shared 10 kW installation serving 4 residential units in cooperative housing.",
                "shared",
                date.today() - timedelta(days=45),
                datetime.now() - timedelta(days=45),
            ),
        ])
    ]

    return {
        "projects": sample_projects,
        "has_real_projects": False,
    }

