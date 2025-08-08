# generate_pdf.py
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
import datetime, os

# ============== helpers ==============

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

def _maybe_logo(flow, logo_path):
    path = _find_file(logo_path, [
        "assets/logo_clinics_northside.png", "assets/logo.png",
        "assets/logo.jpg", "logo.png", "logo.jpg", "2.jpg"
    ])
    if not path: return
    try:
        img = Image(path)
        img._restrictSize(2.8*inch, 0.9*inch)  # keep aspect ratio
        flow.append(img); flow.append(Spacer(1, 8))
    except Exception:
        pass

def _maybe_qr(flow, qr_path):
    path = _find_file(qr_path, ["assets/whatsapp_qr.png", "whatsapp_qr.png"])
    if not path: return
    try:
        img = Image(path)
        img._restrictSize(2.0*inch, 2.0*inch)
        flow.append(img)
    except Exception:
        pass

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

def _bmi_note(bmi):
    try:
        b = float(bmi)
    except Exception:
        return None
    if b < 18.5: cls = "Underweight"
    elif b < 23: cls = "Normal (Asian cut-off)"
    elif b < 25: cls = "Overweight (Asian)"
    else: cls = "Obese (Asian)"
    return f"BMI classification: {cls}. Weight management can improve ovulation and insulin sensitivity in PCOS."

# ============== footer callbacks ==============

def _footer(canvas: Canvas, doc, footer_text="Clinics Northside | Confidential | www.clinicsnorthside.com"):
    canvas.saveState()
    w, h = A4
    # thin line above footer
    canvas.setStrokeColor(colors.lightgrey)
    canvas.setLineWidth(0.3)
    canvas.line(40, 30, w-40, 30)
    # footer text (left)
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawString(40, 18, footer_text)
    # page number (right)
    canvas.drawRightString(w-40, 18, f"Page {doc.page}")
    canvas.restoreState()

# ============== main ==============

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
    whatsapp_qr_path=None  # optional png path
):
    """
    patient_data keys:
      name, age, bmi,
      criteria* : dict[str,bool]
      alerts*   : list[str]
      labs*     : list[{name, value, unit, range*, reference*}]
      meal_plan*: list[{Day,Breakfast,Lunch,Snack,Dinner}]
      references*: list[str]
    """

    # Doc & styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=12))
    TitlePink = ParagraphStyle("TitlePink", parent=styles["Title"], textColor=colors.HexColor("#d63384"))

    # Create a BaseDocTemplate with a repeating footer
    doc = BaseDocTemplate(
        filename, pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=36, bottomMargin=50,
        title="MyPCOS AI – Powered by Clinics Northside"
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height-10, id='normal')
    template = PageTemplate(id='with-footer', frames=[frame],
                            onPage=lambda c, d: _footer(c, d, footer_text))
    doc.addPageTemplates([template])

    flow = []

    # Header & brand
    _maybe_logo(flow, logo_path)
    flow.append(Paragraph("MyPCOS AI – Powered by Clinics Northside™", TitlePink))
    flow.append(Paragraph(f"Date: {datetime.date.today().strftime('%B %d, %Y')}", styles["Normal"]))
    flow.append(Spacer(1, 6))
    _kv(flow, "Patient Name", patient_data.get("name", ""), styles)
    _kv(flow, "Age", patient_data.get("age", ""), styles)
    _kv(flow, "BMI", patient_data.get("bmi", ""), styles)
    note = _bmi_note(patient_data.get("bmi"))
    if note: flow.append(Paragraph(note, styles["Small"]))
    flow.append(Spacer(1, 8))

    # Diagnosis Summary
    flow.append(_h2("Diagnosis Summary", styles))
    flow.append(Paragraph(f"<b>Assessment:</b> {diagnosis}", styles["Normal"]))
    flow.append(Paragraph(f"<b>PCOS Phenotype:</b> {phenotype}", styles["Normal"]))
    if isinstance(diagnosis, str) and diagnosis.lower().startswith("pcos"):
        flow.append(Paragraph(
            "Diagnosis based on ≥2 Rotterdam criteria: oligo/anovulation, clinical/biochemical hyperandrogenism, and polycystic ovaries.",
            styles["Small"]))
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
            for a in alerts:
                flow.append(Paragraph(f"• {_fmt(a)}", styles["Normal"]))
            flow.append(Spacer(1, 6))

    # Lab Results
    labs = patient_data.get("labs", [])
    if labs:
        flow.append(_h2("Lab Results", styles))
        have_range = any(l.get("range") for l in labs)
        have_ref   = any(l.get("reference") for l in labs)
        header = ["Test", "Value", "Units"]
        if have_range: header.append("Normal Range")
        if have_ref:   header.append("Evidence / Note")
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
        plan = [["Day", "Breakfast", "Lunch", "Snack", "Dinner"]]
        for r in meal_plan:
            plan.append([
                r.get("Day",""), r.get("Breakfast",""), r.get("Lunch",""),
                r.get("Snack",""), r.get("Dinner","")
            ])
        flow.append(_table(plan, widths=[45, 120, 120, 90, 120]))
        flow.append(Spacer(1, 6))
        flow.append(Paragraph(
            "Low-GI, high-fiber focus. Portions may be adjusted to meet calorie targets and insulin-resistance goals.",
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
    next_points = [
        "Recheck key labs (glucose/insulin, lipids, vitamin D) and cycles in 3 months.",
        "Prioritize sleep (7–8h), resistance training 2–3x/week, and stress reduction.",
        f"Suggested follow-up date: {follow_up}."
    ]
    for p in next_points:
        flow.append(Paragraph(f"• {p}", styles["Normal"]))
    flow.append(Spacer(1, 8))

    # References (optional)
    refs = patient_data.get("references", [])
    if refs:
        flow.append(_h2("References", styles))
        for i, r in enumerate(refs, 1):
            flow.append(Paragraph(f"{i}. {r}", styles["Small"]))
        flow.append(Spacer(1, 6))

    # Footer block (doctor + WhatsApp)
    flow.append(Paragraph(doctor_line, styles["Normal"]))
    flow.append(Paragraph(clinic_name, styles["Normal"]))
    if whatsapp_link:
        flow.append(Spacer(1, 4))
        flow.append(Paragraph(f"<a href='{whatsapp_link}'>📲 Join Coaching on WhatsApp</a>", styles["Normal"]))
    if whatsapp_qr_path:
        flow.append(Spacer(1, 8))
        _maybe_qr(flow, whatsapp_qr_path)

    # Build
    doc.build(flow)
