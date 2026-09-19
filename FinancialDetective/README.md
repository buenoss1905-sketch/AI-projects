```markdown
# 💸 Enterprise Financial Fraud Detective

**High-Speed, Rule-Based Financial Anomaly & Expense Audit Engine**

Şirket içi masraf fişlerini ve finansal hareketleri saniyeler içinde denetleyen, usulsüzlükleri (fraud) yakalayan gelişmiş bir kural motorudur. LLM'lerin yavaşlığı ve halüsinasyon riskini ortadan kaldırmak için, gücünü veri bilimi kütüphanesi Pandas'tan ve dinamik JSON yapılandırmasından alır.

## 🚀 Temel Özellikler
* **Işık Hızında Analiz:** Pandas kural motoru sayesinde on binlerce satırlık CSV/Excel masraf dökümünü 1 saniyenin altında denetler.
* **Dinamik Yetenek (Skill) Sistemi:** Koda dokunmadan, sadece `financial_skills.json` dosyasını düzenleyerek şirket limitlerini, hafta sonu yasaklarını ve kara liste kelimelerini güncelleyebilme.
* **Kategori Bazlı Limitler:** Uçak bileti, yemek veya ofis malzemesi gibi her kategori için ayrı onay limitleri tanımlama.
* **Davranışsal ve Zaman Bazlı Denetim:** Mesai saatleri dışı (gece) ve hafta sonu yapılan şüpheli işlemleri otomatik yakalama.

## 🛠️ Teknoloji Yığını (Tech Stack)
* **Python 3.10+**
* **Pandas:** Vektörel veri manipülasyonu ve yüksek hızlı kural motoru
* **JSON:** Dinamik yapılandırma (Configuration/Skill) yönetimi
* **Streamlit:** Noir estetiğine sahip kurumsal raporlama arayüzü

## 💻 Kurulum ve Çalıştırma
1. Repoyu klonlayın ve gereksinimleri kurun:
   ```bash
   pip install pandas streamlit
  Sistemi başlatın (Sistem, financial_skills.json dosyasını otomatik üretecektir):

  ```bash
  streamlit run finance_dashboard.py

---
