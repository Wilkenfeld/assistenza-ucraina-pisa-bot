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
    ctx.bot.send_message(text="Hi!\nChoose a command from the menu or type /help to continue.",
                         chat_id=update.effective_chat.id)


def start_register_user(update: Update, ctx: CallbackContext):
    global data
    user = update.effective_user
    message = update.message

    if not data.get(user.id, False):
        data[user.id] = {}

    data[user.id]["id"] = user.id
    data[user.id]["chat_id"] = message.chat_id
    data[user.id]["username"] = user.username

    update.message.chat.send_message(
        "Welcome in the registration!\nUse /cancel to quit in any moment.")
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
    update.callback_query.message.chat.send_message(
        "What's your location?", 
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Share location", request_location=True)]], resize_keyboard=True, one_time_keyboard=True)
    )

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


def save_location(update: Update, ctx: CallbackContext):
    global data

    if update.message.location:
        data[update.effective_user.id]["position"] = f"{update.message.location.latitude}, {update.message.location.longitude}"
    else:
        data[update.effective_user.id]["position"] = update.message.text

    update.message.chat.send_message(
        "Insert your skills (music, languages spoken, etc.).\nEverything counts!")

    return SKILLS


def cancel_registration(update: Update, ctx: CallbackContext):
    global data

    del data[update.effective_user.id]
    update.effective_chat.send_message(
        'Registration canceled.\nFeel free to start again from the menu.')

    return ConversationHandler.END


def handle_timeout(update: Update, ctx: CallbackContext):
    global data

    del data[update.effective_user.id]
    update.effective_chat.send_message(
        'Registration canceled (due to timeout).\nFeel free to start again from the menu.')

    return ConversationHandler.END

def help_command(update: Update, ctx: CallbackContext): 

    update.effective_chat.send_message('''Available commands:
/register_volunteer - Register yourself as a volunteer
/register-group - Register a new group''')

if __name__ == "__main__":

    global db_handler

    settings = json.load(open('settings.json'))
    updater = Updater(settings['token'], use_context=True)
    _ = gettext.translation('bot', settings["localedir"], fallback=True)
    db_handler = DB('./db/data.db')

    updater.dispatcher.add_handler(CommandHandler('ping', ping))
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))

    updater.dispatcher.add_handler(
        ConversationHandler(
            entry_points=[
                MessageHandler(Filters.regex(
                    'Join us!'), start_register_user),
                CommandHandler('register_volunteer', start_register_user),
                MessageHandler(
                    Filters.regex('Add a new group'), start_register_group),
                CommandHandler('register_user', start_register_user),
            ],
            # TODO: implement a dispatch approach to avoid code duplication
            states={
                NAME: [MessageHandler(Filters.text & ~Filters.command, save_name)],
                SURNAME: [MessageHandler(Filters.text & ~Filters.command, save_surname)],
                UKRANIAN: [CallbackQueryHandler(save_ukranian)],
                RUSSIAN: [CallbackQueryHandler(save_russian)],
                POSITION: [MessageHandler((Filters.location | Filters.text) & ~Filters.command, save_location)],
                SKILLS: [MessageHandler(Filters.text & ~Filters.command, save_skills)],
                ConversationHandler.TIMEOUT: [
                    MessageHandler(Filters.all, handle_timeout)]
            },
            fallbacks=[CommandHandler('cancel', cancel_registration)],
            conversation_timeout=float(3600)  # conversation ends after an hour
        )
    )

    updater.start_polling()
    updater.idle()
