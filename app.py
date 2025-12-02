import streamlit as st
from PIL import Image, ImageOps
import datetime, io, json

# -------------------------
# Theme Config
# -------------------------
PRIMARY = "#0b3b6f"
ACCENT = "#1e90ff"
PAGE_BG = "#e6f0fa"

st.set_page_config(page_title="Sytner AutoSense", page_icon="🚗", layout="centered")

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
    max-width: 600px;
    margin-left:auto;
    margin-right:auto;
}}
.content-card {{
    background-color: white;
    padding: 16px 20px;
    border-radius: 12px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    margin-bottom: 16px;
    max-width: 600px;
    margin-left:auto;
    margin-right:auto;
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
    margin-bottom: 24px;
    width: fit-content;
    margin-left:auto;
    margin-right:auto;
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
# Mock helpers
# -------------------------
def lookup_vehicle_basic(reg):
    return {"reg": reg, "make":"BMW", "model":"3 Series", "year":2018, "vin":"WBA8BFAKEVIN12345", "mileage":54000}

def lookup_mot_and_tax(reg):
    today = datetime.date.today()
    return {"mot_next_due": (today + datetime.timedelta(days=120)).isoformat(),
            "mot_history":[{"date":"2024-08-17","result":"Pass","mileage":52000},
                           {"date":"2023-08-10","result":"Advisory","mileage":48000}],
            "tax_expiry":(today + datetime.timedelta(days=30)).isoformat()}

def lookup_recalls(reg): 
    return [{"id":"R-2023-001","summary":"Airbag inflator recall - replace module","open":True}]

def lookup_history_flags(reg):
    return {"write_off": False, "theft": False, "mileage_anomaly": True, "note":"Mileage shows a 5,000 jump in 2021 record"}

def estimate_value(make, model, year, mileage, condition="good"):
    age = datetime.date.today().year - year
    base = 25000 - (age*2000) - (mileage/10)
    cond_multiplier = {"excellent":1.05,"good":1.0,"fair":0.9,"poor":0.8}
    return max(100,int(base*cond_multiplier.get(condition,1.0)))

# -------------------------
# Session State
# -------------------------
if "reg" not in st.session_state: st.session_state.reg = None
if "image" not in st.session_state: st.session_state.image = None
if "show_summary" not in st.session_state: st.session_state.show_summary = False

# -------------------------
# Header
# -------------------------
st.markdown(f"<div class='header-card'>Sytner AutoSense — POC</div>", unsafe_allow_html=True)

# -------------------------
# Input Page
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
        image = st.camera_input("Take photo of the number plate")
        if image:
            st.session_state.image = image
            st.session_state.reg = "KT68XYZ"  # Mock OCR
            st.session_state.show_summary = True

# -------------------------
# Summary Page
# -------------------------
if st.session_state.show_summary and st.session_state.reg:
    reg = st.session_state.reg
    image = st.session_state.image

    # Centered layout using a single column
    cols = st.columns([1,6,1])
    with cols[1]:

        # Reset / Change Reg button
        if st.button("Change / Reset Registration"):
            st.session_state.reg = None
            st.session_state.image = None
            st.session_state.show_summary = False
            st.experimental_rerun = False  # safe no-op for newer Streamlit

        # Display numberplate
        if image:
            st.image(ImageOps.exif_transpose(Image.open(image)), width=320)
        st.markdown(f"<div class='numberplate'>{reg}</div>", unsafe_allow_html=True)

        # Fetch data
        vehicle = lookup_vehicle_basic(reg)
        mot_tax = lookup_mot_and_tax(reg)
        recalls = lookup_recalls(reg)
        history_flags = lookup_history_flags(reg)

        # Vehicle Summary Card
        st.markdown("<div class='content-card'>", unsafe_allow_html=True)
        st.markdown(f"""
        <h4>Vehicle Summary</h4>
        <p><strong>Make & Model:</strong> {vehicle['make']} {vehicle['model']}</p>
        <p><strong>Year:</strong> {vehicle['year']}</p>
        <p><strong>VIN:</strong> {vehicle['vin']}</p>
        <p><strong>Mileage:</strong> {vehicle['mileage']:,} miles</p>
        <p><strong>Next MOT:</strong> {mot_tax['mot_next_due']}</p>
        """, unsafe_allow_html=True)
        # Flags
        if history_flags.get("write_off"):
            st.error("This vehicle has a previous write-off record")
        if history_flags.get("theft"):
            st.error("This vehicle has a theft record")
        if history_flags.get("mileage_anomaly"):
            st.warning(history_flags.get("note"))
        st.markdown("</div>", unsafe_allow_html=True)

        # Recalls Expander
        with st.expander("Recalls"):
            if any(r['open'] for r in recalls):
                for r in recalls:
                    if r['open']:
                        st.warning(f"Open recall: {r['summary']} — ID: {r['id']}")
            else:
                st.success("No open recalls found")

        # MOT History Expander
        with st.expander("MOT History"):
            for t in mot_tax['mot_history']:
                st.write(f"- {t['date']}: **{t['result']}** — {t['mileage']} miles")

        # Valuation Card
        condition = st.radio("Select condition", ["excellent","good","fair","poor"], index=1, horizontal=True)
        value = estimate_value(vehicle["make"], vehicle["model"], vehicle["year"], vehicle["mileage"], condition)
        st.markdown(f"<div class='content-card'><h4>Valuation</h4><p>£{value:,} ({condition.capitalize()})</p></div>", unsafe_allow_html=True)

        # Send to Buyer
        if st.button("Send to Sytner Buyer"):
            st.success("Sent successfully! Buyer: John Smith | 01234 567890")

        # Insurance Expander
        with st.expander("Insurance (Mocked)"):
            st.info("Insurance quotes are mocked in this POC.")
            if st.button("Get a mock insurance quote"):
                st.success("Sample quote: £320/year (3rd party, excess £250)")

        # Snapshot Expander
        with st.expander("Download JSON Snapshot"):
            snapshot = {
                'vehicle': vehicle,
                'mot_tax': mot_tax,
                'recalls': recalls,
                'history_flags': history_flags,
                'valuation': {'value': value, 'condition': condition},
                'queried_at': datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            st.download_button('Download JSON snapshot', data=json.dumps(snapshot, indent=2),
                               file_name=f"{reg}_snapshot.json", mime='application/json')
