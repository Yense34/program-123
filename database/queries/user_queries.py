# dosya: database/queries/user_queries.py

import sqlite3
import hashlib
import secrets

from database.connection import get_db_connection

def _hash_new_password(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    sifre_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return sifre_hash.hex(), salt

def _verify_password(stored_password_hash: str, salt: str, provided_password: str) -> bool:
    sifre_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return sifre_hash.hex() == stored_password_hash

def add_user(username, password, rol_id, existing_conn=None):
    sifre_hash, sifre_salt = _hash_new_password(password)
    sql = "INSERT INTO kullanicilar (kullanici_adi, sifre_hash, sifre_salt, rol_id) VALUES (?, ?, ?, ?)"
    params = (username, sifre_hash, sifre_salt, rol_id)
    
    conn = existing_conn or get_db_connection()
    try:
        conn.execute(sql, params)
        if not existing_conn: conn.commit()
        return True, "Kullanıcı başarıyla eklendi."
    except sqlite3.IntegrityError:
        return False, "Bu kullanıcı adı zaten mevcut."
    finally:
        if not existing_conn: conn.close()

def get_all_users():
    with get_db_connection() as conn:
        return conn.execute("""
            SELECT u.id, u.kullanici_adi, r.ad as rol_adi, u.rol_id
            FROM kullanicilar u LEFT JOIN roller r ON u.rol_id = r.id
            ORDER BY u.kullanici_adi
        """).fetchall()

def get_user_by_id(user_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM kullanicilar WHERE id = ?", (user_id,)).fetchone()

def delete_user(user_id: int):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM kullanicilar WHERE id = ?", (user_id,))

def update_user_password(user_id: int, new_password: str):
    sifre_hash, sifre_salt = _hash_new_password(new_password)
    with get_db_connection() as conn:
        conn.execute("UPDATE kullanicilar SET sifre_hash = ?, sifre_salt = ? WHERE id = ?", (sifre_hash, sifre_salt, user_id))

def get_kullanici_rol_adi(rol_id):
    if not rol_id: return "Atanmamış"
    with get_db_connection() as conn:
        row = conn.execute("SELECT ad FROM roller WHERE id = ?", (rol_id,)).fetchone()
        return row['ad'] if row else "Bilinmeyen"

def check_user(username, password):
    with get_db_connection() as conn:
        user_row = conn.execute("SELECT * FROM kullanicilar WHERE kullanici_adi = ?", (username,)).fetchone()

        if not user_row or not user_row['sifre_salt']:
            return None

        user_dict = dict(user_row)
        stored_hash = user_dict['sifre_hash']
        stored_salt = user_dict['sifre_salt']

        if _verify_password(stored_hash, stored_salt, password):
            return user_dict
        
        return None

def get_all_roller():
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM roller ORDER BY ad").fetchall()

def add_rol(ad):
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO roller (ad) VALUES (?)", (ad,))
        return True, "Rol başarıyla eklendi."
    except sqlite3.IntegrityError:
        return False, "Bu rol adı zaten mevcut."

def delete_rol(rol_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM roller WHERE id = ?", (rol_id,))
    return True, "Rol başarıyla silindi."

def is_last_admin_role(rol_id: int):
    with get_db_connection() as conn:
        rol = conn.execute("SELECT ad FROM roller WHERE id = ?", (rol_id,)).fetchone()
        if rol and rol['ad'].lower() == 'yönetici':
            yönetici_rol_id = conn.execute("SELECT id FROM roller WHERE ad = 'Yönetici'").fetchone()['id']
            count = conn.execute("SELECT COUNT(id) FROM kullanicilar WHERE rol_id = ?", (yönetici_rol_id,)).fetchone()[0]
            return count <= 1
        return False

def get_all_yetkiler():
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM yetkiler ORDER BY aciklama").fetchall()

def get_yetkiler_for_rol(rol_id):
    with get_db_connection() as conn:
        return conn.execute("""
            SELECT y.id, y.kod, y.aciklama 
            FROM yetkiler y
            JOIN rol_yetki_iliskisi ry ON y.id = ry.yetki_id
            WHERE ry.rol_id = ?
        """, (rol_id,)).fetchall()

def update_yetkiler_for_rol(rol_id, yetki_id_listesi):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM rol_yetki_iliskisi WHERE rol_id = ?", (rol_id,))
        if yetki_id_listesi:
            data_to_insert = [(rol_id, yetki_id) for yetki_id in yetki_id_listesi]
            conn.executemany("INSERT INTO rol_yetki_iliskisi (rol_id, yetki_id) VALUES (?, ?)", data_to_insert)