# generate_pdf.py
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
import datetime
import os


# ---------- Helpers ----------

def _fmt(val):
    """Nicely format numbers; fallback to str for non-numerics."""
    if val is None:
        return "-"
    try:
        f = float(val)
        return str(int(f)) if f.is_integer() else f"{f:.2f}"
    except Exception:
        return str(val)

def _maybe_logo(flow, logo_path):
    """Add a logo if it exists; keep aspect ratio (no distortion)."""
    if not logo_path or not os.path.exists(logo_path):
        return
    try:
        img = Image(logo_path)
        # keep aspect ratio within max box
        max_w, max_h = 2.8 * inch, 0.9 * inch
        img._restrictSize(max_w, max_h)
        flow.append(img)
        flow.append(Spacer(1, 8))
    except Exception:
        # ignore if unreadable
        pass

def _kv(flow, label, value, styles):
    flow.append(Paragraph(f"<b>{label}:</b> {_fmt(value)}", styles["Normal"]))

def _section_title(text, styles):
    return Paragraph(text, styles["Heading2"])

def _table(data, col_widths=None, header_bg=colors.lightgrey, align_right_cols=None, valign="TOP"):
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    style_cmds = [
        ('BACKGROUND', (0,0), (-1,0), header_bg),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), valign),
    ]
    if align_right_cols:
        for c in align_right_cols:
            style_cmds.append(('ALIGN', (c,1), (c,-1), 'RIGHT'))
    t.setStyle(TableStyle(style_cmds))
    return t


# ---------- Main builder ----------

def create_pdf_report(
    filename,
    patient_data,
    diagnosis,
    phenotype,
    treatment_notes,
    *,
    logo_path="2.jpg",                        # change if your logo is elsewhere
    clinic_name="Clinics Northside",
    doctor_line="Dr. Arshad Mohammed, MD",
    whatsapp_link="https://wa.me/?text=I%20want%20to%20join%20the%20PCOS%20program"
):
    """
    Build a branded, evidence-backed PCOS report.

    Parameters
    ----------
    filename : str
        Output PDF path.
    patient_data : dict
        Keys (expected):
          - name (str)
          - age (num/str)
          - bmi (num/str)
          - criteria (dict[str,bool])              # optional
          - alerts (list[str])                     # optional
          - labs (list[dict])                      # optional; each: {name, value, unit, range?, reference?}
          - meal_plan (list[dict])                 # optional; 7-day plan rows: {Day, Breakfast, Lunch, Snack, Dinner}
          - references (list[str])                 # optional
    diagnosis : str
    phenotype : str
    treatment_notes : list[str]
    logo_path : str
    clinic_name : str
    doctor_line : str
    whatsapp_link : str
    """

    # --- Doc & styles ---
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=36,
        bottomMargin=36,
        title="MyPCOS AI – Powered by Clinics Northside"
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="Tiny", fontSize=8, leading=10))
    TitlePink = ParagraphStyle(
        "TitlePink", parent=styles["Title"], textColor=colors.HexColor("#d63384"), leading=22, spaceAfter=6
    )

    flow = []

    # --- Brand/Header ---
    _maybe_logo(flow, logo_path)
    flow.append(Paragraph("MyPCOS AI – Powered by Clinics Northside™", TitlePink))
    flow.append(Paragraph(f"Date: {datetime.date.today().strftime('%B %d, %Y')}", styles["Normal"]))
    flow.append(Spacer(1, 6))

    # Patient details
    _kv(flow, "Patient Name", patient_data.get("name", ""), styles)
    _kv(flow, "Age", patient_data.get("age", ""), styles)
    _kv(flow, "BMI", patient_data.get("bmi", ""), styles)
    flow.append(Spacer(1, 8))

    # --- Diagnosis Summary ---
    flow.append(_section_title("Diagnosis Summary", styles))
    flow.append(Paragraph(f"<b>Assessment:</b> {diagnosis}", styles["Normal"]))
    flow.append(Paragraph(f"<b>PCOS Phenotype:</b> {phenotype}", styles["Normal"]))
    if isinstance(diagnosis, str) and diagnosis.lower().startswith("pcos"):
        flow.append(Paragraph(
            "Diagnosis based on ≥2 of the Rotterdam criteria: oligo/anovulation, clinical/biochemical hyperandrogenism, and polycystic ovaries.",
            styles["Small"]
        ))
    flow.append(Spacer(1, 8))

    # --- Evidence Summary ---
    criteria = patient_data.get("criteria", {})
    alerts = patient_data.get("alerts", [])
    if criteria or alerts:
        flow.append(_section_title("Evidence Summary", styles))

        # Criteria table
        if criteria:
            # Order columns as standard
            ordered = ["Oligo/anovulation", "Hyperandrogenism", "Polycystic ovaries"]
            table_rows = [["Criterion", "Met?"]]
            for k in ordered:
                if k in criteria:
                    table_rows.append([k, "Yes" if criteria[k] else "No"])
            crit_table = _table(table_rows, col_widths=[300, 80], align_right_cols=None)
            flow.append(crit_table)
            flow.append(Spacer(1, 6))

        # Alerts
        if alerts:
            flow.append(Paragraph("<b>Clinical / Lab Alerts:</b>", styles["Normal"]))
            for a in alerts:
                flow.append(Paragraph(f"• {_fmt(a)}", styles["Normal"]))
            flow.append(Spacer(1, 6))

    # --- Lab Results ---
    labs = patient_data.get("labs", [])
    if labs:
        flow.append(_section_title("Lab Results", styles))
        # Build columns dynamically if reference range present
        have_range = any("range" in l and l.get("range") for l in labs)
        have_refcol = any("reference" in l and l.get("reference") for l in labs)

        headers = ["Test", "Value", "Units"]
        if have_range:
            headers.append("Ref. Range")
        if have_refcol:
            headers.append("Evidence/Notes")

        lab_rows = [headers]
        for l in labs:
            row = [l.get("name", ""), _fmt(l.get("value", "")), l.get("unit", "")]
            if have_range:
                row.append(l.get("range", ""))
            if have_refcol:
                row.append(l.get("reference", ""))
            lab_rows.append(row)

        # Widths tuned for A4; adjust as needed
        col_widths = [180, 70, 60]
        if have_range: col_widths.append(90)
        if have_refcol: col_widths.append(140)

        lab_table = _table(lab_rows, col_widths=col_widths, align_right_cols=[1])
        flow.append(lab_table)
        flow.append(Spacer(1, 8))

    # --- Nutrition Plan (7 days) ---
    meal_plan = patient_data.get("meal_plan", [])
    if meal_plan:
        flow.append(_section_title("Nutrition Plan (7 days)", styles))
        plan_rows = [["Day", "Breakfast", "Lunch", "Snack", "Dinner"]]
        for r in meal_plan:
            plan_rows.append([
                r.get("Day", ""),
                r.get("Breakfast", ""),
                r.get("Lunch", ""),
                r.get("Snack", ""),
                r.get("Dinner", "")
            ])
        plan_table = _table(
            plan_rows,
            col_widths=[45, 120, 120, 90, 120],
            align_right_cols=None,
            valign="TOP"
        )
        flow.append(plan_table)
        flow.append(Spacer(1, 6))
        flow.append(Paragraph(
            "Notes: Focus on low-GI, high-fiber foods. Portions may be adjusted to meet calorie targets and insulin resistance goals.",
            styles["Small"]
        ))
        flow.append(Spacer(1, 6))

    # --- Treatment Recommendations ---
    if treatment_notes:
        flow.append(_section_title("Treatment Recommendations", styles))
        for item in treatment_notes:
            flow.append(Paragraph(f"• {_fmt(item)}", styles["Normal"]))
        flow.append(Spacer(1, 8))

    # --- References (optional) ---
    refs = patient_data.get("references", [])
    if refs:
        flow.append(_section_title("References", styles))
        for i, r in enumerate(refs, 1):
            flow.append(Paragraph(f"{i}. {r}", styles["Small"]))
        flow.append(Spacer(1, 6))

    # --- Footer / Contact ---
    flow.append(Paragraph(_fmt(doctor_line), styles["Normal"]))
    flow.append(Paragraph(_fmt(clinic_name), styles["Normal"]))
    if whatsapp_link:
        flow.append(Spacer(1, 6))
        flow.append(Paragraph(
            f"<a href='{whatsapp_link}'>📲 WhatsApp to enroll in PCOS coaching</a>",
            styles["Normal"]
        ))

    # Build
    doc.build(flow)
