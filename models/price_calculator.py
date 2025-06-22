# dosya: models/price_calculator.py

from database import database_manager as db

def calculate_prices(product_data: dict, settings: dict) -> dict:
    if not product_data:
        return {}
        
    try:
        purchase_price = float(str(product_data.get('alis_fiyati', 0)).replace(',', '.'))
        currency = product_data.get('alis_para_birimi', 'TL')

        purchase_price_tl = purchase_price
        if currency != 'TL':
            rate_str = (settings.get(f"{currency.lower()}_tl_kuru") or '0').replace(',', '.')
            rate = float(rate_str)
            if rate > 0:
                purchase_price_tl *= rate
            else:
                purchase_price_tl = 0
    except (ValueError, TypeError):
        return {}

    kar_yontemi = settings.get('kar_yontemi', 'Yüzdesel Kâr (%)')
    kar_degeri_str = (settings.get('kar_degeri') or '50.0').replace(',', '.')
    kar_degeri = float(kar_degeri_str)
    
    if category_id := product_data.get('kategori_id'):
        category_details = db.get_category_details(category_id)
        
        if category_details and category_details['kar_tipi'] is not None and category_details['kar_degeri'] is not None:
            kar_yontemi = category_details['kar_tipi']
            kar_degeri = category_details['kar_degeri']

    vat_percent_str = (settings.get('kdv_orani') or '20.0').replace(',', '.')
    vat_percent = float(vat_percent_str)
    
    if tax_id := product_data.get('vergi_id'):
        if tax_rate_row := db.get_vergi_orani_by_id(tax_id):
            vat_percent = tax_rate_row['oran']

    cc_commission_str = (settings.get('kk_komisyonu') or '2.5').replace(',', '.')
    cc_commission_percent = float(cc_commission_str)

    profit_amount = 0.0
    if kar_yontemi == 'Yüzdesel Kâr (%)':
        profit_amount = purchase_price_tl * (kar_degeri / 100)
    elif kar_yontemi == 'Sabit Tutar (TL)':
        profit_amount = kar_degeri
    
    price_with_profit_no_vat = purchase_price_tl + profit_amount
    price_with_vat = price_with_profit_no_vat * (1 + vat_percent / 100)
    
    price_with_cc_commission = price_with_profit_no_vat * (1 + cc_commission_percent / 100)
    price_with_cc = price_with_cc_commission * (1 + vat_percent / 100)

    return {
        "karli_fiyat_kdv_haric": round(price_with_profit_no_vat, 2),
        "kdvli_fiyat": round(price_with_vat, 2),
        "kkli_fiyat": round(price_with_cc, 2)
    }