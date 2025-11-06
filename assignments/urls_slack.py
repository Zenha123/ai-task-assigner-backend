from django.urls import path
from . import slack_views

urlpatterns = [
    path("", slack_views.slack_event, name="slack_event"),
]
