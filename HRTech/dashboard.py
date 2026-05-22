import streamlit as st
import os
import tempfile
import json
from logic import process_and_save_cv
from database import search_candidates

# --- SAYFA AYARLARI VE NOIR/GLASSMORPHISM TEMA ---
st.set_page_config(page_title="AI HR Asistanı", page_icon="🕵️", layout="wide")

st.markdown("""
    <style>
    /* Karanlık arka plan */
    .stApp { background-color: #0f1115; color: #e2e8f0; }
    
    /* Cam efektli paneller (Glassmorphism) */
    .glass-panel {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Neon mavisi butonlar */
    .stButton>button {
        background-color: transparent;
        color: #38bdf8;
        border: 1px solid #38bdf8;
        border-radius: 6px;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #38bdf8;
        color: #0f1115;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# Ana Başlık
st.title("🕵️ Çevrimdışı İK Asistanı (Privacy-First)")
st.caption("KVKK/GDPR uyumlu, %100 yerel çalışan özgeçmiş analizi ve eşleştirme sistemi.")

# --- İKİ SÜTUNLU TASARIM ---
col1, col2 = st.columns([1, 1.5])

# SOL SÜTUN: Toplu CV Yükleme Alanı
with col1:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.subheader("📁 Toplu CV Yükle (PDF)")
    
    # accept_multiple_files=True ile çoklu seçim aktif edildi
    uploaded_files = st.file_uploader("Adayların özgeçmişlerini yükleyin", type=["pdf"], accept_multiple_files=True)
    
    if uploaded_files:
        st.info(f"📂 {len(uploaded_files)} adet CV seçildi.")
        
        if st.button("🚀 Tüm CV'leri Analiz Et ve Kaydet"):
            # İşlem çubuğu (Progress bar) ve durum metni
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            basarili_kayit = 0
            
            # Seçilen tüm dosyalar üzerinde döngü
            for i, uploaded_file in enumerate(uploaded_files):
                # Ekranda hangi dosyanın işlendiğini göster
                status_text.text(f"İşleniyor: {uploaded_file.name} ({i+1}/{len(uploaded_files)})")
                
                try:
                    # Gelen dosyayı geçici olarak sisteme kaydetme
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_path = tmp_file.name
                    
                    # logic.py'deki AI motorunu çalıştırma
                    analiz_sonucu = process_and_save_cv(temp_path)
                    basarili_kayit += 1
                    
                    # Temizlik
                    os.remove(temp_path)
                except Exception as e:
                    st.error(f"Hata ({uploaded_file.name}): {e}")
                
                # İlerleme çubuğunu güncelle
                progress_bar.progress((i + 1) / len(uploaded_files))
                
            status_text.text("Bütün işlemler tamamlandı!")
            st.success(f"✅ {basarili_kayit} adet profil veritabanına işlendi!")
            
    st.markdown('</div>', unsafe_allow_html=True)

# SAĞ SÜTUN: Akıllı Eşleştirme Sistemi
with col2:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.subheader("🎯 Akıllı Aday Eşleştirme")
    job_desc = st.text_area("İlan Açıklaması veya Aranan Yetenekler:", 
                            placeholder="Örn: 3 yıl tecrübeli, React Native bilen mobil geliştirici...")
    
    if st.button("🔍 En Uygun Adayları Bul"):
        if job_desc:
            with st.spinner("Vektör veritabanı taranıyor..."):
                # database.py üzerinden arama yapma
                sonuclar = search_candidates(job_desc, top_k=3)
                
                if not sonuclar['ids'][0]:
                    st.warning("Veritabanında uygun aday bulunamadı.")
                else:
                    st.markdown("### 🏆 Eşleşen Adaylar")
                    for i in range(len(sonuclar['ids'][0])):
                        isim = sonuclar['metadatas'][0][i]['isim']
                        ozellikler = sonuclar['documents'][0][i]
                        mesafe = sonuclar['distances'][0][i] # Düşük = İyi Eşleşme
                        
                        st.info(f"**{i+1}. Aday:** {isim} (Skor: {mesafe:.2f})\n\n**Profil:** {ozellikler}")
    st.markdown('</div>', unsafe_allow_html=True)