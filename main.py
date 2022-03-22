import sqlite3
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
import json
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
import gettext
from db.db import DB

# TODO: implement an architecture to abstract the different services
menu_voices = ["Join us!", "Add a new group"]
data = {}
NAME, SURNAME, UKRANIAN, RUSSIAN, POSITION, SKILLS = range(6)


def yes_no_keyboard(inline=True):
    if inline:
        return InlineKeyboardMarkup([[InlineKeyboardButton("Yes", callback_data="Yes"), InlineKeyboardButton("No", callback_data="No")]])
    else:
        return ReplyKeyboardMarkup([[ReplyKeyboardButton("Yes", callback_data="Yes"), ReplyKeyboardButton("No", callback_data="No")]])


def ping(update: Update, ctx: CallbackContext) -> None:
    ctx.bot.send_message(text="pong", chat_id=update.effective_chat.id)


def start(update: Update, ctx: CallbackContext) -> None:
    menu_kbd = ReplyKeyboardMarkup([[KeyboardButton(v) for v in menu_voices]])
    ctx.bot.send_message(text="Hi!\nWhat do you want to do?",
                         chat_id=update.effective_chat.id, reply_markup=menu_kbd)


def start_register_user(update: Update, ctx: CallbackContext):
    global data
    user = update.effective_user
    message = update.message

    if not data.get(user.id, False):
        data[user.id] = {}

    data[user.id]["id"] = user.id
    data[user.id]["chat_id"] = message.chat_id
    data[user.id]["username"] = user.username

    update.message.chat.send_message("What's your name?")

    return NAME


def save_name(update: Update, ctx: CallbackContext):
    global data

    data[update.effective_user.id]["name"] = update.message.text
    update.message.chat.send_message("What's your surname?")

    return SURNAME


def save_surname(update: Update, ctx: CallbackContext):
    global data

    data[update.effective_user.id]["surname"] = update.message.text
    update.message.chat.send_message(
        "Can you speak ukranian?", reply_markup=yes_no_keyboard())

    return UKRANIAN


def save_ukranian(update: Update, ctx: CallbackContext):
    global data

    update.callback_query.answer()
    data[update.effective_user.id]["ukranian"] = True if update.callback_query.data == "Yes" else False
    update.callback_query.message.chat.send_message(
        "Can you speak russian?", reply_markup=yes_no_keyboard())

    return RUSSIAN


def save_russian(update: Update, ctx: CallbackContext):
    global data

    update.callback_query.answer()
    data[update.effective_user.id]["russian"] = True if update.callback_query.data == "Yes" else False
    update.callback_query.message.chat.send_message("What's your location?")

    return POSITION


def save_skills(update: Update, ctx: CallbackContext):
    global data

    data[update.effective_user.id]["skills"] = update.message.text
    update.message.chat.send_message(
        "Yay! You joined the team.\nFeel free to add or change any information from the menu!")

    db_handler.save(list(data[update.effective_user.id].items()), "volunteers")
    return ConversationHandler.END


def start_register_group(chat):
    pass


def handle_error(update: Update, ctx: CallbackContext):
    update.message.reply_markdown('Invalid text')


def handle_messages(update: Update, ctx: CallbackContext) -> None:
    if update.message in menu_voices:
        if update.message.text == "Join us!":
            register_user(update.effective_user, update.message)
        elif update.message.text == "Add a new group":
            register_group(update.effective_chat)
        else:
            pass


def save_location(update: Update, ctx: CallbackContext):
    global data

    data[update.effective_user.id]["position"] = f"{update.message.location.latitude}, {update.message.location.longitude}"

    update.message.chat.send_message(
        "Insert your skills (music, languages spoken, etc.).\nEverything counts!")

    return SKILLS


if __name__ == "__main__":

    global db_handler

    settings = json.load(open('settings.json'))
    updater = Updater(settings['token'], use_context=True)
    _ = gettext.translation('bot', settings["localedir"], fallback=True)
    db_handler = DB('./db/data.db')

    updater.dispatcher.add_handler(CommandHandler('ping', ping))
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(
        ConversationHandler(
            entry_points=[
                MessageHandler(Filters.regex(
                    'Join us!'), start_register_user),
                MessageHandler(
                    Filters.regex('Add a new group'), start_register_group),
            ],
            # TODO: implement a dispatch approach to avoid code duplication
            states={
                NAME: [MessageHandler(Filters.all, save_name)],
                SURNAME: [MessageHandler(Filters.all, save_surname)],
                UKRANIAN: [CallbackQueryHandler(save_ukranian)],
                RUSSIAN: [CallbackQueryHandler(save_russian)],
                POSITION: [MessageHandler(Filters.location, save_location)],
                SKILLS: [MessageHandler(Filters.all, save_skills)]
            },
            fallbacks=[MessageHandler(Filters.text, handle_error)]
        )
    )
    updater.dispatcher.add_handler(
        MessageHandler(Filters.text, handle_messages))
    updater.dispatcher.add_handler(
        MessageHandler(Filters.location, save_location))

    updater.start_polling()
    updater.idle()
