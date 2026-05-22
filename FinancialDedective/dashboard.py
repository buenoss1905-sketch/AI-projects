import streamlit as st
import tempfile
import os
import pandas as pd
from logic import run_financial_audit

st.set_page_config(page_title="Finansal Dedektif AI", page_icon="🕵️‍♂️", layout="wide")

# Noir & Glassmorphism Tema Ayarları
st.markdown("""
    <style>
    .stApp { background-color: #0b0c10; color: #c5c6c7; }
    .glass-panel {
        background: rgba(31, 40, 51, 0.4);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(69, 162, 158, 0.2);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .status-normal { color: #66fcf1; font-weight: bold; }
    .status-sus { color: #ff5722; font-weight: bold; text-shadow: 0 0 8px rgba(255,87,34,0.6); }
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️‍♂️ Finansal Dedektif: AI Usulsüzlük Tespiti")
st.caption("Şirket içi masraf fişlerini KVKK uyumlu yerel LLM ile analiz edin.")

# CSV Yükleme Alanı
st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Masraf Dökümünü Yükle (CSV)", type=["csv"])
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file is not None:
    # Kullanıcıya veriyi göster
    st.subheader("📊 Yüklenen Orijinal Veri")
    df_preview = pd.read_csv(uploaded_file)
    st.dataframe(df_preview, width='stretch')
    
    if st.button("🔍 Yapay Zeka Denetimini Başlat"):
        with st.spinner("Llama 3 masrafları inceliyor... Bu işlem veri boyutuna göre sürebilir."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
                
            # Denetimi Başlat
            sonuc_df = run_financial_audit(tmp_path)
            
            st.subheader("🚨 Yapay Zeka Denetim Raporu")
            
            # Sonuçları ekrana basma (Şüpheli olanları kırmızı göster)
            for index, row in sonuc_df.iterrows():
                if row['AI_Durum'] == "ŞÜPHELİ":
                    st.markdown(f"""
                    <div class="glass-panel" style="border-left: 5px solid #ff5722;">
                        <h4>Çalışan: {row['Calisan']} | Tutar: {row['Tutar_TL']} TL <span class="status-sus">[ŞÜPHELİ]</span></h4>
                        <p><b>Harcama:</b> {row['Aciklama']} ({row['Tarih']})</p>
                        <p><b>🤖 AI Tespit Nedeni:</b> {row['AI_Neden']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="glass-panel" style="border-left: 5px solid #66fcf1;">
                        <h4>Çalışan: {row['Calisan']} | Tutar: {row['Tutar_TL']} TL <span class="status-normal">[NORMAL]</span></h4>
                        <p><b>Harcama:</b> {row['Aciklama']}</p>
                        <p><b>🤖 AI Onayı:</b> {row['AI_Neden']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
            os.remove(tmp_path)