import unittest
import os
import sys
import json
import tempfile
import pandas as pd
from pathlib import Path

# Test dosyasının bulunduğu dizinden bir üst klasöre git
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic import load_skills, run_financial_audit


class TestLoadSkills(unittest.TestCase):
    """load_skills fonksiyonunun testleri"""

    def setUp(self):
        """Her test öncesinde çalışacak"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Her test sonrasında temizleme"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_load_skills_nonexistent_file(self):
        """Dosya bulunamazsa None dönmeli"""
        result = load_skills(os.path.join(self.temp_dir, "nonexistent.json"))
        self.assertIsNone(result)

    def test_load_skills_with_valid_path(self):
        """Geçerli dosyadan doğru veri yüklenmeli"""
        test_data = {
            "sirket_politikalari": {
                "genel_onay_limiti_tl": 1000,
                "kategori_limitleri_tl": {"Yemek": 500},
                "yasakli_saatler": {"baslangic": 22, "bitis": 6},
                "haftasonu_yasagi": True,
                "zorunlu_aciklama_uzunlugu": 10,
                "kara_liste_kelimeler": ["kumar", "alkol"]
            }
        }
        filepath = os.path.join(self.temp_dir, "test_skills.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        result = load_skills(filepath)
        self.assertIsNotNone(result)
        self.assertEqual(result["sirket_politikalari"]["genel_onay_limiti_tl"], 1000)

    def test_load_skills_invalid_json(self):
        """Bozuk JSON dosyası None dönmeli"""
        filepath = os.path.join(self.temp_dir, "broken.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("{invalid json content")

        result = load_skills(filepath)
        self.assertIsNone(result)

    def test_load_skills_default_path(self):
        """Varsayılan path ile yükleme testi (gerçek dosyayı kullanır)"""
        # Gerçek financial_skills.json'u test et (proje klasöründe olmalı)
        result = load_skills()
        if result is not None:  # Dosya varsa kontrol et
            self.assertIn("sirket_politikalari", result)


class TestRunFinancialAudit(unittest.TestCase):
    """run_financial_audit fonksiyonunun testleri"""

    def setUp(self):
        """Her test öncesinde çalışacak"""
        self.temp_dir = tempfile.mkdtemp()
        self.create_test_skills_file()

    def tearDown(self):
        """Her test sonrasında temizleme"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_test_skills_file(self, empty_blacklist=False, disable_weekend=False):
        """Test için politika dosyası oluştur"""
        test_data = {
            "sirket_politikalari": {
                "genel_onay_limiti_tl": 1000,
                "kategori_limitleri_tl": {
                    "Yemek": 500,
                    "Konaklama": 1000,
                    "Yolculuk": 1500,
                    "Ofis Malzemesi": 800
                },
                "yasakli_saatler": {"baslangic": 22, "bitis": 6},
                "haftasonu_yasagi": not disable_weekend,
                "zorunlu_aciklama_uzunlugu": 10,
                "kara_liste_kelimeler": [] if empty_blacklist else ["kumar", "alkol", "gece kulüb"]
            }
        }
        self.skills_path = os.path.join(self.temp_dir, "skills.json")
        with open(self.skills_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

    def create_test_csv(self, data_rows):
        """Test CSV dosyası oluştur"""
        df = pd.DataFrame(data_rows)
        csv_path = os.path.join(self.temp_dir, "test.csv")
        df.to_csv(csv_path, index=False, encoding='utf-8')
        return csv_path

    def test_skills_file_not_found(self):
        """Politika dosyası bulunamazsa ValueError"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 10:00',
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Normal harcama'
            }
        ])

        with self.assertRaises(ValueError) as context:
            run_financial_audit(csv_path, os.path.join(self.temp_dir, "nonexistent.json"))
        self.assertIn("Kural dosyası yüklenemedi", str(context.exception))

    def test_csv_file_not_found(self):
        """CSV dosyası bulunamazsa FileNotFoundError"""
        with self.assertRaises(FileNotFoundError):
            run_financial_audit(os.path.join(self.temp_dir, "nonexistent.csv"), self.skills_path)

    def test_missing_required_columns(self):
        """Gerekli sütunlar eksikse ValueError"""
        df = pd.DataFrame({
            'Calisan': ['Test'],
            'Tutar_TL': [100]
        })
        csv_path = os.path.join(self.temp_dir, "incomplete.csv")
        df.to_csv(csv_path, index=False)

        with self.assertRaises(ValueError) as context:
            run_financial_audit(csv_path, self.skills_path)
        self.assertIn("Eksik sütunlar", str(context.exception))

    def test_empty_blacklist(self):
        """Boş kara liste hata vermemeli"""
        self.create_test_skills_file(empty_blacklist=True)
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 10:00',
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Kumar ve alkol'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        # Boş liste olsa da hata olmamalı, sorgu sonucu NORMAL olmalı
        self.assertEqual(result['AI_Durum'].iloc[0], 'NORMAL')
        self.assertNotIn("Kara liste", result['AI_Neden'].iloc[0])

    def test_nan_aciklama(self):
        """NaN açıklama hata vermemeli"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 10:00',
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': None  # NaN
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        # NaN açıklama çok kısa olarak sayılmalı (Açıklama çok yetersiz)
        self.assertEqual(result['AI_Durum'].iloc[0], 'ŞÜPHELİ')
        self.assertIn("Açıklama çok yetersiz", result['AI_Neden'].iloc[0])

    def test_regex_special_characters_in_blacklist(self):
        """Kara liste içinde regex özel karakterleri olsa bile çalışmalı"""
        test_data = {
            "sirket_politikalari": {
                "genel_onay_limiti_tl": 1000,
                "kategori_limitleri_tl": {"Yemek": 500},
                "yasakli_saatler": {"baslangic": 22, "bitis": 6},
                "haftasonu_yasagi": True,
                "zorunlu_aciklama_uzunlugu": 10,
                "kara_liste_kelimeler": ["kumar(t)", "sp[a]", "c++"]  # Regex özel karakterleri
            }
        }
        self.skills_path = os.path.join(self.temp_dir, "skills_special.json")
        with open(self.skills_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 10:00',
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Kumar alıştırması'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        # Fonksiyon hata vermeden çalışmalı
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

    def test_weekend_disabled(self):
        """haftasonu_yasagi=false iken hafta sonu harcamalar NORMAL"""
        self.create_test_skills_file(disable_weekend=True)
        # Cumartesi: 2026-05-23 (Gun=5)
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-23 10:00',
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Cumartesi kahvesi'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        # Hafta sonu yasağı kapalıysa, sadece bu nedenle şüpheli olmamalı
        self.assertNotIn("Hafta sonu", result['AI_Neden'].iloc[0])

    def test_weekend_enabled(self):
        """haftasonu_yasagi=true iken hafta sonu harcamalar ŞÜPHELİ"""
        self.create_test_skills_file(disable_weekend=False)
        # Cumartesi: 2026-05-23 (Gun=5)
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-23 10:00',
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Cumartesi kahvesi - açıklama yeterli'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        self.assertEqual(result['AI_Durum'].iloc[0], 'ŞÜPHELİ')
        self.assertIn("Hafta sonu", result['AI_Neden'].iloc[0])

    def test_blacklist_keyword_detection(self):
        """Kara liste kelimeler doğru tespit edilmeli"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 10:00',
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Gece kulüb harcaması'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        self.assertEqual(result['AI_Durum'].iloc[0], 'ŞÜPHELİ')
        self.assertIn("Kara liste", result['AI_Neden'].iloc[0])

    def test_normal_expense(self):
        """Normal harcama NORMAL durumu döndürmeli"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 10:00',
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'İftar kahvesi müşteriyle buluşma'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        self.assertEqual(result['AI_Durum'].iloc[0], 'NORMAL')

    def test_short_description_warning(self):
        """Kısa açıklama uyarı vermeli"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 10:00',
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Kısa'  # 4 karakter, limit 10
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        self.assertEqual(result['AI_Durum'].iloc[0], 'ŞÜPHELİ')
        self.assertIn("Açıklama çok yetersiz", result['AI_Neden'].iloc[0])

    def test_amount_exceeds_category_limit(self):
        """Kategori limiti aşılırsa uyarı vermeli"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 10:00',
                'Calisan': 'Test',
                'Kategori': 'Yemek',  # Limit 500
                'Tutar_TL': 1000,  # Aşımı
                'Aciklama': 'Yüksek tutarlı yemek harcaması'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        self.assertEqual(result['AI_Durum'].iloc[0], 'ŞÜPHELİ')
        self.assertIn("Kategori limiti aşıldı", result['AI_Neden'].iloc[0])

    def test_night_hours_detection(self):
        """Gece saatlerinde harcamalar uyarı vermeli"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 23:00',  # 23:00, yasaklı saatler: 22-6
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Gece harcaması - detaylı açıklama'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        self.assertEqual(result['AI_Durum'].iloc[0], 'ŞÜPHELİ')
        self.assertIn("mesai saatleri dışında", result['AI_Neden'].iloc[0])

    def test_multiple_violations(self):
        """Birden fazla ihlal varsa hepsi rapor edilmeli"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-23 23:00',  # Cumartesi, gece
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 1000,  # Kategori limiti aşımı (500)
                'Aciklama': 'Kısa'  # Kısa açıklama + kara liste
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        reasons = result['AI_Neden'].iloc[0]
        # Birden fazla nedenin olması gerekir
        self.assertTrue(len(reasons.split(" | ")) >= 3)

    def test_unknown_category_general_limit(self):
        """Bilinmeyen kategori için genel limit kullanılmalı"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 10:00',
                'Calisan': 'Test',
                'Kategori': 'Diğer',  # Kategori limitleri'nde yok
                'Tutar_TL': 1500,  # Genel limit aşımı (1000)
                'Aciklama': 'Bilinmeyen kategori harcaması'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        self.assertEqual(result['AI_Durum'].iloc[0], 'ŞÜPHELİ')
        self.assertIn("Genel limit aşımı", result['AI_Neden'].iloc[0])

    def test_sunday_restriction(self):
        """Pazar günü de hafta sonu yasağı altında olmalı"""
        self.create_test_skills_file(disable_weekend=False)
        # Pazar: 2026-05-24 (Gun=6)
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-24 10:00',
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Pazar kahvesi - açıklama yeterli'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        self.assertEqual(result['AI_Durum'].iloc[0], 'ŞÜPHELİ')
        self.assertIn("Hafta sonu", result['AI_Neden'].iloc[0])

    def test_case_insensitive_blacklist_uppercase(self):
        """Kara liste tespiti büyük/küçük harflere duyarsız olmalı"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 10:00',
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'ALKOL KÖŞESİ ZİYARETİ'  # Büyük harf
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        self.assertEqual(result['AI_Durum'].iloc[0], 'ŞÜPHELİ')
        self.assertIn("Kara liste", result['AI_Neden'].iloc[0])

    def test_edge_case_exact_category_limit(self):
        """Kategori limitine tam eşit tutarlı harcama NORMAL olmalı"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 10:00',
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 500,  # Kategori limiti tam eşit
                'Aciklama': 'Yemek harcaması - limite eşit'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        self.assertEqual(result['AI_Durum'].iloc[0], 'NORMAL')
        self.assertNotIn("Kategori limiti aşıldı", result['AI_Neden'].iloc[0])

    def test_edge_case_one_char_description(self):
        """1 karakterlik açıklama yeterli değil"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 10:00',
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'X'  # 1 karakter
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        self.assertEqual(result['AI_Durum'].iloc[0], 'ŞÜPHELİ')
        self.assertIn("Açıklama çok yetersiz", result['AI_Neden'].iloc[0])

    def test_early_morning_hour(self):
        """Erken sabah saati (05:00) yasaklı saatler içinde"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 05:00',  # 05:00, yasaklı saatler 22-6
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Erken sabah harcaması - açıklama'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        self.assertEqual(result['AI_Durum'].iloc[0], 'ŞÜPHELİ')
        self.assertIn("mesai saatleri dışında", result['AI_Neden'].iloc[0])

    def test_allowed_hour_boundary(self):
        """07:00 izin verili olmalı (gece yasağı 22-6 arası)"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 07:00',  # 07:00, yasaklı saatler dışı
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Sabah 7 harcaması - açıklama yeterli'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        # 07:00 izin verili
        self.assertNotIn("mesai saatleri dışında", result['AI_Neden'].iloc[0])

    def test_forbidden_hour_boundary_22(self):
        """22:00 (yasağın başlangıcı) yasak olmalı"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 22:00',  # 22:00, yasaklı saatler başlangıcı
                'Calisan': 'Test',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Saat 22 harcaması - açıklama yeterli'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        self.assertEqual(result['AI_Durum'].iloc[0], 'ŞÜPHELİ')
        self.assertIn("mesai saatleri dışında", result['AI_Neden'].iloc[0])

    def test_multiple_expenses_batch(self):
        """Birden fazla harcama aynı anda işlenebilmeli"""
        csv_path = self.create_test_csv([
            {
                'Tarih': '2026-05-20 10:00',
                'Calisan': 'Test1',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Normal harcama - açıklama'
            },
            {
                'Tarih': '2026-05-23 10:00',
                'Calisan': 'Test2',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Cumartesi harcaması - açıklama'
            },
            {
                'Tarih': '2026-05-20 23:00',
                'Calisan': 'Test3',
                'Kategori': 'Yemek',
                'Tutar_TL': 100,
                'Aciklama': 'Gece harcaması - açıklama'
            }
        ])

        result = run_financial_audit(csv_path, self.skills_path)
        self.assertEqual(len(result), 3)
        self.assertEqual(result.iloc[0]['AI_Durum'], 'NORMAL')
        self.assertEqual(result.iloc[1]['AI_Durum'], 'ŞÜPHELİ')
        self.assertEqual(result.iloc[2]['AI_Durum'], 'ŞÜPHELİ')


if __name__ == '__main__':
    unittest.main()
