import logging
from random import getrandbits

import telegram
import zmq

import db

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
# A server to keep da links ##########
######################################
addr = 'tcp://127.0.0.1:5678'

class cTelegramServer():

    def __init__(self, data_requester):
        self.db_handler = db.c_database_handler(db_conn_str)
        self.data_requests_handler = data_requester
        # init command environment
        self.env = cCommandEnv(self.db_handler, self.data_requests_handler)
        self.updater = telegram.Updater(telegram_token, workers=10)
        self.job_queue = self.updater.job_queue
        # Get the dispatcher to register handlers
        self.dispatcher = self.updater.dispatcher
        self.init_handlers()
        # External queue for messages

    def get_job_queue(self):
        return self.job_queue

    def init_handlers(self):
        self.dispatcher.addTelegramCommandHandler("start", start)
        self.dispatcher.addTelegramCommandHandler("register", self.env.register)
        self.dispatcher.addTelegramCommandHandler("secret", self.env.secret)
        self.dispatcher.addTelegramCommandHandler("clients", self.env.clients)
        # self.dispatcher.addTelegramCommandHandler("listen", self.listen)
        self.dispatcher.addTelegramCommandHandler("alarm", self.alarm)

        self.dispatcher.addUnknownTelegramCommandHandler(unknown_command)
        self.dispatcher.addTelegramRegexHandler("^\?.*", self.env.search)
        self.dispatcher.addTelegramInlineHandler(self.env.inlinequery)
        self.dispatcher.addErrorHandler(error)

    def start(self):
        self.updater.start_polling()
        self.updater.idle()

    def alarm(self, bot, update, text=None, time=None):
        data = None
        # Info from chat
        if len(update.message.text.split(' ')) > 2:
            cmd, text, time = update.message.text.split(' ')
            text = str(text)
            time = int(time)
            # TODO write botid to base
            data = (text, time)
            print(data)

        # setup reply socket
        context = zmq.Context()
        sock = context.socket(zmq.REQ)
        sock.connect(addr)

        if data:
            sock.send_json(data)
            rep = sock.recv_json()
            bot.sendMessage(chat_id=update.message.chat_id, text = rep)
        else:
            for i in range(5):
                sock.send_json(['ping', i])
                rep = sock.recv_json()
                bot.sendMessage(chat_id=update.message.chat_id, text = rep)
                print('Ping got reply: {} from {}'.format(rep, update.message.chat_id))

        # TODO make wise disconnecting
        # sock.send_json(['plzdiekthxbye', None])


        # def listen(self, bot, update):
        #     """  long blocking process """
        #     print('hehe')
        #     for chat in self.ext_get_chats():
        #         bot.sendMessage(chat_id = update.message.chat_id, text = "starting")
        #     print('socket comming')
        #     for i in range(10):
        #         req = self.sock.recv_unicode()  # This also blocks
        #         print('Pong got request:', req)
        #         bot.sendMessage(chat_id = update.message.chat_id, text = "socket spam !!! ")
        #         self.sock.send_unicode('pong %s' % update.message.chat_id)

    # External calls from  (another thread!)
    def extjob_send_all(self, bot):
        for chat in self.ext_get_chats():
            bot.sendMessage(chat.chat_id, "some stupid reminder ")

    def ext_get_chats(self):
        return db.get_all_chats(self.db_handler.get_active_session())


######################################
# Environment for advanced commands ##
######################################

class cCommandEnv:
    def __init__(self, bot_db_handler, data_handler):
        self.db_hand = bot_db_handler
        self.data_handler = data_handler.make_test_client()

    def _check_user(self, user):
        usr_id = user.id
        return db.check_for_user(self.db_hand.get_active_session(), usr_id)

    def _check_user_new_con(self, user):
        self.db_hand2 = db.c_database_handler(db_conn_str)
        usr_id = user.id
        res = db.check_for_user(self.db_hand2.get_active_session(), usr_id)
        self.db_hand2.commit_and_close_session()
        return res

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
        self.db_hand.commit_session()
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
        bot.sendMessage(chat_id=update.message.chat_id, text="Chose client", reply_markup=reply_markup)

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

