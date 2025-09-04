from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

class BotKeyboards:
    """Bot klaviaturalarini yaratish sinfi"""
    
    @staticmethod
    def role_selection_keyboard():
        """Rol tanlash klaviaturasi"""
        keyboard = [
            [InlineKeyboardButton("👥 Mijoz", callback_data="role_mijoz")],
            [InlineKeyboardButton("👨‍💼 Manager", callback_data="role_manager")],
            [InlineKeyboardButton("💰 Investor", callback_data="role_investor")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def mijoz_keyboard():
        """Mijoz uchun klaviatura"""
        keyboard = [
            [InlineKeyboardButton("✈️ Air", callback_data="mijoz_balans")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def manager_keyboard():
        """Manager uchun klaviatura - doim ko'rinadigan"""
        keyboard = [
            [InlineKeyboardButton("📋 Qarzdorlar", callback_data="manager_qarzdorlar")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def manager_persistent_keyboard():
        """Manager uchun doim ko'rinadigan klaviatura"""
        keyboard = [
            [InlineKeyboardButton("📋 Qarzdorlar", callback_data="manager_qarzdorlar")],
            [InlineKeyboardButton("📊 Hisobotlar", callback_data="manager_hisobotlar")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def manager_qarzdorlar_keyboard():
        """Manager qarzdorlar bo'limi uchun klaviatura - doim ko'rinadigan"""
        keyboard = [
            [InlineKeyboardButton("✈️ Air", callback_data="manager_air")],
            [InlineKeyboardButton("📦 Container", callback_data="manager_container")],
            [InlineKeyboardButton("📋 Qarzdorlar", callback_data="manager_qarzdorlar")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_manager")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def investor_keyboard():
        """Investor uchun klaviatura"""
        keyboard = [
            [InlineKeyboardButton("📈 Foyda", callback_data="investor_foyda")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_keyboard(callback_data):
        """Orqaga qaytish tugmasi"""
        keyboard = [
            [InlineKeyboardButton("🔙 Orqaga", callback_data=callback_data)]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def super_user_role_selection_keyboard():
        """Super user uchun rol tanlash klaviaturasi"""
        keyboard = [
            [InlineKeyboardButton("👨‍💼 Manager", callback_data="super_role_manager")],
            [InlineKeyboardButton("💰 Investor", callback_data="super_role_investor")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def super_user_manager_keyboard():
        """Super user Manager menyusi"""
        keyboard = [
            [InlineKeyboardButton("📋 Qarzdorlar", callback_data="manager_qarzdorlar")],
            [InlineKeyboardButton("🔙 Rol tanlash", callback_data="back_to_super_user")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def super_user_investor_keyboard():
        """Super user Investor menyusi"""
        keyboard = [
            [InlineKeyboardButton("📈 Foyda", callback_data="investor_foyda")],
            [InlineKeyboardButton("🔙 Rol tanlash", callback_data="back_to_super_user")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def phone_request_keyboard():
        """Telefon raqamini so'rash uchun klaviatura"""
        keyboard = [
            [KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]
        ]
        return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    @staticmethod
    def persistent_mijoz_keyboard():
        """Mijoz uchun doim ko'rinadigan tugmalar"""
        keyboard = [
            [KeyboardButton("✈️ Air"), KeyboardButton("📦 Container")],
            [KeyboardButton("💰 Umumiy balans")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    @staticmethod
    def persistent_manager_keyboard():
        """Manager uchun doim ko'rinadigan tugmalar"""
        keyboard = [
            [KeyboardButton("✈️ Air"), KeyboardButton("📦 Container")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    @staticmethod
    def persistent_investor_keyboard():
        """Investor uchun doim ko'rinadigan tugmalar"""
        keyboard = [
            [KeyboardButton("📈 Foyda")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    @staticmethod
    def investor_years_keyboard():
        """Investor uchun yillar tugmalari"""
        keyboard = [
            [InlineKeyboardButton("📅 2025", callback_data="investor_year_2025"),
             InlineKeyboardButton("📅 2026", callback_data="investor_year_2026")],
            [InlineKeyboardButton("📅 2027", callback_data="investor_year_2027"),
             InlineKeyboardButton("📅 2028", callback_data="investor_year_2028")],
            [InlineKeyboardButton("📅 2029", callback_data="investor_year_2029"),
             InlineKeyboardButton("📅 2030", callback_data="investor_year_2030")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def investor_months_keyboard(year):
        """Investor uchun oylar tugmalari"""
        months = [
            ("📌 Yanvar", f"investor_month_{year}_01"),
            ("📌 Fevral", f"investor_month_{year}_02"),
            ("📌 Mart", f"investor_month_{year}_03"),
            ("📌 Aprel", f"investor_month_{year}_04"),
            ("📌 May", f"investor_month_{year}_05"),
            ("📌 Iyun", f"investor_month_{year}_06"),
            ("📌 Iyul", f"investor_month_{year}_07"),
            ("📌 Avgust", f"investor_month_{year}_08"),
            ("📌 Sentyabr", f"investor_month_{year}_09"),
            ("📌 Oktyabr", f"investor_month_{year}_10"),
            ("📌 Noyabr", f"investor_month_{year}_11"),
            ("📌 Dekabr", f"investor_month_{year}_12")
        ]
        
        keyboard = []
        # 3 ta tugma har qatorda
        for i in range(0, len(months), 3):
            row = [InlineKeyboardButton(name, callback_data=callback) 
                   for name, callback in months[i:i+3]]
            keyboard.append(row)
        
        # Orqaga qaytish tugmasi
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="investor_back_to_years")])
        
        return InlineKeyboardMarkup(keyboard)
