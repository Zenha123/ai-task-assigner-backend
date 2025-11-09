from django.db import models
from django.contrib.auth.models import AbstractUser


class Employee(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=200)
    skills = models.JSONField(default=list)  
    responsibilities = models.TextField(blank=True)
    workload_score = models.FloatField(default=0.0) 

    def __str__(self):
        return f"{self.name} ({self.role})"


class Task(models.Model):
    PRIORITY_CHOICES = [("low","Low"), ("medium","Medium"), ("high","High")]
    STATUS_CHOICES = [("open","Open"), ("assigned","Assigned"), ("in_progress","In Progress"),
                      ("done","Done"), ("review","Review")]

    title = models.CharField(max_length=500)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    assigned_to = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.SET_NULL, related_name='tasks')
    created_by = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_tasks')
    confidence_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AssignmentLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='logs')
    reasoning_text = models.TextField()
    confidence = models.FloatField()
    reviewed_by = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.SET_NULL)
    decision_status = models.CharField(max_length=50)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for {self.task_id} ({self.decision_status})"
