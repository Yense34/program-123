# dosya: database/queries/sale_queries.py

import sqlite3
import logging
from datetime import datetime

from database.connection import get_db_connection
from . import product_queries 

def create_sale(sale_data, sale_details, sale_date_str=None):
    try:
        with get_db_connection() as conn:
            satis_tarihi = sale_date_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor = conn.execute(
                "INSERT INTO satislar (musteri_id, satis_tarihi, toplam_tutar, odenen_tutar) VALUES (?, ?, ?, ?)",
                (sale_data['musteri_id'], satis_tarihi, sale_data['toplam_tutar'], sale_data['odenen_tutar'])
            )
            satis_id = cursor.lastrowid
            
            for detail in sale_details:
                conn.execute(
                    "INSERT INTO satis_detaylari (satis_id, urun_id, miktar, birim_fiyat) VALUES (?, ?, ?, ?)",
                    (satis_id, detail['urun_id'], detail['miktar'], detail['birim_fiyat'])
                )
                product_queries.add_stock_movement(
                    urun_id=detail['urun_id'], hareket_tipi="Satış", 
                    miktar=-detail['miktar'], aciklama=f"Satış No: {satis_id}", conn=conn
                )
            
            if sale_data['odenen_tutar'] > 0:
                payment_description = f"#{satis_id} Nolu Satış İçin Ödeme"
                conn.execute(
                    "INSERT INTO odeme_gecmisi (musteri_id, tarih, tutar, aciklama) VALUES (?, ?, ?, ?)",
                    (sale_data['musteri_id'], satis_tarihi, sale_data['odenen_tutar'], payment_description)
                )
        return satis_id
    except (sqlite3.Error, ValueError) as e:
        logging.error(f"Satış oluşturma sırasında veritabanı hatası: {e}", exc_info=True)
        return None

def delete_sale_by_id(sale_id: int):
    try:
        with get_db_connection() as conn:
            sale_details = conn.execute("SELECT urun_id, miktar FROM satis_detaylari WHERE satis_id = ?", (sale_id,)).fetchall()
            if not sale_details:
                conn.execute("DELETE FROM satislar WHERE id = ?", (sale_id,))
                return True, "Satış detayı bulunamasa da ana kayıt silindi."

            for detail in sale_details:
                product_queries.add_stock_movement(
                    urun_id=detail['urun_id'], hareket_tipi='Satış İptali', 
                    miktar=detail['miktar'], aciklama=f"İptal Edilen Satış No: {sale_id}", conn=conn
                )
            
            conn.execute("DELETE FROM satislar WHERE id = ?", (sale_id,))
        return True, f"#{sale_id} numaralı satış başarıyla iptal edildi ve stoklar iade edildi."
    except (sqlite3.Error, ValueError) as e:
        logging.error(f"Satış silinirken veritabanı hatası oluştu: {e}", exc_info=True)
        return False, f"Satış silinemedi: {e}"

def get_sales_by_day_for_month():
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    query = """
        SELECT strftime('%Y-%m-%d', satis_tarihi) as gun, SUM(toplam_tutar) as toplam_satis
        FROM satislar WHERE satis_tarihi >= ? GROUP BY gun ORDER BY gun ASC
    """
    with get_db_connection() as conn:
        return conn.execute(query, (start_of_month,)).fetchall()

def get_sales_by_category():
    query = """
        SELECT COALESCE(k.ad, 'Kategorisiz') as kategori_adi, SUM(sd.miktar * sd.birim_fiyat) as toplam_ciro
        FROM satis_detaylari sd
        JOIN urunler u ON sd.urun_id = u.id LEFT JOIN kategoriler k ON u.kategori_id = k.id
        WHERE u.aktif_mi = 1 GROUP BY kategori_adi ORDER BY toplam_ciro DESC
    """
    with get_db_connection() as conn:
        return conn.execute(query).fetchall()

def get_recent_sales():
    with get_db_connection() as conn:
        return conn.execute("""
            SELECT s.id, s.satis_tarihi, COALESCE(m.ad || ' ' || m.soyad, 'Genel Müşteri') as musteri_adi, s.toplam_tutar 
            FROM satislar s LEFT JOIN musteriler m ON s.musteri_id = m.id 
            ORDER BY s.id DESC LIMIT 5
        """).fetchall()

def get_sale_details_for_report(sale_id):
    with get_db_connection() as conn:
        sale_info = conn.execute("SELECT s.*, COALESCE(m.ad || ' ' || m.soyad, 'Genel Müşteri') as musteri_adi, m.telefon, m.id as musteri_id FROM satislar s LEFT JOIN musteriler m ON s.musteri_id = m.id WHERE s.id = ?", (sale_id,)).fetchone()
        if not sale_info: return None
        
        details = conn.execute("SELECT sd.urun_id, sd.miktar, sd.birim_fiyat, u.ad as urun_ad, u.stok_kodu FROM satis_detaylari sd JOIN urunler u ON sd.urun_id = u.id WHERE sd.satis_id = ?", (sale_id,)).fetchall()
        return {"sale_info": sale_info, "details": details}

def get_sales_by_date_range(start_date, end_date, customer_id=None):
    with get_db_connection() as conn:
        query = "SELECT s.id, s.satis_tarihi, COALESCE(m.ad || ' ' || m.soyad, 'Genel Müşteri') as musteri_adi, s.toplam_tutar FROM satislar s LEFT JOIN musteriler m ON s.musteri_id = m.id"
        conditions, params = ["s.satis_tarihi BETWEEN ? AND ?"], [start_date, end_date]
        if customer_id:
            conditions.append("s.musteri_id = ?")
            params.append(customer_id)
        query += " WHERE " + " AND ".join(conditions) + " ORDER BY s.satis_tarihi DESC;"
        sales = conn.execute(query, params).fetchall()
        total = sum(s['toplam_tutar'] for s in sales)
        return sales, total

def get_sales_with_profit_by_date_range(start_date, end_date, customer_id=None):
    with get_db_connection() as conn:
        query = """
        WITH SaleCosts AS (
            SELECT sd.satis_id, SUM(sd.miktar * u.alis_fiyati) as toplam_maliyet
            FROM satis_detaylari sd JOIN urunler u ON sd.urun_id = u.id
            GROUP BY sd.satis_id
        )
        SELECT s.id, s.satis_tarihi, COALESCE(m.ad || ' ' || m.soyad, 'Genel Müşteri') as musteri_adi,
               s.toplam_tutar, COALESCE(sc.toplam_maliyet, 0) as toplam_maliyet,
               (s.toplam_tutar - COALESCE(sc.toplam_maliyet, 0)) as kar
        FROM satislar s
        LEFT JOIN SaleCosts sc ON s.id = sc.satis_id
        LEFT JOIN musteriler m ON s.musteri_id = m.id
        """
        conditions, params = ["s.satis_tarihi BETWEEN ? AND ?"], [start_date, end_date]
        if customer_id:
            conditions.append("s.musteri_id = ?")
            params.append(customer_id)
        query += " WHERE " + " AND ".join(conditions) + " ORDER BY s.satis_tarihi DESC;"
        
        sales_data = conn.execute(query, params).fetchall()
        total_revenue = sum(s['toplam_tutar'] for s in sales_data)
        total_cost = sum(s['toplam_maliyet'] for s in sales_data)
        totals = {'total_revenue': total_revenue, 'total_cost': total_cost, 'total_profit': total_revenue - total_cost}
        return sales_data, totals

def get_all_sales_history():
    with get_db_connection() as conn:
        return conn.execute("SELECT s.id, s.satis_tarihi, COALESCE(m.ad || ' ' || m.soyad, 'Genel Müşteri') as musteri_adi, s.toplam_tutar FROM satislar s LEFT JOIN musteriler m ON s.musteri_id = m.id ORDER BY s.id DESC").fetchall()

def search_sales_history(query):
    with get_db_connection() as conn:
        search_term = f"%{query}%"
        return conn.execute("SELECT s.id, s.satis_tarihi, COALESCE(m.ad || ' ' || m.soyad, 'Genel Müşteri') as musteri_adi, s.toplam_tutar FROM satislar s LEFT JOIN musteriler m ON s.musteri_id = m.id WHERE musteri_adi LIKE ? OR s.id LIKE ? ORDER BY s.id DESC", (search_term, search_term)).fetchall()

def get_product_sales_report(start_date, end_date, category_id=None):
    with get_db_connection() as conn:
        query = """
        SELECT u.id as urun_id, u.stok_kodu, u.ad as urun_adi, SUM(sd.miktar) as toplam_satilan_adet,
               SUM(sd.miktar * sd.birim_fiyat) as toplam_ciro, SUM(sd.miktar * u.alis_fiyati) as toplam_maliyet,
               (SUM(sd.miktar * sd.birim_fiyat) - SUM(sd.miktar * u.alis_fiyati)) as toplam_kar
        FROM satis_detaylari sd
        JOIN urunler u ON sd.urun_id = u.id JOIN satislar s ON sd.satis_id = s.id
        """
        conditions, params = ["s.satis_tarihi BETWEEN ? AND ?"], [start_date, end_date]
        if category_id:
            conditions.append("u.kategori_id = ?")
            params.append(category_id)
        query += " WHERE " + " AND ".join(conditions) + " GROUP BY u.id, u.ad, u.stok_kodu ORDER BY toplam_ciro DESC;"
        return conn.execute(query, params).fetchall()

def get_daily_sales_for_period(start_date, end_date, customer_id=None):
    with get_db_connection() as conn:
        query = "SELECT strftime('%Y-%m-%d', satis_tarihi) as gun, SUM(toplam_tutar) as toplam_satis FROM satislar"
        conditions, params = ["satis_tarihi BETWEEN ? AND ?"], [start_date, end_date]
        if customer_id:
            conditions.append("musteri_id = ?")
            params.append(customer_id)
        query += " WHERE " + " AND ".join(conditions) + " GROUP BY gun ORDER BY gun ASC;"
        return conn.execute(query, params).fetchall()

def add_suspended_sale(musteri_id, sepet_json, not_str):
    with get_db_connection() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("INSERT INTO askidaki_satislar (musteri_id, sepet_icerigi, not_str, askiya_alinma_tarihi) VALUES (?, ?, ?, ?)", (musteri_id, sepet_json, not_str, now))

def get_all_suspended_sales():
    with get_db_connection() as conn:
        return conn.execute("""
            SELECT a.id, a.askiya_alinma_tarihi, a.not_str, COALESCE(m.ad || ' ' || m.soyad, 'Genel Müşteri') as musteri_adi
            FROM askidaki_satislar a LEFT JOIN musteriler m ON a.musteri_id = m.id
            ORDER BY a.askiya_alinma_tarihi DESC
        """).fetchall()

def get_suspended_sale_by_id(sale_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM askidaki_satislar WHERE id = ?", (sale_id,)).fetchone()

def delete_suspended_sale(sale_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM askidaki_satislar WHERE id = ?", (sale_id,))