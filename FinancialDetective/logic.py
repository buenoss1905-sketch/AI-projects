import pandas as pd
import json
import os
import re

def load_skills(filepath=None):
    """Şirket politikalarını yükler."""
    if filepath is None:
        # Script'in bulunduğu dizine göre relative path
        filepath = os.path.join(os.path.dirname(__file__), 'financial_skills.json')

    if not os.path.exists(filepath):
        print("HATA: JSON kural dosyası bulunamadı!")
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"HATA: JSON dosyası okunurken hata: {e}")
        return None
    except Exception as e:
        print(f"HATA: Dosya okunurken hata: {e}")
        return None

def run_financial_audit(csv_path, skills_path=None):
    """Gelişmiş JSON kural dosyasına (Skill) bağlı denetim motoru."""
    # 1. Kural Dosyasını (Skills) Sisteme Çek
    skills = load_skills(skills_path)
    if skills is None:
        raise ValueError("Kural dosyası yüklenemedi!")

    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV dosyası bulunamadı: {csv_path}")
    except Exception as e:
        raise ValueError(f"CSV dosyası okunurken hata: {e}")

    # Gerekli sütunları kontrol et
    required_columns = ['Tarih', 'Aciklama', 'Kategori', 'Tutar_TL']
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Eksik sütunlar: {missing}")

    df['Tarih'] = pd.to_datetime(df['Tarih'])
    df['Saat'] = df['Tarih'].dt.hour
    df['Gun'] = df['Tarih'].dt.weekday # 5: Cumartesi, 6: Pazar

    politika = skills["sirket_politikalari"]

    # --- KURALLARI UYGULAMA ---
    gece_islemi = (df['Saat'] >= politika["yasakli_saatler"]["baslangic"]) | (df['Saat'] <= politika["yasakli_saatler"]["bitis"])

    # Hafta sonu kontrolü - Series cinsine dönüştür
    if politika["haftasonu_yasagi"]:
        haftasonu_islemi = df['Gun'] >= 5
    else:
        haftasonu_islemi = pd.Series([False] * len(df), index=df.index)

    # Kara liste kontrolü - regex escape ve boş liste kontrolü
    kara_liste = politika["kara_liste_kelimeler"]
    if kara_liste and len(kara_liste) > 0:
        # Özel karakterleri escape et
        escaped_words = [re.escape(word) for word in kara_liste]
        kara_liste_regex = '|'.join(escaped_words)
        yasakli_kelime = df['Aciklama'].fillna("").str.lower().str.contains(kara_liste_regex, na=False, regex=True)
    else:
        yasakli_kelime = pd.Series([False] * len(df), index=df.index)

    # Açıklama kontrolü - NaN için fillna("")
    kisa_aciklama = df['Aciklama'].fillna("").str.len() < politika["zorunlu_aciklama_uzunlugu"]
    
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
        if kategori in politika["kategori_limitleri_tl"]:
            kat_limit = politika["kategori_limitleri_tl"][kategori]
            if row['Tutar_TL'] > kat_limit:
                nedenler.append(f"Kategori limiti aşıldı ({kategori} için max {kat_limit} TL).")

            # 4. Genel Limit Kontrolü
            elif asiri_tutar[index]:
                nedenler.append(f"Genel limit aşımı (>{politika['genel_onay_limiti_tl']} TL).")
        else:
            # Bilinmeyen kategori - sadece genel limiti kontrol et
            if asiri_tutar[index]:
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