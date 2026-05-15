import os
import sqlite3
import ollama
from faster_whisper import WhisperModel

# Path configuration for Windows CUDA
os.environ["PATH"] += os.pathsep + r'C:\Users\hasan\AppData\Local\Programs\Python\Python310\Lib\site-packages\nvidia\cublas\bin'
os.environ["PATH"] += os.pathsep + r'C:\Users\hasan\AppData\Local\Programs\Python\Python310\Lib\site-packages\nvidia\cudnn\bin'

def process_interview(audio_path):
    """Transcribes audio, analyzes via Local LLM, and saves to DB."""
    
    # 1. WHISPER: Transcription
    print("--- STEP 1: Speech Recognition (RTX 5060) ---")
    model = WhisperModel("large-v3", device="cuda", compute_type="float16")
    segments, _ = model.transcribe(audio_path)
    transcript_text = " ".join([s.text for s in segments])

    # 2. OLLAMA: Name Extraction
    name_query = f"""
    Analyze the following transcript and find the full name of the interviewee (the client). 
    If no name is explicitly mentioned, return 'Unknown Client'.
    Return ONLY the name, no extra text.
    Transcript start: {transcript_text[:1000]}
    """
    name_res = ollama.generate(model='llama3.1:latest', prompt=name_query)
    extracted_name = name_res['response'].strip()

    # 3. OLLAMA: Detailed Profile Analysis
    analysis_prompt = f"""
    You are a Belgian Real Estate Expert. Extract a detailed Investor Profile from the transcript below.
    Please fill out the following fields in English:
    - Budget:
    - Preferred Region:
    - Property Type:
    - Investment Goal (Rental Yield / Capital Appreciation):
    - No-Go's (Deal breakers):
    - Summary of the conversation:
    
    TRANSCRIPT: {transcript_text}
    """
    analysis_res = ollama.generate(model='llama3.1:latest', prompt=analysis_prompt)
    analysis_result = analysis_res['response']

    # 4. DATABASE: Save
    save_to_db(extracted_name, analysis_result, transcript_text)
    return extracted_name, analysis_result

def save_to_db(name, analysis, transcript):
    conn = sqlite3.connect('realestate_ai.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO profiles (name, category, ai_analysis, raw_transcript)
        VALUES (?, ?, ?, ?)
    ''', (name, "Investor", analysis, transcript))
    conn.commit()
    conn.close()
    print(f"✅ Profile for {name} saved to local database!")