import os
import tempfile
import unittest

from utils import storage


class StorageTests(unittest.TestCase):
    def test_saves_and_loads_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            original = os.environ.get("DATABASE_PATH")
            os.environ["DATABASE_PATH"] = os.path.join(directory, "audits.db")
            result = {
                "url": "https://example.test",
                "warnings": [],
                "pages_reviewed": 15,
                "pec_score": 1.0,
                "classification": "Inicial",
                "dimension_scores": {"Tecnológica": {"score": 1.0, "max": 1}},
                "is_ecommerce": True,
                "qualification_status": "qualified",
                "ecommerce_evidence": [{"label": "Catalogo", "source_url": "https://example.test"}],
                "confidence_score": 80,
                "confidence_label": "Alta",
                "confidence_reasons": ["Cobertura alta"],
                "brand_assets": {
                    "brand_name": "Example",
                    "logo_url": "https://example.test/logo.png",
                    "logo_source": "Open Graph image",
                    "site_domain": "example.test",
                },
                "ai_review": {"summary": "OK", "risks": []},
                "factors": [{
                    "id": "T01", "name": "HTTPS/SSL", "dimension": "Tecnológica", "status": "present", "score": 1.0,
                    "evidence": "HTTPS", "source_url": "https://example.test", "manual_correction": None,
                    "recommendation": "Mantener HTTPS.",
                }],
            }
            audit_id = storage.save_audit(result)
            loaded = storage.get_audit(audit_id)
            self.assertEqual(loaded["pec_score"], 1.0)
            self.assertEqual(loaded["pages_reviewed"], 15)
            self.assertTrue(loaded["is_ecommerce"])
            self.assertEqual(loaded["qualification_status"], "qualified")
            self.assertEqual(loaded["confidence_label"], "Alta")
            self.assertEqual(loaded["confidence_reasons"], ["Cobertura alta"])
            self.assertEqual(loaded["brand_assets"]["brand_name"], "Example")
            self.assertEqual(loaded["brand_assets"]["logo_source"], "Open Graph image")
            self.assertEqual(loaded["ai_review"]["summary"], "OK")
            self.assertEqual(loaded["factors"][0]["id"], "T01")
            if original is None:
                os.environ.pop("DATABASE_PATH", None)
            else:
                os.environ["DATABASE_PATH"] = original
