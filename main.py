import os
import telebot
import logging
import threading
from time import sleep

# BalanceMonitor import qilamiz
try:
    from balance_monitor import BalanceMonitor
    monitoring_enabled = True
except ImportError:
    monitoring_enabled = False

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("Bot ishga tushirilmoqda...")

# Telegram token
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN topilmadi!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# ------------------------
# Background monitoring
# ------------------------
if monitoring_enabled:
    monitor = BalanceMonitor(bot_application=bot)
    threading.Thread(target=monitor.start_monitoring, daemon=True).start()
    logger.info("Background monitoring ishga tushdi...")

# ------------------------
# Start komandasi
# ------------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Bot ishlamoqda.")

# ------------------------
# Inline tugmalar uchun callback
# ------------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "air":
        bot.send_message(call.message.chat.id, "Siz Air tugmasini bosdingiz")
    elif call.data == "other":
        bot.send_message(call.message.chat.id, "Siz Other tugmasini bosdingiz")
    else:
        bot.send_message(call.message.chat.id, f"Siz {call.data} tugmasini bosdingiz")

# ------------------------
# Oddiy echo handler
# ------------------------
@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, message.text)

# ------------------------
# Pollingni ishga tushirish
# ------------------------
if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True, timeout=20, long_polling_timeout=30)
        except Exception as e:
            logger.error(f"Xatolik yuz berdi: {e}")
            sleep(10)
