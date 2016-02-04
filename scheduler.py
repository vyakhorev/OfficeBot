
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor
from datetime import datetime

import zmq

def tick():
    print('Tick! The time is: %s' % datetime.now())

class cScheduler():
    addr = 'tcp://127.0.0.1:5678'
    context = zmq.Context()
    work_receiver = context.socket(zmq.PULL)
    work_receiver.connect("tcp://127.0.0.1:5557")

    poller = zmq.Poller()
    poller.register(work_receiver, zmq.POLLIN)

    telegram_server = None
    last_msg = None

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

        # self.telegram_server = None
        self.job_queue = None


    def start(self):
        job_added = self.the_sched.add_job(tick, 'interval', seconds=3)
        self.the_sched.start()

    # def set_telegram_server(self, telegram_server):
    #     self.telegram_server = telegram_server
    #     self.telegram_job_queue = telegram_server.get_job_queue()

    # as server side
    @classmethod
    def remind(cls, bot):
        print(cls.__dict__)
        cls.telegram_server.extjob_send_all(bot)
        print('message in time')

    def start_main_schedule(self, dt, bot):
        self.the_sched.add_job(self.remind(bot), 'interval', seconds=dt)

    def reminder(self):
        while True:
            socks = dict(self.poller.poll(1000))
            if socks:
                if socks.get(self.work_receiver) == zmq.POLLIN:
                    mes = self.work_receiver.recv_json(zmq.NOBLOCK)
                    print(mes)
                    self.start_main_schedule(mes[1], mes[2])

                    break
            else:
                print("error: message timeout")
                break

        # req = cls.sock.recv_unicode()
        # print('got a task {}'.format(req))
        # cls.sock.send_unicode('as u wish')

    # def startme(self):
    #     self.reminder()


    # as client side
    @classmethod
    def send_to_tele(cls):
        cls.sock.send_unicode('spam spam spam from ')
        rep = cls.sock.recv_unicode()  # This blocks until we get something
        print('Ping got reply:', rep)
    #
    # def start_main_schedule(self):
    #     self.the_sched.add_job(self.send_to_tele, 'interval', seconds=12)


        # self.the_sched.add_job(self.send_to_tele, 'cron', second=12)
        # self.telegram_job_queue.put(self.send_to_tele, 5, repeat=True)

