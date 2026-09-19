# AI Projects

Yerel LLM'ler (Ollama / LM Studio), Whisper ve Streamlit ile yapılmış küçük,
bağımsız araçlar. Her klasör kendi başına çalışır; hepsi tamamen çevrimdışı.

| Proje | Ne yapar | Yığın |
|---|---|---|
| [FinancialDedective](FinancialDedective/) | CSV masraf kayıtlarını JSON'da tanımlı şirket politikalarına ("skill") göre denetler, ihlalleri raporlar. 27 birim testi | pandas, Streamlit, pytest |
| [HRTech](HRTech/) | PDF CV'leri yerel Llama 3 ile yapılandırılmış profile çevirir, vektör DB'de arar | pdfplumber, Ollama, ChromaDB, Streamlit |
| [UnifiedThreatAnalyzer](UnifiedThreatAnalyzer/) | Sunucu loglarında regex tabanlı hızlı tarama (SQLi, XSS, path traversal, brute force) + şüpheli satırlar için LLM derin analizi | pandas, Ollama, Streamlit |
| [RealEstateAI](RealEstateAI/) | Yatırımcı görüşme kayıtlarını Whisper ile yazıya döker, LLM ile profil çıkarır, SQLite'a kaydeder | faster-whisper (CUDA), Ollama, Streamlit |
| [AITakipRobotu](AITakipRobotu/) | GitHub / Hugging Face / Civitai / arXiv kaynaklarını tarayıp yerel AI gelişmelerini raporlar; `--analyze` ile LM Studio üzerinden fırsat analizi | requests, LM Studio API |

Daha büyük projeler ayrı repolarda:
[Suru](https://github.com/hasanycee/suru) ·
[etsy-pipelines](https://github.com/hasanycee/etsy-pipelines) ·
[vn-character-pipeline](https://github.com/hasanycee/vn-character-pipeline) ·
[livedub](https://github.com/hasanycee/livedub)
