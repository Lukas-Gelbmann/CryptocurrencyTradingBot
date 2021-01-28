from telegram import Update
from telegram.ext import CallbackContext


class Telegram:
    def __init__(self, framework):
        self.messaging = None
        self.framework = framework

    def start(self, update: Update, context: CallbackContext):
        self.messaging = update.message
        update.message.reply_text('You now receive messages about all the trades!')

    def stop(self, update: Update, context: CallbackContext):
        self.messaging = None
        update.message.reply_text('Messaging service disabled!')

    def response(self, update: Update, context: CallbackContext):
        update.message.reply_text('/help for more info')

    def help(self, update: Update, context: CallbackContext):
        update.message.reply_text(
            'To receive information about trades send /start\nTo get status send /status\nTo stop receiving '
            'information about trades send /stop')

    def status(self, update: Update, context: CallbackContext):
        holdings = self.framework.get_holdings()
        new_dict = dict()
        for (k, v) in holdings.items():
            if v != 0.0:
                new_dict[k] = v
        update.message.reply_text('Holdings:\n' + str(new_dict))
