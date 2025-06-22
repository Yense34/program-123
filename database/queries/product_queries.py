# dosya: database/queries/product_queries.py

import sqlite3
from datetime import datetime
import logging

from database.connection import get_db_connection

def add_product(data: dict, conn=None) -> int | None:
    sql = """
    INSERT INTO urunler (ad, stok_kodu, barkod, kategori_id, vergi_id, alis_para_birimi, 
                         alis_fiyati, stok_miktari, min_stok_seviyesi, ana_urun_kodu, gorsel_yolu, varyant_tipi_id)
    VALUES (:ad, :stok_kodu, :barkod, :kategori_id, :vergi_id, :alis_para_birimi, 
            :alis_fiyati, :stok_miktari, :min_stok_seviyesi, :ana_urun_kodu, :gorsel_yolu, :varyant_tipi_id)
    """
    db_conn = conn or get_db_connection()
    try:
        data.setdefault('barkod', None)
        data.setdefault('ana_urun_kodu', None)
        data.setdefault('gorsel_yolu', None)
        data.setdefault('varyant_tipi_id', None)

        if not data.get('barkod'): data['barkod'] = None
        
        cursor = db_conn.execute(sql, data)
        if not conn: db_conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        logging.error(f"Ürün ekleme hatası (IntegrityError): {e} - Veri: {data}")
        if conn: raise e
        return None
    finally:
        if not conn: db_conn.close()

def update_product(product_id: int, data: dict, conn=None) -> bool:
    data['id'] = product_id
    sql = """
    UPDATE urunler SET
        ad = :ad, stok_kodu = :stok_kodu, barkod = :barkod, kategori_id = :kategori_id,
        vergi_id = :vergi_id, alis_para_birimi = :alis_para_birimi, alis_fiyati = :alis_fiyati,
        stok_miktari = :stok_miktari, min_stok_seviyesi = :min_stok_seviyesi,
        ana_urun_kodu = :ana_urun_kodu, gorsel_yolu = :gorsel_yolu, varyant_tipi_id = :varyant_tipi_id
    WHERE id = :id
    """
    db_conn = conn or get_db_connection()
    try:
        data.setdefault('varyant_tipi_id', None)
        if 'barkod' in data and not data['barkod']: data['barkod'] = None
        db_conn.execute(sql, data)
        if not conn: db_conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        logging.error(f"Ürün güncelleme hatası (IntegrityError): {e}")
        if conn: raise e
        return False
    finally:
        if not conn: db_conn.close()

def save_product_with_variants(product_id: int, main_data: dict, variants_list: list) -> bool:
    main_sku = main_data['stok_kodu']
    try:
        with get_db_connection() as conn:
            update_product(product_id, main_data, conn=conn)
            conn.execute("DELETE FROM urunler WHERE ana_urun_kodu = ?", (main_sku,))

            for variant in variants_list:
                variant_name = variant.get('variant_name') or variant.get('ad','').split(' - ')[-1].strip()
                variant_sku_suffix = variant_name.replace(" ", "-").upper()[:10]
                
                variant_product_data = {
                    "ad": f"{main_data['ad']} - {variant_name}",
                    "stok_kodu": f"{main_sku}-{variant_sku_suffix}",
                    "barkod": variant.get('barkod'), "alis_fiyati": variant.get('alis_fiyati'),
                    "stok_miktari": variant.get('stok_miktari'), "ana_urun_kodu": main_sku,
                    "kategori_id": main_data.get('kategori_id'), "vergi_id": main_data.get('vergi_id'),
                    "alis_para_birimi": main_data.get('alis_para_birimi'), "gorsel_yolu": main_data.get('gorsel_yolu'),
                    "min_stok_seviyesi": 0, "varyant_tipi_id": variant.get("variant_tipi_id")
                }
                add_product(variant_product_data, conn=conn)
        return True
    except Exception as e:
        logging.error(f"Varyantlı ürün kaydedilirken hata oluştu: {e}", exc_info=True)
        return False

def check_varyant_tipi_in_use(tip_id: int) -> bool:
    with get_db_connection() as conn:
        result = conn.execute("SELECT 1 FROM urunler WHERE varyant_tipi_id = ? AND aktif_mi = 1 LIMIT 1", (tip_id,)).fetchone()
        return result is not None

def get_product_by_id(product_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM urunler WHERE id = ?", (product_id,)).fetchone()

def get_products_by_stok_codes(codes: list):
    if not codes: return []
    with get_db_connection() as conn:
        placeholders = ','.join('?' for _ in codes)
        return conn.execute(f"SELECT * FROM urunler WHERE stok_kodu IN ({placeholders})", codes).fetchall()

def get_variants_by_main_code(main_code):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM urunler WHERE ana_urun_kodu = ? AND aktif_mi = 1", (main_code,)).fetchall()

def get_products(search_query=None, category_id=None, stock_status=None, sort_by='ad', sort_order='ASC'):
    with get_db_connection() as conn:
        query = "SELECT u.*, k.ad as kategori_ad FROM urunler u LEFT JOIN kategoriler k ON u.kategori_id = k.id"
        conditions, params = ["u.aktif_mi = 1"], []
        if search_query:
            conditions.append("(u.ad LIKE ? OR u.stok_kodu LIKE ? OR u.barkod LIKE ?)")
            params.extend([f"%{search_query}%"] * 3)
        if category_id is not None:
            conditions.append("u.kategori_id = ?")
            params.append(category_id)
        if stock_status == "Stokta Olanlar": conditions.append("u.stok_miktari > 0")
        elif stock_status == "Tükenenler": conditions.append("u.stok_miktari <= 0")
        elif stock_status == "Kritik Seviyedekiler": conditions.append("u.stok_miktari <= u.min_stok_seviyesi AND u.min_stok_seviyesi > 0")
        if conditions: query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY u.ad"
        return conn.execute(query, params).fetchall()

def check_product_in_use(product_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT 1 FROM satis_detaylari WHERE urun_id = ? LIMIT 1", (product_id,)).fetchone() is not None

def archive_product(product_id):
    with get_db_connection() as conn:
        conn.execute("UPDATE urunler SET aktif_mi = 0 WHERE id = ?", (product_id,))

def delete_product(product_id):
    if check_product_in_use(product_id): return False
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM urunler WHERE id = ?", (product_id,))
        return True
    except sqlite3.Error as e:
        logging.error(f"Ürün silinirken veritabanı hatası: {e}")
        return False

def add_stock_movement(urun_id: int, hareket_tipi: str, miktar: int, aciklama: str, conn=None):
    if miktar == 0: return True
    db_conn = conn or get_db_connection()
    try:
        cursor = db_conn.execute("UPDATE urunler SET stok_miktari = stok_miktari + ? WHERE id = ?", (miktar, urun_id))
        if cursor.rowcount == 0: raise ValueError(f"Stok hareketi için ürün bulunamadı: ID {urun_id}")
        new_stock = db_conn.execute("SELECT stok_miktari FROM urunler WHERE id = ?", (urun_id,)).fetchone()[0]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db_conn.execute("INSERT INTO stok_hareketleri (urun_id, tarih, hareket_tipi, miktar, aciklama, son_stok) VALUES (?, ?, ?, ?, ?, ?)", (urun_id, now, hareket_tipi, miktar, aciklama, new_stock))
        if not conn: db_conn.commit()
        return True
    except (sqlite3.Error, ValueError) as e:
        if not conn: db_conn.rollback()
        return False
    finally:
        if not conn: db_conn.close()

def get_low_stock_products():
    with get_db_connection() as conn:
        return conn.execute("SELECT id, ad, stok_kodu, stok_miktari, min_stok_seviyesi FROM urunler WHERE stok_miktari <= min_stok_seviyesi AND min_stok_seviyesi > 0 AND aktif_mi = 1 ORDER BY stok_miktari ASC").fetchall()

def archive_variant_group(main_product_code: str):
    with get_db_connection() as conn:
        conn.execute("UPDATE urunler SET aktif_mi = 0 WHERE ana_urun_kodu = ? OR stok_kodu = ?", (main_product_code, main_product_code))

def get_inventory_report(category_id=None):
    with get_db_connection() as conn:
        base_query = "SELECT u.stok_kodu, u.ad, k.ad as kategori_ad, u.stok_miktari, u.alis_fiyati, (u.stok_miktari * u.alis_fiyati) as toplam_maliyet FROM urunler u LEFT JOIN kategoriler k ON u.kategori_id = k.id"
        conditions, params = ["u.aktif_mi = 1"], []
        if category_id:
            conditions.append("u.kategori_id = ?"); params.append(category_id)
        query = base_query + " WHERE " + " AND ".join(conditions)
        report_data = conn.execute(query, params).fetchall()
        total_value = sum(item['toplam_maliyet'] for item in report_data)
        return report_data, total_value