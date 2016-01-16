
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor

class cScheduler():
    def __init__(self):
        jobstores = {
            'default': SQLAlchemyJobStore(url='sqlite:///__secret//jobs.db')
        }
        executors = {
            'default': {'type': 'threadpool', 'max_workers': 20},
            'processpool': ProcessPoolExecutor(max_workers=5)
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 1
        }
        self.the_sched = BackgroundScheduler()
        self.the_sched.configure(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)

        self.telegram_server = None
        self.job_queue = None

    def start(self):
        self.the_sched.start()

    def set_telegram_server(self, telegram_server):
        self.telegram_server = telegram_server
        self.telegram_job_queue = telegram_server.get_job_queue()

    def start_main_schedule(self):
        self.telegram_job_queue.put(self.telegram_server.extjob_send_all, 5, repeat=True)


