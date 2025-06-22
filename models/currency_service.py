# dosya: models/currency_service.py

import requests
import xml.etree.ElementTree as ET
import logging
from typing import Dict, Optional

TCMB_URL = "https://www.tcmb.gov.tr/kurlar/today.xml"

def get_all_rates() -> Optional[Dict[str, float]]:
    try:
        response = requests.get(TCMB_URL, timeout=10)
        response.raise_for_status() 
        
        root = ET.fromstring(response.content)
        
        rates = {}
        
        usd_node = root.find("./Currency[@Kod='USD']/ForexSelling")
        if usd_node is not None and usd_node.text:
            rates['USD'] = float(usd_node.text)

        eur_node = root.find("./Currency[@Kod='EUR']/ForexSelling")
        if eur_node is not None and eur_node.text:
            rates['EUR'] = float(eur_node.text)

        if not rates:
            logging.warning("XML içinde USD veya EUR kuru bulunamadı.")
            return None
            
        logging.info(f"Kurlar başarıyla çekildi: {rates}")
        return rates

    except requests.exceptions.Timeout:
        logging.error("Kur bilgisi çekilemedi: İstek zaman aşımına uğradı.")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Kur bilgisi çekilemedi. Ağ hatası: {e}")
        return None
    except Exception as e:
        logging.error(f"Kur bilgisi alınırken beklenmedik bir hata oluştu: {e}")
        return None