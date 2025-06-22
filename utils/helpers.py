# dosya: utils/helpers.py

import re

def sanitize_filename(name: str) -> str:
    if not name or not isinstance(name, str):
        return "isimsiz_kayit"
    
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = name.replace(" ", "_")
    
    sanitized_name = name[:60]
    
    if not sanitized_name.strip("_"):
        return "isimsiz_kayit"
        
    return sanitized_name