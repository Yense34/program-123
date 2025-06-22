# dosya: models/sms_service.py

import requests
import logging
import re
from typing import Tuple, Dict, Any, List, Optional
import xml.etree.ElementTree as ET

API_SEND_URL = "https://smsgw.mutlucell.com/smsgw-ws/sndblkex"
API_CREDIT_URL = "https://smsgw.mutlucell.com/smsgw-ws/gtcrdtex"

MUTLUCELL_ERROR_CODES = {
    '20': "Post edilen xml eksik veya hatalı.", '21': "Kullanılan originatör (gönderici başlığı) hatalı.",
    '22': "Telefon numarası hatalı.", '23': "Kullanıcı adı veya şifre hatalı.",
    '24': "Şifre veya parola süresi dolmuş.", '25': "SOAP/XML hatası.",
    '30': "Kontör/kredi yetersiz.", '40': "Bilinmeyen bir hata oluştu.",
    '50': "İleri tarihli mesaj gönderimlerinde tarih formatı hatalı.",
    '51': "Tekrarlanan numaralar mevcut.", '60': "Hesap pasif durumda.",
    '70': "IP kısıtlaması.",
}

def _get_api_credentials(api_settings: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    username = api_settings.get('sms_username')
    password = api_settings.get('sms_password')
    if not all([username, password]):
        logging.warning("SMS işlemi yapılamadı: API kullanıcı adı veya şifre eksik.")
        return None, None
    return username, password

def get_credit_info(api_settings: Dict[str, Any]) -> Optional[str]:
    username, password = _get_api_credentials(api_settings)
    if not username:
        return None

    root = ET.Element("smskredi", attrib={"ka": username, "pwd": password})
    xml_payload = ET.tostring(root, encoding="unicode")
    headers = {"Content-Type": "text/xml; charset=UTF-8"}

    try:
        response = requests.post(API_CREDIT_URL, data=xml_payload.encode("utf-8"), headers=headers, timeout=10)
        response.raise_for_status()
        response_text = response.text.strip()

        if response_text.startswith('$'):
            credit = response_text.lstrip('$')
            logging.info(f"Kredi başarıyla sorgulandı: {credit}")
            return credit
        else:
            error_description = MUTLUCELL_ERROR_CODES.get(response_text, "Bilinmeyen Hata")
            logging.error(f"Kredi sorgulama hatası: {error_description} (Kod: {response_text})")
            return None
    except Exception as e:
        logging.error(f"Kredi sorgulanırken beklenmedik bir hata oluştu: {e}", exc_info=True)
        return None

def _clean_phone_number(phone: str) -> Optional[str]:
    if not isinstance(phone, str): return None
    cleaned_phone = re.sub(r'\D', '', phone)
    
    if len(cleaned_phone) == 12 and cleaned_phone.startswith('90'): return cleaned_phone
    if len(cleaned_phone) == 11 and cleaned_phone.startswith('0'): return '90' + cleaned_phone[1:]
    if len(cleaned_phone) == 10: return '90' + cleaned_phone
        
    logging.warning(f"Geçersiz telefon numarası formatı atlandı: {phone}")
    return None

def send_bulk_sms(api_settings: Dict[str, Any], phone_numbers: List[str], message: str) -> Tuple[bool, str]:
    username, password = _get_api_credentials(api_settings)
    originator = api_settings.get('sms_originator')
    if not all([username, password, originator, phone_numbers, message]):
        return False, "SMS gönderilemedi: API ayarları, alıcı listesi veya mesaj içeriği eksik."

    valid_numbers = [p for p in (_clean_phone_number(phone) for phone in phone_numbers) if p]
    if not valid_numbers:
        return False, "Listede gönderilebilecek geçerli formatta telefon numarası bulunamadı."
        
    root = ET.Element("smspack", attrib={"ka": username, "pwd": password, "org": originator, "charset": "turkish"})
    msg_element = ET.SubElement(root, "mesaj")
    ET.SubElement(msg_element, "metin").text = message
    ET.SubElement(msg_element, "nums").text = ",".join(valid_numbers)
    xml_payload = ET.tostring(root, encoding="unicode")
    headers = {"Content-Type": "text/xml; charset=UTF-8"}

    try:
        response = requests.post(API_SEND_URL, data=xml_payload.encode("utf-8"), headers=headers, timeout=20)
        response.raise_for_status() 
        response_text = response.text.strip()
        
        if response_text.startswith('$'):
            success_msg = f"Toplam {len(valid_numbers)} adet SMS gönderim talebi başarıyla işleme alındı."
            logging.info(f"İşlem başarılı. Sunucu yanıtı: {response_text}")
            return True, success_msg
        else:
            error_description = MUTLUCELL_ERROR_CODES.get(response_text, "Bilinmeyen Hata")
            error_msg = f"SMS gönderilemedi. Sunucu hatası: {error_description} (Kod: {response_text})"
            logging.error(error_msg)
            return False, error_msg
    except requests.exceptions.Timeout:
        return False, "SMS gönderimi zaman aşımına uğradı. İnternet bağlantınızı kontrol edin."
    except requests.exceptions.RequestException as e:
        return False, f"SMS gönderilirken bir ağ/bağlantı hatası oluştu: {e}"
    except Exception as e:
        logging.error(f"SMS gönderiminde beklenmedik bir hata oluştu: {e}", exc_info=True)
        return False, f"SMS gönderiminde beklenmedik bir hata oluştu: {e}"