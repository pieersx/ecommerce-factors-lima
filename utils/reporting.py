"""Reporte PDF local de una auditoría PEC."""

from __future__ import annotations

from html import escape
from io import BytesIO

import requests
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _status_label(status: str) -> str:
    return {
        "present": "Presente",
        "partial": "Parcial",
        "absent": "Ausente",
        "not_evaluable": "No evaluable",
    }.get(status, status)


def _safe_logo(logo_url: str):
    if not logo_url or logo_url.lower().endswith(".svg"):
        return None
    try:
        response = requests.get(logo_url, timeout=8)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        if not any(kind in content_type for kind in ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/x-icon", "image/vnd.microsoft.icon"]):
            return None
        image = Image(BytesIO(response.content), width=2.2 * cm, height=2.2 * cm)
        image.hAlign = "LEFT"
        return image
    except Exception:
        return None


def _brand_header(result: dict, title: str, subtitle: str, styles) -> list:
    brand = result.get("brand_assets", {}) or {}
    brand_name = brand.get("brand_name") or brand.get("site_domain") or "Marca auditada"
    domain = brand.get("site_domain") or result.get("url", "")
    logo = _safe_logo(brand.get("logo_url", ""))
    text = [
        Paragraph(title, styles["Title"]),
        Paragraph(f"{brand_name} | {domain}", styles["Heading2"]),
        Paragraph(subtitle, styles["BodyText"]),
    ]
    if logo:
        table = Table([[logo, text]], colWidths=[2.6 * cm, 12.2 * cm])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        return [table, Spacer(1, 0.25 * cm)]
    return text + [Spacer(1, 0.25 * cm)]


def build_pdf(result: dict) -> bytes:
    stream = BytesIO()
    document = SimpleDocTemplate(stream, pagesize=A4, rightMargin=1.3 * cm, leftMargin=1.3 * cm, topMargin=1.2 * cm)
    styles = getSampleStyleSheet()
    flow = _brand_header(
        result,
        "PEC Auditor - Informe de diagnóstico TOEC",
        (
            f"Calificación e-commerce: {result.get('qualification_status', 'qualified')} | "
            f"Confianza: {result.get('confidence_label', 'No disponible')} "
            f"({result.get('confidence_score', 0)}/100) | "
            f"Páginas revisadas: {result.get('pages_reviewed', 0)}/15 | URL: {result['url']}"
        ),
        styles,
    )
    flow.extend([
        Paragraph(
            "Nota metodológica: la auditoría revisa hasta 15 páginas públicas del mismo dominio como muestra "
            "acotada, reproducible y no invasiva. El índice usa 30 FCE núcleo observables públicamente; "
            "la matriz TOEC completa queda como referencia académica.",
            styles["BodyText"],
        ),
        Spacer(1, 0.25 * cm),
    ])
    dimensions = [["Dimensión", "Puntaje"]] + [
        [name, f"{value['score']}/{value['max']}"] for name, value in result["dimension_scores"].items()
    ]
    table = Table(dimensions, colWidths=[10.5 * cm, 4 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    flow.extend([table, Spacer(1, 0.35 * cm), Paragraph("Factores y evidencia", styles["Heading2"])])
    factor_rows = [["FCE", "Estado", "Evidencia"]] + [
        [f"{factor['id']} {factor['name']}", factor["status"], factor["evidence"]]
        for factor in result["factors"]
    ]
    factor_table = Table(factor_rows, colWidths=[4.2 * cm, 2.2 * cm, 8.1 * cm], repeatRows=1)
    factor_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.2, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
    ]))
    flow.append(factor_table)
    document.build(flow)
    return stream.getvalue()


def build_recommendations_pdf(result: dict, recommendations: list[dict]) -> bytes:
    stream = BytesIO()
    document = SimpleDocTemplate(
        stream,
        pagesize=A4,
        rightMargin=1.15 * cm,
        leftMargin=1.15 * cm,
        topMargin=1.15 * cm,
        bottomMargin=1.15 * cm,
    )
    styles = getSampleStyleSheet()
    body_small = ParagraphStyle(
        "BodySmall",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
        spaceAfter=0,
    )
    cell_text = ParagraphStyle(
        "CellText",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
        spaceAfter=0,
    )
    header_text = ParagraphStyle(
        "HeaderText",
        parent=styles["BodyText"],
        fontSize=8,
        leading=9,
        textColor=colors.white,
        spaceAfter=0,
    )
    critical = [item for item in recommendations if item.get("priority") == "Alta"]
    review = [item for item in recommendations if item.get("status") == "not_evaluable"]
    flow = _brand_header(
        result,
        "PEC Auditor - Brechas y recomendaciones",
        (
            f"PEC: {result['pec_score']}/30 - Nivel: {result['classification']} | "
            f"Confianza: {result.get('confidence_label', 'No disponible')} "
            f"({result.get('confidence_score', 0)}/100) | "
            f"Cobertura: {result.get('pages_reviewed', 0)}/15 páginas | URL: {result['url']}"
        ),
        styles,
    )
    flow.extend([
        Paragraph(
            f"Resumen: {len(critical)} brecha(s) crítica(s), {len(review)} factor(es) por revisar, "
            f"{len(recommendations)} recomendación(es) en total.",
            styles["Heading2"],
        ),
        Spacer(1, 0.2 * cm),
    ])
    for group in ["Compra", "Confianza", "Operacion", "Experiencia", "Otros"]:
        items = [item for item in recommendations if item.get("impact_group") == group]
        if not items:
            continue
        flow.append(Paragraph(group, styles["Heading2"]))
        for item in items:
            fce = f"{item.get('factor_id', '')} {item.get('factor', '')}".strip()
            details = (
                f"<b>Evidencia:</b> {escape(item.get('evidence', 'No disponible'))}<br/>"
                f"<b>Por qué importa:</b> {escape(item.get('reason', 'No disponible'))}<br/>"
                f"<b>Primer paso:</b> {escape(item.get('first_step', 'No disponible'))}"
            )
            card = Table(
                [
                    [
                        Paragraph(f"<b>{escape(fce)}</b>", header_text),
                        Paragraph(f"<b>Estado:</b> {escape(_status_label(item.get('status', '')))}", header_text),
                        Paragraph(f"<b>Prioridad:</b> {escape(item.get('priority', 'Media'))}", header_text),
                    ],
                    [Paragraph(details, cell_text), "", ""],
                ],
                colWidths=[8.2 * cm, 3.2 * cm, 3.4 * cm],
                hAlign="LEFT",
            )
            card.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f8fafc")),
                ("SPAN", (0, 1), (-1, 1)),
                ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, 0), 0.25, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            flow.append(KeepTogether([card, Spacer(1, 0.16 * cm)]))
    document.build(flow)
    return stream.getvalue()
