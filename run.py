from __future__ import annotations

from app import create_app, db
from app.models import User, Reminder, Project, HealthStat, HealthLog

app = create_app()
                               

@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Reminder": Reminder,
        "Project": Project,
        "HealthStat": HealthStat,
        "HealthLog": HealthLog,
    }


if __name__ == "__main__":
    app.run(debug=True, port=8080)

