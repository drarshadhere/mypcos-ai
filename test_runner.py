from generate_pdf import create_pdf_report
import os

# --- Dummy test data ---
patient_data = {
    "name": "Lahari Sameeraja",
    "age": 22,
    "bmi": 25.2,
    "labs": [
        {"name": "Total Testosterone", "value": 78, "unit": "ng/dL"},
        {"name": "DHEAS", "value": 325, "unit": "µg/dL"},
        {"name": "Fasting Insulin", "value": 16.3, "unit": "µIU/mL"},
        {"name": "Fasting Glucose", "value": 96, "unit": "mg/dL"},
        {"name": "HOMA-IR", "value": round((96 * 16.3) / 405, 2), "unit": ""},
        {"name": "LH", "value": 11.2, "unit": "mIU/mL"},
        {"name": "FSH", "value": 5.4, "unit": "mIU/mL"},
        {"name": "SHBG", "value": 42.5, "unit": "nmol/L"},
        {"name": "TSH", "value": 2.4, "unit": "µIU/mL"},
        {"name": "17-OHP", "value": 87, "unit": "ng/dL"},
        {"name": "Vitamin D", "value": 18.6, "unit": "ng/mL"},
        {"name": "Vitamin B12", "value": 412, "unit": "pg/mL"},
        {"name": "Cholesterol", "value": 182, "unit": "mg/dL"},
        {"name": "LDL", "value": 117, "unit": "mg/dL"},
        {"name": "HDL", "value": 42, "unit": "mg/dL"},
        {"name": "Triglycerides", "value": 184, "unit": "mg/dL"}
    ]
}

diagnosis = "✅ PCOS Likely (meets Rotterdam Criteria)"
phenotype = "Phenotype D"

treatment_notes = [
    "Target 5–10% weight loss",
    "Consider Myo-Inositol or Metformin",
    "Optimize sleep, stress, and exercise routine",
    "Recheck labs in 3–6 months",
    "Supplement Vitamin D and B12 if low"
]

# --- Output PDF filename ---
filename = "test_pcos_report.pdf"

# --- Call the PDF creation function ---
create_pdf_report(filename, patient_data, diagnosis, phenotype, treatment_notes)

print(f"✅ PDF generated: {filename}")

# Optional: Open the PDF automatically (Windows only)
try:
    os.startfile(filename)
except:
    print("💡 Open the PDF manually if you're not on Windows.")

