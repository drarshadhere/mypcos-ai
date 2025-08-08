from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import datetime
import qrcode
import os

# --- Function to draw footer on every page ---
def add_footer(canvas, doc):
    footer_text = "Clinics Northside | Confidential | www.clinicsnorthside.com"
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(A4[0] / 2.0, 20, footer_text)
    canvas.restoreState()

# --- Main PDF Generator ---
def create_pdf_report(filename, patient_data, diagnosis, phenotype, treatment_notes):
    doc = SimpleDocTemplate(filename, pagesize=A4, bottomMargin=40)
    styles = getSampleStyleSheet()
    flow = []

    # --- Logo ---
    logo_path = "clinics_logo.png"  # your final logo file saved in folder
    if os.path.exists(logo_path):
        img = Image(logo_path, width=3*inch, height=1*inch)
        img.hAlign = 'CENTER'
        flow.append(img)
        flow.append(Spacer(1, 6))

    # --- Header ---
    flow.append(Paragraph("<b>MyPCOS AI – Powered by Clinics Northside™</b>", styles['Title']))
    flow.append(Spacer(1, 6))
    flow.append(Paragraph(f"Date: {datetime.date.today().strftime('%B %d, %Y')}", styles['Normal']))
    flow.append(Paragraph(f"Patient Name: {patient_data.get('name', '')}", styles['Normal']))
    flow.append(Paragraph(f"Age: {patient_data.get('age', '')}", styles['Normal']))
    flow.append(Paragraph(f"BMI: {patient_data.get('bmi', '')}", styles['Normal']))
    flow.append(Spacer(1, 12))

    # --- Diagnosis ---
    flow.append(Paragraph("<b>Diagnosis Summary:</b>", styles['Heading2']))
    flow.append(Paragraph(diagnosis, styles['Normal']))
    flow.append(Paragraph(f"PCOS Phenotype: {phenotype}", styles['Normal']))
    flow.append(Spacer(1, 12))

    # --- Lab Table ---
    if "labs" in patient_data:
        flow.append(Paragraph("<b>Lab Results:</b>", styles['Heading2']))
        lab_data = [["Test", "Value", "Units"]]
        for lab in patient_data["labs"]:
            lab_data.append([lab["name"], lab["value"], lab["unit"]])
        lab_table = Table(lab_data, hAlign='LEFT')
        lab_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#D9D9D9")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER')
        ]))
        flow.append(lab_table)
        flow.append(Spacer(1, 12))

    # --- Recommendations ---
    flow.append(Paragraph("<b>Treatment Recommendations:</b>", styles['Heading2']))
    for item in treatment_notes:
        flow.append(Paragraph(f"• {item}", styles['Normal']))
    flow.append(Spacer(1, 12))

    flow.append(Paragraph("Dr. Arshad Mohammed, MD", styles['Normal']))
    flow.append(Paragraph("Clinics Northside", styles['Normal']))
    flow.append(Spacer(1, 12))

    # --- WhatsApp QR Code ---
    whatsapp_link = "https://wa.me/919000000000?text=I%20want%20to%20join%20your%20PCOS%20program"
    qr_filename = "whatsapp_qr.png"
    if not os.path.exists(qr_filename):
        img = qrcode.make(whatsapp_link)
        img.save(qr_filename)

    qr = Image(qr_filename, width=1.5*inch, height=1.5*inch)
    qr_caption = Paragraph("📲 Join Coaching on WhatsApp", styles['Normal'])
    flow.append(qr_caption)
    flow.append(qr)

    # --- Build PDF ---
    doc.build(flow, onFirstPage=add_footer, onLaterPages=add_footer)
