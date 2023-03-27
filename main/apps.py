from django.apps import AppConfig
import os


class MainConfig(AppConfig):
    name = 'main'

     # Start scheduler (for removing old rejected listings)
    def ready(self):
        from . import jobs
        
        if os.environ.get('RUN_MAIN', None) != 'true':
            jobs.start_scheduler()
    
