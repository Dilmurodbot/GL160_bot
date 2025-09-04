import os
import telebot
import logging
from time import sleep

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Bot ishga tushirilmoqda...")

# Telegram tokenini environment variable'dan olamiz
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN topilmadi!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# Oddiy start komandasi
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Bot ishlamoqda.")

# Misol uchun echo handler
@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, message.text)

# Botni polling bilan ishga tushirish
if __name__ == "__main__":
    while True:
        try:
            logger.info("Bot polling ishga tushdi...")
            bot.polling(none_stop=True)
        except Exception as e:
            logger.error(f"Xatolik yuz berdi: {e}")
            sleep(5)  # xatolikdan keyin 5 soniya kutish
