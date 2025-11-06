

from django.contrib import admin
from .models import Employee, Task, AssignmentLog


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "role", "workload_score")
    search_fields = ("name", "email", "role", "skills", "responsibilities")
    list_filter = ("role",)
    ordering = ("name",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "status",
        "priority",
        "assigned_to",
        "confidence_score",
        "created_by",
    )
    search_fields = ("title", "description")
    list_filter = ("status", "priority")
    ordering = ("-id",)
    raw_id_fields = ("assigned_to", "created_by")


@admin.register(AssignmentLog)
class AssignmentLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "task",
        "confidence",
        "reviewed_by",
        "decision_status",
        "created_at",
    )
    search_fields = ("reasoning_text",)
    list_filter = ("decision_status",)
    ordering = ("-created_at",)

