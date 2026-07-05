"""Estimacion de confianza para una auditoria PEC."""

from __future__ import annotations

from urllib.parse import urlparse


def coverage_label(pages_reviewed: int) -> str:
    if pages_reviewed >= 12:
        return "Alta"
    if pages_reviewed >= 6:
        return "Media"
    if pages_reviewed >= 1:
        return "Baja"
    return "No disponible"


class ConfidenceAssessmentAgent:
    def assess(self, extraction: dict, qualification: dict, factors: list[dict], max_pages: int = 15) -> dict:
        pages = extraction.get("pages", [])
        warnings = extraction.get("warnings", [])
        pages_reviewed = len(pages)
        paths = {urlparse(page.get("url", "")).path.rstrip("/") or "/" for page in pages}
        not_evaluable = sum(1 for factor in factors if factor.get("status") == "not_evaluable")

        score = 100
        reasons: list[str] = []

        if pages_reviewed <= 1:
            score -= 50
            reasons.append("Solo se reviso una pagina publica; la evidencia puede ser incompleta.")
        elif pages_reviewed < 6:
            score -= 20
            reasons.append("La cobertura es baja porque se revisaron menos de 6 paginas.")
        elif pages_reviewed < 12:
            score -= 8
            reasons.append("La cobertura es media; no se alcanzo la muestra completa de 12 a 15 paginas.")
        else:
            reasons.append("La cobertura de paginas es alta para una auditoria publica acotada.")

        if len(paths) <= 1 and pages_reviewed > 1:
            score -= 10
            reasons.append("Las URLs revisadas tienen poca diversidad de rutas.")

        signal_count = qualification.get("ecommerce_signal_count", 0)
        if qualification.get("qualification_status") == "weak":
            score -= 25
            reasons.append("La tienda solo presento senales debiles de e-commerce.")
        elif signal_count < 4:
            score -= 10
            reasons.append("Se encontraron pocas senales comerciales directas.")
        else:
            reasons.append("Se encontraron varias senales comerciales directas.")

        if not_evaluable:
            score -= min(20, not_evaluable * 5)
            reasons.append(f"{not_evaluable} factor(es) quedaron como no evaluables.")

        if warnings:
            score -= min(15, len(warnings) * 5)
            reasons.append("Hubo advertencias durante la exploracion del sitio.")

        score = max(0, min(100, score))
        if score >= 75:
            label = "Alta"
        elif score >= 50:
            label = "Media"
        else:
            label = "Baja"

        return {
            "confidence_score": score,
            "confidence_label": label,
            "confidence_reasons": reasons,
            "coverage_label": coverage_label(pages_reviewed),
            "coverage_sample": f"{pages_reviewed}/{max_pages} paginas",
        }
