# dosya: services/session_manager.py

from database import database_manager as db

class SessionManager:
    def __init__(self):
        self._current_user = None
        self._user_role_name = None
        self._user_permissions = set()

    def login(self, user_data: dict):
        self._current_user = user_data
        
        rol_id = self._current_user.get('rol_id')
        if rol_id:
            self._user_role_name = db.get_kullanici_rol_adi(rol_id)
            permissions = db.get_yetkiler_for_rol(rol_id)
            self._user_permissions = {p['kod'] for p in permissions}
        else:
            self._user_role_name = "Atanmamış"
            self._user_permissions = set()

    def logout(self):
        self._current_user = None
        self._user_role_name = None
        self._user_permissions = set()

    def get_user_data(self) -> dict | None:
        return self._current_user

    def get_username(self) -> str | None:
        if self._current_user:
            return self._current_user.get('kullanici_adi')
        return None

    def get_user_role(self) -> str | None:
        return self._user_role_name

    def has_permission(self, permission_code: str) -> bool:
        return permission_code in self._user_permissions

session = SessionManager()