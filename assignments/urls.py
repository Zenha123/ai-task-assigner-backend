from django.urls import path, include
from rest_framework import routers
from assignments.views import EmployeeViewSet, TaskViewSet, AssignmentLogViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

router = routers.DefaultRouter()
router.register(r"employees", EmployeeViewSet)
router.register(r"tasks", TaskViewSet)
router.register(r"assignment_logs", AssignmentLogViewSet)

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("", include(router.urls)),
    path("webhook/slack/", include("assignments.urls_slack")),  # slack webhook endpoint
]
