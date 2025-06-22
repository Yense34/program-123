# dosya: database/database_manager.py

import sqlite3
import logging
import os
import shutil
from datetime import datetime

from .connection import get_db_connection
from .queries import user_queries, product_queries, customer_queries, sale_queries, settings_queries

add_user = user_queries.add_user
get_all_users = user_queries.get_all_users
get_user_by_id = user_queries.get_user_by_id
delete_user = user_queries.delete_user
update_user_password = user_queries.update_user_password
check_user = user_queries.check_user
get_all_roller = user_queries.get_all_roller
add_rol = user_queries.add_rol
delete_rol = user_queries.delete_rol
is_last_admin_role = user_queries.is_last_admin_role
get_all_yetkiler = user_queries.get_all_yetkiler
get_yetkiler_for_rol = user_queries.get_yetkiler_for_rol
update_yetkiler_for_rol = user_queries.update_yetkiler_for_rol
get_kullanici_rol_adi = user_queries.get_kullanici_rol_adi

save_product_with_variants = product_queries.save_product_with_variants
add_product = product_queries.add_product
update_product = product_queries.update_product
get_product_by_id = product_queries.get_product_by_id
get_products_by_stok_codes = product_queries.get_products_by_stok_codes
get_variants_by_main_code = product_queries.get_variants_by_main_code
get_products = product_queries.get_products
check_product_in_use = product_queries.check_product_in_use
archive_product = product_queries.archive_product
delete_product = product_queries.delete_product
add_stock_movement = product_queries.add_stock_movement
get_low_stock_products = product_queries.get_low_stock_products
get_inventory_report = product_queries.get_inventory_report
archive_variant_group = product_queries.archive_variant_group

add_customer = customer_queries.add_customer
update_customer = customer_queries.update_customer
archive_customer = customer_queries.archive_customer
add_payment = customer_queries.add_payment
get_customer_by_id = customer_queries.get_customer_by_id
search_customers = customer_queries.search_customers
get_customer_balance = customer_queries.get_customer_balance
get_customer_transaction_history = customer_queries.get_customer_transaction_history
get_customer_sales_report = customer_queries.get_customer_sales_report

create_sale = sale_queries.create_sale
delete_sale_by_id = sale_queries.delete_sale_by_id
get_sales_by_day_for_month = sale_queries.get_sales_by_day_for_month
get_sales_by_category = sale_queries.get_sales_by_category
get_recent_sales = sale_queries.get_recent_sales
get_sale_details_for_report = sale_queries.get_sale_details_for_report
get_sales_by_date_range = sale_queries.get_sales_by_date_range
get_sales_with_profit_by_date_range = sale_queries.get_sales_with_profit_by_date_range
get_all_sales_history = sale_queries.get_all_sales_history
search_sales_history = sale_queries.search_sales_history
get_product_sales_report = sale_queries.get_product_sales_report
get_daily_sales_for_period = sale_queries.get_daily_sales_for_period
add_suspended_sale = sale_queries.add_suspended_sale
get_all_suspended_sales = sale_queries.get_all_suspended_sales
get_suspended_sale_by_id = sale_queries.get_suspended_sale_by_id
delete_suspended_sale = sale_queries.delete_suspended_sale

get_setting = settings_queries.get_setting
save_setting = settings_queries.save_setting
get_all_settings = settings_queries.get_all_settings
get_all_kategoriler = settings_queries.get_all_kategoriler
add_kategori = settings_queries.add_kategori
update_kategori = settings_queries.update_kategori
check_kategori_in_use = settings_queries.check_kategori_in_use
delete_kategori = settings_queries.delete_kategori
get_all_varyant_tipleri = settings_queries.get_all_varyant_tipleri
add_varyant_tipi = settings_queries.add_varyant_tipi
update_varyant_tipi = settings_queries.update_varyant_tipi
delete_varyant_tipi = settings_queries.delete_varyant_tipi
check_varyant_tipi_in_use = settings_queries.check_varyant_tipi_in_use
get_all_musteri_gruplari = settings_queries.get_all_musteri_gruplari
add_musteri_grup = settings_queries.add_musteri_grup
update_musteri_grup = settings_queries.update_musteri_grup
delete_musteri_grup = settings_queries.delete_musteri_grup
get_category_details = settings_queries.get_category_details
update_category_profit = settings_queries.update_category_profit
get_all_vergi_oranlari = settings_queries.get_all_vergi_oranlari
add_vergi_orani = settings_queries.add_vergi_orani
delete_vergi_orani = settings_queries.delete_vergi_orani
get_vergi_orani_by_id = settings_queries.get_vergi_orani_by_id
get_message_templates = settings_queries.get_message_templates
add_message_template = settings_queries.add_message_template
delete_message_template = settings_queries.delete_message_template
get_inventory_value_by_category = settings_queries.get_inventory_value_by_category
get_dashboard_stats = settings_queries.get_dashboard_stats

def _create_user_and_role_tables(cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS roller (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT NOT NULL UNIQUE)")
    cursor.execute("CREATE TABLE IF NOT EXISTS yetkiler (id INTEGER PRIMARY KEY AUTOINCREMENT, kod TEXT NOT NULL UNIQUE, aciklama TEXT NOT NULL)")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rol_yetki_iliskisi (
        rol_id INTEGER NOT NULL, yetki_id INTEGER NOT NULL,
        PRIMARY KEY (rol_id, yetki_id),
        FOREIGN KEY (rol_id) REFERENCES roller(id) ON DELETE CASCADE,
        FOREIGN KEY (yetki_id) REFERENCES yetkiler(id) ON DELETE CASCADE
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kullanicilar (
        id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici_adi TEXT NOT NULL UNIQUE,
        sifre_hash TEXT NOT NULL, rol_id INTEGER, sifre_salt TEXT,
        FOREIGN KEY (rol_id) REFERENCES roller(id) ON DELETE SET NULL
    )""")

def _create_product_related_tables(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kategoriler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT NOT NULL UNIQUE,
        kar_tipi TEXT, kar_degeri REAL
    )""")
    cursor.execute("CREATE TABLE IF NOT EXISTS varyant_tipleri (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT NOT NULL UNIQUE)")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vergi_oranlari (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT NOT NULL UNIQUE, oran REAL NOT NULL
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS urunler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, stok_kodu TEXT NOT NULL UNIQUE,
        ad TEXT NOT NULL, barkod TEXT, ana_urun_kodu TEXT, kategori_id INTEGER,
        vergi_id INTEGER, alis_fiyati REAL NOT NULL, alis_para_birimi TEXT NOT NULL DEFAULT 'TL',
        stok_miktari INTEGER NOT NULL, min_stok_seviyesi INTEGER DEFAULT 0,
        gorsel_yolu TEXT, aktif_mi BOOLEAN NOT NULL DEFAULT 1,
        FOREIGN KEY (kategori_id) REFERENCES kategoriler(id) ON DELETE RESTRICT,
        FOREIGN KEY (vergi_id) REFERENCES vergi_oranlari(id) ON DELETE SET NULL
    )""")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_urunler_barkod ON urunler (barkod) WHERE barkod IS NOT NULL AND barkod != ''")

def _create_customer_related_tables(cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS musteri_gruplari (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT NOT NULL UNIQUE)")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS musteriler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT NOT NULL, soyad TEXT NOT NULL,
        telefon TEXT, ikinci_telefon TEXT, eposta TEXT, tc_no TEXT, vergi_no TEXT,
        il TEXT, ilce TEXT, mahalle TEXT, acik_adres TEXT, notlar TEXT,
        aktif_mi BOOLEAN NOT NULL DEFAULT 1, grup_id INTEGER,
        FOREIGN KEY (grup_id) REFERENCES musteri_gruplari(id) ON DELETE SET NULL 
    )""")

def _create_sales_related_tables(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS satislar (
        id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER,
        satis_tarihi TEXT NOT NULL, toplam_tutar REAL NOT NULL, odenen_tutar REAL NOT NULL,
        FOREIGN KEY (musteri_id) REFERENCES musteriler(id)
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS satis_detaylari (
        id INTEGER PRIMARY KEY AUTOINCREMENT, satis_id INTEGER NOT NULL, urun_id INTEGER NOT NULL,
        miktar INTEGER NOT NULL, birim_fiyat REAL NOT NULL,
        FOREIGN KEY (satis_id) REFERENCES satislar(id) ON DELETE CASCADE,
        FOREIGN KEY (urun_id) REFERENCES urunler(id) ON DELETE RESTRICT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS odeme_gecmisi (
        id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER NOT NULL,
        tarih TEXT NOT NULL, tutar REAL NOT NULL, aciklama TEXT,
        FOREIGN KEY (musteri_id) REFERENCES musteriler(id)
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stok_hareketleri (
        id INTEGER PRIMARY KEY AUTOINCREMENT, urun_id INTEGER NOT NULL, tarih TEXT NOT NULL,
        hareket_tipi TEXT NOT NULL, miktar INTEGER NOT NULL, aciklama TEXT,
        son_stok INTEGER NOT NULL, FOREIGN KEY (urun_id) REFERENCES urunler(id) ON DELETE CASCADE
    )""")

def _create_utility_tables(cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS ayarlar (anahtar TEXT PRIMARY KEY, deger TEXT NOT NULL)")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mesaj_sablonlari (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT NOT NULL UNIQUE,
        icerik TEXT NOT NULL, tip TEXT NOT NULL
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS askidaki_satislar (
        id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, not_str TEXT,
        sepet_icerigi TEXT NOT NULL, askiya_alinma_tarihi TEXT NOT NULL,
        FOREIGN KEY (musteri_id) REFERENCES musteriler(id) ON DELETE CASCADE
    )""")

def _run_migrations(cursor):
    try:
        urun_columns = [c['name'] for c in cursor.execute("PRAGMA table_info(urunler)").fetchall()]
        if 'vergi_id' not in urun_columns:
            cursor.execute("ALTER TABLE urunler ADD COLUMN vergi_id INTEGER REFERENCES vergi_oranlari(id) ON DELETE SET NULL")
        
        musteri_columns = [c['name'] for c in cursor.execute("PRAGMA table_info(musteriler)").fetchall()]
        if 'grup_id' not in musteri_columns:
            cursor.execute("ALTER TABLE musteriler ADD COLUMN grup_id INTEGER REFERENCES musteri_gruplari(id) ON DELETE SET NULL")

        if 'varyant_tipi_id' not in urun_columns:
            cursor.execute("""
                ALTER TABLE urunler 
                ADD COLUMN varyant_tipi_id INTEGER 
                REFERENCES varyant_tipleri(id) ON DELETE SET NULL
            """)
            logging.info("Veritabanı güncellendi: 'urunler' tablosuna 'varyant_tipi_id' sütunu eklendi.")

    except sqlite3.Error as e:
        logging.error(f"Veritabanı migration sırasında hata: {e}")

def _populate_initial_data(cursor):
    cursor.execute("INSERT OR IGNORE INTO roller (ad) VALUES ('Yönetici'), ('Standart Kullanıcı')")
    
    permissions = [
        ('settings:view', 'Ayarlar sayfasını görüntüleme'), ('settings:user_management', 'Kullanıcıları ve rolleri yönetme'),
        ('reports:view', 'Raporlar sayfasını görüntüleme'), ('products:delete', 'Ürün silme/arşivleme'),
        ('products:create', 'Yeni ürün ekleme'), ('products:edit', 'Ürün bilgilerini düzenleme'),
        ('customers:delete', 'Müşteri silme/arşivleme'), ('customers:create', 'Yeni müşteri ekleme'),
        ('customers:edit', 'Müşteri bilgilerini düzenleme'), ('sales:delete', 'Satış kaydını silme'),
        ('sales:edit', 'Satış kaydını düzenleme'), ('bulk_communication:send', 'Toplu SMS/E-posta gönderme')
    ]
    cursor.executemany("INSERT OR IGNORE INTO yetkiler (kod, aciklama) VALUES (?, ?)", permissions)
    
    admin_role_id = cursor.execute("SELECT id FROM roller WHERE ad = 'Yönetici'").fetchone()['id']
    all_permission_ids = [row['id'] for row in cursor.execute("SELECT id FROM yetkiler").fetchall()]
    for perm_id in all_permission_ids:
        cursor.execute("INSERT OR IGNORE INTO rol_yetki_iliskisi (rol_id, yetki_id) VALUES (?, ?)", (admin_role_id, perm_id))
        
    cursor.execute("INSERT OR IGNORE INTO musteriler (id, ad, soyad, aktif_mi) VALUES (1, 'Genel', 'Müşteri', 1)")

    if cursor.execute("SELECT COUNT(id) FROM kullanicilar").fetchone()[0] == 0:
        DEFAULT_ADMIN_PASSWORD = "TicariSistem.2025!"
        DEFAULT_USER_PASSWORD = "kullanici.1234"
        
        logging.warning("İlk kurulum: Varsayılan kullanıcılar oluşturuluyor. Lütfen ilk girişten sonra şifreleri değiştirin.")
        
        user_role_id = cursor.execute("SELECT id FROM roller WHERE ad = 'Standart Kullanıcı'").fetchone()['id']
        user_queries.add_user("admin", DEFAULT_ADMIN_PASSWORD, admin_role_id, cursor.connection)
        user_queries.add_user("kullanici", DEFAULT_USER_PASSWORD, user_role_id, cursor.connection)
        logging.warning(f"-> Yönetici: admin / Şifre: {DEFAULT_ADMIN_PASSWORD}")
        logging.warning(f"-> Kullanıcı: kullanici / Şifre: {DEFAULT_USER_PASSWORD}")

def create_tables():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        _create_user_and_role_tables(cursor)
        _create_product_related_tables(cursor)
        _create_customer_related_tables(cursor)
        _create_sales_related_tables(cursor)
        _create_utility_tables(cursor)
        _run_migrations(cursor)
        _populate_initial_data(cursor)
        conn.commit()

BACKUP_DIR = "backups"
BACKUP_PREFIX = "otomatik_yedek_"
MAX_AUTO_BACKUPS = 5

def perform_automatic_backup():
    try:
        if settings_queries.get_setting('auto_backup_on_exit', 'False') != 'True':
            return
    except Exception as e:
        logging.error(f"Yedekleme ayarı okunurken hata oluştu: {e}")
        return

    logging.info("Otomatik yedekleme işlemi başlatılıyor...")
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        existing_backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith(BACKUP_PREFIX) and f.endswith(".db")])
        
        while len(existing_backups) >= MAX_AUTO_BACKUPS:
            path_to_delete = os.path.join(BACKUP_DIR, existing_backups.pop(0))
            try:
                os.remove(path_to_delete)
                logging.info(f"Eski otomatik yedek silindi: {path_to_delete}")
            except Exception as e:
                logging.error(f"Eski yedek ({path_to_delete}) silinirken hata: {e}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"{BACKUP_PREFIX}{timestamp}.db"
        save_path = os.path.join(BACKUP_DIR, backup_filename)
        
        from .connection import DATABASE_PATH
        shutil.copy(DATABASE_PATH, save_path)
        logging.info(f"Otomatik yedekleme başarıyla oluşturuldu: {save_path}")

    except Exception as e:
        logging.error(f"Otomatik yedekleme sırasında kritik bir hata oluştu: {e}", exc_info=True)