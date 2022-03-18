import sqlite3
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
import json
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import gettext

menu_voices = ["Collabora con noi!", "Aggiungi un gruppo"]

def ping(update: Update, ctx: CallbackContext) -> None:
    ctx.bot.send_message(text="pong", chat_id=update.effective_chat.id)

def start(update: Update, ctx: CallbackContext) -> None:
    menu_kbd = ReplyKeyboardMarkup([[KeyboardButton(v) for v in menu_voices]])
    ctx.bot.send_message(text="Buongiorno!\nScegli una voce dal menù per continuare.", chat_id=update.effective_chat.id, reply_markup=menu_kbd)

def register_user(chat):
    pass

def register_group(chat):
    pass

def handle_messages(update: Update, ctx: CallbackContext) -> None:
    if update.message in menu_voices:
        if update.message == "Collabora con noi!":
            register_user(update.effective_chat)
        elif update.message == "Aggiungi un nuovo gruppo":
            register_group(update.effective_chat)

        
        

if __name__ == "__main__":
    
    settings = json.load(open('settings.json'))
    updater = Updater(settings['token'], use_context=True)
    _ = gettext.translation('bot', settings["localedir"], fallback=True)
    con = sqlite3.connect('./data.db')
    cur = con.cursor()

    updater.dispatcher.add_handler(CommandHandler('ping', ping))
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_messages))

    updater.start_polling()
    updater.idle()