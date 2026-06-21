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
                "pec_score": 1.0,
                "classification": "Inicial",
                "dimension_scores": {"Tecnológica": {"score": 1.0, "max": 1}},
                "factors": [{
                    "id": "T01", "name": "HTTPS/SSL", "dimension": "Tecnológica", "status": "present", "score": 1.0,
                    "evidence": "HTTPS", "source_url": "https://example.test", "manual_correction": None,
                    "recommendation": "Mantener HTTPS.",
                }],
            }
            audit_id = storage.save_audit(result)
            loaded = storage.get_audit(audit_id)
            self.assertEqual(loaded["pec_score"], 1.0)
            self.assertEqual(loaded["factors"][0]["id"], "T01")
            if original is None:
                os.environ.pop("DATABASE_PATH", None)
            else:
                os.environ["DATABASE_PATH"] = original
