```markdown
# 🛡️ Unified SOC Threat Analyzer (Hybrid Rule + AI)

**Offline Cyber Security Log Analyzer with Llama 3 Integration**

Sunucu (Web/SSH vb.) loglarını tamamen kapalı ağda (offline) inceleyerek siber saldırıları tespit eden hibrit bir Güvenlik Operasyon Merkezi (SOC) analizörüdür. İmza tabanlı saldırıları Regex ile anında yakalarken, karmaşık tehditler için yerel Llama 3 modelini bir siber güvenlik analisti gibi kullanır.

## 🚀 Temel Özellikler
* **Çift Katmanlı Mimari (Hybrid Engine):** * *1. Katman (Pandas & Regex):* Brute Force, SQL Injection, XSS, Directory Traversal gibi bilinen saldırıları anında etiketler.
  * *2. Katman (LLM Deep Analysis):* Şüpheli bulunan logları Ollama (Llama 3) modeline göndererek, saldırganın motivasyonunu ve alınması gereken aksiyonları raporlar.
* **Hava Boşluklu (Air-Gapped) Uyumluluk:** Hassas sunucu logları internete çıkarılmaz, %100 yerel donanımda analiz edilir.
* **SOC / Hacker Arayüzü:** Kırmızı alarmların ve log detaylarının rahatça okunabildiği, siber güvenlik temasına uygun (Cyber/Noir) gelişmiş bir UI.

## 🛠️ Teknoloji Yığını (Tech Stack)
* **Python 3.10+**
* **Ollama (Llama 3.1):** Yerel Büyük Dil Modeli (LLM)
* **Pandas & RegEx:** Log ayrıştırma ve imza tabanlı (Signature-based) tespit
* **Streamlit:** Frontend ve Dashboard

## 💻 Kurulum ve Çalıştırma
1. [Ollama](https://ollama.com) uygulamasını bilgisayarınıza kurun ve Llama 3.1 modelini indirin:
   ```bash
   ollama run llama3.1
Gerekli Python kütüphanelerini kurun:

Bash
pip install pandas streamlit ollama
Güvenlik merkezini ayağa kaldırın:

Bash
streamlit run cyber_dashboard.py
