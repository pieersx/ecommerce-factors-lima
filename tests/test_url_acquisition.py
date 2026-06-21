import unittest

from agents.url_acquisition import URLAcquisitionAgent


class URLAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.agent = URLAcquisitionAgent()

    def assert_invalid(self, url):
        valid, _, _ = self.agent.validate_url(url)
        self.assertFalse(valid, url)

    def test_rejects_invalid_and_private_destinations(self):
        for value in ["ftp://example.com", "not a url", "http://localhost:8501", "http://127.0.0.1", "http://192.168.1.10", "http://[::1]", "https://shop.local"]:
            self.assert_invalid(value)

    def test_accepts_public_http_scheme_without_network_dependency(self):
        original = self.agent._host_is_public
        self.agent._host_is_public = lambda host: host == "example.test"
        valid, normalized, _ = self.agent.validate_url("https://example.test/catalog?x=1")
        self.assertTrue(valid)
        self.assertEqual(normalized, "https://example.test/catalog?x=1")
        self.agent._host_is_public = original
