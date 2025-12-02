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

# Color scheme - Dark blue iOS style
DARK_BG = "#0a2540"
CARD_BG = "#1a3a5c"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#a0b8d0"
ACCENT = "#4a9eff"
SUCCESS = "#34c759"

# Custom CSS
st.markdown(f"""
<style>
/* Hide Streamlit branding */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

[data-testid="stAppViewContainer"] {{
    background: linear-gradient(180deg, {DARK_BG} 0%, #0d2f4d 100%);
    padding-top: 20px;
}}

/* Hide default padding */
.block-container {{
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 500px;
}}

/* Header styling */
.app-header {{
    text-align: center;
    margin-bottom: 40px;
    padding: 0 20px;
}}

.app-title {{
    font-size: 32px;
    font-weight: 300;
    color: {TEXT_PRIMARY};
    margin: 0;
    line-height: 1.2;
}}

.app-subtitle {{
    font-size: 48px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    margin: 0;
    line-height: 1.2;
}}

/* Number plate styling */
.numberplate {{
    background: linear-gradient(to bottom, #f9f9f9 0%, #e8e8e8 100%);
    border: 3px solid #000;
    border-radius: 8px;
    padding: 16px 24px;
    font-size: 36px;
    font-weight: 900;
    color: #000;
    text-align: center;
    margin: 30px auto;
    max-width: 280px;
    letter-spacing: 4px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}}

/* Card styling */
.info-card {{
    background-color: {CARD_BG};
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}}

.card-title {{
    font-size: 22px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
    margin-bottom: 16px;
}}

.status-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 0;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}}

.status-row:last-child {{
    border-bottom: none;
}}

.status-label {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 18px;
    color: {TEXT_PRIMARY};
    font-weight: 500;
}}

.status-value {{
    font-size: 16px;
    color: {TEXT_SECONDARY};
    text-align: right;
}}

.check-icon {{
    width: 28px;
    height: 28px;
    background-color: {SUCCESS};
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 16px;
}}

.warning-icon {{
    width: 28px;
    height: 28px;
    background-color: #ff9500;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 16px;
}}

.value-display {{
    text-align: center;
    padding: 24px;
}}

.value-amount {{
    font-size: 56px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    margin: 16px 0 8px 0;
}}

.value-condition {{
    font-size: 18px;
    color: {TEXT_SECONDARY};
}}

.car-icon {{
    font-size: 48px;
    color: {ACCENT};
}}

/* Buttons */
.stButton>button {{
    background-color: {ACCENT};
    color: white;
    font-weight: 600;
    border-radius: 12px;
    border: none;
    padding: 12px 24px;
    font-size: 16px;
    width: 100%;
}}

.stButton>button:hover {{
    background-color: #3a8eef;
}}

/* Recall card */
.recall-card {{
    background-color: {CARD_BG};
    border-radius: 16px;
    padding: 20px;
    margin: 16px 0;
    cursor: pointer;
}}

.recall-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.recall-title {{
    font-size: 20px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
}}

.recall-subtitle {{
    font-size: 14px;
    color: {TEXT_SECONDARY};
    margin-top: 4px;
}}

.chevron {{
    color: {TEXT_SECONDARY};
    font-size: 24px;
}}

/* Hide streamlit elements */
.stExpander {{
    background-color: transparent !important;
    border: none !important;
}}

div[data-testid="stExpander"] {{
    background-color: {CARD_BG};
    border-radius: 16px;
    border: none;
}}

.streamlit-expanderHeader {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    font-size: 20px;
    font-weight: 600;
}}

/* Input styling */
.stTextInput>div>div>input {{
    background-color: {CARD_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 12px;
    padding: 16px;
    font-size: 16px;
}}

.stRadio>div {{
    background-color: {CARD_BG};
    padding: 16px;
    border-radius: 12px;
}}

.stRadio label {{
    color: {TEXT_PRIMARY};
}}

/* Reset button */
.reset-btn {{
    background-color: transparent !important;
    color: {ACCENT} !important;
    border: 2px solid {ACCENT} !important;
}}
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
# Input Page
# -------------------------
def show_input_page():
    """Display the vehicle registration input page"""
    
    # Header
    st.markdown("""
    <div class='app-header'>
        <div class='app-title'>Sytner</div>
        <div class='app-subtitle'>AutoSense</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Input card
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    
    option = st.radio(
        "Choose input method",
        ["Enter Registration", "Take Photo"],
        index=0,
        horizontal=True,
        label_visibility="collapsed"
    )

    if option == "Enter Registration":
        manual_reg = st.text_input(
            "Enter registration",
            placeholder="e.g. KT68 XYZ",
            label_visibility="collapsed"
        )
        
        if st.button("Look Up Vehicle", disabled=not manual_reg):
            if manual_reg and len(manual_reg.strip()) >= 5:
                st.session_state.reg = manual_reg.strip().upper().replace(" ", "")
                st.session_state.image = None
                st.session_state.show_summary = True
                st.rerun()
            else:
                st.error("Please enter a valid registration")
    
    elif option == "Take Photo":
        image = st.camera_input(
            "Take photo of the number plate",
            help="Position the number plate clearly in the frame",
            label_visibility="collapsed"
        )
        
        if image is not None:
            extracted_reg = mock_ocr_numberplate(image)
            
            if extracted_reg:
                st.session_state.reg = extracted_reg
                st.session_state.image = image
                st.session_state.show_summary = True
                st.rerun()
            else:
                st.error("Could not read number plate. Please try again.")
    
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Summary Page
# -------------------------
def show_summary_page():
    """Display the vehicle summary page"""
    reg = st.session_state.reg
    image = st.session_state.image
    
    # Header
    st.markdown("""
    <div class='app-header'>
        <div class='app-title'>Sytner</div>
        <div class='app-subtitle'>AutoSense</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Number plate
    formatted_reg = reg[:4] + " " + reg[4:] if len(reg) > 4 else reg
    st.markdown(
        f"<div class='numberplate'>{formatted_reg}</div>",
        unsafe_allow_html=True
    )
    
    # Fetch vehicle data
    with st.spinner(""):
        vehicle = lookup_vehicle_basic(reg)
        mot_tax = lookup_mot_and_tax(reg)
        recalls = lookup_recalls(reg)
        history_flags = get_history_flags(reg)
    
    # Recalls card
    open_recalls = sum(1 for r in recalls if r["open"])
    
    st.markdown("<div class='recall-card'>", unsafe_allow_html=True)
    if open_recalls > 0:
        st.markdown(f"""
        <div class='recall-header'>
            <div>
                <div class='recall-title'>⚠️ {open_recalls} open recall{'s' if open_recalls > 1 else ''}</div>
                <div class='recall-subtitle'>Check for safety recalls</div>
            </div>
            <div class='chevron'>›</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='recall-header'>
            <div>
                <div class='recall-title'>No open recalls</div>
                <div class='recall-subtitle'>Check for safety recalls</div>
            </div>
            <div class='chevron'>›</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Expand recalls section
    if open_recalls > 0:
        with st.expander("View recall details", expanded=False):
            for idx, recall in enumerate(recalls):
                if recall['open']:
                    st.markdown(f"**{recall['summary']}**")
                    st.markdown(f"ID: `{recall['id']}`")
                    
                    if st.button("📅 Book Repair", key=f"book_recall_{idx}"):
                        st.session_state[f"booking_recall_{idx}"] = True
                    
                    # Booking form
                    if st.session_state.get(f"booking_recall_{idx}", False):
                        st.markdown("---")
                        
                        garage = st.selectbox(
                            "Select Garage",
                            [
                                "Sytner BMW Birmingham",
                                "Sytner BMW Manchester",
                                "Sytner BMW London",
                                "Sytner BMW Bristol"
                            ],
                            key=f"garage_{idx}"
                        )
                        
                        min_date = datetime.date.today() + datetime.timedelta(days=1)
                        max_date = datetime.date.today() + datetime.timedelta(days=60)
                        
                        booking_date = st.date_input(
                            "Preferred Date",
                            min_value=min_date,
                            max_value=max_date,
                            key=f"date_{idx}"
                        )
                        
                        time_slot = st.selectbox(
                            "Preferred Time",
                            ["9:00 AM", "11:00 AM", "2:00 PM", "4:00 PM"],
                            key=f"time_{idx}"
                        )
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            customer_name = st.text_input("Name", key=f"name_{idx}")
                        with col_b:
                            customer_phone = st.text_input("Phone", key=f"phone_{idx}")
                        
                        col_x, col_y = st.columns(2)
                        with col_x:
                            if st.button("✅ Confirm", key=f"confirm_{idx}", use_container_width=True):
                                if customer_name and customer_phone:
                                    st.success(f"✅ Booked at **{garage}** on **{booking_date}** at **{time_slot}**")
                                    st.session_state[f"booking_recall_{idx}"] = False
                                else:
                                    st.error("Please fill in all fields")
                        with col_y:
                            if st.button("Cancel", key=f"cancel_{idx}", use_container_width=True):
                                st.session_state[f"booking_recall_{idx}"] = False
                                st.rerun()
                    
                    st.markdown("---")
    
    # Vehicle status card
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>Vehicle status</div>", unsafe_allow_html=True)
    
    # MOT
    mot_date = datetime.datetime.fromisoformat(mot_tax['mot_next_due']).strftime("%d %b %Y")
    st.markdown(f"""
    <div class='status-row'>
        <div class='status-label'>
            <div class='check-icon'>✓</div>
            <span>MOT</span>
        </div>
        <div class='status-value'>Expires {mot_date}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tax
    tax_date = datetime.datetime.fromisoformat(mot_tax['tax_expiry']).strftime("%d %b %Y")
    st.markdown(f"""
    <div class='status-row'>
        <div class='check-icon'>✓</div>
        <div class='status-label'>
            <span>Tax</span>
        </div>
        <div class='status-value'>Expires {tax_date}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Insurance card
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='status-row'>
        <div class='status-label'>
            <span style='font-size: 18px; font-weight: 500;'>Insurance</span>
        </div>
        <div class='status-value' style='color: {ACCENT}; font-weight: 600;'>Get a quote ›</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Valuation card
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>Estimated value</div>", unsafe_allow_html=True)
    
    condition = st.radio(
        "Condition",
        ["excellent", "good", "fair", "poor"],
        index=1,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    value = estimate_value(
        vehicle["make"],
        vehicle["model"],
        vehicle["year"],
        vehicle["mileage"],
        condition
    )
    
    st.markdown(f"""
    <div class='value-display'>
        <div class='car-icon'>🚗</div>
        <div class='value-amount'>£{value:,}</div>
        <div class='value-condition'>{condition.capitalize()} condition</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📤 Send to Buyer"):
        st.success("✅ Sent to John Smith")
        st.balloons()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Vehicle details expander
    with st.expander("📋 View full vehicle details"):
        st.markdown(f"**Make & Model:** {vehicle['make']} {vehicle['model']}")
        st.markdown(f"**Year:** {vehicle['year']}")
        st.markdown(f"**VIN:** {vehicle['vin']}")
        st.markdown(f"**Mileage:** {vehicle['mileage']:,} miles")
        
        if history_flags.get("mileage_anomaly"):
            st.warning(f"⚠️ {history_flags['note']}")
        
        st.markdown("---")
        st.markdown("**MOT History**")
        for entry in mot_tax['mot_history']:
            result_emoji = "✅" if entry['result'] == "Pass" else "⚠️"
            st.markdown(f"{result_emoji} {entry['date']}: {entry['result']} — {entry['mileage']:,} miles")
    
    # Reset button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Check Another Vehicle", key="reset_btn"):
        reset_state()
        st.rerun()

# -------------------------
# Main App Logic
# -------------------------
if st.session_state.show_summary and st.session_state.reg:
    show_summary_page()
else:
    show_input_page()
