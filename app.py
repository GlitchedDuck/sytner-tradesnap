import streamlit as st
from PIL import Image, ImageOps
import datetime
import re

# -------------------------
# Mock Data Functions
# -------------------------
def lookup_vehicle_basic(reg):
    """Mock vehicle lookup - replace with real API"""
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
    """Mock MOT and tax lookup - replace with DVLA API"""
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
    """Mock recall lookup - replace with DVSA API"""
    return [
        {"id": "R-2023-001", "summary": "Airbag inflator recall - replace module", "open": True},
        {"id": "R-2022-012", "summary": "Steering column check", "open": False}
    ]

def get_history_flags(reg):
    """Mock history check - replace with HPI/Experian API"""
    return {
        "write_off": False,
        "theft": False,
        "mileage_anomaly": True,
        "note": "Mileage shows a 5,000 jump in 2021 record"
    }

def estimate_value(make, model, year, mileage, condition="good"):
    """Mock valuation - replace with CAP/Glass's API"""
    age = datetime.date.today().year - year
    base = 25000 - (age * 2000) - (mileage / 10)
    cond_multiplier = {"excellent": 1.05, "good": 1.0, "fair": 0.9, "poor": 0.8}
    return max(100, int(base * cond_multiplier.get(condition, 1.0)))

def mock_ocr_numberplate(image):
    """Mock OCR - replace with ANPR API"""
    return "KT68XYZ"

# -------------------------
# Streamlit Configuration
# -------------------------
st.set_page_config(
    page_title="Sytner AutoSense",
    page_icon="🚗",
    layout="centered"
)

# Color scheme
PRIMARY = "#0b3b6f"
ACCENT = "#1e90ff"
PAGE_BG = "#e6f0fa"

# Custom CSS
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
    color: {PRIMARY};
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
    margin-bottom: 24px;
}}
.badge {{
    padding: 4px 10px;
    border-radius: 12px;
    color: white;
    margin-right: 4px;
    font-size: 12px;
    display: inline-block;
}}
.badge-warning {{background-color: #ff9800;}}
.badge-error {{background-color: #f44336;}}
.badge-info {{background-color: #0b3b6f;}}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Session State Initialization
# -------------------------
def init_session_state():
    """Initialize session state variables"""
    if "reg" not in st.session_state:
        st.session_state.reg = None
    if "image" not in st.session_state:
        st.session_state.image = None
    if "show_summary" not in st.session_state:
        st.session_state.show_summary = False
    if "vehicle_data" not in st.session_state:
        st.session_state.vehicle_data = None

def reset_state():
    """Reset all session state"""
    st.session_state.reg = None
    st.session_state.image = None
    st.session_state.show_summary = False
    st.session_state.vehicle_data = None

init_session_state()

# -------------------------
# Header
# -------------------------
st.markdown(
    "<div class='header-card'>Sytner AutoSense — POC</div>",
    unsafe_allow_html=True
)

# -------------------------
# Input Page
# -------------------------
def show_input_page():
    """Display the vehicle registration input page"""
    st.markdown("## Enter Vehicle Registration or Take Photo")
    
    option = st.radio(
        "Choose input method",
        ["Enter Registration / VIN", "Take Photo"],
        index=0,
        horizontal=True
    )

    if option == "Enter Registration / VIN":
        manual_reg = st.text_input(
            "Enter registration / VIN",
            placeholder="e.g. KT68XYZ or WBA8BFAKEVIN12345"
        )
        
        if st.button("Look Up Vehicle", disabled=not manual_reg):
            if manual_reg and len(manual_reg.strip()) >= 5:
                st.session_state.reg = manual_reg.strip().upper().replace(" ", "")
                st.session_state.image = None
                st.session_state.show_summary = True
                st.rerun()
            else:
                st.error("Please enter a valid registration or VIN")
    
    elif option == "Take Photo":
        image = st.camera_input(
            "Take photo of the number plate",
            help="Position the number plate clearly in the frame"
        )
        
        if image is not None:
            # Process the image
            extracted_reg = mock_ocr_numberplate(image)
            
            if extracted_reg:
                st.session_state.reg = extracted_reg
                st.session_state.image = image
                st.session_state.show_summary = True
                st.rerun()
            else:
                st.error("Could not read number plate. Please try again or enter manually.")

# -------------------------
# Summary Page
# -------------------------
def show_summary_page():
    """Display the vehicle summary page"""
    reg = st.session_state.reg
    image = st.session_state.image
    
    # Reset button at the top
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Check Another Vehicle", use_container_width=True):
            reset_state()
            st.rerun()
    
    st.markdown("---")
    
    # Display captured image if available
    if image:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(
                ImageOps.exif_transpose(Image.open(image)),
                use_container_width=True,
                caption="Captured Image"
            )
    
    # Display number plate
    st.markdown(
        f"<div class='numberplate'>{reg}</div>",
        unsafe_allow_html=True
    )
    
    # Fetch vehicle data (with loading spinner)
    with st.spinner("Fetching vehicle information..."):
        vehicle = lookup_vehicle_basic(reg)
        mot_tax = lookup_mot_and_tax(reg)
        recalls = lookup_recalls(reg)
        history_flags = get_history_flags(reg)
    
    # Vehicle Summary Card
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.markdown("#### Vehicle Summary")
    
    # Basic info
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Make & Model:** {vehicle['make']} {vehicle['model']}")
        st.markdown(f"**Year:** {vehicle['year']}")
        st.markdown(f"**Mileage:** {vehicle['mileage']:,} miles")
    with col2:
        st.markdown(f"**VIN:** {vehicle['vin']}")
        st.markdown(f"**Next MOT:** {mot_tax['mot_next_due']}")
        st.markdown(f"**Tax Expiry:** {mot_tax['tax_expiry']}")
    
    # Status badges
    st.markdown("---")
    st.markdown("**Status Flags:**")
    
    flags_html = ""
    if history_flags.get("write_off"):
        flags_html += '<span class="badge badge-error">Write-off</span> '
    if history_flags.get("theft"):
        flags_html += '<span class="badge badge-error">Theft Record</span> '
    if history_flags.get("mileage_anomaly"):
        flags_html += '<span class="badge badge-warning">Mileage Anomaly</span> '
    
    open_recalls = sum(1 for r in recalls if r["open"])
    if open_recalls:
        flags_html += f'<span class="badge badge-warning">{open_recalls} Open Recall(s)</span> '
    
    if not flags_html:
        flags_html = '<span class="badge badge-info">No Issues</span>'
    
    st.markdown(flags_html, unsafe_allow_html=True)
    
    if history_flags.get("note"):
        st.info(f"ℹ️ {history_flags['note']}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # MOT History
    with st.expander("📋 MOT History", expanded=False):
        for entry in mot_tax['mot_history']:
            result_emoji = "✅" if entry['result'] == "Pass" else "⚠️"
            st.markdown(
                f"{result_emoji} **{entry['date']}**: {entry['result']} — {entry['mileage']:,} miles"
            )
    
    # Recalls
    with st.expander("🔔 Recalls", expanded=False):
        if not recalls:
            st.success("No recalls found for this vehicle")
        else:
            for recall in recalls:
                status = "⚠️ **Open**" if recall['open'] else "✅ Closed"
                st.markdown(f"- {recall['summary']}")
                st.markdown(f"  - ID: `{recall['id']}` — Status: {status}")
    
    # Insurance
    with st.expander("🛡️ Insurance Quote", expanded=False):
        st.info("Insurance quotes are mocked. Integrate with aggregator APIs for live quotes.")
        if st.button('Get Mock Insurance Quote'):
            st.success('Sample quote: **£320/year** (3rd party, excess £250)')
    
    # Valuation Card
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.markdown("#### 💰 Valuation")
    
    condition = st.radio(
        "Select vehicle condition",
        ["excellent", "good", "fair", "poor"],
        index=1,
        horizontal=True
    )
    
    value = estimate_value(
        vehicle["make"],
        vehicle["model"],
        vehicle["year"],
        vehicle["mileage"],
        condition
    )
    
    st.markdown(
        f"**Estimated Value:** <span style='font-size: 24px; color: {PRIMARY}; font-weight: 700;'>£{value:,}</span>",
        unsafe_allow_html=True
    )
    st.caption(f"Condition: {condition.capitalize()}")
    
    st.markdown("---")
    
    # Send to buyer section
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**Assigned Buyer:** John Smith | 📞 01234 567890")
    with col2:
        if st.button("📤 Send to Buyer", use_container_width=True):
            st.success("✅ Sent successfully!")
            st.balloons()
    
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Main App Logic
# -------------------------
if st.session_state.show_summary and st.session_state.reg:
    show_summary_page()
else:
    show_input_page()
