import pandas as pd
import json
import os

def load_skills(filepath='financial_skills.json'):
    """Şirket politikalarını yükler."""
    if not os.path.exists(filepath):
        print("HATA: JSON kural dosyası bulunamadı!")
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_financial_audit(csv_path):
    """Gelişmiş JSON kural dosyasına (Skill) bağlı denetim motoru."""
    df = pd.read_csv(csv_path)
    df['Tarih'] = pd.to_datetime(df['Tarih'])
    df['Saat'] = df['Tarih'].dt.hour
    df['Gun'] = df['Tarih'].dt.weekday # 5: Cumartesi, 6: Pazar
    
    # 1. Kural Dosyasını (Skills) Sisteme Çek
    skills = load_skills()
    politika = skills["sirket_politikalari"]
    
    # --- KURALLARI UYGULAMA ---
    gece_islemi = (df['Saat'] >= politika["yasakli_saatler"]["baslangic"]) | (df['Saat'] <= politika["yasakli_saatler"]["bitis"])
    haftasonu_islemi = (df['Gun'] >= 5) if politika["haftasonu_yasagi"] else False
    
    kara_liste_regex = '|'.join(politika["kara_liste_kelimeler"])
    # Aciklama boş (NaN) ise hata vermemesi için na=False kullanıyoruz
    yasakli_kelime = df['Aciklama'].str.lower().str.contains(kara_liste_regex, na=False)
    
    kisa_aciklama = df['Aciklama'].str.len() < politika["zorunlu_aciklama_uzunlugu"]
    
    # İŞTE HATANIN ÇÖZÜLDÜĞÜ YER: Yeni isme (genel_onay_limiti_tl) göre arama yapıyor
    asiri_tutar = df['Tutar_TL'] > politika["genel_onay_limiti_tl"]
    
    # --- SONUÇLARI HESAPLAMA ---
    sonuclar = []
    for index, row in df.iterrows():
        nedenler = []
        
        # 1. Kara Liste Kontrolü
        if yasakli_kelime[index]:
            nedenler.append("Kara liste kelime ihlali.")
            
        # 2. Zaman Kontrolleri
        if gece_islemi[index]:
            nedenler.append(f"İşlem mesai saatleri dışında (Saat {row['Saat']}:00).")
        if haftasonu_islemi[index]:
            nedenler.append("Hafta sonu şirket harcaması yapılamaz.")
            
        # 3. Kategori Limiti Kontrolü
        kategori = row['Kategori']
        kat_limit = politika["kategori_limitleri_tl"].get(kategori, politika["genel_onay_limiti_tl"])
        if row['Tutar_TL'] > kat_limit:
            nedenler.append(f"Kategori limiti aşıldı ({kategori} için max {kat_limit} TL).")
            
        # 4. Genel Limit Kontrolü
        elif asiri_tutar[index]:
            nedenler.append(f"Genel limit aşımı (>{politika['genel_onay_limiti_tl']} TL).")
            
        # 5. Açıklama Kalitesi
        if kisa_aciklama[index]:
            nedenler.append("Açıklama çok yetersiz, detay girilmemiş.")
            
        satir_sonucu = row.to_dict()
        
        if nedenler:
            satir_sonucu['AI_Durum'] = 'ŞÜPHELİ'
            satir_sonucu['AI_Neden'] = " | ".join(nedenler)
        else:
            satir_sonucu['AI_Durum'] = 'NORMAL'
            satir_sonucu['AI_Neden'] = 'Harcama şirket politikalarına ve limitlere tam uygundur.'
            
        sonuclar.append(satir_sonucu)
        
    return pd.DataFrame(sonuclar)