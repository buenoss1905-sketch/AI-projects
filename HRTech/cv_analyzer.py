import pdfplumber
import ollama
import json

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
    """Yerel model (Llama 3 veya Phi-3) ile CV'den yapılandırılmış veri çeker."""
    
    prompt = f"""
    Sen uzman bir İnsan Kaynakları asistanısın. Aşağıdaki CV metnini analiz et ve SADECE geçerli bir JSON formatında çıktı ver.
    Başka hiçbir açıklama yazma.
    
    İstenen JSON Formatı:
    {{
        "isim": "Adayın Adı Soyadı",
        "yetenekler": ["Python", "React Native", "İngilizce"],
        "toplam_tecrube_yili": 3,
        "egitim_seviyesi": "Lisans - Bilgisayar Mühendisliği"
    }}
    
    CV METNİ:
    {cv_text}
    """
    
    # Emlak projesindeki gibi model ismini burada değiştirebilirsin (llama3.1 vb.)
    response = ollama.generate(model='llama3.1:latest', prompt=prompt)
    
    # Modelin verdiği metni JSON objesine çeviriyoruz
    try:
        # LLM bazen JSON'ın başına sonuna markdown (```json ... ```) ekler, onu temizliyoruz
        raw_output = response['response']
        clean_json = raw_output.replace('```json', '').replace('```', '').strip()
        cv_data = json.loads(clean_json)
        return cv_data
    except Exception as e:
        print("JSON parse hatası:", e)
        return {"hata": "Model JSON formatını bozdu", "ham_cikti": response['response']}

# --- TEST KISMI ---
if __name__ == "__main__":
    # Test etmek için klasörüne bir tane 'ornek_cv.pdf' koymalısın
    pdf_yolu = "ornek_cv.pdf"
    
    print("📄 PDF okunuyor...")
    cv_metni = read_pdf(pdf_yolu)
    
    print("🧠 Yerel AI CV'yi analiz ediyor...")
    analiz_sonucu = analyze_cv_with_local_llm(cv_metni)
    
    print("\n✅ Çıkarılan Profil:")
    print(json.dumps(analiz_sonucu, indent=4, ensure_ascii=False))