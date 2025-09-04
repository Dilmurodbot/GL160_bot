"""
Balans o'zgarishlarini kuzatish va avtomatik xabar yuborish
"""
import asyncio
import logging
from typing import Dict, Set
from datetime import datetime, timezone, timedelta
from google_sheets import sheets_manager, previous_balances
from config import AUTHENTICATED_USERS

logger = logging.getLogger(__name__)

# Container balanslarini saqlash uchun
previous_container_balances = {}

class BalanceMonitor:
    def __init__(self, bot_application):
        self.app = bot_application
        self.is_running = False
        
    async def start_monitoring(self):
        """Balans kuzatishni boshlash"""
        self.is_running = True
        logger.info("🔍 Balans avtomatik kuzatish boshlandi")
        
        while self.is_running:
            try:
                await self.check_balance_changes()
                await asyncio.sleep(7)  # 7 soniya kutish
                
            except Exception as e:
                logger.error(f"Balans kuzatishda xatolik: {e}")
                await asyncio.sleep(10)  # Xatolik bo'lsa 10 soniya kutish
    
    def stop_monitoring(self):
        """Balans kuzatishni to'xtatish"""
        self.is_running = False
        logger.info("⏹️ Balans avtomatik kuzatish to'xtatildi")
    
    async def check_balance_changes(self):
        """Balans o'zgarishlarini tekshirish va xabar yuborish"""
        global previous_balances, previous_container_balances
        
        try:
            # Air balanslarni tekshirish
            current_balances = sheets_manager.get_all_users_balances()
            
            if current_balances:
                # Har bir foydalanuvchi uchun Air balans o'zgarishini tekshirish
                for phone, current_data in current_balances.items():
                    current_balance = current_data.get("balance", "0")
                    current_name = current_data.get("ism", "")
                    
                    # Oldingi balans bor yoki yo'qligini tekshirish
                    if phone in previous_balances:
                        old_balance = previous_balances[phone].get("balance", "0")
                        new_balance = current_data.get("balance", "0")
                        
                        # Balans o'zgargan bo'lsa
                        if old_balance != new_balance:
                            print(f"💰 Air {current_name}: {old_balance} → {new_balance}")
                            await self.send_balance_notification(phone, current_data, old_balance, new_balance)
                    
                    # Hozirgi balansni saqlash
                    previous_balances[phone] = current_data.copy()
            
            # Container balanslarni tekshirish
            await self.check_container_changes()
        
        except Exception as e:
            logger.error(f"Balans o'zgarishlarini tekshirishda xatolik: {e}")
    
    async def send_balance_notification(self, phone: str, user_data: Dict, old_balance: str, new_balance: str):
        """Balans o'zgarishi haqida xabar yuborish"""
        try:
            print(f"📨 DEBUG: Xabar yuborish uchun user_id qidirmoqda...")
            print(f"📞 DEBUG: Qidirilayotgan telefon: {phone}")
            
            # Avtentifikatsiya qilingan foydalanuvchini topish
            user_id = None
            user_phone = None
            
            print(f"👥 DEBUG: {len(AUTHENTICATED_USERS)} ta autentifikatsiya qilingan foydalanuvchi")
            
            for uid, auth_data in AUTHENTICATED_USERS.items():
                auth_phone = auth_data.get('telefon', '')
                clean_auth_phone = ''.join(filter(str.isdigit, auth_phone))
                
                print(f"🔍 DEBUG: User {uid}: {auth_phone} → clean: {clean_auth_phone}")
                
                if clean_auth_phone == phone:
                    user_id = uid
                    user_phone = auth_phone
                    print(f"✅ DEBUG: TOPILDI! User ID: {user_id}")
                    break
            
            if user_id:
                # Xabar matnini tayyorlash
                ism = user_data.get('ism', 'Nomalum')
                list_nomi = user_data.get('list_nomi', 'Nomalum')
                
                # O'zgarish miqdorini hisoblash
                try:
                    # Balanslarni float'ga aylantirishdan oldin vergul va bo'shliqlarni tozalash
                    # Avval string'ga aylantirish
                    old_str = str(old_balance) if old_balance else "0"
                    new_str = str(new_balance) if new_balance else "0"
                    
                    old_clean = old_str.replace(' ', '').replace(',', '.')
                    new_clean = new_str.replace(' ', '').replace(',', '.')
                    
                    old_amount = float(old_clean)
                    new_amount = float(new_clean)
                    difference = new_amount - old_amount
                    
                    # O'zgarish belgilarini qo'shish
                    if difference > 0:
                        change_text = f"📈 O'zgarish: +{difference:,.2f} $"
                        change_emoji = "📈"
                    elif difference < 0:
                        change_text = f"📉 O'zgarish: {difference:,.2f} $"
                        change_emoji = "📉"
                    else:
                        change_text = "🔄 O'zgarish: 0,00 $"
                        change_emoji = "🔄"
                    
                    # To'g'ri formatlash - vergul va bo'shliqlarni almashtirish
                    change_text = change_text.replace(',', ' ').replace('.', ',')
                    
                except (ValueError, TypeError):
                    change_text = "❓ O'zgarish: hisoblab bo'lmadi"
                    change_emoji = "❓"
                
                # Sana va soat qo'shish (O'zbekiston vaqti GMT+5)
                uzbekistan_tz = timezone(timedelta(hours=5))
                now = datetime.now(uzbekistan_tz)
                formatted_date = now.strftime("%d.%m.%Y")
                formatted_time = now.strftime("%H:%M")
                
                message = f"""🛩️{change_emoji} Air balans o'zgarishi

👤 Ism: {ism}
📱 Telefon: {user_phone}

💰 Oldingi balans: {old_balance} $
{change_text}
💰 Yangi balans: {new_balance} $

🕐 {formatted_date} - {formatted_time}"""
                
                print(f"📤 DEBUG: Xabar yuborilmoqda user {user_id} ga...")
                
                # Foydalanuvchiga xabar yuborish
                await self.app.bot.send_message(
                    chat_id=user_id,
                    text=message
                )
                
                # Avtoxabardan keyin balans tugmasini qaytarish (xabarsiz)
                from keyboards import BotKeyboards
                await self.app.bot.send_message(
                    chat_id=user_id,
                    text="💰",  # Faqat bitta emoji
                    reply_markup=BotKeyboards.persistent_mijoz_keyboard()
                )
                
                print(f"✅ DEBUG: Xabar muvaffaqiyatli yuborildi!")
                logger.info(f"💌 Balans o'zgarishi xabari yuborildi: {user_phone} ({old_balance} → {new_balance})")
            else:
                print(f"❌ DEBUG: User ID topilmadi telefon {phone} uchun")
        
        except Exception as e:
            logger.error(f"Balans xabarini yuborishda xatolik: {e}")
            print(f"💥 DEBUG: Xabar yuborishda xatolik: {e}")

    async def check_container_changes(self):
        """Container balans o'zgarishlarini tekshirish"""
        global previous_container_balances
        
        try:
            # Hozirgi Container ma'lumotlarini olish
            current_container_data = sheets_manager.get_container_data()
            
            if not current_container_data:
                return
            
            # Container ma'lumotlarini kod bo'yicha index qilish
            current_container_dict = {}
            for item in current_container_data:
                kod = item['kod']
                current_container_dict[kod] = item
            
            # Har bir kod uchun o'zgarishni tekshirish
            for kod, current_data in current_container_dict.items():
                current_summa = current_data.get('summa', 0)
                current_ism = current_data.get('ism', '')
                
                # Oldingi ma'lumot bor yoki yo'qligini tekshirish
                if kod in previous_container_balances:
                    old_summa = previous_container_balances[kod].get('summa', 0)
                    
                    # Summa o'zgargan bo'lsa
                    if old_summa != current_summa:
                        print(f"📦 Container {current_ism} ({kod}): {old_summa} → {current_summa}")
                        await self.send_container_notification(kod, current_data, old_summa, current_summa)
                
                # Hozirgi ma'lumotni saqlash
                previous_container_balances[kod] = current_data.copy()
        
        except Exception as e:
            logger.error(f"Container o'zgarishlarini tekshirishda xatolik: {e}")

    async def send_container_notification(self, kod: str, container_data: Dict, old_summa: float, new_summa: float):
        """Container balans o'zgarishi haqida xabar yuborish"""
        try:
            print(f"📦 DEBUG: Container kod {kod} uchun user_id qidirmoqda...")
            
            # Avtentifikatsiya qilingan foydalanuvchini kod orqali topish
            user_id = None
            user_phone = None
            
            for uid, auth_data in AUTHENTICATED_USERS.items():
                auth_kod = auth_data.get('kod', '')
                
                print(f"🔍 DEBUG: User {uid}: kod {auth_kod}")
                
                if auth_kod == kod:
                    user_id = uid
                    user_phone = auth_data.get('telefon', '')
                    print(f"✅ DEBUG: Container kod TOPILDI! User ID: {user_id}")
                    break
            
            if user_id:
                # Xabar matnini tayyorlash
                ism = container_data.get('ism', 'Nomalum')
                
                # O'zgarish miqdorini hisoblash
                try:
                    difference = new_summa - old_summa
                    
                    # O'zgarish belgilarini qo'shish
                    if difference > 0:
                        change_text = f"📈 O'zgarish: +{difference:.2f} $"
                        change_emoji = "📈"
                    elif difference < 0:
                        change_text = f"📉 O'zgarish: {difference:.2f} $"
                        change_emoji = "📉"
                    else:
                        change_text = "🔄 O'zgarish: 0,00 $"
                        change_emoji = "🔄"
                    
                except (ValueError, TypeError):
                    change_text = "❓ O'zgarish: hisoblab bo'lmadi"
                    change_emoji = "❓"
                
                # Sana va soat qo'shish (O'zbekiston vaqti GMT+5)
                uzbekistan_tz = timezone(timedelta(hours=5))
                now = datetime.now(uzbekistan_tz)
                formatted_date = now.strftime("%d.%m.%Y")
                formatted_time = now.strftime("%H:%M")
                
                message = f"""📦{change_emoji} Container balans o'zgarishi

👤 Ism: {ism}
📱 Telefon: {user_phone}
🆔 Kod: {kod}

💰 Oldingi balans: {old_summa:.2f} $
{change_text}
💰 Yangi balans: {new_summa:.2f} $

🕐 {formatted_date} - {formatted_time}"""
                
                print(f"📤 DEBUG: Container xabar yuborilmoqda user {user_id} ga...")
                
                # Foydalanuvchiga xabar yuborish
                await self.app.bot.send_message(
                    chat_id=user_id,
                    text=message
                )
                
                # Avtoxabardan keyin tugmalarni qaytarish (xabarsiz)
                from keyboards import BotKeyboards
                await self.app.bot.send_message(
                    chat_id=user_id,
                    text="💰📦",  # Emoji'lar
                    reply_markup=BotKeyboards.persistent_mijoz_keyboard()
                )
                
                print(f"✅ DEBUG: Container xabar muvaffaqiyatli yuborildi!")
                logger.info(f"📦 Container o'zgarishi xabari yuborildi: {kod} ({old_summa} → {new_summa})")
            else:
                print(f"❌ DEBUG: User ID topilmadi kod {kod} uchun")
        
        except Exception as e:
            logger.error(f"Container xabarini yuborishda xatolik: {e}")
            print(f"💥 DEBUG: Container xabar yuborishda xatolik: {e}")

# Global monitor instance
balance_monitor = None

def get_balance_monitor(app):
    """Balance monitor instance olish"""
    global balance_monitor
    if balance_monitor is None:
        balance_monitor = BalanceMonitor(app)
    return balance_monitor