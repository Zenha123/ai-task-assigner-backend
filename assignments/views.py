from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Employee, Task, AssignmentLog
from .serializers import EmployeeSerializer, TaskSerializer, AssignmentLogSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny

from .ai_engine import run_assignment_pipeline


class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Task.objects.all().order_by("-created_at")
    serializer_class = TaskSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()

        result = run_assignment_pipeline.delay(task.id)

        assigned_to = task.assigned_to.name if task.assigned_to else result.get("recommended_assignee")
        confidence = task.confidence_score or result.get("confidence_score", 0.0)
        reason = result.get("reasoning", "No reasoning provided")
        breakdown = result.get("confidence_breakdown", [])
        email_sent = result.get("email_sent", False)  # Add this
        
        return Response({
            "id": task.id,
            "title": task.title,
            "assigned_to": assigned_to,
            "confidence_score": confidence,
            "assignment_reason": reason,
            "confidence_breakdown": breakdown,
            "email_sent": email_sent,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def manual_assign(self, request, pk=None):
        task = self.get_object()
        assignee_id = request.data.get("assignee_id")
        decision = request.data.get("decision")  # "approve" / "reassign"
        assignee = get_object_or_404(Employee, pk=assignee_id)
        task.assigned_to = assignee
        task.status = "assigned"
        task.confidence_score = float(request.data.get("confidence", 0))
        task.save()
        AssignmentLog.objects.create(task=task, reasoning_text=f"Manual assignment: {decision}", confidence=task.confidence_score, decision_status="manager_assigned")
        return Response(TaskSerializer(task).data, status=status.HTTP_200_OK)


class AssignmentLogViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = AssignmentLog.objects.all().order_by("-created_at")
    serializer_class = AssignmentLogSerializer
