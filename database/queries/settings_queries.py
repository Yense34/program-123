# dosya: database/queries/settings_queries.py

import sqlite3
from database.connection import get_db_connection

def get_setting(anahtar, varsayilan=None):
    with get_db_connection() as conn:
        row = conn.execute("SELECT deger FROM ayarlar WHERE anahtar = ?", (anahtar,)).fetchone()
        return row['deger'] if row else varsayilan

def save_setting(anahtar, deger):
    with get_db_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO ayarlar (anahtar, deger) VALUES (?, ?)", (anahtar, str(deger)))

def get_all_settings():
    with get_db_connection() as conn:
        return {row['anahtar']: row['deger'] for row in conn.execute("SELECT anahtar, deger FROM ayarlar")}

def get_all_kategoriler():
    with get_db_connection() as conn:
        return conn.execute("SELECT id, ad FROM kategoriler ORDER BY ad").fetchall()

def add_kategori(ad):
    if not ad: return
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO kategoriler (ad) VALUES (?)", (ad,))
    except sqlite3.IntegrityError:
        pass

def update_kategori(kategori_id, yeni_ad):
    with get_db_connection() as conn:
        conn.execute("UPDATE kategoriler SET ad = ? WHERE id = ?", (yeni_ad, kategori_id))

def check_kategori_in_use(kategori_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT 1 FROM urunler WHERE kategori_id = ? AND aktif_mi = 1 LIMIT 1", (kategori_id,)).fetchone() is not None

def delete_kategori(kategori_id):
    if check_kategori_in_use(kategori_id):
        return False, "Bu kategori bir veya daha fazla ürüne atanmış olduğu için silinemez."
    with get_db_connection() as conn:
        conn.execute("DELETE FROM kategoriler WHERE id = ?", (kategori_id,))
    return True, "Kategori başarıyla silindi."

def get_all_varyant_tipleri():
    with get_db_connection() as conn:
        return conn.execute("SELECT id, ad FROM varyant_tipleri ORDER BY ad").fetchall()

def add_varyant_tipi(ad):
    if not ad: return
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO varyant_tipleri (ad) VALUES (?)", (ad,))
    except sqlite3.IntegrityError:
        pass

def update_varyant_tipi(tip_id, yeni_ad):
    with get_db_connection() as conn:
        conn.execute("UPDATE varyant_tipleri SET ad = ? WHERE id = ?", (yeni_ad, tip_id))

def check_varyant_tipi_in_use(tip_id):
    with get_db_connection() as conn:
        tip_row = conn.execute("SELECT ad FROM varyant_tipleri WHERE id = ?", (tip_id,)).fetchone()
        if not tip_row: return False
        search_pattern = f"% - {tip_row['ad']}%"
        return conn.execute("SELECT 1 FROM urunler WHERE ad LIKE ? AND aktif_mi = 1 LIMIT 1", (search_pattern,)).fetchone() is not None

def delete_varyant_tipi(tip_id):
    if check_varyant_tipi_in_use(tip_id):
        return False, "Bu varyant tipi bir veya daha fazla üründe kullanıldığı için silinemez."
    with get_db_connection() as conn:
        conn.execute("DELETE FROM varyant_tipleri WHERE id = ?", (tip_id,))
    return True, "Varyant tipi başarıyla silindi."

def get_all_musteri_gruplari():
    with get_db_connection() as conn:
        return conn.execute("SELECT id, ad FROM musteri_gruplari ORDER BY ad").fetchall()

def add_musteri_grup(ad):
    if not ad: return
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO musteri_gruplari (ad) VALUES (?)", (ad,))
    except sqlite3.IntegrityError:
        pass

def update_musteri_grup(grup_id, yeni_ad):
    with get_db_connection() as conn:
        conn.execute("UPDATE musteri_gruplari SET ad = ? WHERE id = ?", (yeni_ad, grup_id))

def check_musteri_grup_in_use(grup_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT 1 FROM musteriler WHERE grup_id = ? AND aktif_mi = 1 LIMIT 1", (grup_id,)).fetchone() is not None

def delete_musteri_grup(grup_id):
    if check_musteri_grup_in_use(grup_id):
        return False, "Bu grup bir veya daha fazla müşteriye atanmış olduğu için silinemez."
    with get_db_connection() as conn:
        conn.execute("DELETE FROM musteri_gruplari WHERE id = ?", (grup_id,))
    return True, "Müşteri grubu başarıyla silindi."

def get_category_details(category_id: int):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM kategoriler WHERE id = ?", (category_id,)).fetchone()

def update_category_profit(category_id: int, profit_type: str, profit_value: float):
    with get_db_connection() as conn:
        conn.execute("UPDATE kategoriler SET kar_tipi = ?, kar_degeri = ? WHERE id = ?", (profit_type, profit_value, category_id))

def get_all_vergi_oranlari():
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM vergi_oranlari ORDER BY ad").fetchall()

def add_vergi_orani(ad, oran):
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO vergi_oranlari (ad, oran) VALUES (?, ?)", (ad, oran))
        return True, "Vergi oranı başarıyla eklendi."
    except sqlite3.IntegrityError:
        return False, "Bu vergi adı zaten mevcut."

def check_vergi_orani_in_use(vergi_id):
     with get_db_connection() as conn:
        return conn.execute("SELECT 1 FROM urunler WHERE vergi_id = ? AND aktif_mi = 1 LIMIT 1", (vergi_id,)).fetchone() is not None

def delete_vergi_orani(vergi_id):
    if check_vergi_orani_in_use(vergi_id):
        return False, "Bu vergi oranı bir veya daha fazla üründe kullanıldığı için silinemez."
    with get_db_connection() as conn:
        conn.execute("DELETE FROM vergi_oranlari WHERE id = ?", (vergi_id,))
    return True, "Vergi oranı başarıyla silindi."

def get_vergi_orani_by_id(vergi_id: int):
    if not vergi_id: return None
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM vergi_oranlari WHERE id = ?", (vergi_id,)).fetchone()

def get_message_templates(template_type: str):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM mesaj_sablonlari WHERE tip = ? ORDER BY ad", (template_type,)).fetchall()

def add_message_template(name: str, content: str, template_type: str):
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO mesaj_sablonlari (ad, icerik, tip) VALUES (?, ?, ?)", (name, content, template_type))
        return True, "Şablon başarıyla eklendi."
    except sqlite3.IntegrityError:
        return False, "Bu şablon adı zaten mevcut."

def delete_message_template(template_id: int):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM mesaj_sablonlari WHERE id = ?", (template_id,))

def get_inventory_value_by_category():
    with get_db_connection() as conn:
        return conn.execute("""
            SELECT COALESCE(k.ad, 'Kategorisiz') as kategori_adi, SUM(u.stok_miktari * u.alis_fiyati) as toplam_deger
            FROM urunler u LEFT JOIN kategoriler k ON u.kategori_id = k.id
            WHERE u.aktif_mi = 1 AND u.stok_miktari > 0 GROUP BY kategori_adi
            HAVING toplam_deger > 0 ORDER BY toplam_deger DESC;
        """).fetchall()

def get_dashboard_stats():
    with get_db_connection() as conn:
        stats = {
            "total_customers": conn.execute("SELECT COUNT(id) FROM musteriler WHERE aktif_mi = 1 AND id != 1").fetchone()[0],
            "total_products": conn.execute("SELECT COUNT(id) FROM urunler WHERE aktif_mi = 1").fetchone()[0]
        }
        top_product_row = conn.execute("""
            SELECT u.ad, SUM(sd.miktar) as toplam_satilan FROM satis_detaylari sd 
            JOIN urunler u ON sd.urun_id = u.id 
            WHERE u.aktif_mi = 1 
            GROUP BY u.ad ORDER BY toplam_satilan DESC LIMIT 1
        """).fetchone()
        stats.update({
            "top_product_name": top_product_row['ad'] if top_product_row else "N/A",
            "top_product_quantity": top_product_row['toplam_satilan'] if top_product_row else 0
        })
        return stats