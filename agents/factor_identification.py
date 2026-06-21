"""Deteccion explicable de los 30 FCE publicamente observables."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "factor_catalog.json"
SCORES = {"present": 1.0, "partial": 0.5, "absent": 0.0, "not_evaluable": 0.0}


def load_catalog() -> list[dict]:
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


class FactorIdentificationAgent:
    def _match(self, page: dict, pattern: str) -> bool:
        return bool(re.search(pattern, page["text"], re.IGNORECASE)) or bool(
            re.search(pattern, page["html"], re.IGNORECASE)
        )

    def _evidence_page(self, pages: list[dict], predicate) -> dict | None:
        return next((page for page in pages if predicate(page)), None)

    def _detect(self, detector: str, pages: list[dict], audit_url: str) -> tuple[str, str, str]:
        combined = " ".join(page["text"] for page in pages)
        combined_html = " ".join(page["html"] for page in pages)
        home = pages[0] if pages else None

        if detector == "https":
            return ("present", "La URL pública utiliza HTTPS.", audit_url) if urlparse(audit_url).scheme == "https" else ("absent", "La URL pública no utiliza HTTPS.", audit_url)
        if detector == "pagespeed":
            return "not_evaluable", "No evaluable automáticamente sin una API de rendimiento configurada.", audit_url
        if detector == "viewport":
            page = self._evidence_page(pages, lambda item: item["has_viewport"])
            return ("present", "Se encontró meta viewport.", page["url"]) if page else ("absent", "No se encontró meta viewport en las páginas revisadas.", audit_url)

        patterns = {
            "navigation": r"<nav\b|menu|categor[ií]as",
            "search": r"type=[\"']search|buscar productos|b[uú]squeda",
            "catalog": r"cat[aá]logo|colecci[oó]n|productos|<article",
            "product": r"descripci[oó]n|a[ñn]adir al carrito|agregar al carrito",
            "price_stock": r"(?:S/|US\$|\$)\s?\d|stock|disponible|agotado",
            "cart": r"carrito|cart|checkout|finalizar compra",
            "payments": r"visa|mastercard|yape|plin|paypal|culqi|mercado pago|m[eé]todos? de pago",
            "privacy": r"pol[ií]tica de privacidad|privacidad",
            "cookies": r"cookies|galletas",
            "terms": r"t[eé]rminos y condiciones|condiciones de uso",
            "shipping": r"pol[ií]tica de env[ií]o|env[ií]os|despacho",
            "delivery_time": r"(?:S/|US\$|\$)\s?\d.*env[ií]o|env[ií]o.*(?:S/|US\$|\$)\s?\d|\d+\s*(?:d[ií]as|horas).*(?:entrega|env[ií]o)|(?:entrega|env[ií]o).*\d+\s*(?:d[ií]as|horas)",
            "returns": r"devoluciones|cambios|reembolso",
            "faq": r"preguntas frecuentes|\bfaq\b",
            "contact": r"contacto|cont[aá]ctanos|[\w.+-]+@[\w.-]+\.[a-z]{2,}|\+?\d[\d\s()-]{7,}",
            "support": r"whatsapp|chat en vivo|soporte en l[ií]nea|ayuda",
            "legal_id": r"\bruc\b\s*[:#-]?\s*\d{8,11}|raz[oó]n social|domicilio fiscal|av\.|jr\.|calle",
            "coverage": r"cobertura|env[ií]os a|entregamos en|lima metropolitana|zonas de entrega",
            "social": r"instagram\.com|facebook\.com|tiktok\.com|linkedin\.com|youtube\.com",
            "promotions": r"oferta|promoci[oó]n|descuento|\bcyber\b|\bsale\b",
            "marketplace": r"mercadolibre|falabella|amazon|ripley|linio",
            "reviews": r"rese[ñn]as|testimonios|opiniones de clientes|calificaci[oó]n",
            "trust": r"compra segura|pago seguro|sitio seguro|ssl|protecci[oó]n al comprador",
            "about": r"nosotros|nuestra historia|qui[eé]nes somos",
            "guarantees": r"garant[ií]a|garantizado",
            "wishlist": r"favoritos|lista de deseos|wishlist|recomendado para ti",
        }
        if detector == "accessibility":
            if not pages:
                return "absent", "No se obtuvo HTML público para revisar accesibilidad.", audit_url
            qualified = [p for p in pages if p["has_lang"] and p["has_main"]]
            alt_ok = any(p["images"] == 0 or p["images_with_alt"] / p["images"] >= 0.7 for p in pages)
            if qualified and alt_ok:
                return "present", "Se identificaron idioma, estructura semántica y alternativas de imágenes en páginas revisadas.", qualified[0]["url"]
            if any(p["has_lang"] or p["has_main"] for p in pages):
                return "partial", "Se identificó accesibilidad básica incompleta en páginas revisadas.", pages[0]["url"]
            return "absent", "No se encontraron señales básicas de accesibilidad en páginas revisadas.", audit_url

        pattern = patterns[detector]
        page = self._evidence_page(pages, lambda item: self._match(item, pattern))
        if page:
            return "present", f"Evidencia pública detectada para {detector.replace('_', ' ')}.", page["url"]
        # Una tienda encontrada, pero sin una página específica, se mantiene como ausencia verificable.
        return "absent", f"No se encontró evidencia pública para {detector.replace('_', ' ')} en las páginas revisadas.", audit_url

    def identify(self, audit_url: str, extraction: dict) -> list[dict]:
        pages = extraction.get("pages", [])
        factors = []
        for item in load_catalog():
            status, evidence, source_url = self._detect(item["detector"], pages, audit_url)
            factors.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "dimension": item["dimension"],
                    "status": status,
                    "score": SCORES[status],
                    "evidence": evidence,
                    "source_url": source_url,
                    "manual_correction": None,
                    "recommendation": item["recommendation"],
                }
            )
        return factors
