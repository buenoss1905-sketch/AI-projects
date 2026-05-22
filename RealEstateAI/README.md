# 🏡 AI-Powered Voice Real Estate Matchmaker (Privacy-First)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Whisper](https://img.shields.io/badge/OpenAI-Whisper_(Local)-black.svg)
![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-orange.svg)
![LocalLLM](https://img.shields.io/badge/LLM-Local_Llama_3-brightgreen.svg)

An entirely offline, privacy-first AI system designed for real estate agencies. This tool automates the process of matching client needs with available properties by analyzing raw voice recordings from customer calls, extracting key parameters, and performing semantic search via a vector database—all without sending sensitive data to external APIs.

## 🚀 Business Value & Problem Solved
Real estate agents spend hours listening to client calls and manually filtering databases to find matching properties. Additionally, sharing client voice data with external APIs (like ChatGPT) violates GDPR/KVKK privacy regulations. 
**This system solves both problems by operating 100% locally.**

## 🧠 System Architecture

1. **Voice Input (STT):** Takes raw `.wav` or `.mp3` call recordings.
2. **Local Transcription:** Uses offline `OpenAI Whisper` to convert speech to text securely.
3. **Information Extraction:** A local LLM parses the transcript and extracts structured JSON (Budget, Location, Family Size, Preferences).
4. **Semantic Matching:** `ChromaDB` matches the extracted client vector against the existing real estate inventory.
5. **Output:** Returns the top 3 best-matching properties with reasoning.

## 🛠️ Tech Stack
* **Backend:** Python
* **Speech-to-Text:** Whisper (Offline Base/Tiny models)
* **Vector Database:** ChromaDB
* **Data Processing:** Pandas, NumPy
* **LLM Engine:** Local execution via Ollama

## 📊 Example Workflow

### 1. Extracted Client Profile (JSON)
After processing the voice call, the local model generates a structured profile:
```json
{
  "client_id": "C-8842",
  "budget_max_try": 5000000,
  "room_preference": "3+1",
  "location_preference": ["Kadıköy", "Bostancı"],
  "must_haves": ["Balcony", "Near Subway"],
  "urgency": "High"
}
