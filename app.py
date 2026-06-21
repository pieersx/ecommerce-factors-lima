"""PEC Auditor: demo académica para diagnóstico observable de e-commerce."""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from agents.factor_identification import FactorIdentificationAgent
from agents.gap_prioritization import GapPrioritizationAgent
from agents.recommendations import RecommendationAgent
from agents.scoring_engine import ScoringEngine
from agents.url_acquisition import URLAcquisitionAgent
from agents.web_extraction import WebExtractionAgent
from utils.reporting import build_pdf
from utils.storage import get_audit, initialize_database, list_audits, save_audit, save_feedback


st.set_page_config(page_title="PEC Auditor", page_icon="P", layout="wide")
initialize_database()
if "audit" not in st.session_state:
    st.session_state.audit = None
if "audit_id" not in st.session_state:
    st.session_state.audit_id = None


def build_result(url: str) -> dict:
    max_pages = int(os.getenv("AUDIT_MAX_PAGES", "10"))
    timeout = int(os.getenv("AUDIT_TIMEOUT_SECONDS", "20"))
    extraction = WebExtractionAgent(max_pages=max_pages, timeout=timeout).crawl(url)
    factors = FactorIdentificationAgent().identify(url, extraction)
    score_data = ScoringEngine().calculate(factors)
    return {
        "url": url,
        "warnings": extraction["warnings"],
        "pages_reviewed": len(extraction["pages"]),
        "factors": factors,
        "recommendations": RecommendationAgent().generate(factors),
        **score_data,
    }


def recalculate(result: dict, corrections: dict[str, dict]) -> dict:
    result["factors"] = ScoringEngine().apply_manual_corrections(result["factors"], corrections)
    result.update(ScoringEngine().calculate(result["factors"]))
    result["recommendations"] = RecommendationAgent().generate(result["factors"])
    return result


def status_label(status: str) -> str:
    return {
        "present": "Presente (1)",
        "partial": "Parcial (0.5)",
        "absent": "Ausente (0)",
        "not_evaluable": "No evaluable (0)",
    }[status]


st.title("PEC Auditor")
st.caption("Diagnóstico transparente de 30 factores críticos de éxito observables en tiendas e-commerce.")
tabs = st.tabs(["Nueva auditoría", "Resumen PEC", "Factores y evidencia", "Brechas y recomendaciones", "Historial", "Feedback"])

with tabs[0]:
    st.subheader("Auditar una tienda pública")
    st.write("La exploración revisa hasta 10 páginas públicas del mismo dominio. No inicia sesión ni recopila datos personales.")
    with st.form("new_audit"):
        url_value = st.text_input("URL de la tienda", placeholder="https://www.ejemplo.com")
        submitted = st.form_submit_button("Auditar tienda", type="primary")
    if submitted:
        valid, normalized, message = URLAcquisitionAgent().validate_url(url_value)
        if not valid:
            st.error(message)
        else:
            progress = st.progress(0, text="Explorando páginas públicas...")
            try:
                progress.progress(35, text="Detectando evidencia de los 30 FCE...")
                result = build_result(normalized)
                if result["pages_reviewed"] == 0:
                    raise RuntimeError("No se obtuvo evidencia pública suficiente para auditar esta URL.")
                progress.progress(80, text="Calculando PEC y recomendaciones...")
                st.session_state.audit = result
                st.session_state.audit_id = save_audit(result)
                progress.progress(100, text="Auditoría guardada.")
                st.success(f"Auditoría completada: {result['pec_score']}/30 ({result['classification']}).")
                st.rerun()
            except Exception as exc:
                st.error(f"La auditoría no pudo completarse: {exc}")


with tabs[1]:
    result = st.session_state.audit
    if not result:
        st.info("Realiza una auditoría para ver el resumen ejecutivo.")
    else:
        a, b, c = st.columns(3)
        a.metric("Índice PEC", f"{result['pec_score']}/30")
        b.metric("Nivel de madurez", result["classification"])
        c.metric("Factores revisados", len(result["factors"]))
        st.subheader("Puntaje por dimensión")
        score_rows = [
            {"Dimensión": name, "Puntaje": values["score"], "Máximo": values["max"]}
            for name, values in result["dimension_scores"].items()
        ]
        st.bar_chart(pd.DataFrame(score_rows).set_index("Dimensión")[["Puntaje", "Máximo"]])
        if result["warnings"]:
            st.warning("Advertencias de exploración: " + " ".join(result["warnings"]))
        st.caption("El rendimiento de carga queda como no evaluable hasta contar con una medición externa o confirmación manual; no se simulan métricas.")


with tabs[2]:
    result = st.session_state.audit
    if not result:
        st.info("No hay factores para mostrar todavía.")
    else:
        st.subheader("Confirmación manual de factores")
        st.write("La corrección manual reemplaza el estado operativo y conserva la evidencia detectada automáticamente.")
        options = ["present", "partial", "absent", "not_evaluable"]
        with st.form("factor_corrections"):
            corrections: dict[str, dict] = {}
            for dimension in sorted({factor["dimension"] for factor in result["factors"]}):
                st.markdown(f"**{dimension}**")
                for factor in [item for item in result["factors"] if item["dimension"] == dimension]:
                    with st.expander(f"{factor['id']} - {factor['name']} | {status_label(factor['status'])}"):
                        st.write(f"Evidencia: {factor['evidence']}")
                        st.caption(f"Fuente: {factor['source_url']}")
                        selected = st.selectbox("Estado confirmado", options, index=options.index(factor["status"]), format_func=status_label, key=f"state_{factor['id']}")
                        note = st.text_input("Nota de confirmación", value=factor.get("manual_correction") or "", key=f"note_{factor['id']}")
                        corrections[factor["id"]] = {"status": selected, "note": note}
            corrected = st.form_submit_button("Recalcular y guardar correcciones", type="primary")
        if corrected:
            updated = recalculate(result, corrections)
            st.session_state.audit = updated
            st.session_state.audit_id = save_audit(updated)
            st.success(f"PEC actualizado: {updated['pec_score']}/30 ({updated['classification']}).")
            st.rerun()


with tabs[3]:
    result = st.session_state.audit
    if not result:
        st.info("No hay brechas por mostrar todavía.")
    else:
        gaps = GapPrioritizationAgent().prioritize(result["factors"])
        rows = [
            {
                "Prioridad": item["priority"], "FCE": item["name"], "Estado": status_label(item["status"]),
                "Evidencia": item["evidence"], "Acción propuesta": item["recommendation"],
            }
            for item in gaps
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


with tabs[4]:
    history = list_audits()
    if not history:
        st.info("Aún no existen auditorías guardadas localmente.")
    else:
        labels = {item["id"]: f"#{item['id']} | {item['pec_score']}/30 | {item['classification']} | {item['url']}" for item in history}
        chosen = st.selectbox("Auditoría guardada", list(labels), format_func=labels.get)
        saved = get_audit(chosen)
        if saved:
            left, right = st.columns([2, 1])
            left.write(f"**{saved['url']}**")
            left.write(f"PEC: {saved['pec_score']}/30 - {saved['classification']}")
            if left.button("Cargar en la sesión", key=f"load_{chosen}"):
                saved["recommendations"] = RecommendationAgent().generate(saved["factors"])
                st.session_state.audit, st.session_state.audit_id = saved, chosen
                st.success("Auditoría cargada.")
                st.rerun()
            right.download_button("Descargar informe PDF", build_pdf(saved), file_name=f"pec_auditoria_{chosen}.pdf", mime="application/pdf", key=f"pdf_{chosen}")


with tabs[5]:
    with st.form("feedback"):
        rating = st.slider("Calificación de la demo", 1, 5, 4)
        comment = st.text_area("Comentario", placeholder="¿Qué evidencia o recomendación mejorarías?")
        send = st.form_submit_button("Guardar feedback")
    if send:
        save_feedback(rating, comment)
        st.success("Feedback guardado localmente. Gracias.")
