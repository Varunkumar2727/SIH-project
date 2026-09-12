import os
import time
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)

class GovernmentReportGenerator:
    """
    Part 8: Government-Ready Reporting Engine.
    Generates official, highly structured PDF reports using ReportLab.
    Strictly complies with legal/survey disclaimers and provenance standards.
    """

    @classmethod
    def generate_project_dossier(
        cls,
        output_pdf_path: str,
        project_meta: Dict[str, Any],
        parcel_data: Optional[List[Dict[str, Any]]] = None,
        change_data: Optional[List[Dict[str, Any]]] = None,
        review_data: Optional[List[Dict[str, Any]]] = None,
        gcp_meta: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generates the Consolidated Land Intelligence Dossier PDF.
        """
        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "GovTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            alignment=1
        )
        subtitle_style = ParagraphStyle(
            "GovSub",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569"),
            alignment=1
        )
        h2_style = ParagraphStyle(
            "GovH2",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "GovBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155")
        )
        disclaimer_style = ParagraphStyle(
            "GovDisclaimer",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#b91c1c")
        )

        story = []

        # 1. Header & Seal block
        story.append(Paragraph("GEOCADASTRAL AI — LAND INTELLIGENCE DOSSIER", title_style))
        story.append(Paragraph("SURVEY & REVENUE DECISION-SUPPORT SYSTEM", subtitle_style))
        story.append(Spacer(1, 10))

        # 2. Metadata Table
        proj_id = project_meta.get("project_id", "PROJ-DEFAULT")
        crs_str = project_meta.get("crs", "EPSG:4326")
        gen_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        meta_rows = [
            ["Project Identifier:", proj_id, "Generated Date:", gen_time],
            ["Geodetic Reference (CRS):", str(crs_str), "Georeference Mode:", project_meta.get("georeferencing_method", "GeoTIFF/GCP")],
            ["AI Model Version:", "GeoCadastral v1.0 (ONNX)", "Classification Level:", "OFFICIAL / SURVEY GRADE"]
        ]
        t_meta = Table(meta_rows, colWidths=[130, 140, 120, 130])
        t_meta.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1e293b")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_meta)
        story.append(Spacer(1, 12))

        # 3. Statutory Legal Disclaimer
        disclaimer_text = (
            "<b>STATUTORY NOTICE & SURVEY POSITIONING:</b> This document provides AI-assisted analytical "
            "delineations, physical access indicators, and temporal change detections for technical verification. "
            "It does NOT constitute legal land title, guarantee deed ownership, or replace authoritative field boundary "
            "settlement. All proposed boundaries and discrepancy cues require survey officer verification."
        )
        story.append(Paragraph(disclaimer_text, disclaimer_style))
        story.append(Spacer(1, 14))

        # 4. Section: Parcel Intelligence Summary
        story.append(Paragraph("1. Parcel Intelligence & Frontage Evaluation", h2_style))
        parcels = parcel_data or []
        parcel_rows = [["Parcel ID", "Area (px)", "Compactness", "Frontage Status", "Confidence"]]
        for p in parcels[:8]: # Top items
            acc = p.get("accessibility", {})
            parcel_rows.append([
                p.get("id", "P-?"),
                str(p.get("area_px", "0")),
                str(p.get("compactness", "N/A")),
                acc.get("access_status", "UNASSESSED"),
                f"{round(float(p.get('confidence', 0.8))*100, 1)}%"
            ])
        if len(parcels) == 0:
            parcel_rows.append(["No parcels registered", "-", "-", "-", "-"])

        t_parcel = Table(parcel_rows, colWidths=[140, 90, 90, 130, 70])
        t_parcel.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_parcel)
        story.append(Spacer(1, 14))

        # 5. Section: Temporal Land Changes
        story.append(Paragraph("2. Temporal Land Change Intelligence", h2_style))
        changes = change_data or []
        change_rows = [["Change ID", "Classification", "Area Delta (px)", "Confidence", "Review State"]]
        for c in changes[:8]:
            change_rows.append([
                c.get("change_id", "CHG-?"),
                c.get("change_type", "UNKNOWN"),
                str(c.get("area_delta_px", "0")),
                f"{round(float(c.get('confidence', 0.8))*100, 1)}%",
                c.get("status", "UNREVIEWED")
            ])
        if len(changes) == 0:
            change_rows.append(["No temporal changes detected", "-", "-", "-", "-"])

        t_change = Table(change_rows, colWidths=[120, 140, 90, 80, 90])
        t_change.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0369a1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_change)
        story.append(Spacer(1, 14))

        # 6. Section: Survey Verification & Signature Block
        story.append(KeepTogether([
            Paragraph("3. Survey Officer Attestation & Verification Record", h2_style),
            Spacer(1, 10),
            Table([
                ["Reviewed By (Officer ID):", "___________________________", "Date:", "___________________"],
                ["Designation / Revenue Circle:", "___________________________", "Signature:", "___________________"],
                ["Verification Decision:", "[  ] CONFIRMED    [  ] REJECTED    [  ] FIELD VERIFICATION REQUIRED", "", ""]
            ], colWidths=[150, 150, 80, 140], style=[
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("PADDING", (0, 0), (-1, -1), 6)
            ])
        ]))

        doc.build(story)
        return output_pdf_path
