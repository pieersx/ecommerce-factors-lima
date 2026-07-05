"""EcomScore: demo académica para diagnóstico observable de e-commerce."""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path

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
from agents.ai_review import AIReviewAgent
from agents.confidence_assessment import ConfidenceAssessmentAgent
from agents.ecommerce_qualification import EcommerceQualificationAgent
from agents.recommendations import RecommendationAgent
from agents.scoring_engine import ScoringEngine
from agents.url_acquisition import URLAcquisitionAgent
from agents.web_extraction import WebExtractionAgent
from utils.reporting import build_pdf, build_recommendations_pdf
from utils.storage import get_audit, initialize_database, list_audits, save_audit


st.set_page_config(page_title="EcomScore", page_icon="E", layout="wide")
initialize_database()
if "audit" not in st.session_state:
    st.session_state.audit = None
if "audit_id" not in st.session_state:
    st.session_state.audit_id = None
if "audit_notice" not in st.session_state:
    st.session_state.audit_notice = None


def inject_design_system() -> None:
    st.markdown(
        """
        <style>
        :root {
            --pec-bg: #ffffff;
            --pec-panel: #ffffff;
            --pec-ink: #162126;
            --pec-muted: #5f6f7a;
            --pec-line: #d9e1e5;
            --pec-teal: #00796b;
            --pec-teal-dark: #005f55;
            --pec-blue: #276d9f;
            --pec-amber: #c98212;
        }

        html, body,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main,
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"],
        [data-testid="stAppViewBlockContainer"],
        section.main,
        main,
        .stApp {
            background: #ffffff !important;
            background-color: #ffffff !important;
            color: var(--pec-ink) !important;
        }

        .stApp > div,
        .main > div,
        div.block-container,
        div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stElementContainer"] {
            background-color: transparent !important;
        }

        header[data-testid="stHeader"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        section[data-testid="stSidebar"] {
            background: #ffffff !important;
            background-color: #ffffff !important;
        }

        .block-container {
            width: min(94vw, 1720px);
            max-width: none;
            padding: 3.5rem 1.2rem 4rem;
        }

        h1, h2, h3 {
            color: var(--pec-ink);
            letter-spacing: 0;
        }

        h1 {
            font-size: 2.7rem;
            line-height: 1.04;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }

        h2, h3 {
            font-weight: 750;
        }

        .pec-hero {
            width: 100%;
            border: 1px solid #d6e3e1;
            border-top: 5px solid var(--pec-teal);
            background: #ffffff !important;
            background-color: #ffffff !important;
            border-radius: 12px;
            padding: 22px 28px;
            margin: 14px 0 18px;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.07);
            display: grid;
            grid-template-columns: minmax(0, 1.65fr) minmax(360px, 0.72fr);
            gap: 24px;
            align-items: center;
        }

        .pec-kicker {
            color: var(--pec-teal-dark);
            font-size: 0.82rem;
            font-weight: 850;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .pec-hero-brand {
            display: flex;
            align-items: center;
            gap: 18px;
            margin-bottom: 8px;
        }

        .pec-hero-logo {
            width: 136px;
            max-width: 32vw;
            height: auto;
            display: block;
        }

        .pec-hero-title {
            min-width: 0;
        }

        .pec-hero h1 {
            margin: 0;
        }

        .pec-hero p {
            color: #344854;
            max-width: 880px;
            margin: 12px 0 0;
            font-size: 1.08rem;
            line-height: 1.58;
        }

        .pec-hero-side {
            background: #ffffff !important;
            background-color: #ffffff !important;
            border: 1px solid #d7e3e1;
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
        }

        .pec-hero-side strong {
            display: block;
            color: var(--pec-ink);
            font-size: 1.02rem;
            margin-bottom: 8px;
        }

        .pec-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 16px;
        }

        .pec-badge {
            border: 1px solid #b9d4d0;
            border-radius: 999px;
            background: #ffffff !important;
            background-color: #ffffff !important;
            color: #164e47;
            padding: 7px 11px;
            font-size: 0.86rem;
            font-weight: 700;
        }

        div[data-testid="stTabs"] [role="tablist"] {
            gap: 6px;
            border-bottom: 1px solid var(--pec-line);
            background: #ffffff !important;
            background-color: #ffffff !important;
        }

        div[data-testid="stTabs"] button {
            border-radius: 10px 10px 0 0;
            color: #485a65 !important;
            font-weight: 700;
            padding: 10px 14px;
        }

        div[data-testid="stTabs"] button * {
            color: inherit !important;
        }

        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: var(--pec-teal-dark);
            background: #ffffff;
            border-bottom: 3px solid var(--pec-teal);
        }

        div[data-testid="stMetric"] {
            min-height: 108px;
            background: #ffffff !important;
            background-color: #ffffff !important;
            border: 1px solid #d8e1e7;
            border-left: 5px solid var(--pec-teal);
            border-radius: 10px;
            padding: 16px 18px;
            box-shadow: 0 10px 24px rgba(22, 33, 38, 0.055);
            color: var(--pec-ink) !important;
        }

        div[data-testid="stMetric"] * {
            color: inherit;
        }

        div[data-testid="stMetricLabel"] {
            color: var(--pec-muted);
            font-weight: 700;
        }

        div[data-testid="stMetricValue"] {
            color: var(--pec-ink);
            font-size: 1.55rem;
            font-weight: 800;
        }

        div[data-testid="stForm"],
        div[data-testid="stExpander"] {
            background: #ffffff !important;
            border: 1px solid #d8e1e7;
            border-radius: 10px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
            color: var(--pec-ink) !important;
        }

        div[data-testid="stForm"] *,
        div[data-testid="stExpander"] * {
            color: var(--pec-ink);
        }

        div[data-testid="stAlert"] {
            border-radius: 10px;
            border: 1px solid rgba(0, 121, 107, 0.18);
            background-color: #ffffff !important;
            color: var(--pec-ink) !important;
        }

        .stButton > button,
        .stDownloadButton > button,
        div[data-testid="stFormSubmitButton"] button {
            min-height: 42px;
            border-radius: 9px;
            border: 1px solid var(--pec-teal);
            background: var(--pec-teal) !important;
            color: #ffffff !important;
            font-weight: 760;
            box-shadow: 0 8px 18px rgba(0, 121, 107, 0.18);
        }

        .stButton > button *,
        .stDownloadButton > button *,
        div[data-testid="stFormSubmitButton"] button *,
        .stButton > button p,
        .stDownloadButton > button p,
        div[data-testid="stFormSubmitButton"] button p,
        .stButton > button span,
        .stDownloadButton > button span,
        div[data-testid="stFormSubmitButton"] button span,
        .stButton > button div,
        .stDownloadButton > button div,
        div[data-testid="stFormSubmitButton"] button div {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            border-color: var(--pec-teal-dark);
            background: var(--pec-teal-dark) !important;
            color: #ffffff !important;
        }

        div[data-baseweb="input"] input,
        div[data-baseweb="select"] > div,
        textarea {
            border-radius: 9px;
            background-color: #ffffff !important;
            color: #162126 !important;
        }

        div[data-baseweb="input"] {
            background-color: #ffffff !important;
        }

        .pec-section-note {
            border-left: 5px solid var(--pec-blue);
            background: #ffffff !important;
            background-color: #ffffff !important;
            border-radius: 10px;
            padding: 16px 18px;
            color: #344854;
            margin: 10px 0 20px;
            border-top: 1px solid #e1e8ed;
            border-right: 1px solid #e1e8ed;
            border-bottom: 1px solid #e1e8ed;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.055);
            line-height: 1.55;
        }

        .pec-section-note *,
        .pec-info-card *,
        .pec-hero *,
        .pec-badge {
            color: inherit;
        }

        .pec-two-col {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 14px;
            margin: 8px 0 18px;
        }

        .pec-info-card {
            background: #ffffff !important;
            background-color: #ffffff !important;
            border: 1px solid #d8e1e7;
            border-radius: 10px;
            padding: 17px 18px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.055);
            line-height: 1.55;
        }

        .pec-info-card strong {
            color: var(--pec-teal-dark);
        }

        .pec-interpretation-card {
            background: #ffffff !important;
            background-color: #ffffff !important;
            border: 1px solid #d8e1e7;
            border-radius: 10px;
            padding: 16px 18px;
            margin: 0;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.055);
        }

        .pec-interpretation-card > strong {
            color: var(--pec-ink);
            display: block;
            font-size: 1.08rem;
            margin-bottom: 12px;
        }

        .pec-interpretation-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 14px;
        }

        .pec-table-card {
            border: 1px solid #d8e1e7;
            border-radius: 8px;
            background: #ffffff;
            overflow: hidden;
        }

        .pec-table-card h4 {
            margin: 0;
            padding: 11px 13px;
            font-size: 0.95rem;
            color: var(--pec-ink);
            background: #f8fafc;
            border-bottom: 1px solid #d8e1e7;
        }

        .pec-guide-table {
            width: 100%;
            border-collapse: collapse;
        }

        .pec-guide-table td {
            padding: 10px 13px;
            border-bottom: 1px solid #e8eef2;
            color: var(--pec-ink);
            font-size: 0.92rem;
            vertical-align: middle;
        }

        .pec-guide-table tr:last-child td {
            border-bottom: 0;
        }

        .pec-guide-table td:last-child {
            text-align: right;
            font-weight: 800;
        }

        .pec-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 4px 9px;
            font-size: 0.78rem;
            font-weight: 800;
            line-height: 1;
            border: 1px solid transparent;
        }

        .pec-pill-present {
            background: #e8f7ee;
            border-color: #b7e3c6;
            color: #166534;
        }

        .pec-pill-partial {
            background: #fff6dd;
            border-color: #f3d58a;
            color: #92400e;
        }

        .pec-pill-absent {
            background: #fdecec;
            border-color: #f5b8b8;
            color: #991b1b;
        }

        .pec-pill-not {
            background: #edf2f7;
            border-color: #cbd5e1;
            color: #334155;
        }

        .pec-guide-note {
            color: #344854;
            font-size: 0.92rem;
            line-height: 1.45;
            margin-top: 12px;
        }

        .pec-factor-head {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
        }

        .pec-factor-title {
            font-weight: 800;
            color: var(--pec-ink);
        }

        .pec-factor-score {
            color: #5f6f7a;
            font-size: 0.84rem;
            font-weight: 750;
        }

        .pec-logo-placeholder {
            width: 112px;
            height: 112px;
            border-radius: 12px;
            border: 1px solid #d8e1e7;
            background: #e5e7eb;
            color: #6b7280;
            display: grid;
            place-items: center;
            font-size: 2.6rem;
            font-weight: 850;
            margin-bottom: 0.35rem;
        }

        @media (max-width: 980px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                width: 100%;
            }
            .pec-hero {
                grid-template-columns: 1fr;
                padding: 22px;
            }
            .pec-hero-brand {
                align-items: flex-start;
            }
            h1 {
                font-size: 2.25rem;
            }
            .pec-two-col {
                grid-template-columns: 1fr;
            }
            .pec-interpretation-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 700px) {
            .block-container {
                padding-top: 2rem;
                padding-left: 0.8rem;
                padding-right: 0.8rem;
            }
            .pec-hero {
                margin-top: 8px;
                padding: 18px;
                gap: 14px;
            }
            .pec-hero-logo {
                width: 112px;
            }
            .pec-hero-brand {
                gap: 12px;
            }
            .pec-hero p {
                font-size: 0.98rem;
            }
            .pec-badges {
                gap: 6px;
            }
            .pec-badge {
                font-size: 0.78rem;
                padding: 6px 9px;
            }
            div[data-testid="stTabs"] button {
                padding: 8px 9px;
                font-size: 0.82rem;
            }
            div[data-testid="stMetric"] {
                min-height: auto;
                padding: 13px 14px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def build_result_interactive(url: str) -> dict:
    """Run audit with interactive st.status updates."""
    max_pages = max(1, min(int(os.getenv("AUDIT_MAX_PAGES", "15")), 15))
    timeout = int(os.getenv("AUDIT_TIMEOUT_SECONDS", "20"))
    timings: list[dict] = []

    def mark(stage: str, started_at: float) -> None:
        timings.append({"stage": stage, "seconds": round(time.perf_counter() - started_at, 2)})

    with st.status("Auditoría en progreso...", expanded=True) as status:
        st.info(
            "La auditoría puede tardar porque valida DNS y seguridad del dominio, descarga hasta 15 páginas "
            "públicas, espera redirecciones o sitios lentos y analiza evidencia sin iniciar sesión ni recopilar "
            "datos privados."
        )
        # Step 1: URL validation
        started = time.perf_counter()
        st.write("Validando URL y resolviendo dominio...")
        valid, normalized, message = URLAcquisitionAgent().validate_url(url)
        if not valid:
            status.update(label="URL inválida", state="error")
            st.error(message)
            st.stop()
        st.write(f"URL normalizada: `{normalized}`")
        mark("Validación de URL y DNS", started)

        # Step 2: Web crawling
        started = time.perf_counter()
        st.write(f"Explorando hasta {max_pages} páginas públicas del dominio...")
        st.caption("Esta etapa suele ser la más lenta: depende de velocidad del sitio, redirecciones, bloqueos y timeouts.")
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
        mark("Exploración de páginas públicas", started)

        # Step 2.5: E-commerce qualification
        started = time.perf_counter()
        st.write("Verificando señales mínimas de e-commerce...")
        qualification = EcommerceQualificationAgent().qualify(extraction)
        if qualification["qualification_status"] == "rejected":
            status.update(label="No califica como e-commerce", state="error")
            st.error("La URL no presenta evidencia suficiente de tienda e-commerce.")
            if qualification["ecommerce_evidence"]:
                st.write("Señales encontradas:")
                for item in qualification["ecommerce_evidence"]:
                    st.write(f"- {item['label']} ({item['source_url']})")
            st.info("El Índice PEC solo se calcula para tiendas con señales públicas de compra, catálogo o checkout.")
            st.stop()
        if qualification["qualification_status"] == "weak":
            st.warning("La URL presenta señales débiles de e-commerce; la auditoría continuará con baja confianza.")
        st.write(f"Señales e-commerce detectadas: **{len(qualification['ecommerce_evidence'])}**.")
        mark("Validación previa e-commerce", started)

        # Step 3: Factor detection
        started = time.perf_counter()
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
        mark("Detección de los 30 FCE", started)

        # Step 4: Scoring
        started = time.perf_counter()
        st.write("Calculando Índice PEC...")
        score_data = ScoringEngine().calculate(factors)
        st.write(
            f"PEC: **{score_data['pec_score']}/30** — Nivel: **{score_data['classification']}**"
        )
        mark("Cálculo del índice PEC", started)

        # Step 4.5: Confidence
        started = time.perf_counter()
        confidence = ConfidenceAssessmentAgent().assess(extraction, qualification, factors, max_pages=max_pages)
        st.write(
            f"Confianza del resultado: **{confidence['confidence_label']}** "
            f"({confidence['confidence_score']}/100)."
        )
        mark("Evaluación de confianza", started)

        # Step 5: Recommendations
        started = time.perf_counter()
        st.write("Generando recomendaciones prioritarias...")
        recommendations = RecommendationAgent().generate(factors)
        mark("Generación de recomendaciones", started)

        # Step 6: Save
        started = time.perf_counter()
        st.write("Guardando auditoría en la base de datos...")
        result = {
            "url": normalized,
            "warnings": extraction["warnings"],
            "pages_reviewed": pages_found,
            "brand_assets": extraction.get("brand_assets", {}),
            "factors": factors,
            "recommendations": recommendations,
            "timings": timings,
            **qualification,
            **confidence,
            **score_data,
        }
        ai_started = time.perf_counter()
        result["ai_review"] = AIReviewAgent().review(result)
        if result["ai_review"]:
            mark("Revisión IA opcional", ai_started)
        audit_id = save_audit(result)
        if not get_audit(audit_id):
            raise RuntimeError("No se pudo confirmar el guardado local de la auditoría.")
        st.write(f"Auditoría guardada y confirmada en SQLite con ID **#{audit_id}**.")
        mark("Guardado local", started)
        with st.expander("Tiempos de ejecución por etapa"):
            for item in timings:
                st.write(f"- {item['stage']}: {item['seconds']} s")

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


def status_short_label(status: str) -> str:
    return {
        "present": "Presente",
        "partial": "Parcial",
        "absent": "Ausente",
        "not_evaluable": "No evaluable",
    }.get(status, status)


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


def qualification_label(status: str) -> str:
    return {
        "qualified": "Sí es e-commerce",
        "weak": "E-commerce débil",
        "rejected": "No es e-commerce",
    }.get(status, "No disponible")


def methodology_note() -> str:
    return (
        "El límite de 15 páginas funciona como muestra pública acotada: permite una revisión reproducible, "
        "no invasiva y manejable para validación manual. Los 30 FCE son el núcleo operativo observable del "
        "marco TOEC; los 74 factores completos quedan como referencia académica porque no todos son verificables "
        "desde una web pública."
    )


def state_pill(status: str) -> str:
    classes = {
        "present": "pec-pill-present",
        "partial": "pec-pill-partial",
        "absent": "pec-pill-absent",
        "not_evaluable": "pec-pill-not",
    }
    return f"<span class='pec-pill {classes.get(status, 'pec-pill-not')}'>{status_short_label(status)}</span>"


def app_logo_data_uri() -> str:
    logo_path = Path("assets/ecomscore-logo.png")
    if not logo_path.exists():
        return ""
    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_interpretation_tables() -> None:
    st.markdown(
        """
        <div class="pec-interpretation-card">
            <strong>Guía de interpretación</strong>
            <div class="pec-interpretation-grid">
                <div class="pec-table-card">
                    <h4>Rangos de EcomScore</h4>
                    <table class="pec-guide-table">
                        <tr><td>25 - 30</td><td>Muy alto</td></tr>
                        <tr><td>19 - 24.5</td><td>Alto</td></tr>
                        <tr><td>12 - 18.5</td><td>Moderado</td></tr>
                        <tr><td>6 - 11.5</td><td>Bajo</td></tr>
                        <tr><td>0 - 5.5</td><td>Inicial</td></tr>
                    </table>
                </div>
                <div class="pec-table-card">
                    <h4>Puntaje por estado del FCE</h4>
                    <table class="pec-guide-table">
                        <tr><td><span class="pec-pill pec-pill-present">Presente</span></td><td>1 punto</td></tr>
                        <tr><td><span class="pec-pill pec-pill-partial">Parcial</span></td><td>0.5 puntos</td></tr>
                        <tr><td><span class="pec-pill pec-pill-absent">Ausente</span></td><td>0 puntos</td></tr>
                        <tr><td><span class="pec-pill pec-pill-not">No evaluable</span></td><td>0 puntos</td></tr>
                    </table>
                </div>
            </div>
            <div class="pec-guide-note">
                EcomScore clasifica el puntaje obtenido sobre 30 FCE observables; no representa ventas,
                utilidad ni éxito financiero. Los factores no evaluables quedan marcados para revisión.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def recommendations_for(result: dict) -> list[dict]:
    recommendations = result.get("recommendations") or []
    if recommendations and all("priority" in item and "impact_group" in item for item in recommendations):
        return recommendations
    return RecommendationAgent().generate(result["factors"])


def brand_initial(brand_assets: dict) -> str:
    name = (brand_assets or {}).get("brand_name") or (brand_assets or {}).get("site_domain") or "?"
    return name.strip()[:1].upper() or "?"


def render_brand_card(result: dict) -> None:
    brand_assets = result.get("brand_assets", {}) or {}
    brand_name = brand_assets.get("brand_name") or brand_assets.get("site_domain") or "Marca auditada"
    domain = brand_assets.get("site_domain") or result.get("url", "")
    logo_url = brand_assets.get("logo_url", "")
    source = brand_assets.get("logo_source") or "Placeholder"
    can_render_logo = logo_url.lower().split("?")[0].endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))
    if logo_url and can_render_logo:
        st.image(logo_url, width=112)
    else:
        st.markdown(f"<div class='pec-logo-placeholder'>{brand_initial(brand_assets)}</div>", unsafe_allow_html=True)
    st.markdown(f"**{brand_name}**")
    st.caption(domain)
    st.caption(f"Imagen: {source if logo_url and can_render_logo else 'No disponible'}")


inject_design_system()
logo_data_uri = app_logo_data_uri()
logo_html = f'<img class="pec-hero-logo" src="{logo_data_uri}" alt="EcomScore logo">' if logo_data_uri else ""
st.markdown(
    f"""
    <section class="pec-hero">
        <div>
            <div class="pec-hero-brand">
                {logo_html}
                <div class="pec-hero-title">
                    <div class="pec-kicker">Auditoría pública de e-commerce</div>
                    <h1>EcomScore</h1>
                </div>
            </div>
            <p>
                Auditoría pública de e-commerce basada en 30 factores críticos de éxito observables.
                Metodología PEC: preparación e-commerce evaluada desde evidencia pública.
                Diseñado para tiendas de Lima Metropolitana; otras URLs se interpretan como referencia comparativa.
            </p>
            <div class="pec-badges">
                <span class="pec-badge">30 FCE núcleo</span>
                <span class="pec-badge">Hasta 15 páginas públicas</span>
                <span class="pec-badge">Confianza del resultado</span>
                <span class="pec-badge">PDF de brechas</span>
            </div>
        </div>
        <aside class="pec-hero-side">
            <strong>Qué mide el PEC</strong>
            Evalúa qué tan completo y verificable es el canal e-commerce desde evidencia pública.
            No mide ventas, rentabilidad ni éxito financiero.
        </aside>
    </section>
    """,
    unsafe_allow_html=True,
)
tabs = st.tabs(["Nueva auditoría", "Resumen PEC", "Factores y evidencia", "Brechas y recomendaciones", "Historial", "Sobre el proyecto"])

with tabs[0]:
    st.subheader("Auditar un e-commerce")
    with st.form("new_audit"):
        url_value = st.text_input("URL del e-commerce", placeholder="https://www.ejemplo.com")
        submitted = st.form_submit_button("Auditar e-commerce", type="primary")
    if st.session_state.audit_notice and st.session_state.audit:
        completed = st.session_state.audit
        st.success(f"Auditoría completada y guardada localmente con ID #{st.session_state.audit_notice}.")
        brand_col, metrics_col = st.columns([0.9, 3.2])
        with brand_col:
            render_brand_card(completed)
        with metrics_col:
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("EcomScore", f"{completed['pec_score']}/30")
            m2.metric("Nivel PEC", completed["classification"])
            m3.metric("Páginas revisadas", completed.get("pages_reviewed", "N/D"))
            m4.metric("Confianza", completed.get("confidence_label", coverage_label(completed.get("pages_reviewed", 0))))
            m5.metric("Validación", qualification_label(completed.get("qualification_status", "qualified")))
        st.info("Los resultados ya están disponibles en Resumen PEC, Factores y evidencia, Brechas e Historial.")
        st.session_state.audit_notice = None
    calc_col, deliver_col = st.columns(2)
    with calc_col:
        st.markdown(
            """
            <div class="pec-info-card">
                <strong>Antes de calcular PEC</strong><br>
                La URL debe mostrar señales mínimas de e-commerce: catálogo, precio, carrito, pagos,
                ficha de producto o condiciones de compra.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with deliver_col:
        st.markdown(
            """
            <div class="pec-info-card">
                <strong>Qué entrega la auditoría</strong><br>
	                EcomScore, nivel de preparación, confianza del resultado, evidencia por factor,
                brechas priorizadas y reportes PDF.
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        f"""
        <div class="pec-section-note">
            <strong>Nota metodológica</strong><br>
            La exploración revisa hasta 15 páginas públicas del mismo dominio. No inicia sesión ni recopila datos personales.
            {methodology_note()}
        </div>
        """,
        unsafe_allow_html=True,
    )
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
        brand_col, summary_col = st.columns([0.85, 3.2])
        with brand_col:
            render_brand_card(result)
        with summary_col:
            a, b, c, d = st.columns(4)
            a.metric("EcomScore", f"{result['pec_score']}/30")
            b.metric("Nivel PEC", result["classification"])
            c.metric("Confianza", result.get("confidence_label", "No disponible"), f"{result.get('confidence_score', 0)}/100")
            pages_reviewed = result.get("pages_reviewed", 0)
            d.metric("Cobertura de auditoría", coverage_label(pages_reviewed), f"{pages_reviewed}/15 páginas" if pages_reviewed else "Sin dato histórico")
        st.caption("EcomScore refleja preparación observable en la web; no mide ventas, utilidades ni éxito financiero de la empresa.")

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
        st.altair_chart(status_chart + labels, width="stretch")

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
        st.altair_chart(dimension_chart, width="stretch")
        with st.expander("Ver guía de interpretación", expanded=False):
            render_interpretation_tables()
        st.info(
            "Primero interpreta EcomScore y el Nivel PEC. La validación e-commerce solo confirma que la URL "
            "tiene señales mínimas de tienda online; no significa que el sitio tenga buen desempeño en los 30 FCE."
        )

        if result.get("qualification_status") == "weak":
            st.warning("La calificación e-commerce es débil; el PEC debe leerse como diagnóstico preliminar.")
        if result.get("confidence_label") == "Baja":
            st.warning("Confianza baja: no compare este puntaje directamente con auditorías de mayor cobertura.")
        q1, q2 = st.columns(2)
        q1.metric("Validación previa e-commerce", qualification_label(result.get("qualification_status", "qualified")))
        q2.metric("Señales comerciales", len(result.get("ecommerce_evidence", [])))
        st.caption("Esta validación es un filtro de entrada: confirma si corresponde auditarla como tienda, no reemplaza el puntaje PEC.")
        if result.get("ecommerce_evidence"):
            with st.expander("Evidencia e-commerce detectada"):
                for item in result["ecommerce_evidence"]:
                    st.write(f"- {item['label']} — {item['source_url']}")
        if result.get("confidence_reasons"):
            with st.expander("Razones de confianza"):
                for reason in result["confidence_reasons"]:
                    st.write(f"- {reason}")
        if result.get("ai_review"):
            with st.expander("Revisión metodológica IA"):
                st.write(result["ai_review"].get("summary", ""))
                for risk in result["ai_review"].get("risks", []):
                    st.write(f"- {risk}")
        if result["warnings"]:
            st.warning("Advertencias de exploración: " + " ".join(result["warnings"]))
        with st.expander("Metodología de la muestra"):
            st.write("La exploración revisa hasta 15 páginas públicas del mismo dominio. No inicia sesión ni recopila datos personales.")
            st.write(methodology_note())
        st.caption("T03 usa PageSpeed Insights cuando existe una API configurada; de lo contrario queda como no evaluable hasta confirmación manual.")


with tabs[2]:
    result = st.session_state.audit
    if not result:
        st.info("No hay factores para mostrar todavía.")
    else:
        st.subheader("Revisión de factores")
        dimensions = sorted({factor["dimension"] for factor in result["factors"]})
        filter_col1, filter_col2, filter_col3 = st.columns([1.2, 1.2, 1.6])
        selected_dimensions = filter_col1.multiselect(
            "Dimensión",
            dimensions,
            default=dimensions,
            help="Seleccione una o más dimensiones para revisar solo esos factores.",
        )
        options = ["present", "partial", "absent", "not_evaluable"]
        selected_statuses = filter_col2.multiselect(
            "Estado",
            options,
            default=options,
            format_func=status_short_label,
            help="Filtre por factores presentes, parciales, ausentes o no evaluables.",
        )
        search_value = filter_col3.text_input(
            "Buscar",
            placeholder="ID, nombre o evidencia",
            help="Ejemplo: T09, carrito, privacidad, checkout.",
        ).strip().lower()
        filtered_factors = [
            factor for factor in result["factors"]
            if factor["dimension"] in selected_dimensions
            and factor["status"] in selected_statuses
            and (
                not search_value
                or search_value in factor["id"].lower()
                or search_value in factor["name"].lower()
                or search_value in factor["evidence"].lower()
                or search_value in factor["source_url"].lower()
            )
        ]
        visible_counts = fce_counts(filtered_factors)
        metric_cols = st.columns(5)
        metric_cols[0].metric("Factores mostrados", len(filtered_factors))
        for column, row in zip(metric_cols[1:], visible_counts.to_dict("records")):
            column.metric(row["Estado"], row["Cantidad de FCE"])
        st.caption("El instrumento evalúa 30 FCE en total; aquí se muestran los que coinciden con los filtros aplicados.")
        st.info("Si no estás conforme con el hallazgo, cambia el resultado y deja una justificación verificable. Ejemplo: 'La política de devolución sí aparece en /devoluciones'.")
        st.download_button(
            "Descargar informe PDF completo",
            build_pdf(result),
            file_name=f"pec_auditoria_{st.session_state.audit_id or 'actual'}.pdf",
            mime="application/pdf",
            key="pdf_full_factors",
        )
        if not filtered_factors:
            st.warning("No hay factores que coincidan con los filtros seleccionados.")
        else:
            with st.form("factor_corrections"):
                corrections: dict[str, dict] = {}
                for dimension in [item for item in dimensions if item in selected_dimensions]:
                    dimension_factors = [item for item in filtered_factors if item["dimension"] == dimension]
                    if not dimension_factors:
                        continue
                    st.markdown(f"**{dimension}**")
                    for factor in dimension_factors:
                        factor_score = {"present": 1, "partial": 0.5, "absent": 0, "not_evaluable": 0}.get(factor["status"], 0)
                        title = (
                            f"<div class='pec-factor-head'>"
                            f"<span class='pec-factor-title'>{factor['id']} - {factor['name']}</span>"
                            f"{state_pill(factor['status'])}"
                            f"<span class='pec-factor-score'>{factor_score} punto(s)</span>"
                            f"</div>"
                        )
                        with st.expander(f"{factor['id']} - {factor['name']} | {status_label(factor['status'])}"):
                            st.markdown(title, unsafe_allow_html=True)
                            st.write(f"Evidencia: {factor['evidence']}")
                            st.caption(f"Fuente: {factor['source_url']}")
                            st.caption(f"Criterio usado: {criterion_example(factor)}")
                            selected = st.selectbox(
                                "Resultado correcto del factor",
                                options,
                                index=options.index(factor["status"]),
                                format_func=status_label,
                                key=f"state_{factor['id']}",
                                help="Déjalo igual si el hallazgo automático es correcto. Cámbialo solo si revisaste evidencia pública.",
                            )
                            note = st.text_input(
                                "Justificación o enlace revisado",
                                value=factor.get("manual_correction") or "",
                                key=f"note_{factor['id']}",
                                placeholder="Ejemplo: La política de devoluciones sí aparece en /devoluciones.",
                                help="Incluye la URL, sección o razón concreta del cambio para mantener trazabilidad.",
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
        recommendations = RecommendationAgent().generate(result["factors"])
        impact_options = ["Compra", "Confianza", "Operacion", "Experiencia", "Otros"]
        status_options = ["absent", "partial", "not_evaluable"]
        priority_options = ["Alta", "Media", "Revision"]
        f1, f2, f3, f4 = st.columns([1, 1, 1, 1.4])
        selected_impacts = f1.multiselect("Impacto", impact_options, default=impact_options)
        selected_gap_statuses = f2.multiselect(
            "Estado",
            status_options,
            default=status_options,
            format_func=status_short_label,
        )
        selected_priorities = f3.multiselect("Prioridad", priority_options, default=priority_options)
        gap_search = f4.text_input("Buscar brecha", placeholder="FCE, evidencia, recomendación o primer paso").strip().lower()
        filtered_recommendations = [
            item for item in recommendations
            if item.get("impact_group") in selected_impacts
            and item.get("status") in selected_gap_statuses
            and item.get("priority") in selected_priorities
            and (
                not gap_search
                or gap_search in item.get("factor_id", "").lower()
                or gap_search in item.get("factor", "").lower()
                or gap_search in item.get("recommendation", "").lower()
                or gap_search in item.get("evidence", "").lower()
                or gap_search in item.get("first_step", "").lower()
            )
        ]
        critical = [item for item in filtered_recommendations if item.get("priority") == "Alta"]
        not_evaluable = [item for item in filtered_recommendations if item.get("status") == "not_evaluable"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Brechas críticas", len(critical))
        c2.metric("Requieren revisión", len(not_evaluable))
        c3.metric("Recomendaciones visibles", len(filtered_recommendations))
        st.caption("Las prioridades se ordenan por impacto en compra, confianza, operación y experiencia.")
        st.download_button(
            "Descargar PDF de brechas",
            build_recommendations_pdf(result, filtered_recommendations),
            file_name=f"pec_brechas_{st.session_state.audit_id or 'actual'}.pdf",
            mime="application/pdf",
            key="pdf_recommendations",
        )

        st.subheader("Vista tabular de brechas")
        if filtered_recommendations:
            rows = [
                {
                    "Prioridad": item.get("priority", "Media"),
                    "Impacto": item.get("impact_group", "Otros"),
                    "FCE": f"{item.get('factor_id', '')} - {item.get('factor', '')}",
                    "Estado": status_label(item.get("status", "absent")),
                    "Evidencia": item.get("evidence", ""),
                    "Acción propuesta": item.get("recommendation", ""),
                    "Primer paso": item.get("first_step", ""),
                }
                for item in filtered_recommendations
            ]
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.warning("No hay brechas que coincidan con los filtros seleccionados.")

        for group in ["Compra", "Confianza", "Operacion", "Experiencia", "Otros"]:
            group_items = [item for item in filtered_recommendations if item.get("impact_group") == group]
            if not group_items:
                continue
            st.subheader(group)
            for item in group_items:
                with st.expander(f"{item.get('priority', 'Media')} | {item.get('factor_id', '')} - {item.get('factor', '')} | {status_label(item.get('status', 'absent'))}"):
                    st.write(f"**Qué falta:** {item.get('recommendation', 'Revisar este factor.')}")
                    st.write(f"**Por qué importa:** {item.get('reason', 'Este factor mejora la preparación observable del canal e-commerce.')}")
                    st.write(f"**Evidencia:** {item.get('evidence', 'No disponible')}")
                    st.write(f"**Primer paso:** {item.get('first_step', 'Revisar y completar evidencia pública verificable.')}")
                    st.caption(f"Fuente: {item.get('source_url', 'No disponible')}")


with tabs[5]:
    st.subheader("En qué consiste EcomScore")
    st.markdown(
        f"""
        <div class="pec-section-note">
            EcomScore es una herramienta académica para revisar, de forma transparente, qué tan preparado
            está un sitio e-commerce según evidencia pública observable. La app no entra a cuentas privadas,
            no compra productos y no recopila datos personales; solo revisa páginas públicas del mismo dominio.
            <br><br>{methodology_note()}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Qué buscamos como grupo")
    st.markdown(
        """
        <div class="pec-two-col">
            <div class="pec-info-card">
                <strong>Objetivo</strong><br>
                Construir un diagnóstico reproducible para comparar tiendas e-commerce sin depender de opiniones subjetivas.
            </div>
            <div class="pec-info-card">
                <strong>Resultado esperado</strong><br>
                Identificar fortalezas, brechas y prioridades de mejora en compra, confianza, operación y experiencia.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Por qué usamos 30 FCE")
    st.markdown(
        """
        <div class="pec-section-note">
            Los 30 factores críticos de éxito son una versión operativa del marco académico: se eligieron porque
            pueden revisarse desde una web pública con evidencia trazable. No representan todos los factores de
            gestión interna de una empresa; por eso la matriz TOEC completa queda como referencia teórica.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.subheader("Fuente académica de los FCE")
    st.write(
        "La selección de factores se sustenta en el informe y revisión académica de factores de éxito en "
        "rendimiento e-commerce. En esta app, esos factores se operacionalizan como 30 FCE observables desde "
        "la web pública para mantener trazabilidad y reproducibilidad."
    )
    st.markdown(
        """
        <div class="pec-info-card">
            <strong>Cita base:</strong> <em>Ten Years of SME E-Commerce Performance Factors: a systematic review.</em><br>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Cómo interpretar el resultado")
    st.write(
        "El puntaje PEC mide preparación observable, no ventas ni éxito financiero. Por eso ahora se muestra junto "
        "con una calificación de confianza: una auditoría con pocas páginas revisadas o señales débiles de "
        "e-commerce debe leerse como preliminar."
    )


with tabs[4]:
    history = list_audits()
    if not history:
        st.info("Aún no existen auditorías guardadas localmente.")
    else:
        st.caption(f"{len(history)} auditorías guardadas en la base de datos local SQLite.")
        st.dataframe(
            pd.DataFrame(history).rename(columns={"id": "ID", "created_at": "Fecha UTC", "url": "URL", "pages_reviewed": "Páginas", "pec_score": "PEC", "classification": "Nivel"}),
            width="stretch",
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
