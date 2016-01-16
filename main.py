import telegram
import logging
import db
from random import getrandbits

# Some structure that gives data.
from ClientsData import make_test_client

'''
Change to run your own bot:
    :telegram_token:
        Your token
    :db_conn_str:
        A connection string for a database (see example below)
'''

try:
    from __secret.ini import token as telegram_token
    from __secret.ini import db_conn_str
except ImportError:
    telegram_token = 'TOKEN'
    db_conn_str = 'sqlite:///bot.db'

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

######################################
# Environment for advanced commands ##
######################################

class cCommandEnv:
    def __init__(self, bot_db_handler, data_handler):
        self.db_hand = bot_db_handler
        self.data_handler = data_handler

    def _check_user(self, user):
        usr_id = user.id
        return db.check_for_user(self.db_hand.get_active_session(), usr_id)

    def _keyboard_from_data(self):
        # TODO make generator for big clients list
        keyboard = []
        for client in self.data_handler.values():
            keyboard.append(['?' + client.name])
        return keyboard

    def register(self, bot, update):
        if self._check_user(update.message.from_user):
            bot.sendMessage(update.message.chat_id, text='Already registered')
            return
        # TODO: mechanics for registering
        bot.sendMessage(update.message.chat_id, text='Doing registration')
        # create user
        usr = db.cUser()
        usr.telegram_id = update.message.from_user.id
        usr.telegram_name = update.message.from_user.first_name
        # create chat_id
        chat = db.cChat()
        chat.chat_id = update.message.chat_id
        chat.user = usr
        #
        self.db_hand.add_object_to_session(usr)
        self.db_hand.add_object_to_session(chat)
        self.db_hand.commit_and_close_session()
        bot.sendMessage(update.message.chat_id, text='Registration is done')

    def search(self, bot, update):
        txt = update.message.text[1:]
        bot.sendMessage(update.message.chat_id, text='lookig for *{}*'.format(txt),parse_mode='Markdown')
        if txt in self.data_handler:
            data = self.data_handler[txt].get_data()
            bot.sendMessage(update.message.chat_id, text='*data* \n {}'.format(data),parse_mode='Markdown')
        else :
            print('Unknown client')

    def clients(self, bot, update):
        keyboard = self._keyboard_from_data()
        reply_markup = telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        bot.sendMessage(chat_id=update.message.chat_id, text="Chose client",reply_markup=reply_markup)

    def secret(self, bot, update):
        if not(self._check_user(update.message.from_user)):
            bot.sendMessage(update.message.chat_id, text='xakghd lkjg ?')
            return
        bot.sendMessage(update.message.chat_id, text='Secret data !')

    def inlinequery(self, bot, update):
        if update.inline_query is not None and update.inline_query.query:
            query = update.inline_query.query
            results = []
            Ar = telegram.InlineQueryResultArticle
            results += [Ar(id=hex(getrandbits(64))[2:],
                           title='secret 1',
                           message_text='This is a very high secret!')]
            results += [Ar(id=hex(getrandbits(64))[2:],
                           title='secret 2',
                           message_text='This is TOP secret!')]
            bot.answerInlineQuery(update.inline_query.id, results=results)

######################################
# Basic commands #####################
######################################

def unknown_command(bot, update):
    bot.sendMessage(update.message.chat_id, text='Command not recognized!')

def unknown_cli_command(bot, update):
    logger.warn("Command not found: %s" % update)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='Wrong one!')

######################################
# Schedule ###########################
######################################

from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor

class cSchedEnv():
    def __init__(self):
        jobstores = {
            'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')
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
        self.telegram_chats = []

    def start(self):
        self.the_sched.start()

    def set_telegram_job_queue(self, job_queue):
        self.job_queue = job_queue

    def set_chats(self, chat_list):
        for ch_i in chat_list:
            self.telegram_chats += [ch_i.chat_id]

    def add_task_telegram_reminder(self, msg):
        # reminds every user about something
        self.job_queue.put(self._telegram_job_reminder, 5, repeat=False)

    def _telegram_job_reminder(self, bot):
        for chat_id in self.telegram_chats:
            bot.sendMessage(chat_id, "some stupid reminder from a bad structured code")



######################################
# MAIN ###############################
######################################

def main(token):
    # init user db with alchemy
    db_handler = db.c_database_handler(db_conn_str)
    data_handler = make_test_client()

    # init command environment
    env = cCommandEnv(db_handler, data_handler)

    updater = telegram.Updater(token, workers=10)
    job_queue = updater.job_queue
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    ######
    sch = cSchedEnv()
    sch.set_telegram_job_queue(job_queue)
    sch.add_task_telegram_reminder("reminder from global scheduler")
    sch.set_chats(db.get_all_chats(db_handler.get_active_session()))
    ######

    # on different commands - answer in Telegram
    dp.addTelegramCommandHandler("start", start)
    dp.addTelegramCommandHandler("register", env.register)
    dp.addTelegramCommandHandler("secret", env.secret)
    dp.addTelegramCommandHandler("clients", env.clients)
    dp.addUnknownTelegramCommandHandler(unknown_command)
    dp.addTelegramRegexHandler("^\?.*", env.search)
    dp.addTelegramInlineHandler(env.inlinequery)
    dp.addErrorHandler(error)
    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main(telegram_token)