"""Calificacion previa para confirmar que la URL auditada es e-commerce."""

from __future__ import annotations

import re


SIGNALS = [
    {
        "key": "catalog",
        "label": "Catalogo o listado de productos",
        "pattern": r"\b(cat[aá]logo de productos|colecci[oó]n de productos|tienda online|all products|shop)\b|/products?/|/collections?/|/categoria",
    },
    {
        "key": "price",
        "label": "Precio visible",
        "pattern": r"(?:S/|US\$|\$|£|€)\s?\d+(?:[.,]\d{2})?|\bprecio regular\b|\bprecio oferta\b",
    },
    {
        "key": "cart",
        "label": "Carrito o checkout",
        "pattern": r"\b(carrito|checkout|basket|finalizar compra|bolsa de compras|shopping cart|add to basket|add to cart|agregar al carrito|a[ñn]adir al carrito)\b|/(cart|basket|checkout)(?:/|$)",
    },
    {
        "key": "payments",
        "label": "Medios de pago",
        "pattern": r"\b(visa|mastercard|yape|plin|paypal|culqi|mercado pago|pago con tarjeta|m[eé]todos? de pago)\b",
    },
    {
        "key": "product_detail",
        "label": "Ficha o detalle de producto",
        "pattern": r"\b(descripci[oó]n del producto|sku|stock|in stock|out of stock|agotado|talla|color)\b|/producto|/product",
    },
    {
        "key": "purchase_terms",
        "label": "Condiciones de compra, envio o devolucion",
        "pattern": r"\b(env[ií]os?|delivery|devoluciones?|cambios|garant[ií]a|t[eé]rminos y condiciones|pol[ií]tica de env[ií]o)\b",
    },
]


class EcommerceQualificationAgent:
    """Evalua si hay evidencia minima para aplicar un indice de e-commerce."""

    def qualify(self, extraction: dict) -> dict:
        pages = extraction.get("pages", [])
        found: dict[str, dict] = {}
        for page in pages:
            searchable = " ".join([page.get("text", ""), *page.get("links", [])])
            for signal in SIGNALS:
                if signal["key"] in found:
                    continue
                if re.search(signal["pattern"], searchable, re.IGNORECASE):
                    found[signal["key"]] = {
                        "key": signal["key"],
                        "label": signal["label"],
                        "source_url": page.get("url", ""),
                    }

        evidence = list(found.values())
        score = len(evidence)
        keys = set(found)
        has_transaction = bool({"cart", "payments"} & keys)
        has_offer = bool({"catalog", "product_detail"} & keys)
        has_price = "price" in keys
        if "cart" in keys and has_offer and (has_price or "payments" in keys):
            status = "qualified"
        elif has_transaction and has_offer and score >= 3:
            status = "weak"
        elif has_offer and has_price and "payments" in keys:
            status = "weak"
        else:
            status = "rejected"

        return {
            "is_ecommerce": status in {"qualified", "weak"},
            "qualification_status": status,
            "ecommerce_evidence": evidence,
            "ecommerce_signal_count": score,
            "message": self._message(status),
        }

    @staticmethod
    def _message(status: str) -> str:
        if status == "qualified":
            return "La URL presenta senales suficientes de tienda e-commerce."
        if status == "weak":
            return "La URL presenta senales debiles de e-commerce; el resultado debe interpretarse con baja confianza."
        return "La URL no presenta evidencia suficiente de tienda e-commerce."
