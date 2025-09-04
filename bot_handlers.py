import logging
from telegram import Update
from telegram.ext import ContextTypes
import pandas as pd
import os
from datetime import datetime

from keyboards import BotKeyboards
from user_roles import UserRoleManager
from config import (ROLES, get_predefined_role, save_user_phone, get_user_phone, 
                    set_authenticated_user, is_user_authenticated, AUTHENTICATED_USERS,
                    set_pending_verification, get_pending_verification, remove_pending_verification)
from google_sheets import sheets_manager

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi handler'i"""
    user = update.effective_user
    user_id = user.id

    logger.info(f"Foydalanuvchi {user.first_name} (ID: {user_id}) botni ishga tushirdi")

    # Foydalanuvchi uchun oldindan belgilangan rolni tekshirish
    predefined_role = get_predefined_role(user_id)

    # Rolni o'rnatish
    UserRoleManager.assign_role(user_id, predefined_role)

    if predefined_role == ROLES["MIJOZ"]:
        # Mijoz uchun avval autentifikatsiya qilish
        if is_user_authenticated(user_id):
            # Agar autentifikatsiya qilingan bo'lsa, to'g'ridan-to'g'ri kirish
            welcome_text = f"Assalomu alaykum, {user.first_name}! 👋"
            await update.message.reply_text(
                welcome_text,
                reply_markup=BotKeyboards.persistent_mijoz_keyboard()
            )
        else:
            # Autentifikatsiya qilinmagan bo'lsa, telefon so'rash
            welcome_text = f"Assalomu alaykum, {user.first_name}! 👋\n\nBotdan foydalanish uchun telefon raqamingizni tasdiqlang:"
            await update.message.reply_text(
                welcome_text,
                reply_markup=BotKeyboards.phone_request_keyboard()
            )
    elif predefined_role == ROLES["MANAGER"]:
        welcome_text = f"Assalomu alaykum, {user.first_name}! 👋\n\nSiz manager sifatida kirdingiz."
        await update.message.reply_text(
            welcome_text,
            reply_markup=BotKeyboards.persistent_manager_keyboard()
        )
    elif predefined_role == ROLES["INVESTOR"]:
        welcome_text = f"Assalomu alaykum, {user.first_name}! 👋\n\nSiz investor sifatida kirdingiz."
        await update.message.reply_text(
            welcome_text,
            reply_markup=BotKeyboards.persistent_investor_keyboard()
        )
    elif predefined_role == "SUPER_USER":
        welcome_text = f"Assalomu alaykum, {user.first_name}! 👋\n\nQaysi rol sifatida kirishni xohlaysiz?"
        await update.message.reply_text(
            welcome_text,
            reply_markup=BotKeyboards.super_user_role_selection_keyboard()
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tugma bosishlarini qayta ishlash handler'i"""
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    await query.answer()

    logger.info(f"Foydalanuvchi {user_id} tugmani bosdi: {data}")

    try:
        # Super user rol tanlash
        if data.startswith("super_role_"):
            role_mapping = {
                "super_role_manager": ROLES["MANAGER"],
                "super_role_investor": ROLES["INVESTOR"]
            }
            selected_role = role_mapping.get(data)
            if selected_role:
                # Vaqtinchalik rolni o'rnatish
                UserRoleManager.assign_role(user_id, selected_role)
                
                if selected_role == ROLES["MANAGER"]:
                    text = f"👨‍💼 Manager paneli\n\nQuyidagi tugmalardan birini tanlang:"
                    await query.edit_message_text(
                        text,
                        reply_markup=BotKeyboards.super_user_manager_keyboard()
                    )
                elif selected_role == ROLES["INVESTOR"]:
                    text = f"💰 Investor paneli\n\nQuyidagi tugmalardan birini tanlang:"
                    await query.edit_message_text(
                        text,
                        reply_markup=BotKeyboards.super_user_investor_keyboard()
                    )

        # Rol tanlash (endi faqat oddiy userlar uchun)
        elif data.startswith("role_"):
            await query.edit_message_text("Sizning rolingiz tayinlangan va o'zgartirib bo'lmaydi.")

        # Rolni o'zgartirish (endi ishlatilmaydi)
        elif data == "change_role":
            await query.edit_message_text("Rolni o'zgartirish imkoni yo'q.")

        # Mijoz tugmalari
        elif data.startswith("mijoz_"):
            await handle_mijoz_actions(query, data)

        # Manager tugmalari
        elif data.startswith("manager_"):
            await handle_manager_actions(query, data)

        # Investor tugmalari
        elif data.startswith("investor_"):
            await handle_investor_actions(query, data)

        # Orqaga qaytish
        elif data == "back_to_manager":
            await show_manager_menu(query)
        elif data == "back_to_mijoz":
            await show_mijoz_menu(query)
        elif data == "back_to_investor":
            await show_investor_menu(query)
        elif data == "back_to_super_user":
            # Super user rol tanlashiga qaytish
            predefined_role = get_predefined_role(user_id)
            if predefined_role == "SUPER_USER":
                welcome_text = "Qaysi rol sifatida kirishni xohlaysiz?"
                await query.edit_message_text(
                    welcome_text,
                    reply_markup=BotKeyboards.super_user_role_selection_keyboard()
                )

        else:
            await query.edit_message_text("Noma'lum komanda!")

    except Exception as e:
        logger.error(f"Button handler xatoligi: {e}")
        await query.edit_message_text("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

async def handle_role_selection(query, data):
    """Rol tanlashni qayta ishlash"""
    user_id = query.from_user.id
    role_mapping = {
        "role_mijoz": ROLES["MIJOZ"],
        "role_manager": ROLES["MANAGER"],
        "role_investor": ROLES["INVESTOR"]
    }

    selected_role = role_mapping.get(data)
    if selected_role:
        UserRoleManager.assign_role(user_id, selected_role)

        if selected_role == ROLES["MIJOZ"]:
            await show_mijoz_menu(query)
        elif selected_role == ROLES["MANAGER"]:
            await show_manager_menu(query)
        elif selected_role == ROLES["INVESTOR"]:
            await show_investor_menu(query)

async def handle_role_change(query):
    """Rolni o'zgartirishni qayta ishlash"""
    text = "Yangi rolni tanlang:"
    await query.edit_message_text(
        text,
        reply_markup=BotKeyboards.role_selection_keyboard()
    )

async def show_mijoz_menu(query):
    """Mijoz menyusini ko'rsatish"""
    text = "👥 Mijoz paneli\n\nQuyidagi tugmalardan birini tanlang:"
    await query.edit_message_text(
        text,
        reply_markup=BotKeyboards.mijoz_keyboard()
    )

async def show_manager_menu(query):
    """Manager menyusini ko'rsatish"""
    text = "👨‍💼 Manager paneli\n\nQuyidagi tugmalardan birini tanlang:"
    await query.edit_message_text(
        text,
        reply_markup=BotKeyboards.manager_keyboard()
    )

async def show_investor_menu(query):
    """Investor menyusini ko'rsatish"""
    text = "💰 Investor paneli\n\nQuyidagi tugmalardan birini tanlang:"
    await query.edit_message_text(
        text,
        reply_markup=BotKeyboards.investor_keyboard()
    )

async def handle_mijoz_actions(query, data):
    """Mijoz tugmalarini qayta ishlash"""
    if data == "mijoz_balans":
        user_id = query.from_user.id
        logger.info(f"🎯 DEBUG: Mijoz {user_id} balans tugmasini bosdi")

        # Autentifikatsiya qilingan foydalanuvchi uchun telefon raqamni olish
        if is_user_authenticated(user_id):
            logger.info(f"🔐 DEBUG: Foydalanuvchi {user_id} autentifikatsiya qilingan")
            # Autentifikatsiya qilingan foydalanuvchi - ma'lumotni AUTHENTICATED_USERS'dan olish
            user_data = AUTHENTICATED_USERS.get(user_id, {})
            phone_number = user_data.get('telefon', get_user_phone(user_id))
            logger.info(f"📱 DEBUG: Telefon raqam: {phone_number}")
        else:
            logger.info(f"❌ DEBUG: Foydalanuvchi {user_id} autentifikatsiya qilinmagan")
            # Autentifikatsiya qilinmagan foydalanuvchi - telefon so'rash
            phone_number = get_user_phone(user_id)
            logger.info(f"📱 DEBUG: Saqlangan telefon: {phone_number}")

        if phone_number:
            # Telefon raqam bor - balansni ko'rsatish
            logger.info(f"💰 DEBUG: {phone_number} uchun balansni qidirmoqda...")
            await query.edit_message_text("⏳ Balans ma'lumotlari yuklanmoqda...")

            try:
                # Google Sheets'dan balans ma'lumotini olish
                logger.info(f"📊 DEBUG: Google Sheets'dan ma'lumot so'ramoqda...")
                balance_info = sheets_manager.find_user_balance(phone_number)
                logger.info(f"📋 DEBUG: Olingan ma'lumot: {balance_info}")

                if balance_info:
                    # Format qilishdan oldin raw ma'lumotni log qilish
                    if 'balance' in balance_info:
                        logger.info(f"💵 DEBUG: Raw balans: '{balance_info['balance']}'")

                    text = sheets_manager.format_balance_message(balance_info)
                    logger.info(f"📝 DEBUG: Formatlanган xabar: {text}")
                else:
                    logger.error(f"❌ DEBUG: balance_info None qaytarildi")
                    text = "❌ Balans ma'lumotini olishda xatolik yuz berdi."

            except Exception as e:
                logger.error(f"💥 DEBUG: Balans olishda xatolik: {e}")
                text = "❌ Balans ma'lumotini olishda texnik xatolik yuz berdi."

            await query.edit_message_text(
                text,
                reply_markup=BotKeyboards.mijoz_keyboard()
            )
        else:
            logger.info(f"📞 DEBUG: Telefon raqam yo'q, so'rashga o'tmoqda")
            # Telefon raqam yo'q - so'rash
            text = "💰 Balans ma'lumotini olish uchun telefon raqamingizni yuboring:"
            await query.edit_message_text(text)

            # Contact so'rash keyboard'ini yuborish
            await query.message.reply_text(
                "Quyidagi tugmani bosing:",
                reply_markup=BotKeyboards.phone_request_keyboard()
            )

async def handle_manager_actions(query, data):
    """Manager tugmalarini qayta ishlash"""
    if data == "manager_qarzdorlar":
        text = "📋 Qarzdorlar bo'limi\n\nQaysi turdagi qarzdorlarni ko'rmoqchisiz?"
        await query.edit_message_text(
            text,
            reply_markup=BotKeyboards.manager_qarzdorlar_keyboard()
        )

    elif data == "manager_air":
        print("✈️ Manager Air: Musbat balanslar yuklanmoqda...")
        # Loading xabari
        await query.edit_message_text("⏳ Musbat balanslar ro'yxati yuklanmoqda...")

        try:
            # Faqat 5$ dan ko'p musbat balansga ega mijozlarni olish
            positive_users = sheets_manager.get_positive_balances_over_amount(5.0)
            print(f"✅ Air musbat balanslar: {len(positive_users)} ta mijoz (5$+)")

            # Musbat balanslar ro'yxatini formatlash (Markdown formatida)
            text = sheets_manager.format_positive_balances_message(positive_users)

        except Exception as e:
            print(f"❌ Air musbat balanslar xatolik: {e}")
            logger.error(f"Musbat balanslar ro'yxatini olishda xatolik: {e}")
            text = "❌ Musbat balanslar ro'yxatini olishda xatolik yuz berdi."

        await query.edit_message_text(
            text,
            reply_markup=BotKeyboards.manager_qarzdorlar_keyboard(),
            parse_mode="Markdown"
        )

    elif data == "manager_container":
        print("📦 Manager Container: Ma'lumotlar yuklanmoqda...")
        # Loading xabari
        await query.edit_message_text("⏳ Container ma'lumotlari yuklanmoqda...")

        try:
            # Container sheet'dan 5$ dan yuqori summalarni olish
            container_data = sheets_manager.get_container_data()

            # Container ma'lumotlarini formatlash
            text = sheets_manager.format_container_message(container_data)

        except Exception as e:
            print(f"❌ Container ma'lumotlarini olishda xatolik: {e}")
            logger.error(f"Container ma'lumotlarini olishda xatolik: {e}")
            text = "❌ Container ma'lumotlarini olishda xatolik yuz berdi."

        await query.edit_message_text(
            text,
            reply_markup=BotKeyboards.back_keyboard("manager_qarzdorlar"),
            parse_mode="Markdown"
        )

async def handle_investor_actions(query, data):
    """Investor tugmalarini qayta ishlash"""
    if data == "investor_foyda":
        text = "📈 Foyda ma'lumotlari\n\nQaysi yil uchun foyda ma'lumotlarini ko'rmoqchisiz?"
        await query.edit_message_text(
            text,
            reply_markup=BotKeyboards.investor_years_keyboard()
        )
    
    elif data.startswith("investor_year_"):
        year = data.split("_")[-1]
        text = f"📅 {year} yili\n\nQaysi oy uchun foyda ma'lumotlarini ko'rmoqchisiz?"
        await query.edit_message_text(
            text,
            reply_markup=BotKeyboards.investor_months_keyboard(year)
        )
    
    elif data.startswith("investor_month_"):
        parts = data.split("_")
        year = parts[2]
        month = parts[3]
        
        # Oy nomini olish
        month_names = {
            "01": "Yanvar", "02": "Fevral", "03": "Mart", "04": "Aprel",
            "05": "May", "06": "Iyun", "07": "Iyul", "08": "Avgust",
            "09": "Sentyabr", "10": "Oktyabr", "11": "Noyabr", "12": "Dekabr"
        }
        month_name = month_names.get(month, month)
        
        # Loading xabari
        await query.edit_message_text(f"⏳ {year} yil {month_name} oyi ma'lumotlari yuklanmoqda...")
        
        try:
            # Google Sheets'dan foyda ma'lumotlarini olish (investor ID'si bilan)
            investor_id = query.from_user.id
            profit_data = sheets_manager.get_investor_profit_data(year, month, investor_id)
            text = sheets_manager.format_investor_profit_message(profit_data, year, month)
        except Exception as e:
            logger.error(f"Investor foyda ma'lumotini olishda xatolik: {e}")
            text = f"❌ {year} yil {month_name} oyi foyda ma'lumotlarini olishda xatolik yuz berdi."
        
        await query.edit_message_text(
            text,
            reply_markup=BotKeyboards.investor_months_keyboard(year),
            parse_mode="Markdown"
        )
    
    elif data == "investor_back_to_years":
        text = "📈 Foyda ma'lumotlari\n\nQaysi yil uchun foyda ma'lumotlarini ko'rmoqchisiz?"
        await query.edit_message_text(
            text,
            reply_markup=BotKeyboards.investor_years_keyboard()
        )

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telefon raqami yuborilganda ishlash"""
    user = update.effective_user
    contact = update.message.contact

    if contact and contact.user_id == user.id:
        phone_number = contact.phone_number
        logger.info(f"Foydalanuvchi {user.id} telefon raqamini yubordi: {phone_number}")

        # Telefon raqamni saqlash
        save_user_phone(user.id, phone_number)

        # Mijoz uchun autentifikatsiya jarayoni
        role = get_predefined_role(user.id)
        if role == ROLES["MIJOZ"] and not is_user_authenticated(user.id):
            # Loading xabari
            await update.message.reply_text("⏳ Telefon raqam tekshirilmoqda...")

            try:
                # Google Sheets'dan foydalanuvchi ma'lumotini olish
                user_info = sheets_manager.find_user_by_phone(phone_number)

                if user_info and user_info.get('kod'):
                    # Foydalanuvchi topilsa, kod so'rash
                    set_pending_verification(user.id, user_info)

                    from telegram import ReplyKeyboardRemove
                    await update.message.reply_text(
                        "📱 Telefon raqam tasdiqlandi!\n\n🔐 Endi tasdiqlash kodini yuboring:",
                        reply_markup=ReplyKeyboardRemove()
                    )
                else:
                    # Foydalanuvchi topilmasa
                    from telegram import ReplyKeyboardRemove
                    await update.message.reply_text(
                        "❌ Sizning telefon raqamingiz tizimda ro'yxatdan o'tmagan.\n\nAdmin bilan bog'laning.",
                        reply_markup=ReplyKeyboardRemove()
                    )

            except Exception as e:
                logger.error(f"Autentifikatsiya xatoligi: {e}")
                from telegram import ReplyKeyboardRemove
                await update.message.reply_text(
                    "❌ Texnik xatolik yuz berdi. Qaytadan urinib ko'ring.",
                    reply_markup=ReplyKeyboardRemove()
                )
        else:
            # Manager/Investor yoki allaqachon autentifikatsiya qilingan mijoz uchun balans
            await handle_balance_request(update, phone_number, user.id)
    else:
        await update.message.reply_text("Iltimos, o'zingizning telefon raqamingizni yuboring.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matn xabarlarini qayta ishlash handler'i"""
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()
    role = get_predefined_role(user_id)

    # Mijozlar uchun Air tugmasi
    if text == "✈️ Air" and role == ROLES["MIJOZ"] and is_user_authenticated(user_id):
        # Authenticated mijoz balansini ko'rsatish
        phone_number = get_user_phone(user_id)
        if phone_number:
            await handle_balance_request(update, phone_number, user_id)
        else:
            await update.message.reply_text("❌ Telefon raqam topilmadi.")
        return

    # Mijozlar uchun Container tugmasi
    if text == "📦 Container" and role == ROLES["MIJOZ"] and is_user_authenticated(user_id):
        # Authenticated mijoz Container ma'lumotini ko'rsatish
        phone_number = get_user_phone(user_id)
        if phone_number:
            await handle_container_request(update, phone_number, user_id)
        else:
            await update.message.reply_text("❌ Telefon raqam topilmadi.")
        return

    # Mijozlar uchun Umumiy balans tugmasi
    if text == "💰 Umumiy balans" and role == ROLES["MIJOZ"] and is_user_authenticated(user_id):
        # Authenticated mijoz umumiy balansini ko'rsatish
        phone_number = get_user_phone(user_id)
        if phone_number:
            await handle_total_balance_request(update, phone_number, user_id)
        else:
            await update.message.reply_text("❌ Telefon raqam topilmadi.")
        return

    # Manager tugmalari
    if role == ROLES["MANAGER"]:
        if text == "✈️ Air":
            await handle_manager_air_keyboard(update)
            return
        elif text == "📦 Container":
            await handle_manager_container_keyboard(update)
            return

    # Investor tugmalari
    if role == ROLES["INVESTOR"]:
        if text == "📈 Foyda":
            await handle_investor_foyda_keyboard(update)
            return

    # Kod verification uchun
    await code_verification_handler(update, context)

async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Excel fayl yuklash handler'i (faqat manager uchun)"""
    user_id = update.effective_user.id

    # Faqat manager foydalanishi mumkin
    current_role = UserRoleManager.get_role(user_id)
    predefined_role = get_predefined_role(user_id)
    
    # Super user bo'lsa, manager rolida ishlash imkoniyatini berish
    if predefined_role == "SUPER_USER":
        # Super user'lar manager funksiyalarini ishlatishi mumkin
        pass
    elif current_role != ROLES["MANAGER"]:
        await update.message.reply_text("❌ Siz Excel fayl yuklash huquqiga ega emassiz.")
        return

    try:
        # Fayl ma'lumotlarini olish
        document = update.message.document
        if not document:
            await update.message.reply_text("❌ Fayl topilmadi.")
            return

        # Excel fayl ekanligini tekshirish
        file_name = document.file_name
        if not (file_name.endswith('.xlsx') or file_name.endswith('.xls')):
            await update.message.reply_text("❌ Faqat Excel fayllar (.xlsx, .xls) qabul qilinadi.")
            return

        await update.message.reply_text("📁 Excel fayl yuklanmoqda...")

        # Faylni yuklab olish
        file = await context.bot.get_file(document.file_id)
        file_path = f"temp_{user_id}_{file_name}"
        await file.download_to_drive(file_path)

        await update.message.reply_text("📊 Excel fayl tahlil qilinyapti...")

        # Excel faylni o'qish va qayta ishlash
        result = await process_excel_file(file_path, file_name)

        # Vaqtinchalik faylni o'chirish
        if os.path.exists(file_path):
            os.remove(file_path)

        if result["success"]:
            # Muvaffaqiyatli natijani ko'rsatish
            await update.message.reply_text(
                f"✅ Excel fayl muvaffaqiyatli qayta ishlandi!\n\n"
                f"📊 Kodlar: {result['codes_count']} ta\n"
                f"📋 Topilgan kodlar: {result['found_codes']}\n"
                f"💰 Umumiy summa: {result['total_amount']}\n"
                f"📝 Yangilangan yozuvlar: {result['updated_records']}\n"
                f"❌ Topilmagan kodlar: {result['not_found_codes']}"
            )

            # Manager tugmalarini qaytadan ko'rsatish
            await update.message.reply_text(
                "🔄 Keyingi amal uchun tanlang:",
                reply_markup=BotKeyboards.manager_persistent_keyboard()
            )
        else:
            # Xatolik holati
            await update.message.reply_text(f"❌ Xatolik: {result['error']}")

            # Xatolik bo'lsa ham manager tugmalarini ko'rsatish
            await update.message.reply_text(
                "🔄 Qaytadan urinish yoki boshqa amal tanlang:",
                reply_markup=BotKeyboards.manager_persistent_keyboard()
            )

    except Exception as e:
        logger.error(f"Excel fayl yuklashda xatolik: {e}")
        await update.message.reply_text("❌ Excel fayl yuklashda xatolik yuz berdi.")

        # Exception holatida ham manager tugmalarini ko'rsatish
        await update.message.reply_text(
            "🔄 Qaytadan urinish yoki boshqa amal tanlang:",
            reply_markup=BotKeyboards.manager_persistent_keyboard()
        )

        # Vaqtinchalik faylni tozalash
        try:
            file_path = f"temp_{user_id}_{update.message.document.file_name if update.message.document else 'unknown'}"
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

async def process_excel_file(file_path, file_name):
    """Excel faylni qayta ishlash va Google Sheets'ga yozish"""
    try:
        print(f"📁 Excel fayl o'qilmoqda: {file_name}")

        # Excel faylni o'qish
        df = pd.read_excel(file_path)

        print(f"📊 Excel tuzilishi:")
        print(f"   📏 Qatorlar: {len(df)}")
        print(f"   📐 Ustunlar: {len(df.columns)}")
        print(f"   📋 Ustun nomlari: {list(df.columns)}")

        # MARK ustunini topish
        mark_column = None
        for col in df.columns:
            col_name = str(col).lower().strip()
            if col_name == 'mark' or col_name.startswith('mark'):
                mark_column = col
                break

        if mark_column is None:
            print("❌ MARK ustuni topilmadi! Mavjud ustunlar:")
            for col in df.columns:
                print(f"   - {col}")
            return {"success": False, "error": "MARK ustuni topilmadi"}

        print(f"📋 MARK ustuni topildi: '{mark_column}'")

        # TOTAL PRICE yoki TOTAL PIRCE ustunini topish
        total_price_column = None
        print(f"🔍 TOTAL PRICE ustunini qidirmoqda...")

        for col in df.columns:
            col_name = str(col).lower()
            print(f"   🔎 Tekshirilmoqda: '{col}' -> '{col_name}'")
            # TOTAL PRICE yoki TOTAL PIRCE ni qidirish
            if 'total' in col_name and ('price' in col_name or 'pirce' in col_name):
                total_price_column = col
                print(f"   ✅ TOTAL PRICE ustuni topildi: '{col}'")
                break

        if total_price_column is None:
            print("❌ TOTAL PRICE ustuni topilmadi! Mavjud ustunlar:")
            for col in df.columns:
                print(f"   - {col}")
            return {"success": False, "error": "TOTAL PRICE yoki TOTAL PIRCE ustuni topilmadi"}

        # MARK va TOTAL PRICE ma'lumotlarini birga olish
        codes_with_prices = []

        print(f"📊 MARK ustunidagi barcha qiymatlar: {df[mark_column].dropna().tolist()}")

        for index, row in df.iterrows():
            try:
                mark_value = row[mark_column]
                price_value = row[total_price_column]

                # Mark qiymatini tekshirish
                if pd.isna(mark_value):
                    continue

                # Mark kodini tozalash
                if isinstance(mark_value, (int, float)):
                    if pd.isna(mark_value):
                        continue
                    clean_code = str(int(mark_value))
                else:
                    clean_code = str(mark_value).strip()
                    if not clean_code or not clean_code.isdigit():
                        continue

                # Price qiymatini tozalash
                if pd.isna(price_value):
                    clean_price = 0.0
                else:
                    clean_price = float(price_value)

                codes_with_prices.append({
                    'code': clean_code,
                    'price': clean_price
                })

                print(f"✅ Qo'shildi: Kod {clean_code} → ${clean_price}")

            except Exception as e:
                print(f"⚠️ Qatorni qayta ishlashda xatolik: {e}")
                continue

        if not codes_with_prices:
            return {"success": False, "error": "Kodlar topilmadi"}

        print(f"📋 Excel'dan topilgan kodlar va narxlar: {len(codes_with_prices)} ta")
        print(f"📅 Bugungi sana: {datetime.now().strftime('%d.%m.%Y')}")
        print(f"✈️ Reys fayli: {file_name}")
        print("=" * 50)

        # Bugungi sana
        today = datetime.now().strftime("%d.%m.%Y")

        # Google Sheets'ga yozish
        found_codes = []
        not_found_codes = []
        updated_records = 0

        # Har bir kod va uning narxi uchun Google Sheets'da qidirish va update qilish
        for item in codes_with_prices:
            code = item['code']
            individual_price = item['price']
            # Sheets'dan kod qidirish
            user_info = sheets_manager.find_user_by_code(code)
            if user_info:
                found_codes.append(code)
                list_nomi = user_info.get('list_nomi', 'N/A')
                print(f"✅ Kod topildi: {code} - List: {list_nomi}")

                # Google Sheets'ga yozish - har bir kodning o'z narxi bilan
                result = await update_list_sheet(list_nomi, {
                    'sana': today,
                    'reys': file_name,
                    'tavsif': 'Yuk keldi',
                    'summa': individual_price
                })

                if result:
                    updated_records += 1
                    print(f"📝 {list_nomi} list'iga yozildi")
                else:
                    print(f"❌ {list_nomi} list'iga yozishda xatolik")
            else:
                not_found_codes.append(code)
                print(f"❌ Kod topilmadi: {code}")

        # Umumiy summa hisoblash
        total_amount = sum([item['price'] for item in codes_with_prices])

        return {
            "success": True,
            "found_codes": len(found_codes),
            "not_found_codes": len(not_found_codes),
            "total_amount": f"{total_amount:,.2f} $".replace(',', ' '),
            "updated_records": updated_records,
            "codes_found": found_codes,
            "codes_not_found": not_found_codes,
            "codes_count": len(codes_with_prices)
        }

    except Exception as e:
        print(f"❌ Excel qayta ishlashda xatolik: {e}")
        return {"success": False, "error": str(e)}

async def update_list_sheet(list_nomi, data):
    """Belgilangan list'ga ma'lumot yozish (haqiqiy Google Sheets)"""
    try:
        print(f"🔄 '{list_nomi}' list'iga yozilmoqda:")
        print(f"   📅 Sana: {data['sana']}")
        print(f"   ✈️ Reys: {data['reys']}")
        print(f"   📦 Tavsif: {data['tavsif']}")
        print(f"   💰 Summa: {data['summa']}")

        # Haqiqiy Google Sheets'ga yozish
        success = sheets_manager.write_to_list_sheet(list_nomi, data)

        if success:
            print(f"✅ '{list_nomi}' list'iga haqiqatan yozildi!")
            return True
        else:
            print(f"❌ '{list_nomi}' list'iga yozishda xatolik")
            return False

    except Exception as e:
        print(f"❌ List update'da xatolik: {e}")
        return False

async def code_verification_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kod tasdiqlash handler'i"""
    user = update.effective_user
    user_id = user.id

    # Faqat mijozlar uchun va kod kutayotgan holatda
    role = get_predefined_role(user_id)
    if role != ROLES["MIJOZ"] or is_user_authenticated(user_id):
        return

    pending_data = get_pending_verification(user_id)
    if not pending_data:
        return

    entered_code = update.message.text.strip()
    correct_code = pending_data.get('kod', '').strip()

    logger.info(f"Foydalanuvchi {user_id} kodni yubordi: {entered_code}")

    if entered_code == correct_code:
        # Kod to'g'ri - autentifikatsiya muvaffaqiyatli
        set_authenticated_user(user_id, pending_data)
        remove_pending_verification(user_id)

        await update.message.reply_text(
            f"✅ Kod tasdiqlandi!\n\nXush kelibsiz, {pending_data.get('ism', 'Mijoz')}!",
            reply_markup=BotKeyboards.persistent_mijoz_keyboard()
        )

        logger.info(f"Foydalanuvchi {user_id} muvaffaqiyatli autentifikatsiya qilindi")
    else:
        # Kod noto'g'ri
        await update.message.reply_text(
            "❌ Noto'g'ri kod!\n\n🔐 Iltimos, to'g'ri kodni kiriting:"
        )

async def handle_balance_request(update, phone_number, user_id):
    """Balans so'rovini qayta ishlash"""
    # Loading xabari
    await update.message.reply_text("⏳ Balans ma'lumotlari yuklanmoqda...")

    try:
        # Google Sheets'dan balans ma'lumotini olish
        balance_info = sheets_manager.find_user_balance(phone_number)

        if balance_info:
            text = sheets_manager.format_balance_message(balance_info)
        else:
            text = "❌ Balans ma'lumotini olishda xatolik yuz berdi."

    except Exception as e:
        logger.error(f"Balans olishda xatolik: {e}")
        text = "❌ Balans ma'lumotini olishda texnik xatolik yuz berdi."

    # Klaviaturani yashirish va natijani ko'rsatish
    from telegram import ReplyKeyboardRemove
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardRemove()
    )

    # Mijozlar uchun balans tugmasini qaytarish (xabarsiz)
    role = get_predefined_role(user_id)
    if role == ROLES["MIJOZ"]:
        # Tugmani xabarsiz qaytarish
        await update.message.reply_text(
            "💰📦",  # Emoji'lar
            reply_markup=BotKeyboards.persistent_mijoz_keyboard()
        )

async def handle_container_request(update, phone_number, user_id):
    """Container so'rovini qayta ishlash"""
    # Loading xabari
    await update.message.reply_text("⏳ Container ma'lumotlari yuklanmoqda...")

    try:
        # Google Sheets'dan foydalanuvchi ma'lumotini olish
        user_info = sheets_manager.find_user_by_phone(phone_number)

        if not user_info or not user_info.get('kod'):
            text = "❌ Sizning kodingiz tizimda topilmadi."
        else:
            user_kod = user_info.get('kod')
            # Container ma'lumotini olish
            container_info = sheets_manager.find_user_container_data(user_kod)

            if container_info:
                text = sheets_manager.format_user_container_message(container_info)
            else:
                text = "📦 Container ma'lumotlaringiz topilmadi yoki 5$ dan kam."

    except Exception as e:
        logger.error(f"Container ma'lumotini olishda xatolik: {e}")
        text = "❌ Container ma'lumotini olishda texnik xatolik yuz berdi."

    # Klaviaturani yashirish va natijani ko'rsatish
    from telegram import ReplyKeyboardRemove
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardRemove()
    )

    # Mijozlar uchun tugmalarni qaytarish (xabarsiz)
    role = get_predefined_role(user_id)
    if role == ROLES["MIJOZ"]:
        # Tugmalarni xabarsiz qaytarish
        await update.message.reply_text(
            "💰📦",  # Emoji'lar
            reply_markup=BotKeyboards.persistent_mijoz_keyboard()
        )

async def handle_total_balance_request(update, phone_number, user_id):
    """Umumiy balans so'rovini qayta ishlash"""
    # Loading xabari
    await update.message.reply_text("⏳ Umumiy balans ma'lumotlari yuklanmoqda...")

    try:
        # Air balansini olish
        air_balance_info = sheets_manager.find_user_balance(phone_number)

        # Container balansini olish
        container_info = None
        user_info = sheets_manager.find_user_by_phone(phone_number)
        if user_info and user_info.get('kod'):
            user_kod = user_info.get('kod')
            container_info = sheets_manager.find_user_container_data(user_kod)

        # Umumiy balans xabarini formatlash
        text = sheets_manager.format_total_balance_message(air_balance_info, container_info)

    except Exception as e:
        logger.error(f"Umumiy balans ma'lumotini olishda xatolik: {e}")
        text = "❌ Umumiy balans ma'lumotini olishda texnik xatolik yuz berdi."

    # Klaviaturani yashirish va natijani ko'rsatish
    from telegram import ReplyKeyboardRemove
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )

    # Mijozlar uchun tugmalarni qaytarish (xabarsiz)
    role = get_predefined_role(user_id)
    if role == ROLES["MIJOZ"]:
        # Tugmalarni xabarsiz qaytarish
        await update.message.reply_text(
            "💰📦",  # Emoji'lar
            reply_markup=BotKeyboards.persistent_mijoz_keyboard()
        )

async def handle_manager_air_keyboard(update):
    """Manager Air tugmasi uchun handler"""
    print("✈️ Manager Air: Musbat balanslar yuklanmoqda...")
    # Loading xabari
    await update.message.reply_text("⏳ Musbat balanslar ro'yxati yuklanmoqda...")

    try:
        # Faqat 5$ dan ko'p musbat balansga ega mijozlarni olish
        positive_users = sheets_manager.get_positive_balances_over_amount(5.0)
        print(f"✅ Air musbat balanslar: {len(positive_users)} ta mijoz (5$+)")

        # Musbat balanslar ro'yxatini formatlash (Markdown formatida)
        text = sheets_manager.format_positive_balances_message(positive_users)

    except Exception as e:
        print(f"❌ Air musbat balanslar xatolik: {e}")
        logger.error(f"Musbat balanslar ro'yxatini olishda xatolik: {e}")
        text = "❌ Musbat balanslar ro'yxatini olishda xatolik yuz berdi."

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )

async def handle_manager_container_keyboard(update):
    """Manager Container tugmasi uchun handler"""
    print("📦 Manager Container: Ma'lumotlar yuklanmoqda...")
    # Loading xabari
    await update.message.reply_text("⏳ Container ma'lumotlari yuklanmoqda...")

    try:
        # Container sheet'dan 5$ dan yuqori summalarni olish
        container_data = sheets_manager.get_container_data()

        # Container ma'lumotlarini formatlash
        text = sheets_manager.format_container_message(container_data)

    except Exception as e:
        print(f"❌ Container ma'lumotlarini olishda xatolik: {e}")
        logger.error(f"Container ma'lumotlarini olishda xatolik: {e}")
        text = "❌ Container ma'lumotlarini olishda xatolik yuz berdi."

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )

async def handle_investor_foyda_keyboard(update):
    """Investor Foyda tugmasi uchun handler"""
    text = "📈 Foyda ma'lumotlari\n\nQaysi yil uchun foyda ma'lumotlarini ko'rmoqchisiz?"
    await update.message.reply_text(
        text,
        reply_markup=BotKeyboards.investor_years_keyboard()
    )

async def handle_manager_qarzdorlar_keyboard(update):
    """Manager Qarzdorlar tugmasi uchun handler"""
    text = "📋 Qarzdorlar bo'limi\n\nQaysi turdagi qarzdorlarni ko'rmoqchisiz?"
    await update.message.reply_text(
        text,
        reply_markup=BotKeyboards.manager_qarzdorlar_keyboard()
    )