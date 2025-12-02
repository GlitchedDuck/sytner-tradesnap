import streamlit as st
from PIL import Image, ImageOps
import datetime, re, json

# -------------------------
# Mock / Helpers
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
    return [
        {"id": "R-2023-001", "summary": "Airbag inflator recall - replace module", "open": True},
        {"id": "R-2022-012", "summary": "Steering column check", "open": False}
    ]

def estimate_value(make, model, year, mileage, condition="good"):
    age = datetime.date.today().year - year
    base = 25000 - (age * 2000) - (mileage / 10)
    cond_multiplier = {"excellent": 1.05, "good": 1.0, "fair": 0.9, "poor": 0.8}
    return max(100, int(base * cond_multiplier.get(condition, 1.0)))

PLATE_REGEX = re.compile(r"[A-Z0-9]{5,10}", re.I)

# -------------------------
# Streamlit config + theming
# -------------------------
st.set_page_config(page_title="Sytner AutoSense", page_icon="🚗", layout="centered")
PRIMARY = "#0b3b6f"
ACCENT = "#1e90ff"
PAGE_BG = "#e6f0fa"

st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-color: {PAGE_BG};
}}
.header-card {{
    background-color: {PRIMARY};
    color: white;
    padding: 16px 24px;
    border-radius: 12px;
    font-size: 24px;
    font-weight: 700;
    text-align: center;
}}
.content-card {{
    background-color: white;
    padding: 16px 20px;
    border-radius: 12px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}}
.stButton>button {{
    background-color: {ACCENT};
    color: white;
    font-weight: 600;
    border-radius: 8px;
}}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Header
# -------------------------
st.markdown(f"<div class='header-card'>Sytner AutoSense — POC</div>", unsafe_allow_html=True)
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
        image = st.camera_input("Take photo of the number plate", camera_facing_mode="environment")

if not reg and not image:
    st.info("Provide a registration or take a photo to proceed.")
    st.stop()

# -------------------------
# Image preview / mock OCR
# -------------------------
if image:
    st.image(ImageOps.exif_transpose(Image.open(image)), width=320)
    st.warning("OCR is mocked in this demo. Extracted reg will be used for summary.")
    reg = "KT68XYZ"

# -------------------------
# Fetch mocked data
# -------------------------
vehicle = lookup_vehicle_basic(reg)
mot_tax = lookup_mot_and_tax(reg)
recalls = lookup_recalls(reg)

# -------------------------
# Valuation Card with condition selector
# -------------------------
st.markdown("<div class='content-card'>", unsafe_allow_html=True)
st.subheader("Vehicle Valuation")
condition = st.radio("Select condition", ["excellent", "good", "fair", "poor"], index=1, horizontal=True)
value = estimate_value(vehicle["make"], vehicle["model"], vehicle["year"], vehicle["mileage"], condition)
st.markdown(f"<p><strong>Estimated Value:</strong> £{value:,} ({condition.capitalize()})</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Vehicle Summary Card
# -------------------------
st.markdown(f"""
<div class='content-card'>
<h4>Vehicle Summary</h4>
<p><strong>Make & Model:</strong> {vehicle['make']} {vehicle['model']}</p>
<p><strong>Year:</strong> {vehicle['year']}</p>
<p><strong>VIN:</strong> {vehicle['vin']}</p>
<p><strong>Mileage:</strong> {vehicle['mileage']:,} miles</p>
<p><strong>Next MOT:</strong> {mot_tax['mot_next_due']}</p>
</div>
""", unsafe_allow_html=True)

# -------------------------
# MOT History Card (expandable)
# -------------------------
with st.expander("MOT History"):
    for t in mot_tax['mot_history']:
        st.write(f"- {t['date']}: **{t['result']}** — {t['mileage']} miles")

# -------------------------
# Recalls Card (expandable)
# -------------------------
with st.expander("Recalls"):
    for r in recalls:
        status = "Open ⚠️" if r['open'] else "Closed ✅"
        st.write(f"- {r['summary']} — ID: {r['id']} ({status})")

# -------------------------
# Insurance Card (mock)
# -------------------------
st.markdown("<div class='content-card'>", unsafe_allow_html=True)
st.markdown("<h4>Insurance (Mock)</h4>", unsafe_allow_html=True)
st.info("Insurance quotes are mocked. Integrate aggregator APIs for live quotes.")
if st.button('Get a mock insurance quote'):
    st.success('Sample quote: £320/year (3rd party, excess £250)')
st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Snapshot Download
# -------------------------
st.markdown("<div class='content-card'>", unsafe_allow_html=True)
st.markdown("<h4>Snapshot</h4>", unsafe_allow_html=True)
snapshot = {
    "vehicle": vehicle,
    "mot_tax": mot_tax,
    "recalls": recalls,
    "valuation": {"value": value, "condition": condition},
    "queried_at": datetime.datetime.utcnow().isoformat()
}
st.download_button("Download JSON snapshot", data=json.dumps(snapshot, indent=2),
                   file_name=f"{reg}_snapshot.json", mime='application/json')
st.markdown("</div>", unsafe_allow_html=True)

