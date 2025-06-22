# dosya: models/email_service.py

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple, Dict, Any, List

def send_bulk_email(smtp_settings: Dict[str, Any], recipients: List[str], subject: str, body: str) -> Tuple[bool, str]:
    host = smtp_settings.get('smtp_host')
    port_str = smtp_settings.get('smtp_port')
    username = smtp_settings.get('smtp_username')
    password = smtp_settings.get('smtp_password')

    if not all([host, port_str, username, password]):
        error_msg = "E-posta gönderilemedi: Lütfen ayarlardan SMTP bilgilerini eksiksiz doldurun."
        logging.warning(error_msg)
        return False, error_msg

    if not all([recipients, subject, body]):
        error_msg = "E-posta gönderilemedi: Alıcı, konu veya mesaj içeriği boş olamaz."
        logging.warning(error_msg)
        return False, error_msg

    try:
        port = int(port_str)
        
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls()
            server.login(username, password)
            
            sent_count = 0
            errors = []

            for recipient in recipients:
                if not recipient or '@' not in recipient:
                    errors.append(f"Geçersiz adres: {recipient}")
                    continue

                msg = MIMEMultipart('alternative')
                msg['From'] = username
                msg['To'] = recipient
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'html', 'utf-8'))

                try:
                    server.send_message(msg)
                    sent_count += 1
                except Exception as e:
                    errors.append(f"{recipient}: {str(e)}")

            if sent_count > 0:
                success_msg = f"Toplam {sent_count} alıcıya e-posta başarıyla gönderildi."
                logging.info(f"{len(recipients)} adresten {sent_count} tanesine e-posta gönderildi.")
                if errors:
                    error_details = ", ".join(errors)
                    success_msg += f"\n\nBaşarısız olan {len(errors)} gönderim: {error_details}"
                return True, success_msg
            else:
                error_details = ", ".join(errors)
                error_msg = f"Hiçbir adrese e-posta gönderilemedi. Hatalar: {error_details}"
                logging.error(error_msg)
                return False, error_msg

    except smtplib.SMTPAuthenticationError:
        error_msg = "E-posta gönderilemedi: SMTP kullanıcı adı veya şifre hatalı."
        logging.error(error_msg)
        return False, error_msg
    except (smtplib.SMTPServerDisconnected, ConnectionRefusedError, OSError) as e:
        error_msg = f"E-posta sunucusuna bağlanılamadı: {e}. Host veya Port bilgilerini kontrol edin."
        logging.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"E-posta gönderiminde beklenmedik bir hata oluştu: {e}"
        logging.error(error_msg, exc_info=True)
        return False, error_msg