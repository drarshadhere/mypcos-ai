import os
from datetime import date
import pandas as pd
import streamlit as st
import smtplib
from email.message import EmailMessage

from generate_pdf import create_pdf_report  # uses the updated evidence-enabled function

# =========================
# Page & Styles
# =========================
st.set_page_config(page_title="MyPCOS AI – Powered by Clinics Northside", layout="wide")

st.markdown("""
    <style>
        .main { background-color: #fff5fa; }
        h1 { color: #d63384; }
        .reportview-container .markdown-text-container { font-family: 'Helvetica'; }
    </style>
""", unsafe_allow_html=True)

st.title("MyPCOS AI – Powered by Clinics Northside™")
st.markdown("A personalized diagnostic & care tool for PCOS reversal.")
st.divider()

# =========================
# Tabs
# =========================
tab = st.sidebar.radio("Select Tab", ["📝 New Report", "📈 Monitor Progress"])

# =========================
# Data persistence
# =========================
DATA_FILE = "progress_tracker.csv"
if not os.path.exists(DATA_FILE):
    pd.DataFrame(
        columns=["Date", "Name", "Weight", "BMI", "Cycle Length", "HOMA-IR", "TSH"]
    ).to_csv(DATA_FILE, index=False)

# =========================
# Monitor tab
# =========================
if tab == "📈 Monitor Progress":
    st.header("📈 Track PCOS Progress Over Time")
    df = pd.read_csv(DATA_FILE)

    if df.empty or df["Name"].fillna("").eq("").all():
        st.info("No data found yet. Add a new report first.")
        st.stop()

    patient_name = st.selectbox("Select patient name to view trends:", sorted(df["Name"].dropna().unique()))
    filtered = df[df["Name"] == patient_name].copy()

    if filtered.empty:
        st.info("No entries for this patient yet.")
        st.stop()

    filtered["Date"] = pd.to_datetime(filtered["Date"], errors="coerce")
    filtered = filtered.sort_values("Date")

    st.subheader("📊 Weight Trend")
    st.line_chart(filtered.set_index("Date")["Weight"])

    st.subheader("📊 BMI Trend")
    st.line_chart(filtered.set_index("Date")["BMI"])

    st.subheader("📊 HOMA-IR Trend")
    st.line_chart(filtered.set_index("Date")["HOMA-IR"])

    st.subheader("📊 TSH Trend")
    st.line_chart(filtered.set_index("Date")["TSH"])

    st.stop()

# =========================
# Sidebar: patient details
# =========================
with st.sidebar:
    st.header("🩺 Patient Details")
    name = st.text_input("Patient Name")
    email = st.text_input("Email to send report")
    age = st.number_input("Age", min_value=10, max_value=60, step=1)
    weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, step=0.1)
    height = st.number_input("Height (cm)", min_value=130.0, max_value=200.0, step=0.1)
    bmi = round(weight / ((height / 100) ** 2), 1) if height else 0.0
    st.write(f"**BMI:** {bmi}")

# =========================
# Menstrual history
# =========================
st.subheader("🩸 Menstrual History")
irregular_cycles = st.selectbox("Irregular periods?", ["Yes", "No"])
cycle_frequency = st.slider("Cycles per year", 0, 12, 6)
prolonged_bleeding = st.selectbox("Prolonged bleeding (>8 days)?", ["Yes", "No"])

# =========================
# Clinical hyperandrogenism
# =========================
st.subheader("🧑‍⚕️ Clinical Signs of Hyperandrogenism")
acne = st.checkbox("Acne")
hirsutism = st.checkbox("Hirsutism (facial/body hair)")
alopecia = st.checkbox("Hair thinning or loss")

# =========================
# Ultrasound
# =========================
st.subheader("🩻 Ultrasound Findings")
pcos_ovaries = st.selectbox("Polycystic ovaries seen on ultrasound?", ["Yes", "No", "Not Done"])

# =========================
# Lab inputs
# =========================
st.subheader("🧪 Lab Results")
col1, col2, col3 = st.columns(3)

with col1:
    total_testosterone = st.number_input("Total Testosterone (ng/dL)", 0.0, 200.0, step=0.1)
    dheas = st.number_input("DHEAS (µg/dL)", 0.0, 1000.0, step=0.1)
    fasting_glucose = st.number_input("Fasting Glucose (mg/dL)", 50.0, 200.0, step=0.1)
    lh = st.number_input("LH (mIU/mL)", 0.0, 50.0, step=0.1)
    tsh = st.number_input("TSH (µIU/mL)", 0.01, 10.0, step=0.01)
    cholesterol = st.number_input("Total Cholesterol (mg/dL)", 50, 400)

with col2:
    fasting_insulin = st.number_input("Fasting Insulin (µIU/mL)", 0.0, 100.0, step=0.1)
    homa_ir = round((fasting_glucose * fasting_insulin) / 405, 2) if fasting_insulin else 0.0
    st.write(f"**HOMA-IR:** {homa_ir}")
    fsh = st.number_input("FSH (mIU/mL)", 0.0, 50.0, step=0.1)
    shbg = st.number_input("SHBG (nmol/L)", 0.0, 200.0, step=0.1)
    vitamin_d = st.number_input("Vitamin D (ng/mL)", 0.0, 100.0, step=0.1)
    ldl = st.number_input("LDL (mg/dL)", 30, 300)

with col3:
    seventeen_ohp = st.number_input("17-OHP (ng/dL)", 0.0, 500.0, step=0.1)
    b12 = st.number_input("Vitamin B12 (pg/mL)", 100, 2000)
    hdl = st.number_input("HDL (mg/dL)", 10, 120)
    triglycerides = st.number_input("Triglycerides (mg/dL)", 30, 600)

st.divider()

# =========================
# Auto-save entry to progress log (lightweight)
# =========================
if name and weight:
    try:
        log_df = pd.read_csv(DATA_FILE)
    except Exception:
        log_df = pd.DataFrame(columns=["Date", "Name", "Weight", "BMI", "Cycle Length", "HOMA-IR", "TSH"])

    new_row = {
        "Date": date.today().strftime("%Y-%m-%d"),
        "Name": name,
        "Weight": weight,
        "BMI": bmi,
        "Cycle Length": cycle_frequency,
        "HOMA-IR": homa_ir,
        "TSH": tsh
    }
    # Avoid duplicate same-day rows for same person (optional)
    dup_mask = (log_df["Date"] == new_row["Date"]) & (log_df["Name"] == name)
    log_df = log_df[~dup_mask]
    log_df = pd.concat([log_df, pd.DataFrame([new_row])], ignore_index=True)
    log_df.to_csv(DATA_FILE, index=False)

# =========================
# Diagnostic logic (Rotterdam)
# =========================
st.subheader("📋 Diagnostic Summary")

criteria = {
    "Oligo/anovulation": (irregular_cycles == "Yes" or cycle_frequency < 9),
    "Hyperandrogenism": (acne or hirsutism or alopecia or total_testosterone > 50 or dheas > 350),
    "Polycystic ovaries": (pcos_ovaries == "Yes")
}
num_positive = sum(criteria.values())

if num_positive >= 2:
    st.success("✅ PCOS Likely (meets Rotterdam Criteria)")
    if all(criteria.values()):
        phenotype = "Phenotype A"
    elif criteria["Oligo/anovulation"] and criteria["Hyperandrogenism"]:
        phenotype = "Phenotype B"
    elif criteria["Hyperandrogenism"] and criteria["Polycystic ovaries"]:
        phenotype = "Phenotype C"
    elif criteria["Oligo/anovulation"] and criteria["Polycystic ovaries"]:
        phenotype = "Phenotype D"
    else:
        phenotype = "Unclassified"
    st.write(f"### 📌 PCOS Phenotype: **{phenotype}**")
    diagnosis = "PCOS Likely"
else:
    st.warning("⚠️ PCOS unlikely based on current data (does not meet Rotterdam criteria).")
    diagnosis = "PCOS Unlikely"
    phenotype = "Not applicable"

# Alerts for evidence section
alerts = []
if homa_ir > 2.5:
    alerts.append("Insulin resistance (HOMA-IR > 2.5)")
if tsh > 4.0:
    alerts.append("Elevated TSH — consider thyroid evaluation")
if total_testosterone > 70 or dheas > 350:
    alerts.append("Possible biochemical hyperandrogenism — consider repeat/confirmatory testing")

st.divider()

# =========================
# Payment + Report
# =========================
st.subheader("📥 Generate Report")
st.markdown("Please complete payment of ₹299 before downloading the PDF.")
st.markdown("[🔗 Pay via Razorpay](https://razorpay.me/@clinicsnorthside)")

paid = st.checkbox("I have completed the payment")

if paid:
    treatment_notes = [
        "Target 5–10% weight loss",
        "Consider Myo-Inositol or Metformin",
        "Optimize sleep, stress, and exercise routine",
        "Recheck labs in 3–6 months",
        "Supplement Vitamin D and B12 if low"
    ]

    if st.button("📄 Generate PDF and Email"):
        # Assemble labs
        labs = [
            {"name": "Total Testosterone", "value": total_testosterone, "unit": "ng/dL"},
            {"name": "DHEAS", "value": dheas, "unit": "µg/dL"},
            {"name": "Fasting Glucose", "value": fasting_glucose, "unit": "mg/dL"},
            {"name": "Fasting Insulin", "value": fasting_insulin, "unit": "µIU/mL"},
            {"name": "HOMA-IR", "value": homa_ir, "unit": ""},
            {"name": "LH", "value": lh, "unit": "mIU/mL"},
            {"name": "FSH", "value": fsh, "unit": "mIU/mL"},
            {"name": "SHBG", "value": shbg, "unit": "nmol/L"},
            {"name": "TSH", "value": tsh, "unit": "µIU/mL"},
            {"name": "17-OHP", "value": seventeen_ohp, "unit": "ng/dL"},
            {"name": "Vitamin D", "value": vitamin_d, "unit": "ng/mL"},
            {"name": "Vitamin B12", "value": b12, "unit": "pg/mL"},
            {"name": "Total Cholesterol", "value": cholesterol, "unit": "mg/dL"},
            {"name": "LDL", "value": ldl, "unit": "mg/dL"},
            {"name": "HDL", "value": hdl, "unit": "mg/dL"},
            {"name": "Triglycerides", "value": triglycerides, "unit": "mg/dL"},
        ]

        # Patient data with evidence for PDF
        patient_data = {
            "name": name,
            "age": age,
            "bmi": bmi,
            "labs": labs,
            "criteria": criteria,  # <-- evidence (Rotterdam criteria)
            "alerts": alerts       # <-- evidence (clinical/lab alerts)
        }

        pdf_filename = f"{name.replace(' ', '_')}_pcos_report.pdf"
        create_pdf_report(pdf_filename, patient_data, diagnosis, phenotype, treatment_notes)

        # Download in-browser
        with open(pdf_filename, "rb") as f:
            st.download_button("⬇️ Download Report", f, file_name=pdf_filename)

        # Email the report (requires secrets)
        try:
            msg = EmailMessage()
            msg["Subject"] = "Your PCOS Report – Clinics Northside"
            msg["From"] = st.secrets["email"]["sender"]
            msg["To"] = email
            msg["Reply-To"] = st.secrets["email"]["sender"]
            msg.set_content(
                f"Dear {name or 'Client'},\n\nYour personalized PCOS report is attached.\n\n— Clinics Northside"
            )
            with open(pdf_filename, "rb") as file:
                msg.add_attachment(file.read(), maintype="application", subtype="pdf", filename=pdf_filename)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(st.secrets["email"]["sender"], st.secrets["email"]["password"])
                smtp.send_message(msg)

            st.success("✅ Report emailed successfully.")
        except Exception as e:
            st.warning("⚠️ Could not send email. Please check credentials or internet.")
            # Uncomment to debug:
            # st.exception(e)

        # Clean up temp file
        try:
            os.remove(pdf_filename)
        except Exception:
            pass

        st.markdown("[📤 Share via WhatsApp](https://wa.me/?text=Your%20PCOS%20report%20is%20ready%20for%20download.)")
else:
    st.info("🔒 Please confirm payment before generating the report.")
