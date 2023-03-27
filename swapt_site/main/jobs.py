from django.utils import timezone

from schedule import Scheduler
import threading
import time

from .models import SwaptListingModel

# Deletes listings >= 30 days old
def delete_rejected_listings():
    SwaptListingModel._base_manager.filter(
        publishing_date__lt=timezone.now()-timezone.timedelta(days=30),
        stage=3
    ).delete()

# Top answer for this stackoverflow thread explains this more in detail
# https://stackoverflow.com/questions/44896618/django-run-a-function-every-x-seconds
def run_continuously(self, interval=1):
    """Continuously run, while executing pending jobs at each elapsed
    time interval.
    @return cease_continuous_run: threading.Event which can be set to
    cease continuous run.
    Please note that it is *intended behavior that run_continuously()
    does not run missed jobs*. For example, if you've registered a job
    that should run every minute and you set a continuous run interval
    of one hour then your job won't be run 60 times at each interval but
    only once.
    """

    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):

        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                self.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.setDaemon(True)
    continuous_thread.start()
    return cease_continuous_run

Scheduler.run_continuously = run_continuously

# Adds job and starts the scheduler
def start_scheduler():
    scheduler = Scheduler()
    scheduler.every().day.do(delete_rejected_listings)
    # scheduler.every().day.at("10:30").do(delete_rejected_listings)
    scheduler.run_continuously()