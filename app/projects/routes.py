from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from ..extensions import db
from ..forms import ProjectForm
from ..models import Project
from ..utils.projects import build_projects_context

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")


@projects_bp.before_request
def require_journey():
    if not current_user.is_authenticated:
        return
    if not current_user.journey_completed:
        return redirect(url_for("subsidy.eligibility"))


def _save_image(file_storage) -> str | None:
    if not file_storage or not file_storage.filename:
        return None
    filename = secure_filename(file_storage.filename)
    if not filename:
        return None

    ext = Path(filename).suffix or ".png"
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid4().hex}{ext.lower()}"
    destination = upload_folder / unique_name
    file_storage.save(destination)
    return unique_name


@projects_bp.route("/", methods=["GET"])
@login_required
def list_projects():
    projects_context = build_projects_context(current_user.id)
    projects = projects_context["projects"]
    simulated_data = not projects_context["has_real_projects"]
    
    return render_template(
        "projects/index.html",
        title="Solar Projects",
        projects=projects,
        simulated_data=simulated_data,
    )


@projects_bp.route("/new", methods=["GET", "POST"])
@login_required
def add_project():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            user_id=current_user.id,
            name=form.name.data.strip(),
            installer=form.installer.data.strip() if form.installer.data else None,
            detail=form.detail.data,
            system_type=form.system_type.data,
            installation_date=form.installation_date.data,
        )

        image_file = request.files.get(form.image.name)
        image_filename = _save_image(image_file)
        if image_filename:
            project.image_filename = image_filename

        db.session.add(project)
        db.session.commit()
        flash("Project saved successfully.", "success")
        return redirect(url_for("projects.list_projects"))

    return render_template(
        "projects/new.html",
        title="Add Solar Project",
        form=form,
    )


@projects_bp.route("/<int:project_id>", methods=["GET"])
@login_required
def project_detail(project_id: int):
    projects_context = build_projects_context(current_user.id)
    
    if projects_context["has_real_projects"]:
        project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    else:
        abort(404, description="Project not found. Demo projects cannot be viewed in detail.")
    
    return render_template(
        "projects/detail.html",
        title=project.name,
        project=project,
    )


@projects_bp.route("/<int:project_id>/delete", methods=["POST"])
@login_required
def delete_project(project_id: int):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for("projects.list_projects"))

    if project.image_filename:
        upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
        image_path = upload_folder / project.image_filename
        if image_path.exists():
            image_path.unlink(missing_ok=True)

    db.session.delete(project)
    db.session.commit()
    flash("Project deleted.", "success")
    return redirect(url_for("projects.list_projects"))

