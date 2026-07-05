"""Revision metodologica opcional con IA."""

from __future__ import annotations

import json
import os

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]


class AIReviewAgent:
    """Usa IA solo como validador de confianza; no reemplaza reglas trazables."""

    def review(self, result: dict, timeout: int = 20) -> dict | None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or requests is None:
            return None
        payload = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            "input": [
                {
                    "role": "system",
                    "content": (
                        "Eres un revisor metodologico de auditorias e-commerce. "
                        "No recalcules el puntaje ni inventes evidencia. Resume riesgos de error, "
                        "falsos positivos o baja cobertura en espanol."
                    ),
                },
                {"role": "user", "content": json.dumps(self._summary_payload(result), ensure_ascii=False)},
            ],
        }
        try:
            response = requests.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
            text = self._extract_text(data)
            if not text:
                return None
            return {
                "summary": text[:1200],
                "risks": [
                    "La revision IA es auxiliar y debe contrastarse con la evidencia y correcciones manuales.",
                ],
            }
        except requests.RequestException as exc:
            return {
                "summary": f"No se pudo ejecutar la revision IA: {exc.__class__.__name__}.",
                "risks": ["El diagnostico se mantiene basado en reglas trazables."],
            }

    @staticmethod
    def _summary_payload(result: dict) -> dict:
        factors = result.get("factors", [])
        return {
            "url": result.get("url"),
            "pec_score": result.get("pec_score"),
            "classification": result.get("classification"),
            "pages_reviewed": result.get("pages_reviewed"),
            "qualification_status": result.get("qualification_status"),
            "ecommerce_evidence": result.get("ecommerce_evidence", []),
            "confidence_label": result.get("confidence_label"),
            "confidence_score": result.get("confidence_score"),
            "confidence_reasons": result.get("confidence_reasons", []),
            "warnings": result.get("warnings", []),
            "factor_status_counts": {
                status: sum(1 for factor in factors if factor.get("status") == status)
                for status in ["present", "partial", "absent", "not_evaluable"]
            },
            "non_present_factors": [
                {
                    "id": factor.get("id"),
                    "name": factor.get("name"),
                    "status": factor.get("status"),
                    "evidence": factor.get("evidence"),
                }
                for factor in factors
                if factor.get("status") != "present"
            ][:12],
        }

    @staticmethod
    def _extract_text(data: dict) -> str:
        if isinstance(data.get("output_text"), str):
            return data["output_text"].strip()
        chunks: list[str] = []
        for output in data.get("output", []):
            for content in output.get("content", []):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    chunks.append(content["text"])
        return "\n".join(chunks).strip()
