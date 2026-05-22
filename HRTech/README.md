# 🕵️‍♂️ Offline AI HR Assistant: Semantic CV Matcher

**Privacy-First, Local Vector Search Engine for Enterprise HR**

Bu proje, şirketlerin İnsan Kaynakları departmanları için geliştirilmiş, %100 yerel (çevrimdışı) çalışan ve KVKK/GDPR uyumlu bir özgeçmiş (CV) analiz ve eşleştirme sistemidir. Aday verileri hiçbir bulut servisine gönderilmeden, lokal vektör veritabanı (ChromaDB) üzerinde anlamsal (semantic) olarak taranır.

## 🚀 Temel Özellikler
* **Çok Dilli Anlamsal Arama (Multilingual Semantic Search):** Kelime eşleştirme değil, "anlam" eşleştirme yapar. (Örn: "Oyun Geliştirici" ilanına "Unity ve C#" bilen adayı çıkarır).
* **Toplu İşlem (Batch Processing):** Onlarca PDF formatındaki CV'yi tek tuşla sisteme yükleme ve vektörize etme imkanı.
* **%100 Gizlilik (Offline-First):** `paraphrase-multilingual-MiniLM-L12-v2` modeli kullanılarak tüm veriler sadece kullanıcının bilgisayarında/sunucusunda işlenir.
* **Modern Arayüz (Glassmorphism & Noir):** Streamlit ile tasarlanmış, karanlık temalı, yarı saydam cam panellere sahip, kullanıcı dostu modern B2B arayüz.

## 🛠️ Teknoloji Yığını (Tech Stack)
* **Python 3.10+**
* **ChromaDB:** Gömülü (Embedded) Vektör Veritabanı
* **Sentence-Transformers:** Hugging Face Multilingual Embedding
* **Streamlit:** UI/UX ve Dashboard
* **pdfplumber / PyPDF2:** PDF Metin Ekstraksiyonu

## 💻 Kurulum ve Çalıştırma
1. Repoyu klonlayın ve gerekli kütüphaneleri kurun:
   ```bash
   pip install streamlit chromadb sentence-transformers

2. Uygulamayı başlatın:

Bash
streamlit run dashboard.py

---
