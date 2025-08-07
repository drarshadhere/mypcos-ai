from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import datetime

def _fmt(val):
    try:
        f = float(val)
        return str(int(f)) if f.is_integer() else f"{f:.2f}"
    except Exception:
        return str(val)

def create_pdf_report(filename, patient_data, diagnosis, phenotype, treatment_notes):
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=12))
    flow = []

    # Logo (keeps aspect, avoids distortion)
    try:
        logo = "2.jpg"
        img = Image(logo)
        img._restrictSize(2.8*inch, 0.9*inch)
        flow.append(img)
        flow.append(Spacer(1, 8))
    except:
        pass

    # Header
    title = Paragraph("MyPCOS AI – Powered by Clinics Northside™", styles['Title'])
    flow.append(title)
    flow.append(Paragraph(f"Date: {datetime.date.today().strftime('%B %d, %Y')}", styles['Normal']))
    flow.append(Spacer(1, 6))
    flow.append(Paragraph(f"<b>Patient Name:</b> {_fmt(patient_data.get('name', ''))}", styles['Normal']))
    flow.append(Paragraph(f"<b>Age:</b> {_fmt(patient_data.get('age', ''))}", styles['Normal']))
    flow.append(Paragraph(f"<b>BMI:</b> {_fmt(patient_data.get('bmi', ''))}", styles['Normal']))
    flow.append(Spacer(1, 10))

    # Diagnosis
    flow.append(Paragraph("Diagnosis Summary", styles['Heading2']))
    flow.append(Paragraph(f"<b>Assessment:</b> {diagnosis}", styles['Normal']))
    flow.append(Paragraph(f"<b>PCOS Phenotype:</b> {phenotype}", styles['Normal']))
    if isinstance(diagnosis, str) and diagnosis.lower().startswith("pcos"):
        flow.append(Paragraph(
            "Diagnosis based on ≥2 Rotterdam criteria: oligo/anovulation, clinical/biochemical hyperandrogenism, and polycystic ovaries.",
            styles["Small"]))
    flow.append(Spacer(1, 8))

    # Evidence Summary (Rotterdam criteria + alerts)
    criteria = patient_data.get("criteria", {})
    alerts = patient_data.get("alerts", [])

    if criteria or alerts:
        flow.append(Paragraph("Evidence Summary", styles['Heading2']))

        if criteria:
            crit_data = [["Criterion", "Met?"]]
            for k in ["Oligo/anovulation", "Hyperandrogenism", "Polycystic ovaries"]:
                if k in criteria:
                    crit_data.append([k, "Yes" if criteria[k] else "No"])
            crit_table = Table(crit_data, colWidths=[300, 80], hAlign='LEFT')
            crit_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (1,1), (1,-1), 'CENTER'),
            ]))
            flow.append(crit_table)
            flow.append(Spacer(1, 6))

        if alerts:
            flow.append(Paragraph("<b>Clinical/Lab Alerts:</b>", styles['Normal']))
            for a in alerts:
                flow.append(Paragraph(f"• {a}", styles['Normal']))
            flow.append(Spacer(1, 6))

    # Labs table
    labs = patient_data.get("labs", [])
    if labs:
        flow.append(Paragraph("Lab Results", styles['Heading2']))
        lab_data = [["Test", "Value", "Units"]]
        for lab in labs:
            lab_data.append([lab.get("name",""), _fmt(lab.get("value","")), lab.get("unit","")])
        lab_table = Table(lab_data, colWidths=[220, 100, 80], hAlign='LEFT')
        lab_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (1,1), (1,-1), 'RIGHT'),
        ]))
        flow.append(lab_table)
        flow.append(Spacer(1, 8))

    # Treatment
    if treatment_notes:
        flow.append(Paragraph("Treatment Recommendations", styles['Heading2']))
        for item in treatment_notes:
            flow.append(Paragraph(f"• {item}", styles['Normal']))
        flow.append(Spacer(1, 10))

    # References (optional)
    refs = patient_data.get("references", [])
    if refs:
        flow.append(Paragraph("References", styles['Heading2']))
        for i, r in enumerate(refs, 1):
            flow.append(Paragraph(f"{i}. {r}", styles['Small']))
        flow.append(Spacer(1, 8))

    # Footer / contact
    flow.append(Paragraph("Dr. Arshad Mohammed, MD", styles['Normal']))
    flow.append(Paragraph("Clinics Northside", styles['Normal']))
    flow.append(Spacer(1, 6))
    flow.append(Paragraph(
        "<a href='https://wa.me/?text=I%20want%20to%20join%20the%20PCOS%20program'>📲 WhatsApp to enroll in PCOS coaching</a>",
        styles['Normal']
    ))

    doc.build(flow)
