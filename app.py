import streamlit as st
from datetime import date
from generate_pdf import create_pdf_report
import os
import pandas as pd
import altair as alt

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

# --- Navigation Tabs ---
tab = st.sidebar.radio("Select Tab", ["📝 New Report", "📈 Monitor Progress"])

# --- CSV Persistence Setup ---
DATA_FILE = "progress_tracker.csv"
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["Date", "Name", "Weight", "BMI", "Cycle Length", "HOMA-IR", "TSH"]).to_csv(DATA_FILE, index=False)

if tab == "📈 Monitor Progress":
    st.header("📈 Track PCOS Progress Over Time")

    # Load data
    df = pd.read_csv(DATA_FILE)
    patient_name = st.selectbox("Select patient name to view trends:", df["Name"].unique())
    filtered = df[df["Name"] == patient_name]

    if not filtered.empty:
        st.subheader("📊 Weight Trend")
        st.line_chart(filtered.set_index("Date")["Weight"])

        st.subheader("📊 BMI Trend")
        st.line_chart(filtered.set_index("Date")["BMI"])

        st.subheader("📊 HOMA-IR Trend")
        st.line_chart(filtered.set_index("Date")["HOMA-IR"])

        st.subheader("📊 TSH Trend")
        st.line_chart(filtered.set_index("Date")["TSH"])
    else:
        st.info("No data found for this patient yet.")

    st.stop()

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

# --- Save Entry to Progress Log ---
if name and weight:
    log_df = pd.read_csv(DATA_FILE)
    new_row = {
        "Date": date.today().strftime("%Y-%m-%d"),
        "Name": name,
        "Weight": weight,
        "BMI": bmi,
        "Cycle Length": cycle_frequency,
        "HOMA-IR": homa_ir,
        "TSH": tsh
    }
    log_df = pd.concat([log_df, pd.DataFrame([new_row])], ignore_index=True)
    log_df.to_csv(DATA_FILE, index=False)

# Ready for diagnostic and PDF generation logic...
