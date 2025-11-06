from rest_framework import serializers
from .models import Employee, Task, AssignmentLog

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = "__all__"


class TaskSerializer(serializers.ModelSerializer):
    assigned_to = EmployeeSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all(), write_only=True, source='assigned_to', required=False)
    created_by_id = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all(), write_only=True, source='created_by')

    class Meta:
        model = Task
        fields = ["id","title","description","priority","status","assigned_to","assigned_to_id","created_by_id","confidence_score","created_at","updated_at"]


class AssignmentLogSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    assigned_to = serializers.CharField(source='task.assigned_to.name', read_only=True, allow_null=True)
    task_status = serializers.CharField(source='task.status', read_only=True)
    
    class Meta:
        model = AssignmentLog
        fields = [
            'id', 
            'task', 
            'task_title', 
            'assigned_to',
            'task_status',
            'reasoning_text', 
            'confidence', 
            'reviewed_by', 
            'decision_status', 
            'created_at'
        ]
