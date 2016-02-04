from data_requester import cDataRequester
from telbot import cTelegramServer
from PongProcExample import pongproc
from scheduler import cScheduler

######################################
# MAIN ###############################
######################################
host = '127.0.0.1'
port = 5678

if __name__ == '__main__':
    # Init main data structures
    crm_data_manager = cDataRequester()
    telegram_server = cTelegramServer(crm_data_manager)
    sched = cScheduler()
    sched.start()
    pong_proc = pongproc.PongProc(bind_addr=(host, port))
    st = pong_proc.start()
    pong_proc.set_sheduler(sched)

    # sched.set_telegram_server(telegram_server)
    # Start everything and hope for the best....

    # sched.start()
    # sched.start_main_schedule()
    telegram_server.start()

    pong_proc.join()












