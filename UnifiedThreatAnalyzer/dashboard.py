import streamlit as st
import tempfile
import os
import pandas as pd
from cyber_logic import rule_based_threat_scan, deep_analyze_with_llm

st.set_page_config(page_title="Offline SOC Analizörü", page_icon="🛡️", layout="wide")

# Hacker/Noir Tema
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .glass-panel {
        background: rgba(22, 27, 34, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(48, 54, 61, 1);
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .temiz { color: #3fb950; font-weight: bold; }
    .alarm { color: #f85149; font-weight: bold; text-shadow: 0 0 10px rgba(248,81,73,0.5); }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ SOC Kapalı Ağ Tehdit Analizörü")
st.caption("Log kayıtlarını internete çıkarmadan, yerel Pandas kuralları ve Llama 3 ile analiz edin.")

st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Sunucu Log Dosyasını Yükle (.log veya .txt)", type=["log", "txt"])
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file:
    with st.spinner("Loglar taranıyor..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
            
        # Hızlı Pandas taraması
        df_sonuc = rule_based_threat_scan(tmp_path)
        os.remove(tmp_path)
        
    st.subheader("📡 Kural Motoru Tarama Sonuçları")
    
    # Tüm sonuçları özet tablo olarak göster (use_container_width hatasını düzelttik)
    st.dataframe(df_sonuc[['Tarih', 'IP', 'Servis', 'Tehdit', 'Durum']], width='stretch')
    
    st.markdown("---")
    st.subheader("🚨 Tespit Edilen Tehditler (Derin AI Analizi)")
    
    # Sadece KIRMIZI ALARM olanları filtrele
    tehditler = df_sonuc[df_sonuc['Durum'] == 'KIRMIZI ALARM']
    
    if tehditler.empty:
        st.success("Tebrikler! Sistemde hiçbir zararlı aktivite bulunamadı.")
    else:
        # Şüpheli logları kartlar halinde göster
        for index, row in tehditler.iterrows():
            st.markdown(f"""
            <div class="glass-panel" style="border-left: 4px solid #f85149;">
                <h4>[{row['Servis']}] Hedef IP: {row['IP']} <span class="alarm">({row['Tehdit']})</span></h4>
                <code>{row['Mesaj']}</code>
            </div>
            """, unsafe_allow_html=True)
            
            # İstendiğinde AI'ı devreye sokan buton (Sistemi yavaşlatmamak için)
            if st.button(f"🧠 Llama 3 ile İncele (Satır: {index})", key=f"btn_{index}"):
                with st.spinner("Llama 3 hacker'ın niyetini analiz ediyor..."):
                    ai_raporu = deep_analyze_with_llm(row)
                    st.info(f"**🤖 SOC Analisti Llama 3 Diyor ki:**\n\n{ai_raporu}")