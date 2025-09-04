import logging
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from bot_handlers import start_handler, button_handler, contact_handler, text_handler, document_handler
from config import get_bot_token

# Logging sozlamalari - HTTP so'rovlarni yashirish
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Webhook va HTTP so'rovlarni yashirish
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.Application").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main():
    """Bot ishga tushirish funksiyasi"""
    # Bot tokenini olish
    bot_token = get_bot_token()
    
    if not bot_token:
        logger.error("BOT_TOKEN muhit o'zgaruvchisi topilmadi!")
        return
    
    # Application yaratish
    application = Application.builder().token(bot_token).build()
    
    # Handler'larni qo'shish
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    application.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    # Balans monitorini post_init'da boshlash
    async def post_init(app):
        """Bot ishga tushgandan keyin balans kuzatishni boshlash"""
        from balance_monitor import get_balance_monitor
        monitor = get_balance_monitor(app)
        
        # Webhook'ni tozalash
        try:
            await app.bot.delete_webhook()
            logger.info("Webhook tozalandi")
        except Exception as e:
            logger.warning(f"Webhook tozalashda ogohlantirish: {e}")
        
        # Background task sifatida ishga tushirish
        import asyncio
        asyncio.create_task(monitor.start_monitoring())
        logger.info("🔍 Balans avtomatik kuzatish background'da boshlandi")
    
    application.post_init = post_init
    
    # Bot ishga tushirish
    logger.info("Bot ishga tushirilmoqda...")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi")
    except Exception as e:
        logger.error(f"Botda xatolik yuz berdi: {e}")
