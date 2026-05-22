import pdfplumber
import ollama
import json
from database import add_candidate

def read_pdf(file_path):
    """PDF dosyasındaki tüm metni çeker."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

def analyze_cv_with_local_llm(cv_text):
    """Llama 3 ile CV metnini JSON profiline çevirir."""
    prompt = f"""
    Sen uzman bir İnsan Kaynakları asistanısın. Aşağıdaki CV metnini analiz et ve SADECE geçerli bir JSON formatında çıktı ver. Başka bir şey yazma.
    Format:
    {{
        "isim": "Ad Soyad",
        "yetenekler": ["Yetenek1", "Yetenek2"],
        "toplam_tecrube_yili": 0,
        "egitim_seviyesi": "Eğitim"
    }}
    
    CV METNİ:
    {cv_text}
    """
    
    response = ollama.generate(model='llama3.1:latest', prompt=prompt)
    try:
        clean_json = response['response'].replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print("JSON parse hatası:", e)
        return {"isim": "Bilinmiyor", "yetenekler": [], "toplam_tecrube_yili": 0, "egitim_seviyesi": "Hata"}

def process_and_save_cv(file_path):
    """Tüm süreci yönetir: Oku -> Analiz Et -> Veritabanına Yaz."""
    cv_metni = read_pdf(file_path)
    cv_data = analyze_cv_with_local_llm(cv_metni)
    
    # Arama için birleştirilmiş düz metin (Vektör)
    arama_metni = f"Yetenekler: {', '.join(cv_data.get('yetenekler', []))}. Tecrübe: {cv_data.get('toplam_tecrube_yili', 0)} yıl. Eğitim: {cv_data.get('egitim_seviyesi', '')}."
    
    # database.py içindeki kayıt fonksiyonunu çağır
    raw_json_str = json.dumps(cv_data)
    add_candidate(cv_data.get("isim", "Bilinmiyor"), arama_metni, file_path, raw_json_str)
    
    return cv_data