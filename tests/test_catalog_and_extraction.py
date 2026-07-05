import unittest

from bs4 import BeautifulSoup

from agents.factor_identification import load_catalog
from agents.web_extraction import WebExtractionAgent


class CatalogAndExtractionTests(unittest.TestCase):
    def test_operational_catalog_has_exactly_thirty_factors(self):
        catalog = load_catalog()
        self.assertEqual(len(catalog), 30)
        self.assertEqual(len({item["id"] for item in catalog}), 30)
        self.assertEqual(
            {item["dimension"] for item in catalog},
            {"Tecnológica", "Organizacional y proceso", "Ambiental visible", "Consumidor"},
        )

    def test_private_redirect_is_blocked(self):
        class RedirectResponse:
            is_redirect = True
            headers = {"location": "http://127.0.0.1/private"}

        class FakeSession:
            def get(self, *args, **kwargs):
                return RedirectResponse()

        response, _, warning = WebExtractionAgent()._fetch(
            FakeSession(), "https://example.com", "https://example.com"
        )
        self.assertIsNone(response)
        self.assertIn("bloqueó", warning)

    def test_brand_assets_prefers_open_graph_image(self):
        html = """
        <html>
          <head>
            <meta property="og:site_name" content="Tienda Demo">
            <meta property="og:image" content="/brand.png">
            <link rel="icon" href="/favicon.ico">
          </head>
        </html>
        """
        assets = WebExtractionAgent()._brand_assets(
            BeautifulSoup(html, "html.parser"),
            "https://example.com/",
        )
        self.assertEqual(assets["brand_name"], "Tienda Demo")
        self.assertEqual(assets["logo_url"], "https://example.com/brand.png")
        self.assertEqual(assets["logo_source"], "Open Graph image")
