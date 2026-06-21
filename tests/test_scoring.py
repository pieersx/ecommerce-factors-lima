import unittest

from agents.scoring_engine import ScoringEngine, classify_pec


class ScoringTests(unittest.TestCase):
    def test_simple_score_and_dimensions(self):
        factors = [
            {"id": "T01", "dimension": "Tecnológica", "status": "present"},
            {"id": "T02", "dimension": "Tecnológica", "status": "partial"},
            {"id": "O01", "dimension": "Proceso", "status": "absent"},
        ]
        result = ScoringEngine().calculate(factors)
        self.assertEqual(result["pec_score"], 1.5)
        self.assertEqual(result["dimension_scores"]["Tecnológica"], {"score": 1.5, "max": 2})
        self.assertEqual(result["classification"], "Inicial")

    def test_maturity_ranges(self):
        self.assertEqual(classify_pec(25), "Muy alto")
        self.assertEqual(classify_pec(24.5), "Alto")
        self.assertEqual(classify_pec(19), "Alto")
        self.assertEqual(classify_pec(18.5), "Moderado")
        self.assertEqual(classify_pec(12), "Moderado")
        self.assertEqual(classify_pec(11.5), "Bajo")
        self.assertEqual(classify_pec(6), "Bajo")

    def test_manual_correction(self):
        factors = [{"id": "T01", "dimension": "Tecnológica", "status": "absent", "manual_correction": None}]
        updated = ScoringEngine().apply_manual_corrections(factors, {"T01": {"status": "present", "note": "Verificado"}})
        self.assertEqual(updated[0]["status"], "present")
        self.assertEqual(updated[0]["manual_correction"], "Verificado")
        self.assertEqual(ScoringEngine().calculate(updated)["pec_score"], 1)
