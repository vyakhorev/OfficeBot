from data_requester import cDataRequester
from telbot import cTelegramServer
from scheduler import cScheduler

######################################
# MAIN ###############################
######################################

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









