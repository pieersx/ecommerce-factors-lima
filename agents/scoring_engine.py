"""Puntaje PEC simple y trazable para los 30 FCE."""

from __future__ import annotations

from collections import defaultdict


SCORES = {"present": 1.0, "partial": 0.5, "absent": 0.0, "not_evaluable": 0.0}


def classify_pec(score: float) -> str:
    if score >= 25:
        return "Muy alto"
    if score >= 19:
        return "Alto"
    if score >= 12:
        return "Moderado"
    if score >= 6:
        return "Bajo"
    return "Inicial"


class ScoringEngine:
    def calculate(self, factors: list[dict]) -> dict:
        dimension_scores: dict[str, float] = defaultdict(float)
        dimension_max: dict[str, int] = defaultdict(int)
        for factor in factors:
            factor["score"] = SCORES.get(factor["status"], 0.0)
            dimension_scores[factor["dimension"]] += factor["score"]
            dimension_max[factor["dimension"]] += 1
        pec = round(sum(factor["score"] for factor in factors), 1)
        return {
            "pec_score": pec,
            "classification": classify_pec(pec),
            "dimension_scores": {
                dimension: {"score": round(dimension_scores[dimension], 1), "max": maximum}
                for dimension, maximum in dimension_max.items()
            },
        }

    def apply_manual_corrections(self, factors: list[dict], corrections: dict[str, dict]) -> list[dict]:
        for factor in factors:
            correction = corrections.get(factor["id"])
            if correction and correction.get("status") in SCORES:
                factor["status"] = correction["status"]
                factor["manual_correction"] = correction.get("note", "Confirmación manual")
        return factors
