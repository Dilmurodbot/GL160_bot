from config import ROLES, get_user_role, set_user_role, get_predefined_role

class UserRoleManager:
    """Foydalanuvchi rollarini boshqarish sinfi"""
    
    @staticmethod
    def assign_role(user_id, role):
        """Foydalanuvchiga rol berish"""
        return set_user_role(user_id, role)
    
    @staticmethod
    def get_role(user_id):
        """Foydalanuvchi rolini olish"""
        # Avval predefined role'ni tekshirish
        predefined_role = get_predefined_role(user_id)
        if predefined_role:
            return predefined_role
        # Agar predefined yo'q bo'lsa, USER_ROLES'dan qidirish
        return get_user_role(user_id)
    
    @staticmethod
    def is_mijoz(user_id):
        """Foydalanuvchi mijoz ekanligini tekshirish"""
        role = UserRoleManager.get_role(user_id)
        return role == ROLES["MIJOZ"]
    
    @staticmethod
    def is_manager(user_id):
        """Foydalanuvchi manager ekanligini tekshirish"""
        role = UserRoleManager.get_role(user_id)
        return role == ROLES["MANAGER"]
    
    @staticmethod
    def is_investor(user_id):
        """Foydalanuvchi investor ekanligini tekshirish"""
        role = UserRoleManager.get_role(user_id)
        return role == ROLES["INVESTOR"]
    
    @staticmethod
    def has_role(user_id):
        """Foydalanuvchining roli bor-yo'qligini tekshirish"""
        role = UserRoleManager.get_role(user_id)
        return role is not None
