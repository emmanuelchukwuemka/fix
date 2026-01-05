
from backend.app import create_app
from backend.extensions import db
from backend.models.task import UserTask, Task

app = create_app()
with app.app_context():
    task_id = 254
    task = Task.query.get(task_id)
    if task:
        print(f"Task: {task.title} (Active: {task.is_active})")
    else:
        print(f"Task {task_id} not found.")

    uts = UserTask.query.filter_by(task_id=task_id).all()
    print(f"UserTask records for task {task_id}:")
    for ut in uts:
        print(f"  User ID: {ut.user_id}, Status: {ut.status}")
