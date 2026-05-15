import streamlit as st
import sqlite3
import pandas as pd
import os
import ollama
from logic import process_interview

st.set_page_config(
    page_title="RealEstate AI | Investor Matching",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    div.stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #007bff; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def get_stats():
    conn = sqlite3.connect('realestate_ai.db')
    count = pd.read_sql_query("SELECT COUNT(*) as total FROM profiles", conn).iloc[0]['total']
    conn.close()
    return count

def get_all_profiles():
    conn = sqlite3.connect('realestate_ai.db')
    df = pd.read_sql_query("SELECT id, name, category, created_at FROM profiles ORDER BY created_at DESC", conn)
    conn.close()
    return df

# --- SIDEBAR (CONTROL CENTER) ---
with st.sidebar:
    st.title("🎙️ Control Center")
    uploaded_files = st.file_uploader("Upload Interviews (Bulk Support)", 
                                      type=["mp3", "wav"], 
                                      accept_multiple_files=True)
    
    if uploaded_files:
        st.info(f"{len(uploaded_files)} files selected.")
        if st.button("🚀 Run AI Batch Analysis"):
            for uploaded_file in uploaded_files:
                with st.status(f"Processing: {uploaded_file.name}", expanded=False) as status:
                    with open("temp_audio.mp3", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    try:
                        name, analysis = process_interview("temp_audio.mp3")
                        st.write(f"✅ {name} processed.")
                        status.update(label=f"Done: {uploaded_file.name}", state="complete")
                    except Exception as e:
                        st.error(f"Error ({uploaded_file.name}): {e}")
            st.success("All profiles processed and saved!")
            st.rerun()

# --- MAIN PANEL ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🇧🇪 RealEstate AI: Investor Dashboard")
    st.caption("Local AI-driven matching and analysis tool for the Belgian market.")

with col2:
    st.metric("Total Profiles", f"{get_stats()}")

st.divider()

try:
    profiles_df = get_all_profiles()
    st.subheader("👥 Investor Database")
    st.dataframe(profiles_df, width=1200)

    st.markdown("### 🔍 Analysis & Matching")
    selected_name = st.selectbox("Select an investor to review:", profiles_df['name'])

    if selected_name:
        conn = sqlite3.connect('realestate_ai.db')
        cur = conn.cursor()
        cur.execute("SELECT name, ai_analysis, raw_transcript FROM profiles WHERE name=?", (selected_name,))
        profile = cur.fetchone()
        conn.close()
        
        t1, t2, t3 = st.tabs(["📊 AI Analysis", "📑 Transcript", "🎯 Property Matching"])
        
        with t1:
            st.markdown(f"#### {profile[0]} Profile Report")
            st.markdown(profile[1])
            
        with t2:
            st.text_area("Full Raw Transcript", profile[2], height=300, disabled=True)
            
        with t3:
            st.subheader("🎯 Smart Matchmaker")
            prop_desc = st.text_area("Paste New Property Listing Details:", 
                                    placeholder="E.g., Apartment in Brussels, €300k, EPC B...")
            
            if st.button("⚖️ Run Matching Analysis"):
                if prop_desc:
                    with st.spinner("Llama 3.1 is analyzing match compatibility..."):
                        match_prompt = f"""
                        You are an expert Belgian Real Estate Advisor. Conduct a rational match analysis.
                        INVESTOR PROFILE: {profile[1]}
                        NEW PROPERTY LISTING: {prop_desc}

                        Please provide a score out of 10 for:
                        1. Budget Fit: (Score must be 10/10 if price is under budget).
                        2. Region Fit: (Does the city/neighborhood match?).
                        3. Strategy Fit: (Renovation, Airbnb, long-term goals?).
                        4. No-Go Check: (Break the score if a deal-breaker exists).

                        Ensure analysis respects Belgian market realities (EPC, local taxes).
                        """
                        res = ollama.generate(model='llama3.1:latest', prompt=match_prompt)
                        st.markdown("---")
                        st.write(res['response'])
except Exception as e:
    st.warning("Database empty. Please upload audio files to start.")