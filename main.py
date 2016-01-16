from data_requester import cDataRequester
from telbot import cTelegramServer
from scheduler import cScheduler

import threading

######################################
# MAIN ###############################
######################################

    # ######
    # sch = cSchedEnv()
    # sch.set_telegram_job_queue(job_queue)
    # sch.add_task_telegram_reminder("reminder from global scheduler")
    # sch.set_chats(db.get_all_chats(db_handler.get_active_session()))
    # ######


if __name__ == '__main__':
    # Init main data structures
    crm_data_manager = cDataRequester()
    telegram_server = cTelegramServer(crm_data_manager)
    sched = cScheduler()
    sched.set_telegram_server(telegram_server)
    # Start everything and hope for the best....
    sched.start()
    sched.start_main_schedule()
    telegram_server.start()

    #t_telegram = threading.Thread(target=)
    #t_telegram.start()









