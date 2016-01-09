import telegram
import logging
import db

# Some structure that gives data.
from ClientsData import make_test_client

'''
Change for other bot:
:telegram_token:
    Your token
:db_conn_str:
    something like "sqlite:///__secret\\bot.db"
'''

try:
    from __secret.ini import token as telegram_token
    from __secret.ini import db_conn_str
except ImportError:
    telegram_token = 'TOKEN'
    db_conn_str = 'sqlite:///__secret\\bot.db'

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
        usr = db.cUser()
        usr.telegram_id = update.message.from_user.id
        usr.telegram_name = update.message.from_user.first_name
        self.db_hand.add_object_to_session(usr)
        bot.sendMessage(update.message.chat_id, text='Registration is done')
        self.db_hand.commit_and_close_session()

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
# MAIN ###############################
######################################

def main(token):
    # init db with alchemy
    db_handler = db.c_database_handler(db_conn_str)
    data_handler = make_test_client()

    env = cCommandEnv(db_handler, data_handler)

    updater = telegram.Updater(token, workers=10)
    job_queue = updater.job_queue
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    # on different commands - answer in Telegram
    dp.addTelegramCommandHandler("start", start)
    dp.addTelegramCommandHandler("register", env.register)
    dp.addTelegramCommandHandler("secret", env.secret)
    dp.addTelegramCommandHandler("clients", env.clients)

    dp.addUnknownTelegramCommandHandler(unknown_command)
    # dp.addTelegramMessageHandler(message)
    dp.addTelegramRegexHandler("^\?.*", env.search)
    # dp.addUnknownStringCommandHandler(unknown_cli_command)
    # dp.addStringRegexHandler('^?', env.search)
    # log all errors
    dp.addErrorHandler(error)
    # Start the Bot
    updater.start_polling()
    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main(telegram_token)