# generate_pdf.py
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
import datetime, os

# =================== helpers ===================

def _fmt(x):
    if x is None: return "-"
    try:
        f = float(x)
        return str(int(f)) if f.is_integer() else f"{f:.2f}"
    except Exception:
        return str(x)

def _find_file(preferred, fallbacks):
    cands = []
    if preferred: cands.append(preferred)
    cands += fallbacks
    here = os.path.dirname(os.path.abspath(__file__))
    cands += [os.path.join(here, p) for p in cands]
    for p in cands:
        if p and os.path.exists(p):
            return p
    return None

def _bmi_note(bmi):
    try: b = float(bmi)
    except Exception: return None
    if b < 18.5: cls = "Underweight"
    elif b < 23: cls = "Normal (Asian cut-off)"
    elif b < 25: cls = "Overweight (Asian)"
    else: cls = "Obese (Asian)"
    return f"BMI classification: {cls}. Weight management can improve ovulation and insulin sensitivity in PCOS."

def _h2(text, styles): return Paragraph(text, styles["Heading2"])
def _kv(flow, label, value, styles): flow.append(Paragraph(f"<b>{label}:</b> {_fmt(value)}", styles["Normal"]))

def _table(data, widths=None, align_right_cols=None):
    t = Table(data, colWidths=widths, hAlign="LEFT")
    style = [
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]
    if align_right_cols:
        for c in align_right_cols:
            style.append(('ALIGN', (c,1), (c,-1), 'RIGHT'))
    t.setStyle(TableStyle(style))
    return t

# ============== header / footer drawing ==============

def _draw_header(canvas: Canvas, doc, logo_path, title_style_color="#d63384"):
    canvas.saveState()
    w, h = A4
    left, right = 40, w - 40
    top = h - 30

    # light divider
    canvas.setStrokeColor(colors.lightgrey)
    canvas.setLineWidth(0.3)
    canvas.line(left, top-28, right, top-28)

    # logo (left)
    path = _find_file(logo_path, [
        "assets/logo_clinics_northside.png", "assets/logo.png",
        "assets/logo.jpg", "logo.png", "logo.jpg", "2.jpg"
    ])
    if path:
        try:
            canvas.drawImage(
                path, left, top-22, width=110, height=22,
                preserveAspectRatio=True, mask='auto'
            )
        except Exception:
            pass

    # title (center)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.setFillColor(colors.HexColor(title_style_color))
    canvas.drawCentredString(w/2, top-18, "MyPCOS AI – Powered by Clinics Northside™")
    canvas.restoreState()

def _draw_footer(canvas: Canvas, doc, footer_text="Clinics Northside | Confidential | www.clinicsnorthside.com"):
    canvas.saveState()
    w, h = A4
    left, right = 40, w - 40

    canvas.setStrokeColor(colors.lightgrey)
    canvas.setLineWidth(0.3)
    canvas.line(left, 42, right, 42)

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawString(left, 30, footer_text)
    canvas.drawRightString(right, 30, f"Page {doc.page}")
    canvas.restoreState()

# =================== main ===================

def create_pdf_report(
    filename,
    patient_data,
    diagnosis,
    phenotype,
    treatment_notes,
    *,
    logo_path="assets/logo_clinics_northside.png",
    clinic_name="Clinics Northside",
    doctor_line="Dr. Arshad Mohammed, MD",
    footer_text="Clinics Northside | Confidential | www.clinicsnorthside.com",
    whatsapp_link="https://wa.me/?text=I%20want%20to%20join%20the%20PCOS%20program",
    whatsapp_qr_path=None    # optional PNG path
):
    """
    patient_data expected keys (optional ones marked *):
      name, age, bmi,
      criteria*: dict[str,bool]             # {"Oligo/anovulation": True, ...}
      alerts*  : list[str]
      labs*    : list[{name,value,unit,range*,reference*}]
      meal_plan*: list[{Day,Breakfast,Lunch,Snack,Dinner}]
      references*: list[str]
    """

    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=12))
    TitlePink = ParagraphStyle("TitlePink", parent=styles["Title"], textColor=colors.HexColor("#d63384"))

    # Document with header+footer on every page
    top_band = 45
    bottom_band = 55
    doc = BaseDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=40, rightMargin=40,
        topMargin=40 + top_band, bottomMargin=bottom_band + 10,
        title="MyPCOS AI – Powered by Clinics Northside"
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='body')
    page_tmpl = PageTemplate(
        id='with-bands',
        frames=[frame],
        onPage=lambda c, d: (_draw_header(c, d, logo_path), _draw_footer(c, d, footer_text))
    )
    doc.addPageTemplates([page_tmpl])

    flow = []

    # Patient header
    flow.append(Paragraph(f"Date: {datetime.date.today().strftime('%B %d, %Y')}", styles["Normal"]))
    flow.append(Spacer(1, 4))
    _kv(flow, "Patient Name", patient_data.get("name", ""), styles)
    _kv(flow, "Age", patient_data.get("age", ""), styles)
    _kv(flow, "BMI", patient_data.get("bmi", ""), styles)
    note = _bmi_note(patient_data.get("bmi"))
    if note: flow.append(Paragraph(note, styles["Small"]))
    flow.append(Spacer(1, 8))

    # Diagnosis summary
    flow.append(_h2("Diagnosis Summary", styles))
    flow.append(Paragraph(f"<b>Assessment:</b> {diagnosis}", styles["Normal"]))
    flow.append(Paragraph(f"<b>PCOS Phenotype:</b> {phenotype}", styles["Normal"]))
    if isinstance(diagnosis, str) and diagnosis.lower().startswith("pcos"):
        flow.append(Paragraph(
            "Diagnosis based on ≥2 Rotterdam criteria: oligo/anovulation, clinical/biochemical hyperandrogenism, and polycystic ovaries.",
            styles["Small"]
        ))
    flow.append(Spacer(1, 8))

    # Evidence Summary
    criteria = patient_data.get("criteria", {})
    alerts = patient_data.get("alerts", [])
    if criteria or alerts:
        flow.append(_h2("Evidence Summary", styles))
        if criteria:
            ordered = ["Oligo/anovulation", "Hyperandrogenism", "Polycystic ovaries"]
            rows = [["Criterion", "Met?"]]
            for k in ordered:
                if k in criteria:
                    rows.append([k, "Yes" if criteria[k] else "No"])
            flow.append(_table(rows, widths=[300, 80]))
            flow.append(Spacer(1, 6))
        if alerts:
            flow.append(Paragraph("<b>Clinical / Lab Alerts:</b>", styles["Normal"]))
            for a in alerts: flow.append(Paragraph(f"• {_fmt(a)}", styles["Normal"]))
            flow.append(Spacer(1, 6))

    # Lab Results (with optional ranges/evidence)
    labs = patient_data.get("labs", [])
    if labs:
        flow.append(_h2("Lab Results", styles))
        have_range = any(l.get("range") for l in labs)
        have_ref   = any(l.get("reference") for l in labs)
        header = ["Test", "Value", "Units"]
        if have_range: header.append("Normal Range")
        if have_ref:   header.append("Evidence / Notes")
        rows = [header]
        for l in labs:
            r = [l.get("name",""), _fmt(l.get("value","")), l.get("unit","")]
            if have_range: r.append(l.get("range",""))
            if have_ref:   r.append(l.get("reference",""))
            rows.append(r)
        widths = [170, 60, 55]
        if have_range: widths.append(95)
        if have_ref:   widths.append(150)
        flow.append(_table(rows, widths=widths, align_right_cols=[1]))
        flow.append(Spacer(1, 8))

    # Nutrition Plan (optional)
    meal_plan = patient_data.get("meal_plan", [])
    if meal_plan:
        flow.append(_h2("Nutrition Plan (7 days)", styles))
        plan_rows = [["Day", "Breakfast", "Lunch", "Snack", "Dinner"]]
        for r in meal_plan:
            plan_rows.append([r.get("Day",""), r.get("Breakfast",""), r.get("Lunch",""),
                              r.get("Snack",""), r.get("Dinner","")])
        flow.append(_table(plan_rows, widths=[45, 120, 120, 90, 120]))
        flow.append(Spacer(1, 6))
        flow.append(Paragraph("Low-GI, high-fiber focus. Portions may be adjusted to meet calorie targets and insulin-resistance goals.",
                              styles["Small"]))
        flow.append(Spacer(1, 6))

    # Treatment Recommendations
    if treatment_notes:
        flow.append(_h2("Treatment Recommendations", styles))
        for t in treatment_notes:
            flow.append(Paragraph(f"• {_fmt(t)}", styles["Normal"]))
        flow.append(Spacer(1, 6))

    # Next Steps (auto)
    follow_up = (datetime.date.today() + datetime.timedelta(days=90)).strftime("%b %d, %Y")
    flow.append(_h2("Next Steps", styles))
    for p in [
        "Recheck key labs (glucose/insulin, lipids, vitamin D) and cycles in 3 months.",
        "Prioritize sleep (7–8h), resistance training 2–3x/week, and stress reduction.",
        f"Suggested follow-up date: {follow_up}."
    ]:
        flow.append(Paragraph(f"• {p}", styles["Normal"]))
    flow.append(Spacer(1, 8))

    # References (optional)
    refs = patient_data.get("references", [])
    if refs:
        flow.append(_h2("References", styles))
        for i, r in enumerate(refs, 1):
            flow.append(Paragraph(f"{i}. {r}", styles["Small"]))
        flow.append(Spacer(1, 6))

    # Closing block
    flow.append(Paragraph(doctor_line, styles["Normal"]))
    flow.append(Paragraph(clinic_name, styles["Normal"]))
    if whatsapp_link:
        flow.append(Spacer(1, 4))
        flow.append(Paragraph(f"<a href='{whatsapp_link}'>📲 Join Coaching on WhatsApp</a>", styles["Normal"]))
    if whatsapp_qr_path:
        from reportlab.platypus import Image as PLImage
        path = _find_file(whatsapp_qr_path, ["assets/whatsapp_qr.png", "whatsapp_qr.png"])
        if path:
            flow.append(Spacer(1, 6))
            img = PLImage(path)
            img._restrictSize(2.0*inch, 2.0*inch)
            flow.append(img)

    doc.build(flow)
# === One-pager: Meal Plan Only PDF ==========================================
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
import datetime

def create_mealplan_pdf(
    filename,
    *,
    patient_name="",
    age=None,
    bmi=None,
    meal_plan=None,                 # list of dicts: Day, Breakfast, Lunch, Snack, Dinner
    calories_target=None,           # optional int
    logo_path="assets/logo_clinics_northside.png",
    footer_text="Clinics Northside | Confidential | www.clinicsnorthside.com",
    whatsapp_link=None,
    whatsapp_qr_path=None           # optional PNG path
):
    """
    Build a one-page, print-friendly Meal Plan PDF.
    Uses the same header/footer as the main report.
    """
    meal_plan = meal_plan or []

    # styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="Tiny", fontSize=8, leading=10))
    H2 = styles["Heading2"]

    # Page bands
    top_band = 45
    bottom_band = 55

    doc = BaseDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=40, rightMargin=40,
        topMargin=40 + top_band, bottomMargin=bottom_band + 10,
        title="MyPCOS AI – Meal Plan"
    )

    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    page_tmpl = PageTemplate(
        id="with-bands",
        frames=[frame],
        onPage=lambda c, d: (_draw_header(c, d, logo_path), _draw_footer(c, d, footer_text)),
    )
    doc.addPageTemplates([page_tmpl])

    # build
    flow = []

    # Header text
    today = datetime.date.today().strftime("%b %d, %Y")
    heading_bits = [f"Date: {today}"]
    if patient_name: heading_bits.append(f"Patient: {patient_name}")
    if age is not None: heading_bits.append(f"Age: {age}")
    if bmi is not None: heading_bits.append(f"BMI: {bmi}")
    flow.append(Paragraph(" | ".join(heading_bits), styles["Small"]))
    if calories_target:
        flow.append(Paragraph(f"Calorie target: <b>{calories_target} kcal/day</b>", styles["Small"]))
    flow.append(Spacer(1, 6))

    # Title
    flow.append(Paragraph("Nutrition Plan (7 days)", H2))

    # Table
    table_rows = [["Day", "Breakfast", "Lunch", "Snack", "Dinner"]]
    for r in meal_plan:
        table_rows.append([
            r.get("Day", ""),
            r.get("Breakfast", ""),
            r.get("Lunch", ""),
            r.get("Snack", ""),
            r.get("Dinner", ""),
        ])

    tbl = Table(table_rows, colWidths=[45, 120, 120, 90, 120], hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    flow.append(tbl)
    flow.append(Spacer(1, 8))

    # Notes
    flow.append(Paragraph(
        "Notes: Focus on low-GI, high-fiber foods. Adjust portions to meet targets and individual tolerance. "
        "Pair carbohydrates with protein/fat to blunt glycemic spikes.",
        styles["Small"]
    ))

    # WhatsApp CTA / QR (optional)
    if whatsapp_link:
        flow.append(Spacer(1, 6))
        flow.append(Paragraph(f"<a href='{whatsapp_link}'>📲 Join Coaching on WhatsApp</a>", styles["Small"]))
    if whatsapp_qr_path:
        from reportlab.platypus import Image as PLImage
        path = _find_file(whatsapp_qr_path, ["assets/whatsapp_qr.png", "whatsapp_qr.png"])
        if path:
            flow.append(Spacer(1, 6))
            img = PLImage(path)
            img._restrictSize(1.8 * inch, 1.8 * inch)
            flow.append(img)

    # Build
    doc.build(flow)

