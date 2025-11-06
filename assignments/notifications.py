import logging
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)

def send_assignment_email(assignee_email: str, context: dict):
    """
    Send a formal assignment email (both text and HTML).
    context should contain keys: assignee_name, task_title, task_description,
    confidence_score, task_url (optional), assigned_by, assigned_at, summary_lines (optional list)
    """
    try:
        subject = f"[Assignment] New Task: {context.get('task_title')}"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [assignee_email]

        # Render plain text from template (fallback)
        text_content = render_to_string("assignments/email_assignment.txt", context)
        html_content = render_to_string("assignments/email_assignment.html", context)

        msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=to)
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        # ✅ Add this line below
        print(f"✅ Assignment email sent to {assignee_email}")

        # (Optional: keep logger also for file/debug logs)
        # logger.info("✅ Assignment email sent to %s", assignee_email)

    except Exception as e:
        # Log and swallow to avoid breaking main flow
        logger.exception("Failed to send assignment email to %s: %s", assignee_email, e)
