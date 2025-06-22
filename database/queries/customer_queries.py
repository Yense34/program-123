# dosya: database/queries/customer_queries.py

from datetime import datetime
from database.connection import get_db_connection
import sqlite3
import logging

GENERAL_CUSTOMER_ID = 1

def add_customer(data):
    with get_db_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO musteriler (ad, soyad, telefon, ikinci_telefon, eposta, tc_no, vergi_no, il, ilce, mahalle, acik_adres, notlar, grup_id) 
            VALUES (:ad, :soyad, :telefon, :ikinci_telefon, :eposta, :tc_no, :vergi_no, :il, :ilce, :mahalle, :acik_adres, :notlar, :grup_id)
            """, data)
        return cursor.lastrowid

def update_customer(customer_id, data):
    with get_db_connection() as conn:
        data['id'] = customer_id
        conn.execute("""
            UPDATE musteriler SET 
            ad=:ad, soyad=:soyad, telefon=:telefon, ikinci_telefon=:ikinci_telefon, eposta=:eposta, 
            tc_no=:tc_no, vergi_no=:vergi_no, il=:il, ilce=:ilce, mahalle=:mahalle, 
            acik_adres=:acik_adres, notlar=:notlar, grup_id=:grup_id 
            WHERE id=:id
            """, data)

def archive_customer(customer_id: int):
    with get_db_connection() as conn:
        conn.execute("UPDATE musteriler SET aktif_mi = 0 WHERE id = ?", (customer_id,))

def add_payment(musteri_id, tutar, aciklama, conn=None):
    db_conn = conn or get_db_connection()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db_conn.execute("INSERT INTO odeme_gecmisi (musteri_id, tarih, tutar, aciklama) VALUES (?, ?, ?, ?)", (musteri_id, now, tutar, aciklama))
        if not conn: db_conn.commit()
    except Exception as e:
        logging.error(f"Ödeme eklenirken hata: {e}")
        if not conn: db_conn.rollback()
    finally:
        if not conn: db_conn.close()


def get_customer_by_id(customer_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM musteriler WHERE id = ?", (customer_id,)).fetchone()

def search_customers(query, group_id=None):
    with get_db_connection() as conn:
        base_query = "SELECT m.id, m.ad, m.soyad, m.telefon, m.eposta, g.ad as grup_adi FROM musteriler m LEFT JOIN musteri_gruplari g ON m.grup_id = g.id"
        conditions = ["m.aktif_mi = 1", "m.id != :general_customer_id"]
        params = {'general_customer_id': GENERAL_CUSTOMER_ID}
        if query:
            conditions.append("(m.ad LIKE :query OR m.soyad LIKE :query OR m.telefon LIKE :query OR m.eposta LIKE :query)")
            params['query'] = f"%{query}%"
        if group_id and group_id > 0:
            conditions.append("m.grup_id = :group_id")
            params['group_id'] = group_id
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        base_query += " ORDER BY m.ad, m.soyad"
        return conn.execute(base_query, params).fetchall()

def get_customer_balance(musteri_id):
    query = """
    SELECT
        (SELECT COALESCE(SUM(toplam_tutar), 0) FROM satislar WHERE musteri_id = :id) -
        (SELECT COALESCE(SUM(tutar), 0) FROM odeme_gecmisi WHERE musteri_id = :id)
    AS balance
    """
    with get_db_connection() as conn:
        result = conn.execute(query, {"id": musteri_id}).fetchone()
        return {"balance": result['balance']}

def get_customer_transaction_history(customer_id: int):
    with get_db_connection() as conn:
        query = """
        SELECT satis_tarihi AS tarih, 'Satış' AS islem_tipi, '#' || id || ' Nolu Satış' AS aciklama,
               toplam_tutar AS borc, 0 AS alacak
        FROM satislar WHERE musteri_id = :id
        UNION ALL
        SELECT tarih, 'Ödeme' AS islem_tipi, aciklama, 0 AS borc, tutar AS alacak
        FROM odeme_gecmisi WHERE musteri_id = :id
        ORDER BY tarih ASC;
        """
        return conn.execute(query, {"id": customer_id}).fetchall()

def get_customer_sales_report(start_date, end_date):
    with get_db_connection() as conn:
        query = """
            SELECT m.id as musteri_id, m.ad || ' ' || m.soyad as musteri_adi,
                   SUM(sd.miktar * sd.birim_fiyat) as toplam_ciro,
                   SUM(sd.miktar * u.alis_fiyati) as toplam_maliyet,
                   (SUM(sd.miktar * sd.birim_fiyat) - SUM(sd.miktar * u.alis_fiyati)) as toplam_kar
            FROM musteriler m
            JOIN satislar s ON m.id = s.musteri_id
            JOIN satis_detaylari sd ON s.id = sd.satis_id
            JOIN urunler u ON sd.urun_id = u.id
            WHERE s.satis_tarihi BETWEEN ? AND ? AND m.id != ?
            GROUP BY m.id, musteri_adi HAVING toplam_ciro > 0
            ORDER BY toplam_kar DESC;
        """
        return conn.execute(query, (start_date, end_date, GENERAL_CUSTOMER_ID)).fetchall()