import os

def get_bot_token():
    """Bot tokenini muhit o'zgaruvchisidan olish"""
    return os.getenv("BOT_TOKEN", "")

# Rol identifikatorlari
ROLES = {
    "MIJOZ": "mijoz",
    "MANAGER": "manager",
    "INVESTOR": "investor"
}

# Foydalanuvchi rollarini saqlash uchun oddiy dict (haqiqiy loyihada database ishlatiladi)
USER_ROLES = {}

# Foydalanuvchi telefon raqamlarini saqlash
USER_PHONE_NUMBERS = {}

# Autentifikatsiya holati - kodini tasdiqlagan mijozlar
AUTHENTICATED_USERS = {}

# Kod kutayotgan foydalanuvchilar
PENDING_CODE_VERIFICATION = {}

# Belgilangan foydalanuvchilar - ID'lari asosida avtomatik rol berish
PREDEFINED_USERS = {
    # Mijozlar ID'lari - bo'sh, chunki boshqa ID'lar avtomatik mijoz bo'ladi
    "MIJOZ_USERS": [
        # ID qo'shilmaganlar avtomatik mijoz bo'ladi
    ],

    # Managerlar ID'lari
    "MANAGER_USERS": [
        1454267949,  # Manager ID'si
        1604406356,
    ],

    # Investorlar ID'lari
    "INVESTOR_USERS": [
        2051160422,  # Investor 1 ID'si
        1454267949,  # Investor 2 ID'si
        # INVESTOR_3_ID va INVESTOR_4_ID ni haqiqiy ID'lar bilan almashtiring
        # "INVESTOR_3_TELEGRAM_ID",  # Investor 3 ID'si
        # "INVESTOR_4_TELEGRAM_ID",  # Investor 4 ID'si
    ],

    # Super user - har ikkala rolga ham kirishi mumkin
    "SUPER_USERS": [
        1604406356,  # Super user ID'si - manager va investor
        1454267949,  # Super user ID'si - manager va investor
    ]
}

def get_user_role(user_id):
    """Foydalanuvchi rolini olish"""
    return USER_ROLES.get(user_id, None)

def set_user_role(user_id, role):
    """Foydalanuvchi rolini o'rnatish"""
    if role in ROLES.values():
        USER_ROLES[user_id] = role
        return True
    return False

def get_predefined_role(user_id):
    """Foydalanuvchi ID asosida oldindan belgilangan rolni olish"""
    if user_id in PREDEFINED_USERS["SUPER_USERS"]:
        return "SUPER_USER"  # Super user - rol tanlash imkoniyati
    elif user_id in PREDEFINED_USERS["MANAGER_USERS"]:
        return ROLES["MANAGER"]
    elif user_id in PREDEFINED_USERS["INVESTOR_USERS"]:
        return ROLES["INVESTOR"]
    else:
        # ID qo'shilmagan barcha foydalanuvchilar mijoz bo'ladi
        return ROLES["MIJOZ"]

def save_user_phone(user_id, phone_number):
    """Foydalanuvchi telefon raqamini saqlash"""
    USER_PHONE_NUMBERS[user_id] = phone_number

def get_user_phone(user_id):
    """Foydalanuvchi telefon raqamini olish"""
    return USER_PHONE_NUMBERS.get(user_id)

def set_authenticated_user(user_id, user_data):
    """Foydalanuvchini autentifikatsiya qilingan deb belgilash"""
    AUTHENTICATED_USERS[user_id] = user_data

def is_user_authenticated(user_id):
    """Foydalanuvchi autentifikatsiya qilinganligini tekshirish"""
    return user_id in AUTHENTICATED_USERS

def set_pending_verification(user_id, user_data):
    """Foydalanuvchini kod kutish holatiga qo'yish"""
    PENDING_CODE_VERIFICATION[user_id] = user_data

def get_pending_verification(user_id):
    """Kod kutayotgan foydalanuvchi ma'lumotini olish"""
    return PENDING_CODE_VERIFICATION.get(user_id)

def remove_pending_verification(user_id):
    """Kod kutish holatini o'chirish"""
    if user_id in PENDING_CODE_VERIFICATION:
        del PENDING_CODE_VERIFICATION[user_id]

# Har bir investor uchun alohida Google Sheets konfiguratsiyasi
INVESTOR_SHEETS_CONFIG = {
    2051160422: {  # Investor 1
        "sheet_id": "1kskVRDNmM1PUpGtQ7_YMQ3U3--9dHyKktnHUZ7fP_bg",
        "worksheet_id": 1601344247,  # 12 nomli list
        "name": "Investor 1"
    },
    1454267949: {  # Investor 2  
        "sheet_id": "1kskVRDNmM1PUpGtQ7_YMQ3U3--9dHyKktnHUZ7fP_bg",
        "worksheet_id": 13,  # 13 nomli list - GID olish kerak
        "name": "Investor 2"
    },
    # Investor 3 uchun
    "INVESTOR_3_ID": {
        "sheet_id": "1kskVRDNmM1PUpGtQ7_YMQ3U3--9dHyKktnHUZ7fP_bg",
        "worksheet_id": 14,  # 14 nomli list - GID olish kerak
        "name": "Investor 3"
    },
    # Investor 4 uchun
    "INVESTOR_4_ID": {
        "sheet_id": "1kskVRDNmM1PUpGtQ7_YMQ3U3--9dHyKktnHUZ7fP_bg",
        "worksheet_id": 15,  # 15 nomli list - GID olish kerak
        "name": "Investor 4"
    }
}

def get_investor_sheet_config(investor_id):
    """Investor ID'siga qarab sheet konfiguratsiyasini olish"""
    return INVESTOR_SHEETS_CONFIG.get(investor_id, None)