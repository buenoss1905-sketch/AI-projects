import pandas as pd
import re
import ollama

def rule_based_threat_scan(log_path):
    """Pandas ve Regex ile ışık hızında kapsamlı tehdit taraması yapar."""
    # Log dosyasını | ayırıcısı ile okuyoruz
    df = pd.read_csv(log_path, sep='|', names=['Tarih', 'Servis', 'IP', 'Mesaj'])
    
    # --- SİBER TEHDİT KURALLARI (REGEX) ---
    sqli_pattern = r"(?i)(\b(union|select|insert|drop|update)\b|' OR '1'='1|--)"
    xss_pattern = r"(?i)(<script>|javascript:|onerror=)"
    path_traversal_pattern = r"(?i)(\.\./\.\./|/etc/passwd|/bin/sh|cmd\.exe)"
    ssh_bruteforce_pattern = r"(?i)(failed password|invalid user)"
    
    sonuclar = []
    
    for index, row in df.iterrows():
        mesaj = str(row['Mesaj'])
        tehdit_turu = []
        
        # Kuralları test et
        if re.search(sqli_pattern, mesaj):
            tehdit_turu.append("SQL Injection")
        if re.search(xss_pattern, mesaj):
            tehdit_turu.append("Cross-Site Scripting (XSS)")
        if re.search(path_traversal_pattern, mesaj):
            tehdit_turu.append("Directory Traversal")
        if row['Servis'] == 'SSH' and re.search(ssh_bruteforce_pattern, mesaj):
            tehdit_turu.append("SSH Brute Force Denemesi")
            
        satir = row.to_dict()
        if tehdit_turu:
            satir['Durum'] = 'KIRMIZI ALARM'
            satir['Tehdit'] = " + ".join(tehdit_turu)
        else:
            satir['Durum'] = 'TEMİZ'
            satir['Tehdit'] = 'Zararlı aktivite bulunamadı'
            
        sonuclar.append(satir)
        
    return pd.DataFrame(sonuclar)

def deep_analyze_with_llm(log_row):
    """Llama 3'ü bir Siber Güvenlik (SOC) Analisti olarak kullanarak logu detaylı inceler."""
    prompt = f"""
    Sen kıdemli bir Siber Güvenlik Analistisin (SOC L3). Aşağıdaki sunucu logunda şüpheli bir aktivite tespit edildi. 
    Lütfen saldırganın ne yapmaya çalıştığını ve sistem yöneticisinin hangi önlemi alması gerektiğini KISA ve NET bir şekilde, Türkçe açıkla.
    
    [LOG DETAYI]
    Tarih: {log_row['Tarih']}
    Servis: {log_row['Servis']}
    IP Adresi: {log_row['IP']}
    Tespit Edilen Tehdit: {log_row['Tehdit']}
    Log Mesajı: {log_row['Mesaj']}
    """
    try:
        response = ollama.generate(model='llama3.1:latest', prompt=prompt)
        return response['response'].strip()
    except Exception as e:
        return f"AI Analiz Hatası: {e}"