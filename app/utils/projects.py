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

    return {
        "projects": projects,
        "has_real_projects": has_real_projects,
    }

