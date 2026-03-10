import telebot
from dotenv import load_dotenv
import os

load_dotenv('keys.env')

CHAVE_API = os.getenv('bot')
ID_CHANNEL = int(os.getenv('chatid'))
DEBUG = int(os.getenv('debugid'))
OWNER = int(os.getenv('ownerid'))

bot = telebot.TeleBot(CHAVE_API)

@bot.message_handler(func=lambda message: True)
def filtru_acces(message):
    if message.chat.id == ID_CHANNEL or message.chat.id == DEBUG:
        print('Mesaj primit pe canalul LG')
    else:
        return

print('Botul este activ')
#bot.polling()