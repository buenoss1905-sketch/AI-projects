#!/usr/bin/env python3
"""
Yerel AI Takip Robotu v2
=========================
Lokal LLM'ler, ComfyUI, AI ile 3D model üretimi, oyun geliştirme ve
bilimsel/teknolojik yenilikler (arXiv) alanlarındaki gelişmeleri tarar.

YENİ: --analyze bayrağıyla, ham veriyi bir LLM'e gönderip Etsy/Asset Store/Upwork'te
paraya çevirebileceğin fırsatları ayıklatabilirsin. Varsayılan motor LM Studio
(senin kurulu modelin: qwen2.5-7b-nerd-uncensored-v0.9-mfann, http://127.0.0.1:1234).

Kurulum:
    pip install requests
    # LM Studio'da: modeli yükle (load), Developer sekmesinden 'Start Server' de.

Kullanım:
    python yerel_ai_takip.py                        # ham tarama, tüm kategoriler
    python yerel_ai_takip.py --only llm comfy        # sadece belirli kategoriler
    python yerel_ai_takip.py --analyze               # LM Studio ile analiz (varsayılan)
    python yerel_ai_takip.py --analyze --save        # analiz edip markdown'a kaydet

Claude API key ayarlamak istersen (opsiyonel, sadece --engine claude için):
    export ANTHROPIC_API_KEY="sk-ant-..."            # Mac/Linux
    setx ANTHROPIC_API_KEY "sk-ant-..."               # Windows

YENİ KAYNAK EKLEMEK İÇİN:
    Aşağıdaki SOURCES sözlüğüne, uygun 'type' ile yeni bir satır eklemen yeterli.
    Kod yazmana gerek yok. Desteklenen tipler: github_releases, hf_trending,
    rss, civitai_trending. Örnekler dosyanın altında.

NOT: Reddit kaynağı bu sürümden kaldırıldı — Reddit script/bot trafiğini
    engelliyor (403 Blocked) ve resmi OAuth ('script' app) kurulumu bile
    her zaman güvenilir çalışmıyordu. İstersen ileride tekrar eklenebilir.
"""

import re
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HEADERS = {"User-Agent": "yerel-ai-takip-robotu/2.0 (kisisel kullanim)"}
TIMEOUT = 15
ANTHROPIC_MODEL = "claude-sonnet-5"

_CJK_PATTERN = re.compile(
    r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]"  # Çince/Japonca/Korece karakter aralıkları
)


def contains_foreign_script(text):
    return bool(_CJK_PATTERN.search(text or ""))


def fetch_json(url, headers=None):
    req = urllib.request.Request(url, headers={**HEADERS, **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_text(url, headers=None):
    req = urllib.request.Request(url, headers={**HEADERS, **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def safe_fetch(label, func):
    try:
        return func()
    except Exception as e:
        print(f"  [!] {label} çekilemedi: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Kaynak tipleri (fetcher'lar) — yeni bir "type" eklemek istersen buraya
# ---------------------------------------------------------------------------

def fetch_github_releases(repo, limit=5, **_):
    url = f"https://api.github.com/repos/{repo}/releases?per_page={limit}"
    data = fetch_json(url)
    return [{
        "baslik": r.get("name") or r.get("tag_name"),
        "tarih": (r.get("published_at") or "")[:10],
        "url": r.get("html_url"),
        "skor": None,
    } for r in data]


def fetch_hf_trending(terms, limit=8, **_):
    out = []
    for term in terms:
        url = (
            "https://huggingface.co/api/models"
            f"?search={urllib.parse.quote(term)}&sort=trendingScore&direction=-1&limit={limit}"
        )
        for m in fetch_json(url):
            out.append({
                "baslik": m.get("id"),
                "tarih": m.get("lastModified", "")[:10],
                "url": f"https://huggingface.co/{m.get('id')}",
                "skor": m.get("likes"),
            })
    return out


def fetch_rss(url, limit=10, **_):
    """Genel RSS/Atom okuyucu — arXiv, itch.io, blog'lar, changelog'lar için kullanılabilir."""
    xml_text = fetch_text(url)
    root = ET.fromstring(xml_text)
    items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
    out = []
    for it in items[:limit]:
        title_el = it.find("title")
        if title_el is None:
            title_el = it.find("{http://www.w3.org/2005/Atom}title")
        link_el = it.find("link")
        if link_el is None:
            link_el = it.find("{http://www.w3.org/2005/Atom}link")
        date_el = it.find("pubDate")
        if date_el is None:
            date_el = it.find("{http://www.w3.org/2005/Atom}updated")
        link = link_el.text if link_el is not None and link_el.text else (
            link_el.get("href") if link_el is not None else None
        )
        out.append({
            "baslik": title_el.text.strip() if title_el is not None and title_el.text else "?",
            "tarih": date_el.text[:16] if date_el is not None and date_el.text else None,
            "url": link,
            "skor": None,
        })
    return out


def fetch_civitai_trending(period="Week", types=None, limit=10, **_):
    """Civitai'nin genel/auth-gerektirmeyen API'sinden trend LoRA/checkpoint listesi."""
    params = {"limit": limit, "sort": "Most Downloaded", "period": period}
    if types:
        params["types"] = types
    url = "https://civitai.com/api/v1/models?" + urllib.parse.urlencode(params)
    data = fetch_json(url)
    out = []
    for m in data.get("items", []):
        stats = m.get("stats", {})
        out.append({
            "baslik": f"{m.get('name')} ({m.get('type')})",
            "tarih": None,
            "url": f"https://civitai.com/models/{m.get('id')}",
            "skor": stats.get("downloadCount"),
        })
    return out


FETCHERS = {
    "github_releases": fetch_github_releases,
    "hf_trending": fetch_hf_trending,
    "rss": fetch_rss,
    "civitai_trending": fetch_civitai_trending,
}


# ---------------------------------------------------------------------------
# KATEGORİLER VE KAYNAKLAR — yeni kaynak/kategori eklemek için sadece
# buraya yeni bir satır/sözlük ekle, başka hiçbir yeri değiştirmene gerek yok.
# ---------------------------------------------------------------------------

SOURCES = {
    "llm": {
        "baslik": "Lokal LLM'ler (8GB VRAM sınıfı)",
        "kaynaklar": [
            {"ad": "HF trend LLM modelleri", "type": "hf_trending",
             "terms": ["gguf 7B", "gguf 8B", "quantized instruct"]},
        ],
    },
    "comfy": {
        "baslik": "ComfyUI / Görsel Üretim Workflow'ları",
        "kaynaklar": [
            {"ad": "ComfyUI sürüm notları", "type": "github_releases", "repo": "comfyanonymous/ComfyUI"},
            {"ad": "Civitai trend LoRA/checkpoint (haftalık)", "type": "civitai_trending",
             "period": "Week", "limit": 10},
        ],
    },
    "3d": {
        "baslik": "AI ile 3D Model Üretimi",
        "kaynaklar": [
            {"ad": "HF trend 3D modeller", "type": "hf_trending",
             "terms": ["text-to-3d", "image-to-3d", "3d generation"]},
            {"ad": "Hunyuan3D sürüm notları", "type": "github_releases", "repo": "Tencent/Hunyuan3D-2"},
        ],
    },
    "gamedev": {
        "baslik": "Oyun Geliştirmede AI",
        "kaynaklar": [
            # Reddit kaynağı kaldırıldı (403 Blocked). İstersen buraya
            # github_releases / hf_trending / rss tipinde yeni kaynak ekleyebilirsin.
        ],
    },
    "arxiv": {
        "baslik": "Bilimsel/Teknolojik Yenilikler (arXiv)",
        "kaynaklar": [
            {"ad": "arXiv cs.AI (Yapay Zeka) son yayınlar", "type": "rss",
             "url": "https://rss.arxiv.org/rss/cs.AI", "limit": 10},
            {"ad": "arXiv cs.GR (Grafik/3D) son yayınlar", "type": "rss",
             "url": "https://rss.arxiv.org/rss/cs.GR", "limit": 10},
        ],
    },
    # ÖRNEK — kendi eklemek istediğin bir kaynak için şablon:
    # "yeni_konu": {
    #     "baslik": "Görünen Adı",
    #     "kaynaklar": [
    #         {"ad": "Kaynak adı", "type": "rss", "url": "https://.../feed.xml"},
    #         {"ad": "Başka kaynak", "type": "github_releases", "repo": "sahip/repo"},
    #         {"ad": "HF araması", "type": "hf_trending", "terms": ["anahtar kelime"]},
    #     ],
    # },
}


def collect_raw(secilenler):
    """Seçilen kategoriler için ham veriyi toplar: {kategori: {kaynak_adi: [kayıt, ...]}}"""
    sonuc = {}
    for key in secilenler:
        cat = SOURCES[key]
        sonuc[key] = {}
        for kaynak in cat["kaynaklar"]:
            fetcher = FETCHERS[kaynak["type"]]
            params = {k: v for k, v in kaynak.items() if k not in ("ad", "type")}
            veri = safe_fetch(kaynak["ad"], lambda p=params, f=fetcher: f(**p))
            sonuc[key][kaynak["ad"]] = veri
    return sonuc


def heuristic_filter(kayitlar, top_n=6):
    """API key yoksa: skora/tarihe göre sırala, tekrarları at, ilk top_n'i döndür."""
    gorulen = set()
    temiz = []
    for k in kayitlar:
        anahtar = (k.get("baslik") or "").lower().strip()
        if not anahtar or anahtar in gorulen:
            continue
        gorulen.add(anahtar)
        temiz.append(k)
    temiz.sort(key=lambda k: (k.get("skor") or 0), reverse=True)
    return temiz[:top_n]


# ---------------------------------------------------------------------------
# Claude ile analiz (opsiyonel)
# ---------------------------------------------------------------------------

def call_claude(prompt, api_key):
    body = json.dumps({
        "model": ANTHROPIC_MODEL,
        "max_tokens": 1200,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    parts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
    return "\n".join(parts).strip()


def call_ollama(prompt, model="qwen3:8b", url="http://localhost:11434"):
    """Yerel Ollama sunucusuna istek atar. Önce `ollama serve` çalışıyor
    ve `ollama pull qwen3:8b` (veya seçtiğin model) çekilmiş olmalı."""
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3},
    }).encode("utf-8")
    req = urllib.request.Request(
        url.rstrip("/") + "/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return (data.get("response") or "").strip()
    except urllib.error.URLError as e:
        return (
            f"(Ollama'ya bağlanılamadı: {e}\n"
            f"  -> 'ollama serve' çalışıyor mu kontrol et, ve modelin çekili olduğundan emin ol: "
            f"'ollama pull {model}')"
        )


def call_lmstudio(prompt, model="qwen2.5-7b-nerd-uncensored-v0.9-mfann", url="http://127.0.0.1:1234",
                   temperature=0.15, extra_system_note=""):
    """LM Studio'nun OpenAI-uyumlu yerel sunucusuna istek atar.
    LM Studio'da: Developer / Local Server sekmesinden 'Start Server' demen,
    ve modelin yüklü (loaded) olması gerekir. Model adı eşleşmezse LM Studio
    Server loglarındaki tam model kimliğini kullan (genelde dosya adına yakındır)."""
    system_msg = (
        "Sen sadece Türkçe yanıt veren, kısa ve öz konuşan bir analiz asistanısın. "
        "Hiçbir koşulda İngilizce, Çince ya da başka bir dile geçme. Sana verilen "
        "ham veri listesinde OLMAYAN hiçbir bilgi, model adı, sayı ya da fırsat UYDURMA. "
        "Emin olmadığın bir şeyi 'bundan emin değilim' diye belirt, asla icat etme."
        + (" " + extra_system_note if extra_system_note else "")
    )
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "top_p": 0.85,
        "frequency_penalty": 0.4,
        "presence_penalty": 0.2,
        "max_tokens": 6000,
    }).encode("utf-8")
    req = urllib.request.Request(
        url.rstrip("/") + "/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        cevap = data["choices"][0]["message"]["content"].strip()
    except urllib.error.URLError as e:
        return (
            f"(LM Studio'ya bağlanılamadı: {e}\n"
            f"  -> LM Studio'da Developer/Local Server sekmesinden sunucuyu başlattın mı? "
            f"  -> '{model}' modeli LM Studio'da yüklü (loaded) mu?)"
        )
    except (KeyError, IndexError):
        return f"(LM Studio'dan beklenmeyen yanıt: {data})"

    # Model Çince/Japonca/Korece karakter üretmişse: daha sert ayarla bir kez
    # daha dene (temperature=0, ekstra uyarı). Yine olursa elimizdekiyle
    # devam edip kullanıcıyı açıkça uyarıyoruz.
    if contains_foreign_script(cevap):
        print("  [!] Yanıtta yabancı alfabe tespit edildi, temperature=0 ile tekrar deneniyor...",
              file=sys.stderr)
        retry_prompt = prompt + "\n\nUYARI: Önceki denemende Çince/yabancı karakterler kullandın. Bu SEFER SADECE TÜRKÇE yaz, tek bir yabancı karakter bile olmasın."
        body2 = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": retry_prompt},
            ],
            "temperature": 0.0,
            "top_p": 0.8,
            "frequency_penalty": 0.4,
            "presence_penalty": 0.2,
            "max_tokens": 6000,
        }).encode("utf-8")
        req2 = urllib.request.Request(
            url.rstrip("/") + "/v1/chat/completions",
            data=body2,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req2, timeout=180) as resp2:
                data2 = json.loads(resp2.read().decode("utf-8"))
            cevap2 = data2["choices"][0]["message"]["content"].strip()
            if not contains_foreign_script(cevap2):
                return cevap2
            cevap = "[UYARI: Model tekrar denemede de yabancı alfabe kullandı, çıktı güvenilmez olabilir]\n\n" + cevap2
        except Exception:
            cevap = "[UYARI: Yanıtta yabancı alfabe var, tekrar deneme başarısız]\n\n" + cevap

    return cevap


def analyze_category(baslik, kaynak_verileri, engine="lmstudio", api_key=None,
                      ollama_model="qwen3:8b", ollama_url="http://localhost:11434",
                      lmstudio_model="qwen2.5-7b-nerd-uncensored-v0.9-mfann",
                      lmstudio_url="http://127.0.0.1:1234"):
    ham_blok = []
    toplam_kayit = 0
    for kaynak_adi, kayitlar in kaynak_verileri.items():
        ham_blok.append(f"### {kaynak_adi}")
        for k in kayitlar[:15]:
            ham_blok.append(f"- {k.get('baslik')} | tarih: {k.get('tarih')} | skor: {k.get('skor')} | {k.get('url')}")
            toplam_kayit += 1
    ham_metin = "\n".join(ham_blok) if ham_blok else "(veri yok)"

    # Elde hiç kayıt yoksa modele hiç sormuyoruz — küçük modeller boş veri
    # verilince veri uydurmaya başlıyor. Bu kontrol o sorunu kökten engeller.
    if toplam_kayit == 0:
        return "(Bu kategoride hiç kaynak/veri toplanamadı, analiz atlandı — SOURCES'a kaynak eklemen gerekiyor.)"

    prompt = f"""Aşağıda "{baslik}" kategorisinde son dönemde çekilmiş ham başlık listesi var.

BENİM DURUMUM: 8GB VRAM + 32GB RAM'lik bir bilgisayarım var. Lokal AI araçlarıyla
(LLM, ComfyUI, 3D model üretimi, oyun/asset araçları) dijital ürünler üretip
Etsy, Unity/Unreal Asset Store gibi pazar yerlerinde satmak ve Upwork'te bu
becerilerle iş almak istiyorum. Bütçem donanım değil, zaman ve emek.

KATI KURALLAR (bunlara uymazsan cevap geçersiz sayılır):
1. SADECE Türkçe yaz. Tek bir kelime bile başka dilde olamaz (İngilizce model/repo
   adları hariç — onları olduğu gibi bırak, örn. "Qwen2.5-7B-Instruct-GGUF").
2. SADECE aşağıdaki HAM LİSTE'de gerçekten var olan başlıkları/modelleri konu al.
   Listede olmayan bir model adı, sayı, VRAM değeri, indirme sayısı ya da fırsat
   ASLA uydurma. Listedeki başlığı seçtiğinde, o başlığı kısaca (parantez içinde)
   tekrar et ki hangi maddeden bahsettiğin belli olsun.
3. Listede senin durumuna uygun GERÇEKTEN hiçbir şey yoksa, tek satırda
   "Bu kategoride uygun bir fırsat bulunamadı." yaz ve DUR. Madde uydurma.
4. En fazla 5 madde seç. Her madde için TOPLAM 3 kısa cümleyi geçme:
   a) Ne olduğu (1 cümle)
   b) 8GB VRAM'de çalışır mı, çalışırsa hangi quant/boyutla (1 cümle)
   c) Nasıl paraya çevrilir: hangi platform (Etsy/Asset Store/Upwork/başka) +
      ne tür ürün/gig (1 cümle). Somut fırsat yoksa "Doğrudan satılabilir bir
      fırsat yok" yaz, zorlama.
5. Giriş cümlesi, kapanış cümlesi, özet, yorum YAZMA. Sadece madde işaretli liste.
6. Kısa ve öz yaz — laf kalabalığı yok, tekrar yok, her madde birbirinden farklı
   bir açı sunmalı (aynı cümleyi başka kelimelerle tekrar etme).

HAM LİSTE (sadece burada geçenleri kullan):
{ham_metin}
"""
    if engine == "claude":
        return call_claude(prompt, api_key)
    if engine == "lmstudio":
        return call_lmstudio(prompt, model=lmstudio_model, url=lmstudio_url)
    return call_ollama(prompt, model=ollama_model, url=ollama_url)


# ---------------------------------------------------------------------------
# Çıktı biçimlendirme
# ---------------------------------------------------------------------------

def format_raw_digest(secilenler, raw_data):
    today = datetime.date.today().isoformat()
    lines = [f"# Yerel AI Takip Raporu (ham liste) — {today}", ""]
    for key in secilenler:
        lines.append(f"## {SOURCES[key]['baslik']}")
        for kaynak_adi, kayitlar in raw_data[key].items():
            lines.append(f"\n**{kaynak_adi}**")
            filtreli = heuristic_filter(kayitlar)
            if not filtreli:
                lines.append("- (veri alınamadı ya da sonuç yok)")
                continue
            for k in filtreli:
                tarih = f" ({k['tarih']})" if k.get("tarih") else ""
                skor = f" [skor:{k['skor']}]" if k.get("skor") is not None else ""
                lines.append(f"- {k['baslik']}{tarih}{skor} — {k['url']}")
        lines.append("")
    return "\n".join(lines)


def format_analyzed_digest(secilenler, raw_data, engine, api_key, ollama_model, ollama_url,
                            lmstudio_model, lmstudio_url):
    today = datetime.date.today().isoformat()
    motor_adlari = {"ollama": "Ollama (yerel)", "lmstudio": "LM Studio (yerel)", "claude": "Claude API"}
    motor_adi = motor_adlari.get(engine, engine)
    lines = [f"# Yerel AI Takip Raporu ({motor_adi} analizli) — {today}", ""]
    for key in secilenler:
        baslik = SOURCES[key]["baslik"]
        print(f"  -> {baslik} analiz ediliyor ({motor_adi})...", file=sys.stderr)
        lines.append(f"## {baslik}")
        analiz = analyze_category(baslik, raw_data[key], engine=engine, api_key=api_key,
                                   ollama_model=ollama_model, ollama_url=ollama_url,
                                   lmstudio_model=lmstudio_model, lmstudio_url=lmstudio_url)
        lines.append(analiz if analiz else "(analiz alınamadı)")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Yerel AI trend takip robotu")
    parser.add_argument("--only", nargs="+", choices=SOURCES.keys(),
                         help="Sadece belirtilen kategorileri tara (varsayılan: hepsi)")
    parser.add_argument("--save", action="store_true", help="Raporu markdown dosyasına da kaydet")
    parser.add_argument("--analyze", action="store_true",
                         help="Ham veriyi bir LLM ile analiz ettir")
    parser.add_argument("--engine", choices=["lmstudio", "ollama", "claude"], default=None,
                         help="Analiz motoru. Varsayılan: lmstudio (yerel). Claude için "
                              "açıkça --engine claude yaz.")
    parser.add_argument("--lmstudio-model", default="qwen2.5-7b-nerd-uncensored-v0.9-mfann",
                         help="LM Studio'da yüklü modelin adı")
    parser.add_argument("--lmstudio-url", default="http://127.0.0.1:1234",
                         help="LM Studio sunucu adresi (varsayılan: http://127.0.0.1:1234)")
    parser.add_argument("--ollama-model", default="qwen3:8b",
                         help="Ollama'da kullanılacak model adı (varsayılan: qwen3:8b)")
    parser.add_argument("--ollama-url", default="http://localhost:11434",
                         help="Ollama sunucu adresi (varsayılan: http://localhost:11434)")
    args = parser.parse_args()

    secilenler = args.only if args.only else list(SOURCES.keys())
    print(f"Taranıyor: {', '.join(secilenler)}\n", file=sys.stderr)

    raw_data = collect_raw(secilenler)

    engine = args.engine or "lmstudio"
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if args.analyze and engine == "claude" and not api_key:
        print("[!] --engine claude istendi ama ANTHROPIC_API_KEY ortam değişkeni bulunamadı.", file=sys.stderr)
        print("    Ham liste gösteriliyor.\n", file=sys.stderr)
        args.analyze = False

    if args.analyze:
        digest = format_analyzed_digest(secilenler, raw_data, engine, api_key,
                                         args.ollama_model, args.ollama_url,
                                         args.lmstudio_model, args.lmstudio_url)
    else:
        digest = format_raw_digest(secilenler, raw_data)

    print(digest)

    if args.save:
        etiket = "analizli" if args.analyze else "ham"
        fname = f"ai_takip_raporu_{etiket}_{datetime.date.today().isoformat()}.md"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(digest)
        print(f"\n[Rapor kaydedildi: {fname}]", file=sys.stderr)


if __name__ == "__main__":
    main()