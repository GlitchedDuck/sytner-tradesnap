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
    today_dt = datetime.date.today()
    return {
        "mot_next_due": (today_dt + datetime.timedelta(days=120)).isoformat(),
        "mot_history": [
            {"date": "2024-08-17", "result": "Pass", "mileage": 52000},
            {"date": "2023-08-10", "result": "Advisory", "mileage": 48000},
        ],
        "tax_expiry": (today_dt + datetime.timedelta(days=30)).isoformat(),
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
    margin-bottom: 24px;
}}
.content-card {{
    background-color: white;
    padding: 16px 20px;
    border-radius: 12px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}}
.content-card h4 {{
    margin-top: 0;
    margin-bottom: 8px;
}}
.stButton>button {{
    background-color: {ACCENT};
    color: white;
    font-weight: 600;
    border-radius: 8px;
}}
.numberplate {{
    background-color: #fff;
    border: 2px solid {PRIMARY};
    border-radius: 12px;
    padding: 12px 20px;
    font-size: 28px;
    font-weight: 700;
    color: {PRIMARY};
    text-align: center;
    margin: 24px auto;
    width: fit-content;
}}
.badge {{
    padding: 4px 10px;
    border-radius: 12px;
    color: white;
    margin-right: 4px;
    font-size: 12px;
}}
.badge-warning {{background-color: #ff9800;}}
.badge-error {{background-color: #f44336;}}
.badge-info {{background-color: #0b3b6f;}}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Header
# -------------------------
st.markdown(f"<div class='header-card'>Sytner AutoSense — POC</div>", unsafe_allow_html=True)

# -------------------------
# Session state
# -------------------------
if "reg" not in st.session_state: st.session_state.reg = None
if "image" not in st.session_state: st.session_state.image = None
if "show_summary" not in st.session_state: st.session_state.show_summary = False

# -------------------------
# Input page
# -------------------------
if not st.session_state.show_summary:
    st.markdown("## Enter Vehicle Registration or Take Photo")
    option = st.radio("Choose input method", ["Enter Registration / VIN", "Take Photo"], index=0)

    if option == "Enter Registration / VIN":
        manual_reg = st.text_input("Enter registration / VIN", placeholder="KT68XYZ or VIN...")
        if manual_reg:
            st.session_state.reg = manual_reg.strip().upper().replace(" ", "")
            st.session_state.show_summary = True
    elif option == "Take Photo":
        image = st.camera_input("Take photo of the number plate (use rear camera on mobile)")
        if image:
            st.session_state.image = image
            st.session_state.reg = "KT68XYZ"  # Mock OCR
            st.session_state.show_summary = True

# -------------------------
# Summary page
# -------------------------
if st.session_state.show_summary and st.session_state.reg:
    # Reset button
    if st.button("Change / Reset Registration"):
        st.session_state.reg = None
        st.session_state.image = None
        st.session_state.show_summary = False
        st.experimental_rerun()

    reg = st.session_state.reg
    image = st.session_state.image

    # Display numberplate
    if image:
        st.image(ImageOps.exif_transpose(Image.open(image)), width=320)
    st.markdown(f"<div class='numberplate'>{reg}</div>", unsafe_allow_html=True)

    # Fetch mocked data
    vehicle = lookup_vehicle_basic(reg)
    mot_tax = lookup_mot_and_tax(reg)
    recalls = lookup_recalls(reg)

    # Mock flags
    history_flags = {
        "write_off": False,
        "theft": False,
        "mileage_anomaly": True,
        "note": "Mileage shows a 5,000 jump in 2021 record"
    }

    # Vehicle Summary with badges
    st.markdown("<div class='content-card' style='margin-left:auto;margin-right:auto;width:fit-content;'>", unsafe_allow_html=True)
    st.markdown("<h4>Vehicle Summary</h4>", unsafe_allow_html=True)
    summary_html = f"""
    <p><strong>Make & Model:</strong> {vehicle['make']} {vehicle['model']}</p>
    <p><strong>Year:</strong> {vehicle['year']}</p>
    <p><strong>VIN:</strong> {vehicle['vin']}</p>
    <p><strong>Mileage:</strong> {vehicle['mileage']:,} miles</p>
    <p><strong>Next MOT:</strong> {mot_tax['mot_next_due']}</p>
    """

    # Badges
    flags_html = "<p><strong>Status:</strong> "
    flag_list = []
    if history_flags.get("write_off"):
        flag_list.append('<span class="badge badge-error">Write-off</span>')
    if history_flags.get("theft"):
        flag_list.append('<span class="badge badge-error">Theft</span>')
    if history_flags.get("mileage_anomaly"):
        flag_list.append('<span class="badge badge-warning">Mileage Anomaly</span>')
    open_recalls = sum(1 for r in recalls if r["open"])
    if open_recalls:
        flag_list.append(f'<span class="badge badge-warning">{open_recalls} Open Recall(s)</span>')
    flags_html += " ".join(flag_list) + "</p>"

    st.markdown(summary_html + flags_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # MOT History
    with st.expander("MOT History"):
        for t in mot_tax['mot_history']:
            st.write(f"- {t['date']}: **{t['result']}** — {t['mileage']} miles")

    # Recalls
    with st.expander("Recalls"):
        for r in recalls:
            status = "Open ⚠️" if r['open'] else "Closed ✅"
            st.write(f"- {r['summary']} — ID: {r['id']} ({status})")

    # Insurance
    with st.expander("Insurance (Mock)"):
        st.info("Insurance quotes are mocked. Integrate aggregator APIs for live quotes.")
        if st.button('Get a mock insurance quote'):
            st.success('Sample quote: £320/year (3rd party, excess £250)')

    # Valuation card with Send to Buyer
    st.markdown("<div class='content-card' style='margin-left:auto;margin-right:auto;width:fit-content;'>", unsafe_allow_html=True)
    st.markdown("<h4>Valuation</h4>", unsafe_allow_html=True)
    condition = st.radio("Select condition", ["excellent", "good", "fair", "poor"], index=1, horizontal=True)
    value = estimate_value(vehicle["make"], vehicle["model"], vehicle["year"], vehicle["mileage"], condition)
    st.markdown(f"<p><strong>Estimated Value:</strong> £{value:,} ({condition.capitalize()})</p>", unsafe_allow_html=True)
    if st.button("Send to Sytner Buyer"):
        st.success("Sent successfully!")
    st.markdown("<small>Buyer: John Smith | 01234 567890</small>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
