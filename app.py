# Sytner AutoSense - Landing Page POC
import streamlit as st
from PIL import Image, ImageOps
import io, datetime, json, re

# -------------------------
# OCR Libraries (same as before)
# -------------------------
EASYOCR_AVAILABLE = False
PYTESSERACT_AVAILABLE = False
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except Exception:
    EASYOCR_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except Exception:
    PYTESSERACT_AVAILABLE = False

# -------------------------
# Mock / Helpers (same as before)
# -------------------------
def lookup_vehicle_basic(reg):
    reg = reg.upper().replace(" ", "")
    return {
        "reg": reg,
        "make": "BMW",
        "model": "3 Series",
        "year": 2018,
        "vin": "WBA8BFAKEVIN12345",
        "mileage": 54000
    }

def lookup_mot_and_tax(reg):
    today = datetime.date.today()
    return {
        "mot_next_due": (today + datetime.timedelta(days=120)).isoformat(),
        "mot_history": [
            {"date": "2024-08-17", "result": "Pass", "mileage": 52000},
            {"date": "2023-08-10", "result": "Advisory", "mileage": 48000},
        ],
        "tax_expiry": (today + datetime.timedelta(days=30)).isoformat(),
    }

def lookup_recalls(reg_or_vin):
    return [{"id": "R-2023-001", "summary": "Airbag inflator recall - replace module", "open": True}]

def lookup_history_flags(reg):
    return {"write_off": False, "theft": False, "mileage_anomaly": True, "note": "Mileage shows a 5,000 jump in 2021 record"}

def estimate_value(make, model, year, mileage, condition="good"):
    age = datetime.date.today().year - year
    base = 25000 - (age * 2000) - (mileage / 10)
    cond_multiplier = {"excellent": 1.05, "good": 1.0, "fair": 0.9, "poor": 0.8}
    return max(100, int(base * cond_multiplier.get(condition, 1.0)))

PLATE_REGEX = re.compile(r"[A-Z0-9]{5,10}", re.I)

# -------------------------
# Streamlit Config
# -------------------------
st.set_page_config(page_title="Sytner AutoSense", page_icon="🚗", layout="centered")
PRIMARY = "#0b3b6f"

# Header
st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px">
  <div style="background:{PRIMARY};padding:10px 14px;border-radius:8px;color:white;font-weight:700;">Sytner</div>
  <div style="font-size:22px;font-weight:700;color:{PRIMARY};">AutoSense — POC</div>
</div>
""", unsafe_allow_html=True)

st.markdown("## Welcome to AutoSense")
st.write("Start by entering a vehicle registration / VIN or take a photo of the number plate.")

# -------------------------
# Landing Page Options
# -------------------------
option = st.radio("Choose input method", ["Enter Registration / VIN", "Take Photo"], index=0)

reg = None
image = None

if option == "Enter Registration / VIN":
    manual_reg = st.text_input("Enter registration / VIN", placeholder="KT68XYZ or VIN...")
    if manual_reg:
        reg = manual_reg.strip().upper().replace(" ", "")

elif option == "Take Photo":
    if st.button("Open Camera"):
        # Only show camera input when button is clicked
        image = st.camera_input("Take photo of the number plate")

# Stop until either reg or image is provided
if not reg and not image:
    st.info("Provide a registration or take a photo to proceed.")
    st.stop()

# -------------------------
# If image is provided, show preview and run OCR
# -------------------------
ocr_texts = []
if image:
    st.image(ImageOps.exif_transpose(Image.open(image)), width=320)
    st.info("OCR will run here (EasyOCR or pytesseract) in full app version.")
    # Placeholder: in full version, run OCR and extract reg
    st.warning("OCR is mocked in this landing page POC.")
    reg = "KT68XYZ"  # Mocked extracted reg for demo

# -------------------------
# Fetch mocked data
# -------------------------
vehicle = lookup_vehicle_basic(reg)
mot_tax = lookup_mot_and_tax(reg)
recalls = lookup_recalls(reg)
history_flags = lookup_history_flags(reg)
value = estimate_value(vehicle["make"], vehicle["model"], vehicle["year"], vehicle["mileage"], "good")

# -------------------------
# Summary Metrics
# -------------------------
st.markdown("---")
st.markdown("### Vehicle Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Estimated Value", f"£{value:,}", "Good")
col2.metric("Next MOT", mot_tax['mot_next_due'])
col3.metric("Open Recalls", sum(1 for r in recalls if r['open']))
