from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Task
from .notifications import send_assignment_email
import logging

logger = logging.getLogger(__name__)

# @receiver(post_save, sender=Task)
# def task_assignment_email(sender, instance: Task, created, **kwargs):
#     """
#     Send email when a Task becomes 'assigned'.
#     This runs safely: only triggers on new assignments (not every save).
#     """
#     try:
#         # Only trigger when the status is "assigned" and an employee is linked
#         if instance.status == "assigned" and instance.assigned_to and instance.assigned_to.email:
#             # We'll use updated_at as the assignment time
#             assigned_time = instance.updated_at or timezone.now()

#             # Prepare email context
#             context = {
#                 "assignee_name": instance.assigned_to.name,
#                 "task_title": instance.title,
#                 "task_description": instance.description,
#                 "confidence_score": instance.confidence_score or "N/A",
#                 "assigned_by": getattr(instance.created_by, "name", "AI System"),
#                 "assigned_at": assigned_time,
#                 "task_url": None,  # you can fill this later if you have a frontend link
#                 "summary_lines": [
#                     f"Priority: {instance.priority.capitalize()}",
#                     f"Status: {instance.status.capitalize()}",
#                 ]
#             }

#             # Send the email (safe inside try/except)
#             send_assignment_email(instance.assigned_to.email, context)
#             logger.info(f"✅ Assignment email triggered for task '{instance.title}' to {instance.assigned_to.email}")

#     except Exception as e:
#         logger.exception("⚠️ Error while sending assignment email: %s", e)
