import os
import sqlite3
import logging
from datetime import datetime, timedelta

from database.connection import get_db_connection, DATABASE_PATH
from database import database_manager as db

def setup_test_database():
    print("--- Test Veritabanı Oluşturma Betiği ---")
    
    confirm = input(
        "\nUYARI: Bu işlem mevcut 'database.db' dosyanızı SİLECEK ve\n"
        "yerine test verileriyle dolu yeni bir veritabanı oluşturacaktır.\n"
        "Bu işlem geri alınamaz. Devam etmek için büyük harflerle 'EVET' yazın: "
    )
    
    if confirm != 'EVET':
        print("\nİşlem kullanıcı tarafından iptal edildi.")
        return

    if os.path.exists(DATABASE_PATH):
        try:
            os.remove(DATABASE_PATH)
            print(f"\n[OK] Mevcut veritabanı '{DATABASE_PATH}' silindi.")
        except OSError as e:
            print(f"[HATA] Veritabanı silinemedi, dosya başka bir program tarafından kullanılıyor olabilir: {e}")
            return

    try:
        print("[...] Yeni veritabanı ve tablolar oluşturuluyor...")
        db.create_tables()
        print("[OK] Tablolar ve varsayılan roller başarıyla oluşturuldu.")
    except Exception as e:
        print(f"[HATA] Tablolar oluşturulurken hata oluştu: {e}")
        return
        
    conn = None
    try:
        print("[...] Test verileri ekleniyor...")
        conn = get_db_connection()
        with conn:
            # Temel Ayarlar ve diğer veriler buraya gelecek
            conn.execute("INSERT OR REPLACE INTO ayarlar (anahtar, deger) VALUES (?, ?)", ('company_name', 'Test Şirketi A.Ş.'))
            conn.execute("INSERT OR REPLACE INTO ayarlar (anahtar, deger) VALUES (?, ?)", ('kdv_orani', '20'))
            kategoriler = [('T-Shirt',), ('Pantolon',), ('Elektronik',)]
            conn.executemany("INSERT INTO kategoriler (ad) VALUES (?)", kategoriler)
            kategori_ids = {row['ad']: row['id'] for row in conn.execute("SELECT id, ad FROM kategoriler")}
            varyant_tipleri = [('Renk',), ('Beden',)]
            conn.executemany("INSERT INTO varyant_tipleri (ad) VALUES (?)", varyant_tipleri)
            musteri_gruplari = [('Bayi',), ('Perakende',)]
            conn.executemany("INSERT INTO musteri_gruplari (ad) VALUES (?)", musteri_gruplari)
            grup_ids = {row['ad']: row['id'] for row in conn.execute("SELECT id, ad FROM musteri_gruplari")}
            conn.execute("INSERT INTO vergi_oranlari (ad, oran) VALUES (?, ?)", ('Standart KDV', 20.0))
            vergi_id = conn.execute("SELECT id FROM vergi_oranlari WHERE ad = 'Standart KDV'").fetchone()['id']
            urunler = [
                {'ad': 'Polo Yaka T-Shirt', 'stok_kodu': 'TSHIRT-POLO', 'kategori_id': kategori_ids['T-Shirt'], 'vergi_id': vergi_id, 'alis_fiyati': 0, 'stok_miktari': 0, 'ana_urun_kodu': None},
                {'ad': 'Polo Yaka T-Shirt - Kırmızı', 'stok_kodu': 'TSHIRT-POLO-KIRMIZI', 'kategori_id': kategori_ids['T-Shirt'], 'vergi_id': vergi_id, 'alis_fiyati': 150.0, 'stok_miktari': 50, 'ana_urun_kodu': 'TSHIRT-POLO'},
                {'ad': 'Polo Yaka T-Shirt - Mavi', 'stok_kodu': 'TSHIRT-POLO-MAVI', 'kategori_id': kategori_ids['T-Shirt'], 'vergi_id': vergi_id, 'alis_fiyati': 155.0, 'stok_miktari': 30, 'ana_urun_kodu': 'TSHIRT-POLO'},
                {'ad': 'Kot Pantolon', 'stok_kodu': 'JEAN-01', 'kategori_id': kategori_ids['Pantolon'], 'vergi_id': vergi_id, 'alis_fiyati': 0, 'stok_miktari': 0, 'ana_urun_kodu': None},
                {'ad': 'Kot Pantolon - 32 Beden', 'stok_kodu': 'JEAN-01-32', 'kategori_id': kategori_ids['Pantolon'], 'vergi_id': vergi_id, 'alis_fiyati': 450.0, 'stok_miktari': 25, 'ana_urun_kodu': 'JEAN-01'},
                {'ad': 'Kot Pantolon - 34 Beden', 'stok_kodu': 'JEAN-01-34', 'kategori_id': kategori_ids['Pantolon'], 'vergi_id': vergi_id, 'alis_fiyati': 450.0, 'stok_miktari': 40, 'ana_urun_kodu': 'JEAN-01'},
                {'ad': 'USB-C Şarj Kablosu', 'stok_kodu': 'USB-C-01', 'kategori_id': kategori_ids['Elektronik'], 'vergi_id': vergi_id, 'alis_fiyati': 80.0, 'stok_miktari': 100, 'ana_urun_kodu': None},
            ]
            for urun in urunler:
                urun.update({'barkod': None, 'alis_para_birimi': 'TL', 'min_stok_seviyesi': 10, 'gorsel_yolu': None})
                db.add_product(urun, conn=conn)
            musteriler = [('Ahmet', 'Yılmaz', '5551112233', 'ahmet@test.com', grup_ids['Perakende']), ('Zeynep', 'Kaya', '5448887766', 'zeynep@test.com', grup_ids['Bayi']), ('Mustafa', 'Öztürk', '5331234567', 'mustafa@test.com', grup_ids['Perakende'])]
            conn.executemany("INSERT INTO musteriler (ad, soyad, telefon, eposta, grup_id) VALUES (?, ?, ?, ?, ?)", musteriler)
            musteri_ids = {row['ad']: row['id'] for row in conn.execute("SELECT id, ad FROM musteriler")}
            satis1_tarih = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
            satis1_tutar = 2 * 250.0 + 1 * 120.0
            conn.execute("INSERT INTO satislar (musteri_id, satis_tarihi, toplam_tutar, odenen_tutar) VALUES (?, ?, ?, ?)", (musteri_ids['Ahmet'], satis1_tarih, satis1_tutar, satis1_tutar))
            satis1_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            urun_ids = {row['stok_kodu']: row['id'] for row in conn.execute("SELECT id, stok_kodu FROM urunler")}
            conn.execute("INSERT INTO satis_detaylari (satis_id, urun_id, miktar, birim_fiyat) VALUES (?, ?, ?, ?)", (satis1_id, urun_ids['TSHIRT-POLO-KIRMIZI'], 2, 250.0))
            conn.execute("INSERT INTO satis_detaylari (satis_id, urun_id, miktar, birim_fiyat) VALUES (?, ?, ?, ?)", (satis1_id, urun_ids['USB-C-01'], 1, 120.0))
            satis2_tarih = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
            satis2_tutar = 1 * 750.0
            conn.execute("INSERT INTO satislar (musteri_id, satis_tarihi, toplam_tutar, odenen_tutar) VALUES (?, ?, ?, ?)", (musteri_ids['Zeynep'], satis2_tarih, satis2_tutar, 500.0))
            satis2_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("INSERT INTO satis_detaylari (satis_id, urun_id, miktar, birim_fiyat) VALUES (?, ?, ?, ?)", (satis2_id, urun_ids['JEAN-01-34'], 1, 750.0))
            db.add_payment(musteri_ids['Zeynep'], 500.0, f"#{satis2_id} nolu satış için ödeme", conn=conn)

        print("[OK] Test verileri başarıyla eklendi.")
        
    except Exception as e:
        print(f"[HATA] Test verileri eklenirken bir hata oluştu: {e}")
        # DÜZELTME: Hata durumunda bağlantı kapatılıp sonra dosya siliniyor
        if conn:
            conn.close()
        if os.path.exists(DATABASE_PATH):
            os.remove(DATABASE_PATH)
        return
    finally:
        if conn:
            conn.close()

    print("\n--- İŞLEM TAMAMLANDI ---")
    print("Test veritabanı başarıyla oluşturuldu. Programı şimdi çalıştırabilirsiniz.")


if __name__ == "__main__":
    setup_test_database()