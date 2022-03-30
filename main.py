import gettext
import inspect
import json
import os
import sys

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

from db.db import DB
from services.service import Service


def ping(update: Update, ctx: CallbackContext) -> None:
    ctx.bot.send_message(text="pong", chat_id=update.effective_chat.id)


def start(update: Update, ctx: CallbackContext) -> None:
    ctx.bot.send_message(text="Hi!\nChoose a command from the menu or type /help to continue.",
                         chat_id=update.effective_chat.id)


def start_register_group(chat):
    pass


def handle_error(update: Update, ctx: CallbackContext):
    update.message.reply_markdown('Invalid text')


def help_command(update: Update, ctx: CallbackContext):
    update.effective_chat.send_message('''Available commands:
/register_volunteer - Register yourself as a volunteer
/register-group - Register a new group''')


def load_services() -> list[tuple[str, Service]]:
    servs = []
    for filename in os.listdir('services'):
        modname = "services." + filename
        if sys.modules.get(modname, False):
            classes = inspect.getmembers(sys.modules[modname],
                                         predicate=lambda m: inspect.isclass(m) and (Service in m.__bases__))

            servs.extend([(name, obj(db=db_handler)) for name, obj in classes])

    return servs


if __name__ == "__main__":

    settings = json.load(open('settings.json'))
    updater = Updater(settings['token'], use_context=True)
    _ = gettext.translation('bot', settings["localedir"], fallback=True)
    db_handler = DB('bot', settings['db_passwd'], 'bot_data')

    updater.dispatcher.add_handler(CommandHandler('ping', ping))
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))

    services = load_services()

    for s in services:
        updater.dispatcher.add_handler(s[1].register())
        print(s[0], "registered!")

    updater.start_polling()
    updater.idle()
