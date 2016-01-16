"""
Demonstrates how to use the background scheduler to schedule a job that executes on 3 second
intervals.
"""

from datetime import datetime
import time
import os
from pytz import utc

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor

def tick():
    print('Tick! The time is: %s' % datetime.now())

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')
}
executors = {
    'default': {'type': 'threadpool', 'max_workers': 20},
    'processpool': ProcessPoolExecutor(max_workers=5)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

scheduler = BackgroundScheduler()
scheduler.configure(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)

job_added = scheduler.add_job(tick, 'interval', seconds=3)
scheduler.start()


print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

try:
    # This is here to simulate application activity (which keeps the main thread alive).
    while True:
        time.sleep(100)
except (KeyboardInterrupt, SystemExit):
    # Not strictly necessary if daemonic mode is enabled but should be done if possible
    scheduler.shutdown()