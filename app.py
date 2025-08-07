import streamlit as st
from datetime import date
from generate_pdf import create_pdf_report
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="MyPCOS AI – Powered by Clinics Northside",
    layout="wide"
)

# --- Styles ---
st.markdown("""
    <style>
        .main {
            background-color: #fff5fa;
        }
        h1 {
            color: #d63384;
        }
        .reportview-container .markdown-text-container {
            font-family: 'Helvetica';
        }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("MyPCOS AI – Powered by Clinics Northside™")
st.markdown("A personalized diagnostic & care tool for PCOS reversal.")
st.divider()

# --- Patient Details Sidebar ---
with st.sidebar:
    st.header("🩺 Patient Details")
    name = st.text_input("Patient Name")
    age = st.number_input("Age", min_value=10, max_value=60, step=1)
    weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, step=0.1)
    height = st.number_input("Height (cm)", min_value=130.0, max_value=200.0, step=0.1)
    bmi = round(weight / ((height / 100) ** 2), 1) if height else 0
    st.write(f"**BMI:** {bmi}")

# --- Menstrual History ---
st.subheader("🩸 Menstrual History")
irregular_cycles = st.selectbox("Irregular periods?", ["Yes", "No"])
cycle_frequency = st.slider("Cycles per year", 0, 12, 6)
prolonged_bleeding = st.selectbox("Prolonged bleeding (>8 days)?", ["Yes", "No"])

# --- Clinical Hyperandrogenism ---
st.subheader("🧑‍⚕️ Clinical Signs of Hyperandrogenism")
acne = st.checkbox("Acne")
hirsutism = st.checkbox("Hirsutism (facial/body hair)")
alopecia = st.checkbox("Hair thinning or loss")

# --- Ultrasound Findings ---
st.subheader("🩻 Ultrasound Findings")
pcos_ovaries = st.selectbox("Polycystic ovaries seen on ultrasound?", ["Yes", "No", "Not Done"])

# --- Lab Inputs ---
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
    homa_ir = round((fasting_glucose * fasting_insulin) / 405, 2) if fasting_insulin else 0
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

# --- Payment Wall Before Analysis ---
st.subheader("📋 Diagnostic Summary")

if "payment_success" not in st.session_state:
    st.session_state["payment_success"] = False

if not st.session_state["payment_success"]:
    st.info("🔒 Lab analysis and downloadable report are available after payment of ₹299.")

    if st.button("🔍 Analyze & Download Report (Rs. 299)"):
        st.markdown("""
        ### 💳 Razorpay Secure Payment
        Please complete payment of ₹299 using the link below:

        👉 [Pay ₹299 Now](https://razorpay.me/@clinicsnorthside)
        """, unsafe_allow_html=True)
        st.markdown("> Once paid, check the confirmation box below.")

    paid_confirm = st.checkbox("✅ I have completed the ₹299 payment")

    if paid_confirm:
        st.session_state["payment_success"] = True
        st.success("✅ Payment confirmed! Analyzing your report...")
        st.experimental_rerun()

    st.stop()

# --- Diagnosis ---
criteria = {
    "Oligo/anovulation": (irregular_cycles == "Yes" or cycle_frequency < 9),
    "Hyperandrogenism": (acne or hirsutism or alopecia or total_testosterone > 50 or dheas > 350),
    "Polycystic ovaries": (pcos_ovaries == "Yes")
}
num_positive = sum(criteria.values())

if num_positive >= 2:
    st.success("✅ **PCOS Likely (meets Rotterdam Criteria)**")
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
else:
    phenotype = "None"
    st.warning("⚠️ PCOS unlikely based on current data (does not meet Rotterdam criteria).")

# --- Additional Alerts ---
if homa_ir > 2.5:
    st.error("🧪 Insulin Resistance detected (HOMA-IR > 2.5)")
if tsh > 4.0:
    st.warning("🧪 Consider further thyroid evaluation (TSH elevated)")
if total_testosterone > 70 or dheas > 350:
    st.warning("🧪 Possible biochemical hyperandrogenism – consider repeat or imaging")

st.divider()

# --- Treatment Plan ---
st.subheader("💊 Treatment Plan Recommendation")
treatment_notes = [
    "Target 5–10% weight loss",
    "Consider Myo-Inositol or Metformin",
    "Optimize sleep, stress, and exercise routine",
    "Recheck labs in 3–6 months",
    "Supplement Vitamin D and B12 if low"
]

for item in treatment_notes:
    st.markdown(f"- {item}")

# --- Generate PDF Button ---
if st.button("📥 Download PDF Report"):
    filename = f"{name.replace(' ', '_')}_pcos_report.pdf"
    today = date.today().strftime("%Y-%m-%d")
    pdf_filename = f"PCOS_Report_{name.replace(' ', '_')}_{today}.pdf"
    patient_data = {
        "name": name,
        "age": age,
        "bmi": bmi,
        "labs": [
            {"name": "Total Testosterone", "value": total_testosterone, "unit": "ng/dL"},
            {"name": "DHEAS", "value": dheas, "unit": "µg/dL"},
            {"name": "Fasting Insulin", "value": fasting_insulin, "unit": "µIU/mL"},
            {"name": "Fasting Glucose", "value": fasting_glucose, "unit": "mg/dL"},
            {"name": "HOMA-IR", "value": homa_ir, "unit": ""},
            {"name": "LH", "value": lh, "unit": "mIU/mL"},
            {"name": "FSH", "value": fsh, "unit": "mIU/mL"},
            {"name": "SHBG", "value": shbg, "unit": "nmol/L"},
            {"name": "TSH", "value": tsh, "unit": "µIU/mL"},
            {"name": "17-OHP", "value": seventeen_ohp, "unit": "ng/dL"},
            {"name": "Vitamin D", "value": vitamin_d, "unit": "ng/mL"},
            {"name": "Vitamin B12", "value": b12, "unit": "pg/mL"},
            {"name": "Cholesterol", "value": cholesterol, "unit": "mg/dL"},
            {"name": "LDL", "value": ldl, "unit": "mg/dL"},
            {"name": "HDL", "value": hdl, "unit": "mg/dL"},
            {"name": "Triglycerides", "value": triglycerides, "unit": "mg/dL"}
        ]
    }
    create_pdf_report(pdf_filename, patient_data, "PCOS Likely" if num_positive >= 2 else "Unlikely", phenotype, treatment_notes)
    with open(pdf_filename, "rb") as f:
        st.download_button("📄 Download Your PCOS Report", f, file_name=pdf_filename, mime="application/pdf")
    os.remove(pdf_filename)
