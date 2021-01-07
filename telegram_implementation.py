from telegram import Update
from telegram.ext import CallbackContext


class Telegram:
    def __init__(self, framework):
        self.messaging = None
        self.framework = framework

    def start(self, update: Update, context: CallbackContext):
        self.messaging = update.message
        update.message.reply_text('Bot started!')

    def stop(self, update: Update, context: CallbackContext):
        self.messaging = None
        update.message.reply_text('Bot stopped!')

    def response(self, update: Update, context: CallbackContext):
        update.message.reply_text('/help for more info')

    def help(self, update: Update, context: CallbackContext):
        update.message.reply_text(
            'To receive trades send /start\nTo get status send /status\nTo stop receiving trades send /stop')

    def status(self, update: Update, context: CallbackContext):
        all = self.framework.get_holdings()
        new_dict = dict()
        for (k, v) in all.items():
            if v != 0.0:
                new_dict[k] = v
        update.message.reply_text('Holdings:\n' + str(new_dict))
