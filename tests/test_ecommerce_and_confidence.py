import unittest

from agents.confidence_assessment import ConfidenceAssessmentAgent
from agents.ecommerce_qualification import EcommerceQualificationAgent
from agents.recommendations import RecommendationAgent


def page(url: str, text: str) -> dict:
    return {"url": url, "text": text, "html": text}


class EcommerceAndConfidenceTests(unittest.TestCase):
    def test_rejects_non_ecommerce_site(self):
        extraction = {"pages": [page("https://example.test/", "Somos una consultora con servicios empresariales.")]}
        result = EcommerceQualificationAgent().qualify(extraction)
        self.assertFalse(result["is_ecommerce"])
        self.assertEqual(result["qualification_status"], "rejected")

    def test_rejects_university_with_generic_payment_terms(self):
        extraction = {
            "pages": [
                page(
                    "https://university.test/",
                    "Universidad con admision, pensiones, pagos, precio de matricula, becas, programas, "
                    "servicios academicos, delivery de certificados y garantia educativa.",
                )
            ]
        }
        result = EcommerceQualificationAgent().qualify(extraction)
        self.assertFalse(result["is_ecommerce"])
        self.assertEqual(result["qualification_status"], "rejected")

    def test_qualifies_ecommerce_site(self):
        extraction = {
            "pages": [
                page(
                    "https://shop.test/",
                    "Catalogo de productos S/ 49 agregar al carrito metodos de pago envios",
                )
            ]
        }
        result = EcommerceQualificationAgent().qualify(extraction)
        self.assertTrue(result["is_ecommerce"])
        self.assertEqual(result["qualification_status"], "qualified")
        self.assertGreaterEqual(len(result["ecommerce_evidence"]), 3)

    def test_qualifies_english_demo_shop(self):
        extraction = {
            "pages": [
                page(
                    "http://books.toscrape.com/",
                    "All products 1000 results £51.77 In stock Add to basket",
                )
            ]
        }
        result = EcommerceQualificationAgent().qualify(extraction)
        self.assertTrue(result["is_ecommerce"])
        self.assertEqual(result["qualification_status"], "qualified")

    def test_one_page_audit_has_low_confidence(self):
        extraction = {
            "pages": [page("https://shop.test/", "Catalogo de productos S/ 49 agregar al carrito")],
            "warnings": [],
        }
        qualification = EcommerceQualificationAgent().qualify(extraction)
        factors = [{"id": "T03", "status": "not_evaluable"}]
        confidence = ConfidenceAssessmentAgent().assess(extraction, qualification, factors)
        self.assertEqual(confidence["confidence_label"], "Baja")
        self.assertIn("Solo se reviso una pagina publica", " ".join(confidence["confidence_reasons"]))

    def test_recommendations_are_grouped_by_impact(self):
        factors = [
            {
                "id": "O08", "name": "Canales de contacto", "dimension": "Proceso",
                "status": "absent", "recommendation": "Mostrar contacto.", "evidence": "No encontrado",
                "source_url": "https://shop.test",
            },
            {
                "id": "T09", "name": "Carrito", "dimension": "Tecnologica",
                "status": "absent", "recommendation": "Mostrar carrito.", "evidence": "No encontrado",
                "source_url": "https://shop.test",
            },
        ]
        recommendations = RecommendationAgent().generate(factors)
        self.assertEqual(recommendations[0]["impact_group"], "Compra")
        self.assertEqual(recommendations[0]["priority"], "Alta")


if __name__ == "__main__":
    unittest.main()
