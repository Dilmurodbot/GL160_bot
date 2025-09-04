import gspread
import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from google.oauth2.service_account import Credentials

class GoogleSheetsManager:
    def __init__(self):
        self.sheet_id = "18OUICCqjaN4QvpfxC2YHnwA4gHSoy51eGKyPszFhXSQ"
        self.client = None
        self.worksheet = None
        self.gc = None  # gspread client for write operations

    def connect_with_api_key(self, api_key: str):
        """Google API kaliti bilan ulanish"""
        try:
            # Public sheet uchun oddiy HTTP so'rov
            self.api_key = api_key
            return True
        except Exception as e:
            print(f"API key bilan ulanishda xatolik: {e}")
            return False

    def connect_with_service_account(self, credentials_file="service_account.json"):
        """Service Account bilan ulanish (write access uchun)"""
        try:
            # Service account credentials bilan ulanish
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
            self.gc = gspread.authorize(creds)

            print("✅ Google Sheets service account bilan ulanish muvaffaqiyatli!")
            return True

        except Exception as e:
            print(f"❌ Service account bilan ulanishda xatolik: {e}")
            return False

    def get_public_sheet_data(self, gid=None):
        """Public sheet'dan ma'lumot olish (Google Sheets API orqali)"""
        try:
            # Agar gid berilmasa, users sheet (default)
            if gid is None:
                gid = 1544289461  # users sheet ID

            # CSV format'da olish (public sheets uchun)
            url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/export?format=csv&gid={gid}"
            response = requests.get(url)
            response.raise_for_status()

            # CSV ma'lumotlarini parse qilish
            lines = response.text.strip().split('\n')
            data = []
            for line in lines:
                if line.strip():  # Bo'sh qatorlarni o'tkazib yuborish
                    # Oddiy CSV parsing
                    row = [cell.strip('"').strip() for cell in line.split(',')]
                    data.append(row)

            return data
        except Exception as e:
            print(f"Sheet'dan ma'lumot olishda xatolik: {e}")
            return None

    def find_user_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Telefon raqam bo'yicha foydalanuvchini topish"""
        try:
            # Users sheet'dan ma'lumot olish
            users_data = self.get_public_sheet_data()  # Default users sheet
            if not users_data or len(users_data) <= 1:  # Header qatori mavjudligini tekshirish
                return None

            # Telefon raqamini tozalash (faqat raqamlar)
            clean_phone = ''.join(filter(str.isdigit, phone_number))

            # Header qatorini o'tkazib yuborish
            for i, row in enumerate(users_data[1:], start=2):
                if not row or len(row) < 5:
                    continue

                try:
                    # A ustuni: Telefon, B: Ism, C: List nomi, D: Kod, E: Summa
                    telefon = str(row[0]).strip()
                    ism = row[1].strip() if len(row) > 1 else ""
                    list_nomi = row[2].strip() if len(row) > 2 else ""
                    kod = row[3].strip() if len(row) > 3 else ""

                    # Summani E va F ustunidan birlashtirish (CSV vergul muammosi)
                    raw_summa = row[4].strip() if len(row) > 4 else "0"

                    # F ustunini tekshirish - onlik qism bo'lishi mumkin
                    if len(row) > 5 and row[5].strip().isdigit():
                        f_value = row[5].strip()
                        # E va F ni vergul bilan birlashtirish
                        full_summa = f"{raw_summa},{f_value}"
                    else:
                        full_summa = raw_summa

                    summa = self.clean_amount(full_summa)

                    # Telefon raqamlarni tozalash va taqqoslash
                    clean_sheet_phone = ''.join(filter(str.isdigit, telefon))


                    # Telefon raqam bo'yicha qidirish - turli formatlarni tekshirish
                    match_found = False
                    if clean_phone and clean_sheet_phone:
                        # To'liq taqqoslash
                        if clean_phone == clean_sheet_phone:
                            match_found = True
                        # 998 bilan boshlanuvchi raqamlarni 9 raqamli raqam bilan taqqoslash
                        elif clean_phone.startswith('998') and len(clean_phone) >= 12:
                            local_part = clean_phone[3:]  # 998 dan keyingi qism
                            if local_part == clean_sheet_phone or clean_sheet_phone.endswith(local_part):
                                match_found = True
                        # 9 raqamli raqamni 998 bilan boshlanuvchi bilan taqqoslash  
                        elif clean_sheet_phone.startswith('998') and len(clean_sheet_phone) >= 12:
                            sheet_local_part = clean_sheet_phone[3:]  # 998 dan keyingi qism
                            if clean_phone == sheet_local_part or clean_phone.endswith(sheet_local_part):
                                match_found = True
                        # Oxirgi 9 raqamni taqqoslash
                        elif len(clean_phone) >= 9 and len(clean_sheet_phone) >= 9:
                            if clean_phone[-9:] == clean_sheet_phone[-9:]:
                                match_found = True

                    if match_found:
                        user_info = {
                            "telefon": telefon,
                            "ism": ism,
                            "list_nomi": list_nomi,
                            "kod": kod,
                            "summa": summa,
                            "row_number": i
                        }
                        return user_info

                except (ValueError, IndexError) as e:
                    print(f"Row {i} da xatolik: {e}")
                    continue

            return None

        except Exception as e:
            print(f"Foydalanuvchi topishda xatolik: {e}")
            return None

    def find_user_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Kod bo'yicha foydalanuvchini topish"""
        try:
            # Users sheet'dan ma'lumot olish
            users_data = self.get_public_sheet_data()  # Default users sheet
            if not users_data or len(users_data) <= 1:
                return None

            # Kodni tozalash
            clean_code = str(code).strip()

            # Header qatorini o'tkazib yuborish
            for i, row in enumerate(users_data[1:], start=2):
                if not row or len(row) < 4:
                    continue

                try:
                    # A ustuni: Telefon, B: Ism, C: List nomi, D: Kod, E: Summa
                    telefon = str(row[0]).strip()
                    ism = row[1].strip() if len(row) > 1 else ""
                    list_nomi = row[2].strip() if len(row) > 2 else ""
                    kod = str(row[3]).strip() if len(row) > 3 else ""

                    # Summani E va F ustunidan birlashtirish
                    raw_summa = row[4].strip() if len(row) > 4 else "0"

                    # F ustunini tekshirish - onlik qism bo'lishi mumkin
                    if len(row) > 5 and row[5].strip().isdigit():
                        f_value = row[5].strip()
                        full_summa = f"{raw_summa},{f_value}"
                    else:
                        full_summa = raw_summa

                    summa = self.clean_amount(full_summa)

                    # Kod bo'yicha qidirish - clean_code ni kod bilan solishtirish
                    # Float qiymatlarni string'ga o'tkazish (1111.0 -> 1111)
                    if '.' in clean_code and clean_code.endswith('.0'):
                        clean_code = clean_code[:-2]

                    if clean_code == kod or clean_code == str(int(float(kod))) if kod.replace('.','').isdigit() else False:
                        user_info = {
                            "telefon": telefon,
                            "ism": ism,
                            "list_nomi": list_nomi,
                            "kod": kod,
                            "summa": summa,
                            "summa_formatted": f"{summa:,.2f} $".replace(',', ' '),
                            "row_number": i
                        }
                        return user_info

                except (ValueError, IndexError) as e:
                    print(f"Row {i} da xatolik: {e}")
                    continue

            return None

        except Exception as e:
            print(f"Kod bo'yicha foydalanuvchi topishda xatolik: {e}")
            return None

    def write_to_list_sheet(self, list_nomi, data):
        """Belgilangan list sheet'ga ma'lumot yozish"""
        try:
            if not self.gc:
                # Service account bilan ulanish
                if not self.connect_with_service_account():
                    return False

            # Asosiy spreadsheet'ni ochish
            spreadsheet = self.gc.open_by_key(self.sheet_id)

            # List nomi bo'yicha worksheet topish
            worksheet_name = str(list_nomi).strip()

            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                print(f"❌ '{worksheet_name}' worksheet topilmadi")
                return False

            # Ma'lumotlarni qo'shish
            # Yangi qator qo'shish (worksheet oxiriga)
            new_row = [
                data.get('sana', ''),
                data.get('reys', ''),
                data.get('tavsif', ''),
                data.get('summa', '')
            ]

            worksheet.append_row(new_row)
            print(f"✅ '{worksheet_name}' sheet'ga yozildi: {new_row}")
            return True

        except Exception as e:
            print(f"❌ Sheet'ga yozishda xatolik: {e}")
            return False

    def clean_amount(self, amount_str: str) -> float:
        """Summa qatorini tozalash va float qaytarish - manfiy qiymatlarni qo'llab-quvvatlaydi"""
        if not amount_str:
            return 0.0

        import re

        # String ga o'tkazish va manfiy belgini saqlab qolish
        amount_str = str(amount_str).strip()
        is_negative = '-' in amount_str

        # Manfiy belgini vaqtincha olib tashlash
        cleaned = amount_str.replace('-', '')

        # Maxsus belgilarni olib tashlash
        cleaned = cleaned.replace('Â', '').replace('\u00A0', ' ').replace('\xa0', ' ')
        cleaned = re.sub(r'[^\d\.,\s]', '', cleaned)
        cleaned = cleaned.strip()

        if not cleaned:
            return 0.0

        # Vergul bor yoki yo'qligini tekshirish
        if ',' in cleaned:
            # Vergul bilan ajratilgan sonni float sifatida parse qilish
            try:
                # Bo'shliqlarni olib tashlash va vergulni nuqta bilan almashtirish
                float_str = cleaned.replace(' ', '').replace(',', '.')
                amount = float(float_str)

                # Manfiy belgini qaytarish
                if is_negative:
                    amount = -amount

                return amount

            except (ValueError, TypeError):
                # Float parse qila olmasa, integer usulini ishlatish
                pass

        # Vergul yo'q - integer sifatida ishlash
        parts = re.findall(r'\d+', cleaned)

        if not parts:
            return 0.0

        # Barcha raqam qismlarini birlashtirish
        number_str = ''.join(parts)

        try:
            # Raqamni integer sifatida parse qilish
            amount = int(number_str)

            # Manfiy belgini qaytarish
            if is_negative:
                amount = -amount

            return float(amount)

        except (ValueError, TypeError):
            return 0.0

    def find_user_balance(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Telefon raqam bo'yicha foydalanuvchi balansini topish"""
        try:
            # Avval users sheet'da foydalanuvchini topish
            user_info = self.find_user_by_phone(phone_number)

            if not user_info:
                return {
                    "phone_number": phone_number,
                    "balance": "0",
                    "currency": "$",
                    "status": "Mijoz ro'yxatida topilmadi"
                }

            # Agar foydalanuvchi topilsa, uning ma'lumotlarini qaytarish
            return {
                "phone_number": phone_number,
                "telefon": user_info["telefon"],
                "ism": user_info["ism"],
                "list_nomi": user_info["list_nomi"],
                "kod": user_info["kod"],
                "balance": user_info["summa"],
                "currency": "$",
                "last_updated": "Hozir"
            }

        except Exception as e:
            print(f"Balans topishda xatolik: {e}")
            return None

    def format_balance_message(self, balance_info: Dict[str, Any]) -> str:
        """Balans ma'lumotini format qilish - yangilangan versiya"""
        if not balance_info:
            return "❌ Balans ma'lumotini olishda xatolik yuz berdi."

        if "status" in balance_info:
            return f"📊 Balans ma'lumotlari\n\n" \
                   f"📱 Telefon: {balance_info['phone_number']}\n" \
                   f"⚠️ {balance_info['status']}\n" \
                   f"💰 Joriy balans: {balance_info['balance']} {balance_info['currency']}"

        # Yangi format - to'liq ma'lumotlar bilan
        message = f"🛩️📊 Air ma'lumotlari\n\n"

        if balance_info.get('ism'):
            message += f"👤 Ism: {balance_info['ism']}\n"

        if balance_info.get('telefon'):
            message += f"📱 Telefon: {balance_info['telefon']}\n"

        if balance_info.get('kod'):
            message += f"🆔 Kod: {balance_info['kod']}\n"


        message += f"\n💰 Balans: {balance_info['balance']} {balance_info['currency']}"

        # Sana va soat qo'shish (O'zbekiston vaqti GMT+5)
        uzbekistan_tz = timezone(timedelta(hours=5))
        now = datetime.now(uzbekistan_tz)
        formatted_date = now.strftime("%d.%m.%Y")
        formatted_time = now.strftime("%H:%M")
        message += f"\n🕐 {formatted_date} - {formatted_time}"

        return message

    def get_all_users_balances(self) -> Dict[str, Dict[str, Any]]:
        """Barcha foydalanuvchilar balansini olish - avtomatik kuzatish uchun"""
        try:
            users_data = self.get_public_sheet_data()
            if not users_data or len(users_data) < 2:
                return {}

            all_balances = {}

            for i, row in enumerate(users_data[1:], start=2):
                if not row or len(row) < 5:
                    continue

                try:
                    # A ustuni: Telefon, B: Ism, C: List nomi, D: Kod, E: Summa
                    telefon = str(row[0]).strip()
                    ism = row[1].strip() if len(row) > 1 else ""
                    list_nomi = row[2].strip() if len(row) > 2 else ""
                    kod = row[3].strip() if len(row) > 3 else ""

                    # Summani E va F ustunidan birlashtirish
                    raw_summa = row[4].strip() if len(row) > 4 else "0"

                    # F ustunini tekshirish - onlik qism bo'lishi mumkin
                    if len(row) > 5 and row[5].strip().isdigit():
                        f_value = row[5].strip()
                        full_summa = f"{raw_summa},{f_value}"
                    else:
                        full_summa = raw_summa

                    summa = self.clean_amount(full_summa)

                    # Telefon raqamlarni tozalash
                    clean_phone = ''.join(filter(str.isdigit, telefon))

                    if len(clean_phone) >= 9:
                        # Balans ma'lumotini saqlash
                        all_balances[clean_phone] = {
                            "telefon": telefon,
                            "ism": ism,
                            "list_nomi": list_nomi,
                            "kod": kod,
                            "balance": summa,
                            "currency": "$"
                        }

                except Exception as e:
                    print(f"Qator {i} da xatolik: {e}")
                    continue

            return all_balances

        except Exception as e:
            print(f"Barcha balanslarni olishda xatolik: {e}")
            return {}

    def get_positive_balances_over_amount(self, min_balance_amount=5.0):
        """Belgilangan miqdordan yuqori musbat balansga ega mijozlarni olish"""
        try:
            # Users sheet'dan ma'lumot olish
            users_data = self.get_public_sheet_data()  # Default users sheet
            if not users_data or len(users_data) <= 1:
                return []

            positive_users = []

            # Header qatorini o'tkazib yuborish
            for i, row in enumerate(users_data[1:], start=2):
                if not row or len(row) < 5:
                    continue

                try:
                    # A ustuni: Telefon, B: Ism, C: List nomi, D: Kod, E: Summa
                    telefon = str(row[0]).strip()
                    ism = row[1].strip() if len(row) > 1 else ""

                    # Summani olish va parse qilish
                    raw_summa = row[4].strip() if len(row) > 4 else "0"

                    # F ustunini tekshirish - onlik qism bo'lishi mumkin
                    if len(row) > 5 and row[5].strip():
                        raw_summa += "," + row[5].strip()

                    # Summani clean_amount funksiyasi bilan tozalash
                    summa = self.clean_amount(raw_summa)

                    # Summa float ekanligini ta'minlash
                    if isinstance(summa, str):
                        try:
                            summa = float(summa.replace(',', '.').replace(' ', ''))
                        except (ValueError, TypeError):
                            summa = 0.0
                    elif not isinstance(summa, (int, float)):
                        summa = 0.0

                    # Faqat musbat balansga ega mijozlarni olish
                    if summa > 0 and summa >= min_balance_amount:
                        kod = row[3].strip() if len(row) > 3 else "N/A"
                        print(f"💰 DEBUG musbat: {kod} = +{summa}")
                        positive_users.append({
                            'ism': ism,
                            'telefon': telefon,
                            'kod': kod,
                            'balans': summa,
                            'balans_formatted': f"{summa:,.2f} $".replace(',', ' ')
                        })

                except (IndexError, ValueError) as e:
                    print(f"Qator {i} ni parse qilishda xatolik: {e}")
                    continue

            # Balans miqdori bo'yicha saralash (eng yuqoridan pastga)
            positive_users.sort(key=lambda x: x['balans'], reverse=True)

            return positive_users

        except Exception as e:
            print(f"Musbat balanslarni olishda xatolik: {e}")
            return []

    def get_debtors_over_amount(self, min_debt_amount=5.0):
        """Belgilangan miqdordan yuqori qarzi bo'lgan mijozlarni olish va tartibga solish"""
        try:
            # Users sheet'dan ma'lumot olish
            users_data = self.get_public_sheet_data()  # Default users sheet
            if not users_data or len(users_data) <= 1:
                return []

            debtors = []

            # Header qatorini o'tkazib yuborish
            for i, row in enumerate(users_data[1:], start=2):
                if not row or len(row) < 5:
                    continue

                try:
                    # A ustuni: Telefon, B: Ism, C: List nomi, D: Kod, E: Summa
                    telefon = str(row[0]).strip()
                    ism = row[1].strip() if len(row) > 1 else ""

                    # Summani olish va parse qilish
                    raw_summa = row[4].strip() if len(row) > 4 else "0"

                    # F ustunini tekshirish - onlik qism bo'lishi mumkin
                    if len(row) > 5 and row[5].strip():
                        raw_summa += "," + row[5].strip()

                    # Summani clean_amount funksiyasi bilan tozalash
                    summa = self.clean_amount(raw_summa)

                    # Summa float ekanligini ta'minlash
                    if isinstance(summa, str):
                        try:
                            summa = float(summa.replace(',', '.').replace(' ', ''))
                        except (ValueError, TypeError):
                            summa = 0.0
                    elif not isinstance(summa, (int, float)):
                        summa = 0.0

                    # Faqat manfiy balansga ega mijozlarni (qarzdorlarni) olish
                    if summa < 0:
                        debt_amount = abs(summa)  # Qarzdorlik miqdori (musbat qiymat)

                        # Belgilangan miqdordan yuqori qarzi bor mijozlarni filtrlash
                        if debt_amount >= min_debt_amount:
                            kod = row[3].strip() if len(row) > 3 else "N/A"
                            print(f"📊 DEBUG qarzdor: {kod} = -{summa} = +{debt_amount}")
                            debtors.append({
                                'ism': ism,
                                'telefon': telefon,
                                'kod': kod,
                                'qarzdorlik': debt_amount,
                                'qarzdorlik_formatted': f"{debt_amount:,.2f} $".replace(',', ' ')
                            })

                except (IndexError, ValueError) as e:
                    print(f"Qator {i} ni parse qilishda xatolik: {e}")
                    continue

            # Qarzdorlik miqdori bo'yicha saralash (eng yuqoridan pastga)
            debtors.sort(key=lambda x: x['qarzdorlik'], reverse=True)

            return debtors

        except Exception as e:
            print(f"Qarzdorlarni olishda xatolik: {e}")
            return []

    def get_all_users_data(self):
        """Barcha mijozlar ma'lumotini olish (manager uchun)"""
        try:
            # Users sheet'dan ma'lumot olish
            users_data = self.get_public_sheet_data()  # Default users sheet

            if not users_data or len(users_data) <= 1:
                return [], 0.0

            all_users = []
            total_balance = 0.0

            # Header qatorini o'tkazib yuborish
            for i, row in enumerate(users_data[1:], start=2):
                if not row or len(row) < 5:
                    continue

                try:
                    # A ustuni: Telefon, B: Ism, C: List nomi, D: Kod, E: Summa
                    telefon = str(row[0]).strip()
                    ism = row[1].strip() if len(row) > 1 else ""
                    list_nomi = row[2].strip() if len(row) > 2 else ""
                    kod = row[3].strip() if len(row) > 3 else ""

                    # Summani olish va parse qilish
                    raw_summa = row[4].strip() if len(row) > 4 else "0"

                    # F ustunini tekshirish - onlik qism bo'lishi mumkin
                    if len(row) > 5 and row[5].strip():
                        raw_summa += "," + row[5].strip()

                    # Summani clean_amount funksiyasi bilan tozalash
                    summa = self.clean_amount(raw_summa)

                    # Summa float ekanligini ta'minlash
                    if isinstance(summa, str):
                        try:
                            summa = float(summa.replace(',', '.').replace(' ', ''))
                        except (ValueError, TypeError):
                            summa = 0.0
                    elif not isinstance(summa, (int, float)):
                        summa = 0.0

                    total_balance += summa

                    # Format qilish
                    summa_formatted = f"{summa:,.2f} $".replace(',', ' ')

                    all_users.append({
                        'ism': ism,
                        'telefon': telefon,
                        'kod': kod,
                        'summa': summa,
                        'summa_formatted': summa_formatted
                    })

                except (IndexError, ValueError) as e:
                    continue

            # Summa bo'yicha saralash (eng yuqoridan pastga)
            all_users.sort(key=lambda x: x['summa'], reverse=True)

            return all_users, total_balance

        except Exception as e:
            print(f"Mijozlar ma'lumotini olishda xatolik: {e}")
            return [], 0.0

    def format_all_users_message(self, users_data, total_balance):
        """Barcha mijozlar ro'yxatini formatlash (manager uchun)"""
        if not users_data:
            return "❌ Mijozlar ma'lumotini olishda xatolik yuz berdi."

        # O'zbekiston vaqti
        uzbekistan_tz = timezone(timedelta(hours=5))
        now = datetime.now(uzbekistan_tz)
        formatted_date = now.strftime("%d.%m.%Y")
        formatted_time = now.strftime("%H:%M")

        message = f"🛩️📋 Air mijozlari jadvali\n\n"
        message += f"{'№':<3} {'Kod':<8} {'Summa':<15}\n"
        message += f"{'─'*3} {'─'*8} {'─'*15}\n"

        # Faqat eng yuqori 30 ta mijozni ko'rsatish (jadval formatida)
        displayed_users = users_data[:30]

        for i, user in enumerate(displayed_users, 1):
            kod = user['kod'][:8]  # Kod qisqartirish
            summa = user['summa_formatted'].replace(' $', '$')
            message += f"{i:<3} {kod:<8} {summa:<15}\n"

        # Agar ko'proq mijozlar bo'lsa
        if len(users_data) > 30:
            message += f"... va yana {len(users_data) - 30} ta mijoz\n"

        # Umumiy ma'lumotlar
        total_formatted = f"{total_balance:,.2f} $".replace(',', ' ')
        message += f"\n📊 Jami: {len(users_data)} ta mijoz\n"
        message += f"💰 Umumiy: {total_formatted}\n"
        message += f"🕐 {formatted_date} - {formatted_time}"

        return message

    def format_positive_balances_message(self, positive_users):
        """Musbat balanslar ro'yxatini Markdown formatida formatlash"""
        if not positive_users:
            return "✅ Hozirda $5 dan yuqori musbat balansga ega mijozlar yo'q."

        # O'zbekiston vaqti
        uzbekistan_tz = timezone(timedelta(hours=5))
        now = datetime.now(uzbekistan_tz)
        formatted_date = now.strftime("%d.%m.%Y")
        formatted_time = now.strftime("%H:%M")

        message = f"🛩️💰 Air balansi ($5+)\n\n"
        message += f"```\n"
        message += f"{'№':<3} {'Kod':<8} {'Balans':<12}\n"
        message += f"{'─'*3} {'─'*8} {'─'*12}\n"

        # Barcha mijozlarni ko'rsatish
        displayed_users = positive_users

        for i, user in enumerate(displayed_users, 1):
            kod = user['kod'][:8] if len(user['kod']) <= 8 else user['kod'][:7] + '…'
            balans = user['balans_formatted']
            message += f"{i:<3} {kod:<8} {balans:<12}\n"

        message += "```\n\n"

        total_positive = sum(user['balans'] for user in positive_users)
        total_formatted = f"{total_positive:,.2f} $".replace(',', ' ')

        message += f"📊 Jami: {len(positive_users)} ta mijoz\n"
        message += f"💰 Umumiy: {total_formatted}\n"
        message += f"🕐 {formatted_date} - {formatted_time}\n\n"

        return message

    def format_debtors_message(self, debtors):
        """Qarzdorlar ro'yxatini Markdown formatida formatlash"""
        if not debtors:
            return "✅ Hozirda $5 dan yuqori qarzi bo'lgan mijozlar yo'q."

        # O'zbekiston vaqti
        uzbekistan_tz = timezone(timedelta(hours=5))
        now = datetime.now(uzbekistan_tz)
        formatted_date = now.strftime("%d.%m.%Y")
        formatted_time = now.strftime("%H:%M")

        message = f"🛩️📋 Air qarzdorlari ($5+)\n\n"
        message += f"```\n"
        message += f"{'№':<3} {'Kod':<8} {'Qarzdorlik':<12}\n"
        message += f"{'─'*3} {'─'*8} {'─'*12}\n"

        for i, debtor in enumerate(debtors, 1):
            kod = debtor.get('kod', 'N/A')[:8]  # Kod qisqartirish
            qarzdorlik = debtor['qarzdorlik_formatted'].replace(' $', '$')
            message += f"{i:<3} {kod:<8} {qarzdorlik:<12}\n"

        message += f"```\n"
        message += f"📊 Jami: {len(debtors)} ta qarzdor\n"
        message += f"🕐 {formatted_date} - {formatted_time}"

        return message

    def get_container_data(self):
        """Container sheet'dan ma'lumot olish - U list, D va E ustunlar"""
        try:
            # Container sheet URL ID
            container_sheet_id = "1k7RMqNH75kTmw88pFGUh7Yg-kgxswz4q1616vxo2HBE"
            container_gid = "267785141"  # U list gid

            # CSV format'da olish
            url = f"https://docs.google.com/spreadsheets/d/{container_sheet_id}/export?format=csv&gid={container_gid}"
            response = requests.get(url)
            response.raise_for_status()

            # CSV ma'lumotlarini parse qilish
            lines = response.text.strip().split('\n')
            container_data = []

            for i, line in enumerate(lines):
                if line.strip():
                    row = [cell.strip('"').strip() for cell in line.split(',')]

                    # Skip header row
                    if i == 0:
                        continue

                    # B ustun (index 1) - ism, D ustun (index 3) - kod, E ustun (index 4) - summa, F ustun (index 5) - onlik qism
                    if len(row) > 4:
                        ism = row[1].strip() if len(row) > 1 and row[1].strip() else "N/A"
                        kod = row[3].strip() if row[3].strip() else None

                        # E ustundan asosiy summani olish
                        raw_summa = row[4].strip() if row[4].strip() else "0"

                        # F ustunini tekshirish - onlik qism bo'lishi mumkin
                        if len(row) > 5 and row[5].strip() and row[5].strip().isdigit():
                            f_value = row[5].strip()
                            # E va F ni vergul bilan birlashtirish
                            full_summa = f"{raw_summa},{f_value}"
                        else:
                            full_summa = raw_summa

                        # Summani tozalash va float'ga o'tkazish
                        try:
                            summa = self.clean_amount(full_summa)

                            # Faqat 5$ dan yuqori summalar va kod mavjud bo'lganlar
                            if kod and summa > 5.0:
                                container_data.append({
                                    'ism': ism,
                                    'kod': kod,
                                    'summa': summa
                                })
                        except (ValueError, TypeError):
                            continue

            print(f"📦 Container: {len(container_data)} ta kod (5$+)")
            return container_data

        except Exception as e:
            print(f"❌ Container ma'lumotlarini olishda xatolik: {e}")
            return []

    def find_user_container_data(self, user_kod):
        """Mijoz kodiga ko'ra Container ma'lumotini topish"""
        try:
            # Barcha Container ma'lumotlarini olish
            container_data = self.get_container_data()

            # Foydalanuvchi kodiga mos keladigan ma'lumotni topish
            for item in container_data:
                if item['kod'] == user_kod and item['summa'] > 0:
                    return item

            return None

        except Exception as e:
            print(f"❌ Mijoz Container ma'lumotini topishda xatolik: {e}")
            return None

    def format_user_container_message(self, container_info: Dict[str, Any]) -> str:
        """Foydalanuvchi Container ma'lumotini formatlash"""
        if not container_info:
            return "📦 Container ma'lumotlaringiz topilmadi."

        # O'zbekiston vaqti
        uzbekistan_tz = timezone(timedelta(hours=5))
        now = datetime.now(uzbekistan_tz)
        formatted_date = now.strftime("%d.%m.%Y")
        formatted_time = now.strftime("%H:%M")

        message = f"📦🔍 Container ma'lumotlari\n\n"

        if container_info.get('ism'):
            message += f"👤 Ism: {container_info['ism']}\n"

        if container_info.get('kod'):
            message += f"🆔 Kod: {container_info['kod']}\n"

        # Summani formatlash
        summa = container_info.get('summa', 0)
        if isinstance(summa, (int, float)):
            summa_formatted = f"{summa:,.2f} $".replace(',', ' ')
        else:
            summa_formatted = f"{summa} $"

        message += f"\n💰 Balans: {summa_formatted}"
        message += f"\n🕐 {formatted_date} - {formatted_time}"

        return message

    def format_total_balance_message(self, air_balance_info: Dict[str, Any], container_info: Dict[str, Any]) -> str:
        """Umumiy balans ma'lumotini formatlash - code box formatida"""
        # O'zbekiston vaqti
        uzbekistan_tz = timezone(timedelta(hours=5))
        now = datetime.now(uzbekistan_tz)
        formatted_date = now.strftime("%d.%m.%Y")
        formatted_time = now.strftime("%H:%M")

        # Air balans hisoblash
        air_balance = 0
        if air_balance_info and air_balance_info.get('balance'):
            try:
                air_balance_str = str(air_balance_info['balance']).replace(' ', '').replace(',', '.')
                air_balance = float(air_balance_str)
                air_formatted = f"{air_balance:,.2f} $".replace(',', ' ')
            except (ValueError, TypeError):
                air_formatted = f"{air_balance_info['balance']} $"
        else:
            air_formatted = "0,00 $"

        # Container balans hisoblash
        container_balance = 0
        if container_info and container_info.get('summa'):
            try:
                container_balance = float(container_info['summa'])
                container_formatted = f"{container_balance:,.2f} $".replace(',', ' ')
            except (ValueError, TypeError):
                container_formatted = f"{container_info['summa']} $"
        else:
            container_formatted = "0,00 $"

        # Umumiy summa
        total_balance = air_balance + container_balance
        total_formatted = f"{total_balance:,.2f} $".replace(',', ' ')

        # Ism va telefon
        ism = air_balance_info.get('ism', 'N/A') if air_balance_info else 'N/A'
        telefon = air_balance_info.get('telefon', 'N/A') if air_balance_info else 'N/A'
        kod = air_balance_info.get('kod', 'N/A') if air_balance_info else 'N/A'

        # Code box formatida xabar yaratish
        message = f"💰📊 Umumiy balans\n\n"
        message += f"```\n"
        message += f"{'Ism:':<6} {ism}\n"
        message += f"{'Tel:':<6} {telefon}\n"
        message += f"{'Kod:':<6} {kod}\n"
        message += f"{'─'*20}\n"
        message += f"{'Air:':<8} {air_formatted:>10}\n"
        message += f"{'Cont:':<8} {container_formatted:>10}\n"
        message += f"{'─'*20}\n"
        message += f"{'UMUMIY:':<8} {total_formatted:>10}\n"
        message += f"```\n\n"
        message += f"🕐 {formatted_date} - {formatted_time}"

        return message

    def format_container_message(self, container_data):
        """Container ma'lumotlarini Markdown formatida formatlash (manager uchun)"""
        if not container_data:
            return "✅ Hozirda $5 dan yuqori Container balansga ega mijozlar yo'q."

        # O'zbekiston vaqti
        uzbekistan_tz = timezone(timedelta(hours=5))
        now = datetime.now(uzbekistan_tz)
        formatted_date = now.strftime("%d.%m.%Y")
        formatted_time = now.strftime("%H:%M")

        message = f"📦💰 Container balanslari ($5+)\n\n"
        message += f"```\n"
        message += f"{'№':<3} {'Ism':<12} {'Kod':<8} {'Balans':<12}\n"
        message += f"{'─'*3} {'─'*12} {'─'*8} {'─'*12}\n"

        # Container ma'lumotlarini balans bo'yicha saralash
        sorted_container = sorted(container_data, key=lambda x: x['summa'], reverse=True)

        for i, item in enumerate(sorted_container, 1):
            ism = item['ism'][:12] if len(item['ism']) <= 12 else item['ism'][:11] + '…'
            kod = item['kod'][:8] if len(item['kod']) <= 8 else item['kod'][:7] + '…'
            balans = f"{item['summa']:,.2f} $".replace(',', ' ')
            message += f"{i:<3} {ism:<12} {kod:<8} {balans:<12}\n"

        message += "```\n\n"

        total_container = sum(item['summa'] for item in container_data)
        total_formatted = f"{total_container:,.2f} $".replace(',', ' ')

        message += f"📊 Jami: {len(container_data)} ta mijoz\n"
        message += f"💰 Umumiy: {total_formatted}\n"
        message += f"🕐 {formatted_date} - {formatted_time}\n\n"

        return message

    def get_worksheet_gid_by_title(self, spreadsheet_id, worksheet_title):
        """Worksheet nomiga qarab GID ni olish"""
        try:
            if not self.gc:
                if not self.connect_with_service_account():
                    return None
            
            spreadsheet = self.gc.open_by_key(spreadsheet_id)
            worksheets = spreadsheet.worksheets()
            
            for worksheet in worksheets:
                if worksheet.title == str(worksheet_title):
                    return worksheet.id
            
            print(f"❌ '{worksheet_title}' nomli worksheet topilmadi")
            return None
            
        except Exception as e:
            print(f"❌ Worksheet GID olishda xatolik: {e}")
            return None

    def get_investor_profit_data(self, year, month, investor_id=None):
        """Investor uchun belgilangan yil va oydan foyda ma'lumotlarini olish - A1:F8 oralig'idan"""
        try:
            print(f"🔍 DEBUG: Investor {investor_id} ma'lumotlari so'ralyapti: {year}-{month}")
            
            # Service account bilan ulanish
            if not self.gc:
                print("🔗 DEBUG: Service account bilan ulanish...")
                if not self.connect_with_service_account():
                    print("❌ Service account bilan ulanishda xatolik")
                    return []

            # Investor ID'siga qarab sheet konfiguratsiyasini olish
            from config import get_investor_sheet_config
            sheet_config = get_investor_sheet_config(investor_id)
            
            if not sheet_config:
                print(f"❌ Investor {investor_id} uchun sheet konfiguratsiyasi topilmadi")
                return []
            
            investor_sheet_id = sheet_config["sheet_id"]
            worksheet_identifier = sheet_config["worksheet_id"]
            investor_name = sheet_config["name"]
            
            print(f"📊 DEBUG: {investor_name} uchun Spreadsheet ID: {investor_sheet_id}")
            print(f"📋 DEBUG: Worksheet identifier: {worksheet_identifier}")
            
            # Service account orqali spreadsheet ochish
            try:
                print("📂 DEBUG: Spreadsheet ochilmoqda...")
                spreadsheet = self.gc.open_by_key(investor_sheet_id)
                
                # Worksheet'ni ochish - title yoki ID bo'yicha
                if isinstance(worksheet_identifier, str) and not worksheet_identifier.isdigit():
                    # Title bo'yicha qidirish
                    worksheet = spreadsheet.worksheet(worksheet_identifier)
                elif isinstance(worksheet_identifier, (int, str)) and str(worksheet_identifier).isdigit():
                    # GID bo'yicha qidirish
                    if str(worksheet_identifier) in ['13', '14', '15']:
                        # Haqiqiy GID olish
                        actual_gid = self.get_worksheet_gid_by_title(investor_sheet_id, str(worksheet_identifier))
                        if actual_gid:
                            worksheet = spreadsheet.get_worksheet_by_id(actual_gid)
                        else:
                            # Title sifatida ishlatish
                            worksheet = spreadsheet.worksheet(str(worksheet_identifier))
                    else:
                        worksheet = spreadsheet.get_worksheet_by_id(int(worksheet_identifier))
                else:
                    print(f"❌ Noto'g'ri worksheet identifier: {worksheet_identifier}")
                    return []
                
                print(f"✅ DEBUG: {investor_name} worksheet '{worksheet.title}' muvaffaqiyatli ochildi")
                
                # A1:F8 oralig'idan ma'lumotlarni olish
                range_values = worksheet.get('A1:F8')
                all_values = range_values
                print(f"📋 DEBUG: A1:F8 oralig'idan {len(all_values)} qator topildi")
                
                # Birinchi bir necha qatorni ko'rsatish
                for i, row in enumerate(all_values[:5]):
                    print(f"📝 DEBUG Row {i}: {row}")
                
            except Exception as e:
                print(f"❌ Spreadsheet ochishda xatolik: {e}")
                print("🔄 DEBUG: CSV fallback ishlatilmoqda...")
                # Fallback: CSV usuli (agar fayl public bo'lsa)
                url = f"https://docs.google.com/spreadsheets/d/{investor_sheet_id}/export?format=csv&gid=1601344247"
                response = requests.get(url)
                response.raise_for_status()
                lines = response.text.strip().split('\n')
                all_values = []
                # Faqat birinchi 8 qatorni olish (A1:F8 oralig'i)
                for i, line in enumerate(lines[:8]):
                    if line.strip():
                        row = [cell.strip('"').strip() for cell in line.split(',')]
                        all_values.append(row)
                print(f"📋 DEBUG CSV: {len(all_values)} qator yuklanди")

            # Oy raqamiga qarab ustun indexini aniqlash
            month_columns = {
                "08": 1,  # August - B ustuni
                "09": 2,  # September - C ustuni  
                "10": 3,  # October - D ustuni
                "11": 4,  # November - E ustuni
                "12": 5,  # December - F ustuni
            }
            
            target_column = month_columns.get(month.zfill(2))
            if target_column is None:
                print(f"❌ DEBUG: {month} oyi uchun ustun topilmadi. Mavjud oylar: {list(month_columns.keys())}")
                return []
            
            print(f"🎯 DEBUG: {month} oy uchun {target_column} ustuni tanlandi")

            # Ma'lumotlarni parse qilish - A1:F8 oralig'idan barcha qatorlar
            profit_data = []

            # Har bir qator uchun aniq hujayra ma'lumotini olish
            for i, row in enumerate(all_values):
                # Header qatorini o'tkazib yuborish
                if i == 0:
                    continue
                
                # A1:F8 oralig'ida bo'lish kerak (maksimal 8 qator)
                if i >= 8:
                    break

                if len(row) > 0:
                    tavsif = row[0].strip() if row[0] else ""  # A ustunidagi tavsif
                    
                    # Target ustunda summa mavjudligini tekshirish
                    summa_str = ""
                    if target_column < len(row):
                        summa_str = row[target_column].strip() if row[target_column] else ""

                    print(f"📋 DEBUG Qator {i}: Tavsif='{tavsif}', Summa='{summa_str}'")

                    # Tavsif mavjud bo'lsa qo'shish (summa bo'sh bo'lsa ham)
                    if tavsif:
                        try:
                            # Agar summa bo'sh yoki "-" bo'lsa, 0 deb belgilash
                            if not summa_str or summa_str in ['-', '0', '0,00', '-,00', '  -     ', '  -  ,00   ']:
                                summa = 0.0
                            else:
                                # Summani tozalash
                                summa = self.clean_amount(summa_str)
                            
                            print(f"💰 DEBUG: Topilgan entry: {tavsif} - {summa}")
                            
                            profit_data.append({
                                'sana': f"{year}.{month.zfill(2)}",  # Sana formati
                                'tavsif': tavsif,
                                'summa': summa
                            })
                        except (ValueError, TypeError) as e:
                            print(f"❌ DEBUG: Summa parse xatolik: {e}")
                            # Xatolik bo'lsa ham tavsifni qo'shish, summa 0 bilan
                            profit_data.append({
                                'sana': f"{year}.{month.zfill(2)}",
                                'tavsif': tavsif,
                                'summa': 0.0
                            })

            print(f"📊 Investor: {year}-{month} oy uchun {len(profit_data)} ta yozuv topildi")
            print(f"🔢 DEBUG: profit_data = {profit_data}")
            return profit_data

        except Exception as e:
            print(f"❌ Investor foyda ma'lumotini olishda xatolik: {e}")
            import traceback
            traceback.print_exc()
            return []

    def format_investor_profit_message(self, profit_data, year, month):
        """Investor foyda ma'lumotlarini formatlash"""
        # Oy nomlarini olish
        month_names = {
            "01": "Yanvar", "02": "Fevral", "03": "Mart", "04": "Aprel",
            "05": "May", "06": "Iyun", "07": "Iyul", "08": "Avgust",
            "09": "Sentyabr", "10": "Oktyabr", "11": "Noyabr", "12": "Dekabr"
        }
        month_name = month_names.get(month, month)

        if not profit_data:
            return f"📊 {year} yil {month_name} oyi\n\n❌ Bu oy uchun foyda ma'lumotlari topilmadi."

        # O'zbekiston vaqti
        uzbekistan_tz = timezone(timedelta(hours=5))
        now = datetime.now(uzbekistan_tz)
        formatted_date = now.strftime("%d.%m.%Y")
        formatted_time = now.strftime("%H:%M")

        message = f"📊💰 {year} yil {month_name} oyi foydasi\n\n"
        message += f"```\n"
        message += f"{'Tavsif':<20} {'Summa':<12}\n"
        message += f"{'─'*20} {'─'*12}\n"

        total_profit = 0
        for item in profit_data:
            tavsif = item['tavsif'][:20] if len(item['tavsif']) <= 20 else item['tavsif'][:19] + '…'
            summa = item['summa']
            total_profit += summa
            
            summa_formatted = f"{summa:,.2f} $".replace(',', ' ')
            message += f"{tavsif:<20} {summa_formatted:<12}\n"

        message += f"{'─'*33}\n"
        total_formatted = f"{total_profit:,.2f} $".replace(',', ' ')
        message += f"{'JAMI:':<20} {total_formatted:<12}\n"
        message += "```\n\n"

        message += f"📈 Jami yozuvlar: {len(profit_data)} ta\n"
        message += f"💰 Umumiy foyda: {total_formatted}\n"
        message += f"🕐 {formatted_date} - {formatted_time}"

        return message

# Global instances
sheets_manager = GoogleSheetsManager()
# Oldingi balanslarni saqlash uchun
previous_balances = {}