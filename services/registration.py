from enum import Enum

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ConversationHandler, MessageHandler, CommandHandler, CallbackQueryHandler, Filters, \
    CallbackContext

from service import Service


def yes_no_keyboard(inline=True):
    if inline:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("Yes", callback_data="Yes"), InlineKeyboardButton("No", callback_data="No")]])
    else:
        return ReplyKeyboardMarkup(
            [[KeyboardButton("Yes", callback_data="Yes"), KeyboardButton("No", callback_data="No")]])


def handle_error(update: Update, _: CallbackContext):
    update.message.reply_markdown('Invalid text')


class Registration(Service):
    data: dict

    class __State(Enum):
        NAME, SURNAME, UKRANIAN, RUSSIAN, POSITION, SKILLS = range(6)

    def __init__(self, db=None, *args, **kwargs):
        super().__init__(db=db, *args, **kwargs)

    def register(self):
        return ConversationHandler(
            entry_points=[
                MessageHandler(Filters.regex(
                    'Join us!'), self.start_register_user),
                CommandHandler('register_volunteer', self.start_register_user),
            ],
            # TODO: implement a dispatch approach to avoid code duplication
            states={
                Registration.__State.NAME: [MessageHandler(Filters.text & ~Filters.command, self.save_name)],
                Registration.__State.SURNAME: [MessageHandler(Filters.text & ~Filters.command, self.save_surname)],
                Registration.__State.UKRANIAN: [CallbackQueryHandler(self.save_ukranian)],
                Registration.__State.RUSSIAN: [CallbackQueryHandler(self.save_russian)],
                Registration.__State.POSITION: [
                    MessageHandler((Filters.location | Filters.text) & ~Filters.command, self.save_location)],
                Registration.__State.SKILLS: [MessageHandler(Filters.text & ~Filters.command, self.save_skills)],
                ConversationHandler.TIMEOUT: [
                    MessageHandler(Filters.all, self.handle_timeout)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel_registration)],
            conversation_timeout=float(3600)  # conversation ends after an hour
        )

    def start_register_user(self, update: Update, _: CallbackContext):
        user = update.effective_user
        message = update.message

        if not self.data.get(user.id, False):
            self.data[user.id] = {}

        self.data[user.id]["id"] = user.id
        self.data[user.id]["chat_id"] = message.chat_id
        self.data[user.id]["username"] = user.username

        update.message.chat.send_message(
            "Welcome in the registration!\nUse /cancel to quit in any moment.")
        update.message.chat.send_message("What's your name?")

        return Registration.__State.NAME

    def save_name(self, update: Update, _: CallbackContext):
        self.data[update.effective_user.id]["name"] = update.message.text
        update.message.chat.send_message("What's your surname?")

        return Registration.__State.SURNAME

    def save_surname(self, update: Update, _: CallbackContext):
        self.data[update.effective_user.id]["surname"] = update.message.text
        update.message.chat.send_message(
            "Can you speak ukranian?", reply_markup=yes_no_keyboard())

        return Registration.__State.UKRANIAN

    def save_ukranian(self, update: Update, _: CallbackContext):
        update.callback_query.answer()
        self.data[update.effective_user.id]["ukranian"] = True if update.callback_query.data == "Yes" else False
        update.callback_query.message.chat.send_message(
            "Can you speak russian?", reply_markup=yes_no_keyboard())

        return Registration.__State.RUSSIAN

    def save_russian(self, update: Update, _: CallbackContext):
        update.callback_query.answer()
        self.data[update.effective_user.id]["russian"] = True if update.callback_query.data == "Yes" else False
        update.callback_query.message.chat.send_message(
            "What's your location?",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Share location", request_location=True)]],
                                             resize_keyboard=True, one_time_keyboard=True)
        )

        return Registration.__State.POSITION

    def save_skills(self, update: Update, _: CallbackContext):
        self.data[update.effective_user.id]["skills"] = update.message.text
        update.message.chat.send_message(
            "Yay! You joined the team.\nFeel free to add or change any information from the menu!")

        super().db.save(self.data[update.effective_user.id], "volunteers")
        return ConversationHandler.END

    def save_location(self, update: Update, _: CallbackContext):
        if update.message.location:
            self.data[update.effective_user.id][
                "position"] = f"{update.message.location.latitude}, {update.message.location.longitude}"
        else:
            self.data[update.effective_user.id]["position"] = update.message.text

        update.message.chat.send_message(
            "Insert your skills (music, languages spoken, etc.).\nEverything counts!")

        return Registration.__State.SKILLS

    def cancel_registration(self, update: Update, _: CallbackContext):

        del self.data[update.effective_user.id]
        update.effective_chat.send_message(
            'Registration canceled.\nFeel free to start again from the menu.')

        return ConversationHandler.END

    def handle_timeout(self, update: Update, _: CallbackContext):
        del self.data[update.effective_user.id]
        update.effective_chat.send_message(
            'Registration canceled (due to timeout).\nFeel free to start again from the menu.')

        return ConversationHandler.END
