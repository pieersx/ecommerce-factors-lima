"""PEC Auditor: demo académica para diagnóstico observable de e-commerce."""

from __future__ import annotations

import os

import altair as alt
import pandas as pd
import streamlit as st

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

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
if "audit_notice" not in st.session_state:
    st.session_state.audit_notice = None


def build_result_interactive(url: str) -> dict:
    """Run audit with interactive st.status updates."""
    max_pages = max(1, min(int(os.getenv("AUDIT_MAX_PAGES", "15")), 15))
    timeout = int(os.getenv("AUDIT_TIMEOUT_SECONDS", "20"))

    with st.status("Auditoría en progreso...", expanded=True) as status:
        # Step 1: URL validation
        st.write("Validando URL y resolviendo dominio...")
        valid, normalized, message = URLAcquisitionAgent().validate_url(url)
        if not valid:
            status.update(label="URL inválida", state="error")
            st.error(message)
            st.stop()
        st.write(f"URL normalizada: `{normalized}`")

        # Step 2: Web crawling
        st.write(f"Explorando hasta {max_pages} páginas públicas del dominio...")
        extraction = WebExtractionAgent(max_pages=max_pages, timeout=timeout).crawl(normalized)
        pages_found = len(extraction["pages"])
        if pages_found == 0:
            status.update(label="No se encontraron páginas", state="error")
            st.error("No se obtuvo evidencia pública suficiente para auditar esta URL.")
            st.stop()
        st.write(f"Se exploraron **{pages_found}** páginas públicas exitosamente.")
        if extraction["warnings"]:
            for w in extraction["warnings"]:
                st.write(f"  - {w}")

        # Step 3: Factor detection
        st.write("Detectando evidencia de los 30 FCE...")
        factors = FactorIdentificationAgent().identify(normalized, extraction)

        # Count by status
        present = sum(1 for f in factors if f["status"] == "present")
        partial = sum(1 for f in factors if f["status"] == "partial")
        absent = sum(1 for f in factors if f["status"] == "absent")
        not_eval = sum(1 for f in factors if f["status"] == "not_evaluable")
        st.write(
            f"Evidencia detectada: **{present}** presentes, "
            f"**{partial}** parciales, **{absent}** ausentes, "
            f"**{not_eval}** no evaluables."
        )

        # Step 4: Scoring
        st.write("Calculando Índice PEC...")
        score_data = ScoringEngine().calculate(factors)
        st.write(
            f"PEC: **{score_data['pec_score']}/30** — Nivel: **{score_data['classification']}**"
        )

        # Step 5: Recommendations
        st.write("Generando recomendaciones prioritarias...")
        recommendations = RecommendationAgent().generate(factors)

        # Step 6: Save
        st.write("Guardando auditoría en la base de datos...")
        result = {
            "url": normalized,
            "warnings": extraction["warnings"],
            "pages_reviewed": pages_found,
            "factors": factors,
            "recommendations": recommendations,
            **score_data,
        }
        audit_id = save_audit(result)
        if not get_audit(audit_id):
            raise RuntimeError("No se pudo confirmar el guardado local de la auditoría.")
        st.write(f"Auditoría guardada y confirmada en SQLite con ID **#{audit_id}**.")

        status.update(label="Auditoría completada", state="complete")

    return result, audit_id


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


def fce_counts(factors: list[dict]) -> pd.DataFrame:
    labels = {
        "present": "Presentes",
        "partial": "Parciales",
        "absent": "Ausentes",
        "not_evaluable": "No evaluables",
    }
    rows = [
        {"Estado": label, "Cantidad de FCE": sum(factor["status"] == key for factor in factors)}
        for key, label in labels.items()
    ]
    return pd.DataFrame(rows)


def criterion_example(factor: dict) -> str:
    examples = {
        "T01": "La URL debe iniciar con https://.",
        "T02": "Se busca la etiqueta meta viewport en el HTML.",
        "T03": "Se usa PageSpeed Insights cuando existe una API configurada; de lo contrario requiere confirmación manual.",
        "T04": "Se buscan menús, navegación o enlaces de categorías visibles.",
        "T05": "Se busca un campo de búsqueda o texto como 'buscar productos'.",
        "T06": "Se buscan enlaces o secciones de catálogo, colección o productos.",
        "T07": "Se buscan descripciones y controles para añadir o agregar al carrito.",
        "T08": "Se buscan precios, stock, disponibilidad o aviso de agotado.",
        "T09": "Se buscan enlaces o botones de carrito, checkout o finalizar compra.",
        "T10": "Se buscan referencias como Visa, Mastercard, Yape, Plin, PayPal o Mercado Pago.",
        "O01": "Se busca un enlace o texto de política de privacidad.",
        "O02": "Se busca aviso o política de cookies.",
        "O03": "Se busca una sección de términos y condiciones.",
        "O04": "Se busca política de envío, despacho o información de envíos.",
        "O05": "Se busca un monto o plazo asociado a entrega o envío.",
        "O06": "Se buscan devoluciones, cambios o reembolsos.",
        "O07": "Se busca FAQ o preguntas frecuentes.",
        "O08": "Se busca contacto, correo, teléfono o formulario de atención.",
        "O09": "Se busca WhatsApp, chat en vivo, soporte o ayuda.",
        "O10": "Se busca RUC, razón social o dirección comercial.",
        "A01": "Se buscan zonas de entrega, cobertura o ciudades atendidas.",
        "A02": "Se buscan enlaces oficiales a Instagram, Facebook, TikTok, LinkedIn o YouTube.",
        "A03": "Se buscan ofertas, promociones, descuentos o campañas Cyber/Sale.",
        "A04": "Se buscan enlaces a Mercado Libre, Falabella, Amazon, Ripley o Linio.",
        "C01": "Se buscan reseñas, testimonios, opiniones o calificaciones.",
        "C02": "Se buscan expresiones como compra segura, pago seguro o protección al comprador.",
        "C03": "Se busca una sección Nosotros, Quiénes somos o Nuestra historia.",
        "C04": "Se busca información de garantía o productos garantizados.",
        "C05": "Se buscan favoritos, lista de deseos, wishlist o recomendaciones.",
        "C06": "Se revisan idioma, estructura semántica y texto alternativo en imágenes.",
    }
    return examples.get(factor["id"], "Se revisa evidencia pública relacionada con este FCE.")


def coverage_label(pages_reviewed: int) -> str:
    if pages_reviewed >= 12:
        return "Alta"
    if pages_reviewed >= 6:
        return "Media"
    if pages_reviewed >= 1:
        return "Baja"
    return "No disponible"


st.title("PEC Auditor")
st.caption("Diagnóstico transparente de 30 factores críticos de éxito observables en tiendas e-commerce.")
tabs = st.tabs(["Nueva auditoría", "Resumen PEC", "Factores y evidencia", "Brechas y recomendaciones", "Historial", "Feedback"])

with tabs[0]:
    st.subheader("Auditar una tienda pública")
    st.write("La exploración revisa hasta 15 páginas públicas del mismo dominio. No inicia sesión ni recopila datos personales.")
    if st.session_state.audit_notice and st.session_state.audit:
        completed = st.session_state.audit
        st.success(f"Auditoría completada y guardada localmente con ID #{st.session_state.audit_notice}.")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Índice PEC", f"{completed['pec_score']}/30")
        m2.metric("Nivel", completed["classification"])
        m3.metric("Páginas revisadas", completed.get("pages_reviewed", "N/D"))
        m4.metric("Cobertura", coverage_label(completed.get("pages_reviewed", 0)))
        m5.metric("Factores evaluados", len(completed["factors"]))
        st.info("Los resultados ya están disponibles en Resumen PEC, Factores y evidencia, Brechas e Historial.")
        st.session_state.audit_notice = None
    with st.form("new_audit"):
        url_value = st.text_input("URL de la tienda", placeholder="https://www.ejemplo.com")
        submitted = st.form_submit_button("Auditar tienda", type="primary")
    if submitted:
        try:
            result, audit_id = build_result_interactive(url_value)
            st.session_state.audit = result
            st.session_state.audit_id = audit_id
            st.session_state.audit_notice = audit_id
            st.rerun()
        except Exception as exc:
            st.error(f"La auditoría no pudo completarse: {exc}")


with tabs[1]:
    result = st.session_state.audit
    if not result:
        st.info("Realiza una auditoría para ver el resumen ejecutivo.")
    else:
        a, b, c, d = st.columns(4)
        a.metric("Índice PEC", f"{result['pec_score']}/30")
        b.metric("Nivel de madurez", result["classification"])
        c.metric("Factores revisados", len(result["factors"]))
        pages_reviewed = result.get("pages_reviewed", 0)
        d.metric("Cobertura de auditoría", coverage_label(pages_reviewed), f"{pages_reviewed}/15 páginas" if pages_reviewed else "Sin dato histórico")
        st.caption("El PEC refleja madurez observable en la web; no mide ventas, utilidades ni éxito financiero de la empresa.")
        counts = fce_counts(result["factors"])
        count_columns = st.columns(4)
        for column, row in zip(count_columns, counts.to_dict("records")):
            column.metric(row["Estado"], row["Cantidad de FCE"])
        st.subheader("Distribución de los 30 FCE")
        status_chart = (
            alt.Chart(counts)
            .mark_bar(cornerRadiusEnd=5)
            .encode(
                x=alt.X("Cantidad de FCE:Q", scale=alt.Scale(domain=[0, 30]), title="Cantidad"),
                y=alt.Y("Estado:N", sort=["Presentes", "Parciales", "Ausentes", "No evaluables"], title=None),
                color=alt.Color(
                    "Estado:N",
                    scale=alt.Scale(
                        domain=["Presentes", "Parciales", "Ausentes", "No evaluables"],
                        range=["#15803d", "#ca8a04", "#dc2626", "#64748b"],
                    ),
                    legend=None,
                ),
                tooltip=["Estado", "Cantidad de FCE"],
            )
            .properties(height=190)
        )
        labels = status_chart.mark_text(align="left", baseline="middle", dx=5, color="#111827").encode(text="Cantidad de FCE:Q")
        st.altair_chart(status_chart + labels, use_container_width=True)
        st.subheader("Puntaje por dimensión")
        score_rows = [
            {"Dimensión": name, "Puntaje": values["score"], "Máximo": values["max"]}
            for name, values in result["dimension_scores"].items()
        ]
        dimension_df = pd.DataFrame(score_rows)
        dimension_chart = (
            alt.Chart(dimension_df)
            .transform_fold(["Puntaje", "Máximo"], as_=["Tipo", "Valor"])
            .mark_bar()
            .encode(
                x=alt.X("Valor:Q", title="FCE"),
                y=alt.Y("Dimensión:N", title=None),
                color=alt.Color("Tipo:N", scale=alt.Scale(domain=["Puntaje", "Máximo"], range=["#0f766e", "#cbd5e1"])),
                xOffset=alt.XOffset("Tipo:N"),
                tooltip=[alt.Tooltip("Dimensión:N"), alt.Tooltip("Tipo:N"), alt.Tooltip("Valor:Q")],
            )
            .properties(height=220)
        )
        st.altair_chart(dimension_chart, use_container_width=True)
        if result["warnings"]:
            st.warning("Advertencias de exploración: " + " ".join(result["warnings"]))
        st.caption("T03 usa PageSpeed Insights cuando existe una API configurada; de lo contrario queda como no evaluable hasta confirmación manual.")


with tabs[2]:
    result = st.session_state.audit
    if not result:
        st.info("No hay factores para mostrar todavía.")
    else:
        st.subheader("Confirmación manual de factores")
        st.write("La corrección manual reemplaza el estado operativo y conserva la evidencia automática como trazabilidad.")
        dimensions = sorted({factor["dimension"] for factor in result["factors"]})
        selected_dimensions = st.multiselect(
            "Filtrar grupos de FCE",
            dimensions,
            default=dimensions,
            help="Seleccione una o más dimensiones para revisar solo esos factores.",
        )
        st.info("Si no estás conforme con el hallazgo, elige el estado correcto y escribe una justificación verificable en la nota. Ejemplo: 'La política de devolución está visible en https://tienda.pe/devoluciones'.")
        options = ["present", "partial", "absent", "not_evaluable"]
        with st.form("factor_corrections"):
            corrections: dict[str, dict] = {}
            for dimension in selected_dimensions:
                st.markdown(f"**{dimension}**")
                for factor in [item for item in result["factors"] if item["dimension"] == dimension]:
                    with st.expander(f"{factor['id']} - {factor['name']} | {status_label(factor['status'])}"):
                        st.write(f"Evidencia: {factor['evidence']}")
                        st.caption(f"Fuente: {factor['source_url']}")
                        st.caption(f"Criterio usado: {criterion_example(factor)}")
                        selected = st.selectbox("Estado confirmado", options, index=options.index(factor["status"]), format_func=status_label, key=f"state_{factor['id']}")
                        note = st.text_input(
                            "Nota de confirmación",
                            value=factor.get("manual_correction") or "",
                            key=f"note_{factor['id']}",
                            help="Explique qué evidencia pública revisó e incluya la URL o sección exacta cuando sea posible.",
                        )
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
        st.caption(f"{len(history)} auditorías guardadas en la base de datos local SQLite.")
        st.dataframe(
            pd.DataFrame(history).rename(columns={"id": "ID", "created_at": "Fecha UTC", "url": "URL", "pages_reviewed": "Páginas", "pec_score": "PEC", "classification": "Nivel"}),
            use_container_width=True,
            hide_index=True,
        )
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
