import os
from django.apps import AppConfig

class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'

    def ready(self):
        # Prevent scheduler from running twice when Django's autoreloader is active
        import attendance.signals
        
        if os.environ.get("RUN_MAIN") == "true":
            from .scheduler import start_scheduler
            start_scheduler()
            