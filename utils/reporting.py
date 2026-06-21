"""Reporte PDF local de una auditoría PEC."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf(result: dict) -> bytes:
    stream = BytesIO()
    document = SimpleDocTemplate(stream, pagesize=A4, rightMargin=1.3 * cm, leftMargin=1.3 * cm, topMargin=1.2 * cm)
    styles = getSampleStyleSheet()
    flow = [
        Paragraph("PEC Auditor - Informe de diagnóstico TOEC", styles["Title"]),
        Paragraph(f"URL auditada: {result['url']}", styles["BodyText"]),
        Paragraph(f"Índice PEC: {result['pec_score']}/30 - Nivel: {result['classification']}", styles["Heading2"]),
        Spacer(1, 0.25 * cm),
    ]
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
