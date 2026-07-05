"""Explorador HTTP acotado, sin autenticacion ni recoleccion de datos personales."""

from __future__ import annotations

from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

from agents.url_acquisition import URLAcquisitionAgent


class WebExtractionAgent:
    def __init__(self, max_pages: int = 15, timeout: int = 20) -> None:
        self.max_pages = max(1, min(max_pages, 15))
        self.timeout = timeout
        self.validator = URLAcquisitionAgent()

    @staticmethod
    def _same_origin(candidate: str, origin: str) -> bool:
        value, base = urlparse(candidate), urlparse(origin)
        return value.scheme == base.scheme and value.netloc.lower() == base.netloc.lower()

    def _fetch(self, session: requests.Session, url: str, origin: str) -> tuple[requests.Response | None, str, str]:
        current = url
        for _ in range(6):
            valid, current, warning = self.validator.validate_url(current)
            if not valid:
                return None, current, warning
            if not self._same_origin(current, origin):
                return None, current, "Se bloqueó una URL fuera del dominio público original."
            try:
                response = session.get(current, timeout=self.timeout, allow_redirects=False)
            except requests.RequestException as exc:
                return None, current, f"No se pudo abrir {current}: {exc.__class__.__name__}."
            if response.is_redirect:
                target = urljoin(current, response.headers.get("location", ""))
                valid, target, warning = self.validator.validate_url(target)
                if not valid or not self._same_origin(target, origin):
                    return None, current, "Se bloqueó una redirección fuera del dominio público original."
                current = target
                continue
            return response, current, ""
        return None, current, "Se excedió el límite de redirecciones."

    def _brand_assets(self, soup: BeautifulSoup, final_url: str) -> dict:
        parsed = urlparse(final_url)
        domain = parsed.netloc.lower()
        brand_name = ""
        site_name = soup.select_one('meta[property="og:site_name"], meta[name="application-name"]')
        if site_name and site_name.get("content"):
            brand_name = site_name["content"].strip()
        if not brand_name and soup.title:
            brand_name = soup.title.get_text(" ", strip=True).split("|")[0].split("-")[0].strip()
        if not brand_name:
            brand_name = domain.replace("www.", "")

        candidates: list[tuple[str, str]] = []
        selectors = [
            ('meta[property="og:logo"]', "content", "Open Graph logo"),
            ('meta[property="og:image"]', "content", "Open Graph image"),
            ('link[rel~="apple-touch-icon"]', "href", "Apple touch icon"),
            ('link[rel~="icon"]', "href", "Favicon"),
            ('link[rel~="shortcut"][rel~="icon"]', "href", "Favicon"),
        ]
        for selector, attr, source in selectors:
            for item in soup.select(selector):
                value = item.get(attr)
                if value:
                    candidates.append((urljoin(final_url, value), source))
        for image in soup.find_all("img"):
            marker = " ".join(
                str(image.get(attr, "")) for attr in ["alt", "class", "id", "src"]
            ).lower()
            if any(token in marker for token in ["logo", "brand", "marca"]):
                src = image.get("src") or image.get("data-src")
                if src:
                    candidates.append((urljoin(final_url, src), "HTML logo image"))

        logo_url, logo_source = "", ""
        for candidate, source in candidates:
            valid, normalized, _ = self.validator.validate_url(candidate)
            if valid and urlparse(normalized).scheme in {"http", "https"}:
                logo_url, logo_source = normalized, source
                break

        return {
            "brand_name": brand_name,
            "logo_url": logo_url,
            "logo_source": logo_source,
            "site_domain": domain,
        }

    def crawl(self, initial_url: str) -> dict:
        queue = deque([initial_url])
        visited: set[str] = set()
        pages: list[dict] = []
        warnings: list[str] = []
        brand_assets: dict = {}
        origin = initial_url
        session = requests.Session()
        session.headers.update({"User-Agent": "PEC-Auditor/1.0 (academic public audit)"})

        while queue and len(pages) < self.max_pages:
            candidate = urldefrag(queue.popleft())[0]
            if candidate in visited or not self._same_origin(candidate, origin):
                continue
            visited.add(candidate)
            response, final_url, warning = self._fetch(session, candidate, origin)
            if warning:
                warnings.append(warning)
            if not response or "text/html" not in response.headers.get("content-type", "").lower():
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            if not brand_assets:
                brand_assets = self._brand_assets(soup, final_url)
            for ignored in soup(["script", "style", "noscript"]):
                ignored.decompose()
            text = soup.get_text(" ", strip=True)
            links: list[str] = []
            for anchor in soup.find_all("a", href=True):
                link = urldefrag(urljoin(final_url, anchor["href"]))[0]
                if self._same_origin(link, origin) and link not in visited and link not in queue:
                    links.append(link)
            queue.extend(links[:25])
            pages.append(
                {
                    "url": final_url,
                    "title": soup.title.get_text(" ", strip=True) if soup.title else "",
                    "html": response.text,
                    "text": text,
                    "links": links,
                    "has_viewport": bool(soup.select_one('meta[name="viewport"]')),
                    "images": len(soup.find_all("img")),
                    "images_with_alt": len([img for img in soup.find_all("img") if img.get("alt")]),
                    "has_lang": bool(soup.html and soup.html.get("lang")),
                    "has_main": bool(soup.find("main")),
                }
            )

        if not pages:
            warnings.append("No se obtuvo HTML público utilizable del sitio; el diagnóstico no debe interpretarse como una evaluación completa.")

        return {
            "pages": pages,
            "warnings": warnings,
            "brand_assets": brand_assets,
            "performance": {
                "available": False,
                "reason": "No evaluable automáticamente sin una API de rendimiento configurada.",
            },
        }
