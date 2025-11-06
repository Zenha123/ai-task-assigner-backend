# from django.apps import AppConfig


# class AssignmentsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'assignments'



# assignments/apps.py
from django.apps import AppConfig

class AssignmentsConfig(AppConfig):
    name = "assignments"

    def ready(self):
        # import signals to register them
        from . import signals  # noqa: F401
