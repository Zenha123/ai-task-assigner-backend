from slack_sdk.web import WebClient
from django.conf import settings
from .models import Task, Employee
import os

slack_token = os.getenv('SLACK_BOT_TOKEN')
slack_client = WebClient(token=slack_token) if slack_token else None

def notify_assignment(task_id: int, assignee_id: int | None, decision_status: str):
    task = Task.objects.get(id=task_id)
    creator = task.created_by
    # Slack notify assigned user
    if assignee_id and slack_client:
        assignee = Employee.objects.get(id=assignee_id)
        try:
            slack_client.chat_postMessage(
                channel=assignee.email,  # might need mapping from employee to slack_id in real setup
                text=f"You have been assigned task: *{task.title}* (Confidence: {task.confidence_score:.2f})"
            )
        except Exception as e:
            # log error
            print("Slack notify failed:", e)
    # notify creator
    if slack_client and creator:
        try:
            slack_client.chat_postMessage(
                channel=creator.email,
                text=f"Task *{task.title}* processed. Decision: {decision_status} (Confidence: {task.confidence_score})"
            )
        except Exception as e:
            print("Slack notify failed:", e)
    # fallback: send email via Django EmailBackend
    from django.core.mail import send_mail
    send_mail(
        subject=f"Task processed: {task.title}",
        message=f"Decision: {decision_status}\nConfidence: {task.confidence_score}",
        from_email=os.getenv('EMAIL_HOST_USER'),
        recipient_list=[creator.email] + ([assignee.email] if assignee_id else [])
    )
