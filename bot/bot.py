"""
Class for Telegram bot object.
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, Filters
from telegram.ext import CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import MessageHandler
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update
import os
import re
import time
import logging



class Bot:
    def __init__(self, ACCESS_TOKEN, WEBHOOK_PORT, game_mechanic, players_db, words_db, LOG_PATH) -> None:
        self._access_token = ACCESS_TOKEN
        self._webhook_port = WEBHOOK_PORT
        self.game_mechanic = game_mechanic
        self._words = words_db
        self._players = players_db
        self.LOG_PATH = LOG_PATH
        self._START_BUTTON, self._TIP_BUTTON, self._SKIP_BUTTON = range(3)
        self._game = self.game_mechanic

        self.INSUFFICIENT_PERMISSIONS_TEXT = "You don't have permission to send this command."
        logging.basicConfig(filename=os.path.join(self.LOG_PATH, 'bot_logs.log'), level=logging.DEBUG)

        # Instance of the Telegram's Updater class, it receives our Access token.
        # The use_context argument sets the Telegram's backward compatibility to True.
        self._updater = Updater(token=self._access_token, use_context=True)

        # Creating a variable for quicker access to the the updater's dispatcher.
        self._dispatcher = self._updater.dispatcher

        # Adding the handlers to our callback functions.
        self._dispatcher.add_handler(CommandHandler("start", self._start_bot))
        self._dispatcher.add_handler(CommandHandler("addword", self._add_word))
        self._dispatcher.add_handler(CommandHandler("echoword", self._echo_word))
        self._dispatcher.add_handler(CommandHandler("leaderboard", self._leaderboard))
        self._dispatcher.add_handler(CommandHandler("mystats", self._mystats))
        self._dispatcher.add_handler(CommandHandler("makeadmin", self._make_admin))
        self._dispatcher.add_handler(CommandHandler("removeadmin", self._remove_admin))
        self._dispatcher.add_handler(CommandHandler("getword", self._get_word))
        self._dispatcher.add_handler(MessageHandler(Filters.text, callback=self._word_answer))

        # Adding the query handlers, responsible for handling the queries from the Keyboard Buttons.
        self._dispatcher.add_handler(CallbackQueryHandler(callback=self._start_game_button, pattern='^start_button$'))
        self._dispatcher.add_handler(CallbackQueryHandler(callback=self._get_tip, pattern='^show_tip_button$'))
        self._dispatcher.add_handler(CallbackQueryHandler(callback=self._skip_word, pattern='^skip_word_button$'))

        # Creates the option button below the welcome text, it will be passed as the reply_markup argument.
        self._starter_option_button_elements = [
            [InlineKeyboardButton(text='Start Game', callback_data='start_button')]
        ]

        self._starter_option_button = InlineKeyboardMarkup(self._starter_option_button_elements)
        ##################################################

        # Creates the option button for the progress game text, it will be passed as the reply_markup argument.
        self._game_status_button_elements = [
            [InlineKeyboardButton(text='Skip word', callback_data='skip_word_button'),
             InlineKeyboardButton(text='Show tip', callback_data='show_tip_button')]]

        self._game_status_button = InlineKeyboardMarkup(self._game_status_button_elements)
        ##################################################



    def _join_arguments(self, word: CallbackContext.args):
        """
        Tool function to join context arguments into a single word.
        """
        return " ".join(word)

    def _send_game_status(self, update: Update, context: CallbackContext):
        """
        Shows the game status page.
        """

        return update.message.reply_text(
            f"===================================================\n\n"
            f"The scrambled word is:\n\n {self._game.get_scrambled_word()}\n\n"
            f"You have:\n{self._game.get_tries()} "
            f"tries,\n{self._game.get_skips()} skips,\n{self._game.get_tips()} tips.\n "
            f"Reply this message with the correct word.\n\n"
            f"===================================================\n", reply_markup=self._game_status_button)

    def _send_welcome_page(self, update: Update, context: CallbackContext):
        """
        Shows the welcome page to the user.
        """

        update.message.reply_text(
            f"*                                            "
            f"Hello, {update.message.from_user.first_name}!                            "
            f"                 *\n"
            f"\n"
            f"\n"
            f"======WELCOME TO THE SCRAMBLED WORDS GAME======\n"
            f"\n"
            f"In this game, a random scrambled word is given to you and you have to guess it.\n"
            f"\n"
            f"Each correct word is equivalent to 1 point and it will be added to your score.\n"
            f"\n"
            f"If you can't guess a certain word, you have 3 chances to skip it and 3 tips to help"
            f" you figure it out.\n"
            f"\n"
            f"If you miss the word for 3 times, you lose.\n"
            f"\n"
            f"Press the command below to begin playing it let's rock!!!\n"
            f"\n"
            f"===================================================\n\n",
            reply_markup=self._starter_option_button)

    def _start_game_button(self, update: Update, context: CallbackContext) -> None:
        """
        Parses the callback query of the keyboard button and updates the message text.
        """

        query = update.callback_query

        query.message.edit_text(
            f"===================================================\n\n"
            f"The scrambled word is:\n\n {self._game.get_scrambled_word()}\n\n"
            f"You have:\n{self._game.get_tries()} "
            f"tries,\n{self._game.get_skips()} skips,\n{self._game.get_tips()} tips.\n "
            f"Reply this message with the correct word.\n\n"
            f"===================================================\n", reply_markup=self._game_status_button)

        query.answer()

    def _skip_word(self, update: Update, context: CallbackContext):

        query = update.callback_query

        self._game.skip_word()

        query.message.reply_text(
            f"===================================================\n\n"
            f"The scrambled word is:\n\n {self._game.get_scrambled_word()}\n\n"
            f"You have:\n{self._game.get_tries()} "
            f"tries,\n{self._game.get_skips()} skips,\n{self._game.get_tips()} tips.\n "
            f"Reply this message with the correct word.\n\n"
            f"===================================================\n", reply_markup=self._game_status_button)

        query.answer()

    def _get_tip(self, update: Update, context: CallbackContext):

        query = update.callback_query

        query.message.reply_text(
            self._game.show_tip()
        )

        query.message.reply_text(
            f"===================================================\n\n"
            f"The scrambled word is:\n\n {self._game.get_scrambled_word()}\n\n"
            f"You have:\n{self._game.get_tries()} "
            f"tries,\n{self._game.get_skips()} skips,\n{self._game.get_tips()} tips.\n "
            f"Reply this message with the correct word.\n\n"
            f"===================================================\n", reply_markup=self._game_status_button)

        query.answer()

    def _is_admin(self, username: str) -> bool:
        """
        Tool function to check whether a user is an admin.
        """
        if self._players.check_admin(username):
            return True
        else:
            return False

    def _start_bot(self, update: Update, context: CallbackContext):
        """
        Initial command to start the bot.
        """

        self._send_welcome_page(update, context)

        try:
            if not self._players.check_if_player_exists(update.message.from_user.username):
                self._players.add_player(
                    chat_id=update.message.from_user.id, 
                    first_name=update.message.from_user.first_name.encode('utf-8', errors='ignore'),
                    last_name=update.message.from_user.last_name,
                    username=update.message.from_user.username
                )

        except Exception as e:
            update.message.reply_text(f'Error adding player to the database: {e.args}.')


    def _word_answer(self, update: Update, context: CallbackContext):
        """
        Defines the answer behavior for the game
        """
        player_answer = update.message.text.lower()
        user_hiscore = self._players.get_stats(update.message.from_user.id)['hiscore']

        # Check if we are replying to the correct bot message.
        if ("The scrambled word is:" in update.message.reply_to_message.text and self._game.get_scrambled_word()
                in update.message.reply_to_message.text):

            result = self._game.check_word(player_answer)

            # If the user answer is not correct.
            if not result:

                if self._game.get_tries() >= 1:
                    update.message.reply_text("You missed it :/, try again.")
                    self._send_game_status(update, context)

                elif self._game.get_tries() < 1:
                    update.message.reply_text(
                        f"===================GAME OVER==================\n\n"
                        f"There are no tries remaining.\n\n"
                        f"You scored {self._game.get_score()} points.\n\n"
                        f"===============================================\n\n"
                    )

                    if self._game.get_score() > user_hiscore:
                        self._players.add_highest_score(update.message.from_user.id, self._game.get_score())
                        update.message.reply_text(
                            f"You have a new High Score !!!\n"
                            f"New HiScore: {self._game.get_score()} points."
                        )

                    self._game.reset_game()
                    time.sleep(1)
                    self._send_welcome_page(update, context)

            # If the user answer is correct.
            else:
                update.message.reply_text(
                    f"Congratulations you guessed it!\n\n"
                    f"The correct word was: {self._game.get_original_word()}\n\n"
                    f"You earned 1 point."
                )
                self._players.add_experience(update.message.from_user.id)
                self._game.get_new_word()
                self._send_game_status(update, context)


    def _add_word(self, update: Update, context: CallbackContext):
        """
        Command to add new words into the database. Only for admins
        """
        
        try:

            is_admin = self._is_admin(update.message.from_user.username)

            if not is_admin:
                update.message.reply_text(text=self.INSUFFICIENT_PERMISSIONS_TEXT)
                logging.warning(f"User: {update.message.from_user.username}, ID: {update.message.from_user.id} tried "
                                f" {__name__} command and got: {self.INSUFFICIENT_PERMISSIONS_TEXT}")

            else:
                original_word = self._join_arguments(context.args)
                pattern = re.search(r'^([a-zA-z]+)\s([\w\s\d.-]+)$', original_word)
                word = pattern.group(1)
                tip = pattern.group(2)

                if pattern:
                    try:
                        self._words.add_word(word, tip)
                        update.message.reply_text(text=f'Word "{word}" added successfully!')

                    except Exception as e:
                        update.message.reply_text(f"An error occurred when adding the word: {e.args}")
                
        
        except Exception as e:
            update.message.reply_text(f"Error adding a new word: {e}")


    def _get_word(self, update: Update, context: CallbackContext):
        """
        Command to test the database word query. Only for admins
        """
        if self._is_admin(update.message.from_user.username):
            update.message.reply_text(self._words.get_word())
        else:
            update.message.reply_text(self.INSUFFICIENT_PERMISSIONS_TEXT)
            logging.warning(f"User: {update.message.from_user.username}, ID: {update.message.from_user.id} tried "
                            f" {__name__} command and got: {self.INSUFFICIENT_PERMISSIONS_TEXT}")


    def _make_admin(self, update: Update, context: CallbackContext):
        """
        Command to make a player admin. Only for admins
        """
        username = self._join_arguments(context.args).strip('@')
        if self._is_admin(update.message.from_user.username):
            if self._players.check_if_player_exists(username):
                if self._is_admin(username):
                    update.message.reply_text(f"User @{username} is already an admin.")
                else:
                    self._players.grant_admin(username)
                    update.message.reply_text(f"Congratulations, @{username}!\nYou're now an admin.")
            else:
                update.message.reply_text("User not found, check the username and try again.")
        else:
            update.message.reply_text(self.INSUFFICIENT_PERMISSIONS_TEXT)
            logging.warning(f"User: {update.message.from_user.username}, ID: {update.message.from_user.id} tried "
                            f" {__name__} command and got: {self.INSUFFICIENT_PERMISSIONS_TEXT}")

    
    def _remove_admin(self, update: Update, context: CallbackContext):
        """
        Command to revoke a player admin. Only for admins
        """
        username = self._join_arguments(context.args).strip('@')
        if self._is_admin(update.message.from_user.username):
            if self._players.check_if_player_exists(username):
                if self._is_admin(username):
                    self._players.revoke_admin(username)
                    update.message.reply_text(f"User @{username}'s admin status has been revoked successfully.")
                else:
                    update.message.reply_text(f"@{username} is not an admin.")
            else:
                update.message.reply_text("User not found, check the username and try again.")
        else:
            update.message.reply_text(self.INSUFFICIENT_PERMISSIONS_TEXT)
            logging.warning(f"User: {update.message.from_user.username}, ID: {update.message.from_user.id} tried "
                            f" {__name__} command and got: {self.INSUFFICIENT_PERMISSIONS_TEXT}")


    def _echo_word(self, update: Update, context: CallbackContext):
        """
        Command to test context arguments handling. Admins only
        """
        phrase = self._join_arguments(context.args)
        pattern = re.search(r'^([a-zA-Z0-9]+)\s([\w\s\d,.]+)$', phrase)
        update.message.reply_text(f"You said: {phrase}\nGroup 1: {pattern.group(1)}\nGroup 2: {pattern.group(2)}")


    def _leaderboard(self, update: Update, context: CallbackContext):
        """
        Command to get the current leaderboard of the game.
        """
        leaderboard = self._players.get_leaderboard()
        returned_leaderboard = """========LEADERBOARD========\n\n"""
        for score in leaderboard:
            returned_leaderboard += score + "\n"
        update.message.reply_text(returned_leaderboard)


    def _mystats(self, update: Update, context: CallbackContext):
        """
        Command to get the player's current stats.
        """
        stats = self._players.get_stats(update.message.from_user.id)

        returned_stats = f"""
        ========STATS========\n\nName: {stats["name"]} {stats["last_name"]}\nUsername: @{update.message.from_user.
            username}\nXP: {stats['xp']}\nCurrent score: {self._game.get_score()}\nHiscore: {stats["hiscore"]} points"""

        update.message.reply_text(returned_stats)


    def run(self):
        """
        Main function to make the bot start to work.
        """
        try:
            self._updater.start_webhook(
                listen='0.0.0.0',
                port=int(self._webhook_port),
                url_path=self._access_token,
                webhook_url='https://scrambledwordsbot.herokuapp.com/' + self._access_token,
                force_event_loop=True
                )

            print(f"[*] BOT RUNNING ON LOCAL SERVER, TOKEN={self._access_token}!")
            logging.info(f"[*] BOT RUNNING ON LOCAL SERVER, TOKEN={self._access_token}!")
        except Exception as e:
            logging.exception(e.args)
            print(e.args)
