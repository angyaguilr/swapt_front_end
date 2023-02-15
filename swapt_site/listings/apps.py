from django.apps import AppConfig
import os


class ListingsConfig(AppConfig):
    # Default app config
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'listings'

    # Start scheduler (for removing old rejected listings)
    def ready(self):
        from . import jobs
        
        if os.environ.get('RUN_MAIN', None) != 'true':
            jobs.start_scheduler()
    