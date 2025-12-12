import json
from pathlib import Path
import random
import string
import streamlit as st
from PIL import Image, ImageOps
import datetime
import re

# ============================================================================
# CONFIGURATION
# ============================================================================

PRIMARY = "#0b3b6f"
ACCENT = "#1e90ff"
PAGE_BG = "#e6f0fa"

PLATE_REGEX = re.compile(r"[A-Z0-9]{5,10}", re.I)

# Sales Pipeline Stages
SALES_STAGES = [
    {"name": "Deposit Taken", "icon": "💰", "color": "#4caf50"},
    {"name": "Demands & Needs", "icon": "📋", "color": "#2196f3"},
    {"name": "Sign/Ink Order", "icon": "✍️", "color": "#9c27b0"},
    {"name": "Sell Option Extras", "icon": "🎁", "color": "#ff9800"},
    {"name": "Collection Day", "icon": "🚗", "color": "#f44336"}
]

GARAGES = [
    "Sytner BMW Cardiff - 285-287 Penarth Road",
    "Sytner BMW Chigwell - Langston Road, Loughton",
    "Sytner BMW Coventry - 128 Holyhead Road",
    "Sytner BMW Harold Wood - A12 Colchester Road",
    "Sytner BMW High Wycombe - 575-647 London Road",
    "Sytner BMW Leicester - Meridian East",
    "Sytner BMW Luton - 501 Dunstable Road",
    "Sytner BMW Maidenhead - Bath Road",
    "Sytner BMW Newport - Oak Way",
    "Sytner BMW Nottingham - Lenton Lane",
    "Sytner BMW Oldbury - 919 Wolverhampton Road",
    "Sytner BMW Sheffield - Brightside Way",
    "Sytner BMW Shrewsbury - 70 Battlefield Road",
    "Sytner BMW Solihull - 520 Highlands Road",
    "Sytner BMW Stevenage - Arlington Business Park",
    "Sytner BMW Sunningdale - Station Road",
    "Sytner BMW Swansea - 375 Carmarthen Road",
    "Sytner BMW Tamworth - Winchester Rd",
    "Sytner BMW Tring - Cow Roast",
    "Sytner BMW Warwick - Fusiliers Way",
    "Sytner BMW Wolverhampton - Lever Street",
    "Sytner BMW Worcester - Knightsbridge Park"
]

GARAGE_COORDS = {
    "Sytner BMW Cardiff": (51.4695, -3.1792),
    "Sytner BMW Chigwell": (51.6460, 0.0750),
    "Sytner BMW Coventry": (52.4162, -1.5121),
    "Sytner BMW Harold Wood": (51.6089, 0.2458),
    "Sytner BMW High Wycombe": (51.6248, -0.7489),
    "Sytner BMW Leicester": (52.6111, -1.1175),
    "Sytner BMW Luton": (51.8929, -0.4372),
    "Sytner BMW Maidenhead": (51.5225, -0.6433),
    "Sytner BMW Newport": (51.5665, -2.9871),
    "Sytner BMW Nottingham": (52.9536, -1.1358),
    "Sytner BMW Oldbury": (52.5050, -2.0150),
    "Sytner BMW Sheffield": (53.4059, -1.4016),
    "Sytner BMW Shrewsbury": (52.7280, -2.7350),
    "Sytner BMW Solihull": (52.4114, -1.7869),
    "Sytner BMW Stevenage": (51.9020, -0.2050),
    "Sytner BMW Sunningdale": (51.3989, -0.6600),
    "Sytner BMW Swansea": (51.6565, -3.9900),
    "Sytner BMW Tamworth": (52.6342, -1.6950),
    "Sytner BMW Tring": (51.7950, -0.6600),
    "Sytner BMW Warwick": (52.2819, -1.5850),
    "Sytner BMW Wolverhampton": (52.5867, -2.1280),
    "Sytner BMW Worcester": (52.1936, -2.2200)
}

TIME_SLOTS = ["09:00 AM", "11:00 AM", "02:00 PM", "04:00 PM"]

# ============================================================================
# MOCK API FUNCTIONS
# ============================================================================

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates using Haversine formula"""
    from math import radians, sin, cos, sqrt, atan2
    R = 3959
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def find_nearest_garage(user_lat, user_lon):
    """Find the nearest Sytner garage"""
    nearest_garage = None
    min_distance = float('inf')
    for garage_name, (lat, lon) in GARAGE_COORDS.items():
        distance = calculate_distance(user_lat, user_lon, lat, lon)
        if distance < min_distance:
            min_distance = distance
            nearest_garage = garage_name
    for garage in GARAGES:
        if garage.startswith(nearest_garage):
            return garage, min_distance
    return None, None

def lookup_vehicle_basic(reg):
    """Mock vehicle lookup"""
    reg_clean = reg.upper().replace(" ", "")
    return {
        "reg": reg_clean,
        "make": "BMW",
        "model": "3 Series",
        "year": 2018,
        "vin": "WBA8BFAKEVIN12345",
        "mileage": 54000
    }

def lookup_mot_and_tax(reg):
    """Mock MOT and tax lookup"""
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
    """Mock recall lookup"""
    return [
        {"id": "R-2023-001", "summary": "Airbag inflator recall - replace module", "open": True},
        {"id": "R-2022-012", "summary": "Steering column check", "open": False}
    ]

def get_history_flags(reg):
    """Mock history check"""
    return {
        "write_off": False,
        "theft": False,
        "mileage_anomaly": True,
        "note": "Mileage shows a 5,000 jump in 2021 record"
    }

def estimate_value(make, model, year, mileage, condition="good"):
    """Mock valuation"""
    age = datetime.date.today().year - year
    base = 25000 - (age * 2000) - (mileage / 10)
    cond_multiplier = {"excellent": 1.05, "good": 1.0, "fair": 0.9, "poor": 0.8}
    return max(100, int(base * cond_multiplier.get(condition, 1.0)))

def mock_ocr_numberplate(image):
    """Mock OCR"""
    return "KT68XYZ"

def get_sytner_buyers():
    """Return list of Sytner buyers"""
    return [
        {
            "name": "Sarah Mitchell",
            "location": "Sytner BMW Cardiff",
            "area": "South Wales",
            "phone": "029 2046 8000",
            "email": "sarah.mitchell@sytner.co.uk",
            "specialties": ["3 Series", "5 Series", "Estate Cars"],
            "rating": 4.9,
            "deals_completed": 247,
            "covers_garages": ["Sytner BMW Cardiff", "Sytner BMW Swansea", "Sytner BMW Newport"]
        },
        {
            "name": "James Thompson",
            "location": "Sytner BMW Birmingham",
            "area": "West Midlands",
            "phone": "0121 456 7890",
            "email": "james.thompson@sytner.co.uk",
            "specialties": ["X Series", "SUV", "4x4"],
            "rating": 4.8,
            "deals_completed": 312,
            "covers_garages": ["Sytner BMW Oldbury", "Sytner BMW Wolverhampton", "Sytner BMW Tamworth"]
        },
        {
            "name": "Emma Richardson",
            "location": "Sytner BMW Leicester",
            "area": "East Midlands",
            "phone": "0116 234 5678",
            "email": "emma.richardson@sytner.co.uk",
            "specialties": ["M Sport", "Performance", "Diesel"],
            "rating": 4.9,
            "deals_completed": 289,
            "covers_garages": ["Sytner BMW Leicester", "Sytner BMW Nottingham", "Sytner BMW Coventry"]
        },
        {
            "name": "David Chen",
            "location": "Sytner BMW Nottingham",
            "area": "East Midlands",
            "phone": "0115 789 0123",
            "email": "david.chen@sytner.co.uk",
            "specialties": ["3 Series", "Saloon", "Hybrid"],
            "rating": 4.7,
            "deals_completed": 198,
            "covers_garages": ["Sytner BMW Nottingham", "Sytner BMW Sheffield"]
        },
        {
            "name": "Sophie Williams",
            "location": "Sytner BMW Coventry",
            "area": "West Midlands",
            "phone": "024 7655 4321",
            "email": "sophie.williams@sytner.co.uk",
            "specialties": ["All Models", "Quick Deals", "Part Exchange"],
            "rating": 4.9,
            "deals_completed": 356,
            "covers_garages": ["Sytner BMW Coventry", "Sytner BMW Solihull", "Sytner BMW Warwick"]
        },
    ]

# ============================================================================
# SALES CHECK-IN DATA FUNCTIONS
# ============================================================================

def load_sales_data():
    """Load sales check-in data from JSON file"""
    try:
        sales_file = Path("data/sales_records.json")
        if sales_file.exists():
            with open(sales_file, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"Error loading sales data: {e}")
        return []

def generate_tracking_id():
    """Generate unique tracking ID"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

def save_customer_journey(journey_data):
    """Save new customer journey"""
    try:
        journeys_file = Path("data/customer_journeys.json")
        journeys_file.parent.mkdir(exist_ok=True)
        
        if journeys_file.exists():
            with open(journeys_file, 'r') as f:
                journeys = json.load(f)
        else:
            journeys = []
        
        journeys.append(journey_data)
        
        with open(journeys_file, 'w') as f:
            json.dump(journeys, f, indent=2)
        
        return True
    except Exception as e:
        st.warning(f"Could not save journey: {e}")
        return False

def get_journey_by_tracking_id(tracking_id):
    """Get journey by tracking ID"""
    try:
        journeys_file = Path("data/customer_journeys.json")
        if journeys_file.exists():
            with open(journeys_file, 'r') as f:
                journeys = json.load(f)
            for journey in journeys:
                if journey.get('tracking_id') == tracking_id:
                    return journey
    except:
        pass
    return None

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_registration(reg):
    """Validate UK registration format"""
    if not reg:
        return False
    reg_clean = reg.upper().replace(" ", "")
    return len(reg_clean) >= 5 and re.match(r'^[A-Z0-9]+$', reg_clean)

def validate_phone(phone):
    """Basic phone validation"""
    return phone and len(phone.strip()) >= 10

# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================

def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "reg": None,
        "image": None,
        "show_summary": False,
        "vehicle_data": None,
        "booking_forms": {},
        "create_journey_mode": False,
        "journey_data": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_all_state():
    """Reset all session state to initial values"""
    st.session_state.reg = None
    st.session_state.image = None
    st.session_state.show_summary = False
    st.session_state.vehicle_data = None
    st.session_state.booking_forms = {}

# ============================================================================
# ANIMATED WHEEL TRACKER
# ============================================================================

def render_wheel_tracker(current_stage_index, stages):
    """Render an animated car wheel progress tracker"""
    
    total_stages = len(stages)
    progress_percent = ((current_stage_index + 1) / total_stages) * 100
    rotation = (progress_percent / 100) * 360
    current_stage = stages[current_stage_index]
    
    # Build all dots HTML first
    dots_html = ""
    for idx, stage in enumerate(stages):
        if idx < current_stage_index:
            dot_class = "completed"
        elif idx == current_stage_index:
            dot_class = "current"
        else:
            dot_class = "pending"
        
        dots_html += f'<div class="stage-dot {dot_class}" title="{stage["name"]}">{stage["icon"]}</div>'
    
    # Render everything in one markdown call
    st.markdown(f"""
    <style>
    @keyframes pulse {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
    }}
    
    .wheel-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        padding: 40px 20px 60px 20px;
        background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%);
        border-radius: 20px;
        margin: 20px 0;
        min-height: 600px;
    }}
    
    .wheel-wrapper {{
        position: relative;
        width: 280px;
        height: 280px;
        margin-bottom: 30px;
    }}
    
    .wheel-outer {{
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        box-shadow: 0 10px 40px rgba(0,0,0,0.3),
                    inset 0 0 20px rgba(255,255,255,0.1);
        transform: rotate({rotation}deg);
        transition: transform 1s ease-out;
    }}
    
    .wheel-rim {{
        position: absolute;
        width: 90%;
        height: 90%;
        top: 5%;
        left: 5%;
        border-radius: 50%;
        background: conic-gradient(
            from 0deg,
            #3498db 0deg,
            #2ecc71 {progress_percent * 3.6}deg,
            #95a5a6 {progress_percent * 3.6}deg,
            #7f8c8d 360deg
        );
        box-shadow: inset 0 0 30px rgba(0,0,0,0.4);
    }}
    
    .wheel-center {{
        position: absolute;
        width: 50%;
        height: 50%;
        top: 25%;
        left: 25%;
        border-radius: 50%;
        background: linear-gradient(135deg, #ecf0f1 0%, #bdc3c7 100%);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3),
                    inset 0 0 10px rgba(255,255,255,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 48px;
        animation: pulse 2s ease-in-out infinite;
    }}
    
    .progress-text {{
        color: white;
        text-align: center;
    }}
    
    .stage-name {{
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 5px;
    }}
    
    .progress-percent {{
        font-size: 48px;
        font-weight: 900;
        margin-top: 10px;
    }}
    
    .stage-dots {{
        display: flex;
        justify-content: center;
        gap: 15px;
        margin-top: 20px;
        padding: 10px 20px 20px 20px;
        flex-wrap: wrap;
    }}
    
    .stage-dot {{
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        transition: all 0.3s ease;
        border: 3px solid rgba(255,255,255,0.3);
    }}
    
    .stage-dot.completed {{
        background-color: #4caf50;
        border-color: #4caf50;
        box-shadow: 0 0 20px rgba(76, 175, 80, 0.5);
    }}
    
    .stage-dot.current {{
        background-color: white;
        border-color: white;
        animation: pulse 1.5s ease-in-out infinite;
        box-shadow: 0 0 30px rgba(255, 255, 255, 0.8);
    }}
    
    .stage-dot.pending {{
        background-color: rgba(255,255,255,0.2);
        border-color: rgba(255,255,255,0.3);
    }}
    </style>
    
    <div class="wheel-container">
        <div class="wheel-wrapper">
            <div class="wheel-outer">
                <div class="wheel-rim"></div>
                <div class="wheel-center">
                    {current_stage['icon']}
                </div>
            </div>
        </div>
        
        <div class="progress-text">
            <div class="stage-name">{current_stage['name']}</div>
            <div style="font-size: 16px; opacity: 0.9;">Stage {current_stage_index + 1} of {total_stages}</div>
            <div class="progress-percent">{progress_percent:.0f}%</div>
        </div>
        
        <div class="stage-dots">
            {dots_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# STYLING
# ============================================================================

def apply_custom_css():
    """Apply custom CSS styling"""
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
        background-color: {ACCENT} !important;
        color: white !important;
        font-weight: 600;
        border-radius: 8px;
        border: none !important;
        padding: 0.5rem 1rem;
        font-size: 16px;
    }}
    .stButton>button:hover {{
        background-color: #1873cc !important;
    }}
    .stFormSubmitButton>button {{
        background-color: {ACCENT} !important;
        color: white !important;
        font-weight: 600;
        border-radius: 8px;
        border: none !important;
        padding: 0.5rem 1rem;
        font-size: 16px;
    }}
    .numberplate {{
        background-color: #FFC600;
        border: 4px solid #000000;
        border-radius: 8px;
        padding: 20px 32px;
        font-size: 48px;
        font-weight: 900;
        color: #000000;
        text-align: center;
        margin: 24px auto;
        letter-spacing: 8px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.25);
        max-width: 500px;
        font-family: 'Charles Wright', Arial, sans-serif;
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
    .badge-success {{background-color: #4caf50;}}
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_header():
    """Render the application header"""
    st.markdown(f"""
    <div class='header-card' style='background: linear-gradient(135deg, {PRIMARY} 0%, #1a4d7a 100%);'>
        <div style='display: flex; align-items: center; justify-content: center;'>
            <div style='text-align: center;'>
                <div style='font-size: 28px; font-weight: 700;'>Sytner TradeSnap</div>
                <div style='font-size: 14px; opacity: 0.9; font-weight: 400;'>Snap it. Value it. Done.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_reset_button():
    """Render reset button when on summary page"""
    if st.session_state.show_summary:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("New Vehicle Lookup", use_container_width=True):
                reset_all_state()
                st.rerun()

def render_status_badges(history_flags, open_recalls):
    """Render status badges for vehicle"""
    flags_html = "<p><strong>Status Flags:</strong> "
    flag_list = []
    
    if history_flags.get("write_off"):
        flag_list.append('<span class="badge badge-error">Write-off</span>')
    if history_flags.get("theft"):
        flag_list.append('<span class="badge badge-error">Theft Record</span>')
    if history_flags.get("mileage_anomaly"):
        flag_list.append('<span class="badge badge-warning">Mileage Anomaly</span>')
    if open_recalls:
        flag_list.append(f'<span class="badge badge-warning">{open_recalls} Open Recall(s)</span>')
    
    if not flag_list:
        flag_list.append('<span class="badge badge-success">No Issues Found</span>')

    flags_html += " ".join(flag_list) + "</p>"
    st.markdown(flags_html, unsafe_allow_html=True)

def render_vehicle_summary(vehicle, mot_tax, history_flags, open_recalls):
    """Render the main vehicle summary card"""
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.markdown("<h4>Vehicle Summary</h4>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Make & Model:** {vehicle['make']} {vehicle['model']}")
        st.markdown(f"**Year:** {vehicle['year']}")
        st.markdown(f"**Mileage:** {vehicle['mileage']:,} miles")
    with col2:
        st.markdown(f"**VIN:** {vehicle['vin']}")
        st.markdown(f"**Next MOT:** {mot_tax['mot_next_due']}")
        st.markdown(f"**Tax Expiry:** {mot_tax['tax_expiry']}")

    st.markdown("---")
    render_status_badges(history_flags, open_recalls)
    
    if history_flags.get("note"):
        st.info(f"ℹ️ {history_flags['note']}")
    
    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# PAGE RENDERERS - CONTINUE FROM PART 1
# ============================================================================

def render_input_page():
    """Render the vehicle input page"""
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%); 
                padding: 40px 24px; border-radius: 16px; margin-bottom: 32px; text-align: center;'>
        <h1 style='color: white; margin: 0 0 16px 0; font-size: 36px;'>Instant Trade-In Valuation</h1>
        <p style='color: rgba(255,255,255,0.95); font-size: 18px; margin: 0;'>
            Get competitive offers in seconds
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Enter Registration")
    manual_reg = st.text_input("Registration", placeholder="AB12 CDE", label_visibility="collapsed")
    
    if st.button("🔍 Look Up Vehicle", disabled=not manual_reg, type="primary", use_container_width=True):
        if validate_registration(manual_reg):
            st.session_state.reg = manual_reg.strip().upper().replace(" ", "")
            st.session_state.image = None
            st.session_state.show_summary = True
            st.rerun()
        else:
            st.error("❌ Please enter a valid registration")

def render_sytner_buyers(vehicle, reg):
    """Render location-based buyer assignment"""
    buyers = get_sytner_buyers()
    
    st.markdown("##### 📍 Your Location")
    selected_garage = st.selectbox("Choose nearest location", GARAGES, key="garage_selector")
    
    garage_name = selected_garage.split(" - ")[0]
    
    allocated_buyer = None
    for buyer in buyers:
        if garage_name in buyer['covers_garages']:
            allocated_buyer = buyer
            break
    
    if allocated_buyer:
        buyer = allocated_buyer
        is_specialty = any(spec.lower() in vehicle['model'].lower() for spec in buyer['specialties'])
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%); 
                    padding: 14px 18px; border-radius: 10px; margin: 16px 0; color: white;'>
            <div style='font-size: 16px; font-weight: 700;'>{buyer['name']}</div>
            <div style='font-size: 12px; opacity: 0.85; margin-top: 4px;'>
                📍 {buyer['location']} • ★ {buyer['rating']}/5.0 • {buyer['deals_completed']} deals
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Specialties
        st.markdown("<div style='margin: 12px 0;'>", unsafe_allow_html=True)
        for specialty in buyer['specialties']:
            badge_color = "#4caf50" if specialty.lower() in vehicle['model'].lower() else "#e0e0e0"
            text_color = "white" if specialty.lower() in vehicle['model'].lower() else "#666"
            st.markdown(f'<span style="display: inline-block; background-color: {badge_color}; color: {text_color}; padding: 3px 8px; border-radius: 10px; margin-right: 4px; font-size: 12px;">{specialty}</span>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Contact button
        if st.button(f"📲 Contact {buyer['name'].split()[0]}", key=f"ping_{buyer['email']}"):
            st.session_state[f"ping_form_{buyer['email']}"] = True
            st.rerun()
        
        # Ping form
        if st.session_state.get(f"ping_form_{buyer['email']}", False):
            with st.form(key=f"ping_form_submit_{buyer['email']}"):
                st.markdown("#### Send Request")
                
                col1, col2 = st.columns(2)
                with col1:
                    customer_name = st.text_input("Your Name *")
                with col2:
                    customer_phone = st.text_input("Your Phone *")
                
                customer_email = st.text_input("Your Email *")
                urgency = st.select_slider("Timeline", options=["This week", "Within 2 weeks", "Within a month", "Just exploring"])
                
                col_a, col_b = st.columns(2)
                with col_a:
                    submitted = st.form_submit_button("✅ Send", type="primary")
                with col_b:
                    cancelled = st.form_submit_button("❌ Cancel")
                
                if submitted and customer_name and customer_phone and customer_email:
                    ref = f"REQ-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                    st.success(f"✅ Request Sent! Reference: {ref}")
                    st.balloons()
                    del st.session_state[f"ping_form_{buyer['email']}"]
                
                if cancelled:
                    del st.session_state[f"ping_form_{buyer['email']}"]
                    st.rerun()

def render_market_trends(vehicle):
    """Display market trends"""
    st.markdown("#### 📊 Market Intelligence")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #4caf50 0%, #45a049 100%); 
                    padding: 20px; border-radius: 12px; text-align: center; color: white;'>
            <div style='font-size: 32px; font-weight: 700;'>HIGH</div>
            <div style='font-size: 14px; margin-top: 8px;'>Demand Level</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {ACCENT} 0%, #1873cc 100%); 
                    padding: 20px; border-radius: 12px; text-align: center; color: white;'>
            <div style='font-size: 32px; font-weight: 700;'>12</div>
            <div style='font-size: 14px; margin-top: 8px;'>Days to sell</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); 
                    padding: 20px; border-radius: 12px; text-align: center; color: white;'>
            <div style='font-size: 32px; font-weight: 700;'>87%</div>
            <div style='font-size: 14px; margin-top: 8px;'>Of asking price</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("##### 📈 6-Month Price Forecast")
    
    current_value = estimate_value(vehicle["make"], vehicle["model"], vehicle["year"], vehicle["mileage"])
    
    for i in range(1, 7):
        month_date = datetime.date.today() + datetime.timedelta(days=30*i)
        depreciation = -2.5 * i
        projected_value = int(current_value * (1 + depreciation / 100))
        
        st.markdown(f"""
        <div style='padding: 8px 0; border-bottom: 1px solid #ddd;'>
            <div style='display: flex; justify-content: space-between;'>
                <span>{month_date.strftime("%b %Y")}</span>
                <span>
                    <strong>£{projected_value:,}</strong>
                    <span style='color: #f44336; font-size: 13px; margin-left: 8px;'>({depreciation:.1f}%)</span>
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_upgrade_options(vehicle, trade_in_value):
    """Show potential upgrade options"""
    st.markdown("### 🚗 Potential Upgrades")
    
    upgrade_options = [
        {"model": "BMW 3 Series 320d M Sport", "year": 2023, "price": 38000},
        {"model": "BMW X3 xDrive20d M Sport", "year": 2023, "price": 48000},
        {"model": "BMW 5 Series 530e M Sport", "year": 2024, "price": 52000},
    ]
    
    for car in upgrade_options:
        remaining_amount = car['price'] - trade_in_value
        trade_in_percentage = int((trade_in_value / car['price']) * 100)
        monthly_payment = int(remaining_amount * 0.023)
        
        border_color = "#4caf50" if trade_in_percentage >= 40 else ACCENT if trade_in_percentage >= 25 else "#ff9800"
        
        st.markdown(f"""
        <div style='background-color: #f8f9fa; padding: 16px 20px; border-radius: 12px; margin: 12px 0; 
                    border-left: 6px solid {border_color};'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='font-size: 18px; font-weight: 700; color: {PRIMARY};'>
                        🚘 {car['model']}
                    </div>
                    <div style='font-size: 13px; color: #666;'>{car['year']} Model • £{car['price']:,}</div>
                </div>
                <div style='text-align: right;'>
                    <div style='background-color: {border_color}; color: white; padding: 4px 10px; 
                                border-radius: 16px; font-weight: 700; font-size: 13px;'>
                        {trade_in_percentage}% Covered
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(f"""
            <div style='background-color: white; padding: 12px; border-radius: 8px; text-align: center;'>
                <div style='font-size: 10px; color: #999; text-transform: uppercase; margin-bottom: 6px;'>
                    TRADE-IN
                </div>
                <div style='font-size: 20px; font-weight: 700; color: #4caf50;'>
                    £{trade_in_value:,}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
            <div style='background-color: white; padding: 12px; border-radius: 8px; text-align: center;'>
                <div style='font-size: 10px; color: #999; text-transform: uppercase; margin-bottom: 6px;'>
                    YOU PAY
                </div>
                <div style='font-size: 20px; font-weight: 700; color: {PRIMARY};'>
                    £{remaining_amount:,}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_c:
            st.markdown(f"""
            <div style='background-color: white; padding: 12px; border-radius: 8px; text-align: center;'>
                <div style='font-size: 10px; color: #999; text-transform: uppercase; margin-bottom: 6px;'>
                    MONTHLY
                </div>
                <div style='font-size: 20px; font-weight: 700; color: {ACCENT};'>
                    £{monthly_payment}/mo
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_deal_accelerator(base_value):
    """Render deal accelerator bonuses"""
    st.markdown("### 🚀 Deal Bonuses")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style='background-color: #e8f5e9; padding: 24px; border-radius: 12px; border-left: 6px solid #4caf50;'>
            <div style='font-size: 20px; font-weight: 600; color: #2e7d32; margin-bottom: 12px;'>
                📦 Stock Priority Bonus
            </div>
            <div style='font-size: 36px; font-weight: 900; color: #1b5e20; margin-bottom: 8px;'>+£500</div>
            <div style='font-size: 14px; color: #666;'>We need this model in stock!</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='background-color: #e3f2fd; padding: 24px; border-radius: 12px; border-left: 6px solid {ACCENT};'>
            <div style='font-size: 20px; font-weight: 600; color: #1565c0; margin-bottom: 12px;'>
                ⚡ Same-Day Completion
            </div>
            <div style='font-size: 36px; font-weight: 900; color: #0d47a1; margin-bottom: 8px;'>+£200</div>
            <div style='font-size: 14px; color: #666;'>If completed today</div>
        </div>
        """, unsafe_allow_html=True)
    
    total_with_bonuses = base_value + 700
    
    st.markdown(f"""
    <div style='background-color: #fff3cd; padding: 24px; border-radius: 12px; border-left: 4px solid #ffc107; margin-top: 24px;'>
        <div style='text-align: center;'>
            <div style='font-size: 16px; color: #666; margin-bottom: 8px;'><strong>Maximum Potential Offer</strong></div>
            <div style='font-size: 42px; font-weight: 900; color: {PRIMARY};'>£{total_with_bonuses:,}</div>
            <div style='font-size: 14px; color: #666; margin-top: 8px;'><em>Base value + all bonuses • Valid for 48 hours</em></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_mot_history(mot_history):
    """Render MOT history"""
    for record in mot_history:
        result_icon = "✅" if record['result'] == "Pass" else "⚠️"
        result_color = "#4caf50" if record['result'] == "Pass" else "#ff9800"
        st.markdown(f"""
        <div style='background-color: #f5f5f5; padding: 16px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid {result_color};'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div><strong>{result_icon} {record['result']}</strong> - {record['date']}</div>
                <div style='color: #666;'>{record['mileage']:,} miles</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_recalls_section(recalls, vehicle, reg):
    """Render recalls management"""
    if not recalls:
        st.success("✅ No outstanding recalls found for this vehicle")
        return
    
    open_count = sum(1 for r in recalls if r["open"])
    if open_count > 0:
        st.warning(f"⚠️ {open_count} open recall(s) require attention")
    
    for recall in recalls:
        status_icon = "🔴" if recall['open'] else "✅"
        status_text = "OPEN - ACTION REQUIRED" if recall['open'] else "COMPLETED"
        status_color = "#f44336" if recall['open'] else "#4caf50"
        
        st.markdown(f"""
        <div style='background-color: #f5f5f5; padding: 16px; border-radius: 8px; margin-bottom: 16px; border-left: 4px solid {status_color};'>
            <div style='margin-bottom: 8px;'>
                <strong>{status_icon} {status_text}</strong>
                <span style='color: #666; margin-left: 12px; font-size: 13px;'>{recall['id']}</span>
            </div>
            <div style='color: #666; font-size: 15px;'>{recall['summary']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if recall['open']:
            recall_key = f"{recall['id']}_{reg}"
            if st.button(f"📅 Book Repair for {recall['id']}", key=f"book_recall_{recall_key}"):
                st.session_state.booking_forms[recall_key] = True
                st.rerun()
            
            if st.session_state.booking_forms.get(recall_key):
                with st.form(key=f"recall_form_{recall_key}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        garage = st.selectbox("Garage", GARAGES)
                        booking_date = st.date_input("Date", min_value=datetime.date.today())
                    with col2:
                        time_slot = st.selectbox("Time", TIME_SLOTS)
                        customer_name = st.text_input("Name *")
                    
                    customer_phone = st.text_input("Phone *")
                    
                    col_x, col_y = st.columns(2)
                    with col_x:
                        submitted = st.form_submit_button("✅ Confirm", type="primary")
                    with col_y:
                        cancelled = st.form_submit_button("❌ Cancel")
                    
                    if submitted and customer_name and validate_phone(customer_phone):
                        booking_ref = f"RCL-{recall['id']}-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
                        st.success(f"✅ Booking Confirmed! Reference: {booking_ref}")
                        del st.session_state.booking_forms[recall_key]
                        st.balloons()
                    
                    if cancelled:
                        del st.session_state.booking_forms[recall_key]
                        st.rerun()

def render_summary_page():
    """Render the complete vehicle summary page with all tabs"""
    reg = st.session_state.reg
    image = st.session_state.image

    if image:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(ImageOps.exif_transpose(Image.open(image)), use_container_width=True)

    st.markdown(f"<div class='numberplate'>{reg}</div>", unsafe_allow_html=True)

    try:
        with st.spinner("🔄 Fetching vehicle information..."):
            vehicle = lookup_vehicle_basic(reg)
            mot_tax = lookup_mot_and_tax(reg)
            recalls = lookup_recalls(reg)
            history_flags = get_history_flags(reg)
    except Exception as e:
        st.error(f"⚠️ Error fetching vehicle data: {str(e)}")
        st.stop()

    open_recalls = sum(1 for r in recalls if r["open"])
    
    render_vehicle_summary(vehicle, mot_tax, history_flags, open_recalls)
    
    # Quick Market Snapshot
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%); 
                padding: 20px; border-radius: 12px; margin-bottom: 20px; color: white;'>
        <h4 style='margin: 0 0 12px 0;'>📊 Quick Market Snapshot</h4>
        <div style='display: flex; justify-content: space-around; flex-wrap: wrap; gap: 16px;'>
            <div style='text-align: center;'>
                <div style='font-size: 24px; font-weight: 700;'>HIGH</div>
                <div style='font-size: 13px; opacity: 0.9;'>Demand</div>
            </div>
            <div style='text-align: center;'>
                <div style='font-size: 24px; font-weight: 700;'>12 days</div>
                <div style='font-size: 13px; opacity: 0.9;'>To Sell</div>
            </div>
            <div style='text-align: center;'>
                <div style='font-size: 24px; font-weight: 700;'>↑ +5%</div>
                <div style='font-size: 13px; opacity: 0.9;'>Price Trend</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main tabbed interface
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 MOT & Recalls",
        "👤 Contact Buyer",
        "💰 Trade-In Value",
        "🏆 Best Offers",
        "📈 Market Intel"
    ])
    
    with tab1:
        st.markdown("### 📋 MOT Test History")
        render_mot_history(mot_tax['mot_history'])
        st.markdown("---")
        st.markdown("### ⚠️ Safety Recalls Management")
        render_recalls_section(recalls, vehicle, reg)
    
    with tab2:
        st.markdown("### 👤 Connect with Sytner Vehicle Buyer")
        render_sytner_buyers(vehicle, reg)
    
    with tab3:
        base_value = estimate_value(vehicle["make"], vehicle["model"], vehicle["year"], vehicle["mileage"], "good")
        st.markdown("### 💰 Estimated Trade-In Value")
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%); 
                    padding: 28px; border-radius: 12px; text-align: center; color: white; margin-bottom: 24px;'>
            <div style='font-size: 16px; opacity: 0.9; margin-bottom: 8px;'>Estimated Vehicle Value</div>
            <div style='font-size: 48px; font-weight: 900; margin: 12px 0;'>£{base_value:,}</div>
            <div style='font-size: 14px; opacity: 0.85;'>
                {vehicle['year']} {vehicle['make']} {vehicle['model']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        render_upgrade_options(vehicle, base_value)
        
        st.markdown("---")
        render_deal_accelerator(base_value)
    
    with tab4:
        st.markdown("### 🏆 Best Offers Across Sytner Network")
        total_value = base_value + 700
        
        network_data = [
            {"location": "Sytner BMW Solihull", "offer": total_value, "badge": "🏆 Best Offer"},
            {"location": "Sytner BMW Birmingham", "offer": total_value - 200, "badge": ""},
            {"location": "Sytner BMW Coventry", "offer": total_value - 400, "badge": ""},
        ]
        
        for loc in network_data:
            badge_html = f"<span style='color: #ffa726; margin-left: 8px;'>{loc['badge']}</span>" if loc['badge'] else ""
            st.markdown(f"""
            <div style='background-color: #f8f9fa; padding: 16px 20px; border-radius: 8px; margin: 12px 0; 
                        display: flex; justify-content: space-between; align-items: center; border-left: 4px solid {ACCENT};'>
                <div>
                    <strong style='font-size: 16px;'>{loc['location']}</strong>{badge_html}
                </div>
                <div style='text-align: right;'>
                    <div style='font-size: 24px; font-weight: 700; color: {PRIMARY};'>£{loc['offer']:,}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with tab5:
        render_market_trends(vehicle)
    
    # Customer Journey Creation Section
    st.markdown("---")
    st.markdown("### ✨ Create Customer Journey")
    st.markdown("*Convert this trade-in into a tracked sale*")
    
    if st.button("🚀 Start Customer Journey", use_container_width=True, type="primary"):
        st.session_state.create_journey_mode = True
        st.rerun()
    
    if st.session_state.get('create_journey_mode', False):
        with st.form("journey_creation_form"):
            st.markdown("#### Customer & Sale Details")
            
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("Customer Name *", placeholder="John Smith")
                customer_email = st.text_input("Email *", placeholder="john@email.com")
            with col2:
                customer_phone = st.text_input("Phone *", placeholder="07700 900000")
                postcode = st.text_input("Postcode", placeholder="B1 1AA")
            
            col3, col4 = st.columns(2)
            with col3:
                deposit_amount = st.number_input("Deposit Amount (£)", min_value=0, value=1000, step=100)
                collection_date = st.date_input(
                    "Expected Collection Date",
                    min_value=datetime.date.today(),
                    value=datetime.date.today() + datetime.timedelta(days=30)
                )
            with col4:
                garage = st.selectbox("Collection Garage", GARAGES)
                salesperson_name = st.text_input("Salesperson", value="Your Name")
            
            col_a, col_b = st.columns(2)
            with col_a:
                submitted = st.form_submit_button("✅ Create Journey", use_container_width=True, type="primary")
            with col_b:
                cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if submitted:
                if customer_name and customer_email and customer_phone:
                    tracking_id = generate_tracking_id()
                    
                    journey = {
                        "tracking_id": tracking_id,
                        "created_date": datetime.datetime.now().isoformat(),
                        "customer": {
                            "name": customer_name,
                            "email": customer_email,
                            "phone": customer_phone,
                            "postcode": postcode
                        },
                        "vehicle": vehicle,
                        "financial": {
                            "deposit": deposit_amount,
                            "trade_in_value": estimate_value(vehicle["make"], vehicle["model"], vehicle["year"], vehicle["mileage"], "good")
                        },
                        "garage": garage,
                        "salesperson": salesperson_name,
                        "collection_date": collection_date.isoformat(),
                        "current_stage": 0,
                        "stage_history": {
                            SALES_STAGES[0]["name"]: datetime.datetime.now().isoformat()
                        }
                    }
                    
                    save_customer_journey(journey)
                    
                    tracking_url = f"https://your-app.streamlit.app/?track={tracking_id}"
                    
                    st.success(f"""
                    ✅ **Customer Journey Created!**
                    
                    **Tracking ID:** `{tracking_id}`
                    **Customer:** {customer_name}
                    **Vehicle:** {vehicle['year']} {vehicle['make']} {vehicle['model']}
                    """)
                    
                    st.code(tracking_url, language=None)
                    
                    # Share tracking link section
                    st.markdown("---")
                    st.markdown("### 📱 Share Tracking Link with Customer")
                    
                    share_method = st.radio(
                        "How would you like to share?",
                        ["📧 Email", "📱 SMS/Text", "📋 Copy Link"],
                        horizontal=True
                    )
                    
                    if share_method == "📧 Email":
                        with st.form("email_tracking_form"):
                            st.markdown("#### Send via Email")
                            email_to = st.text_input("Customer Email", value=customer_email)
                            email_subject = st.text_input(
                                "Subject", 
                                value=f"Track Your {vehicle['year']} {vehicle['make']} {vehicle['model']} Purchase"
                            )
                            email_message = st.text_area(
                                "Message",
                                value=f"""Hi {customer_name},

Thank you for your purchase! You can track your vehicle's progress using the link below:

{tracking_url}

Your Tracking ID: {tracking_id}

Expected Collection: {collection_date.strftime('%d %B %Y')}

If you have any questions, please don't hesitate to contact us.

Best regards,
{salesperson_name}
Sytner BMW"""
                            )
                            
                            if st.form_submit_button("✉️ Send Email", type="primary"):
                                # In production, integrate with SendGrid, AWS SES, or similar
                                st.success(f"✅ Email sent to {email_to}")
                                st.info("💡 **Note:** In production, integrate with SendGrid, AWS SES, or your email service")
                    
                    elif share_method == "📱 SMS/Text":
                        with st.form("sms_tracking_form"):
                            st.markdown("#### Send via SMS")
                            sms_to = st.text_input("Customer Phone", value=customer_phone)
                            sms_message = st.text_area(
                                "Message (160 chars recommended)",
                                value=f"Hi {customer_name}! Track your {vehicle['make']} {vehicle['model']}: {tracking_url} - Tracking ID: {tracking_id}",
                                max_chars=320
                            )
                            st.caption(f"Character count: {len(sms_message)}/320")
                            
                            if st.form_submit_button("📲 Send SMS", type="primary"):
                                # In production, integrate with Twilio, AWS SNS, or similar
                                st.success(f"✅ SMS sent to {sms_to}")
                                st.info("💡 **Note:** In production, integrate with Twilio, AWS SNS, or your SMS service")
                    
                    else:  # Copy Link
                        st.markdown("#### 📋 Copy & Share Link")
                        st.text_input("Tracking URL", value=tracking_url, key="copy_url_field")
                        
                        # QR Code option
                        if st.button("📱 Generate QR Code"):
                            st.info("💡 **Note:** Install `qrcode` package to generate QR codes: `pip install qrcode[pil]`")
                            st.code(f"""
# To generate QR code:
import qrcode
qr = qrcode.make('{tracking_url}')
qr.save('tracking_qr.png')
                            """)
                    
                    st.balloons()
                    st.session_state.create_journey_mode = False
                else:
                    st.error("⚠️ Please fill in all required fields")
            
            if cancelled:
                st.session_state.create_journey_mode = False
                st.rerun()

# ============================================================================
# SALES PIPELINE PAGE
# ============================================================================

def render_sales_pipeline_page():
    """Render sales pipeline dashboard"""
    st.markdown("### 📊 Sales Pipeline Dashboard")
    st.markdown("*Track all active customer journeys*")
    
    sales_data = load_sales_data()
    
    if sales_data:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Active Sales", len(sales_data))
        with col2:
            total_value = sum(sale['financial'].get('total_price', 0) for sale in sales_data)
            st.metric("Pipeline Value", f"£{total_value:,}")
        with col3:
            needs_attention = sum(1 for sale in sales_data if sale['status'].get('needs_attention', False))
            st.metric("Needs Attention", needs_attention)
        
        st.markdown("---")
        st.markdown("### Recent Sales")
        
        for sale in sales_data[:15]:
            with st.expander(
                f"{sale['customer']['first_name']} {sale['customer']['last_name']} - "
                f"{sale['vehicle']['make']} {sale['vehicle']['model']} ({sale['pipeline']['progress_percentage']}%)"
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Sale ID:** {sale['sale_id']}")
                    st.write(f"**Stage:** {sale['pipeline']['current_stage']}")
                    st.write(f"**Salesperson:** {sale['salesperson']['name']}")
                with col2:
                    st.write(f"**Vehicle:** {sale['vehicle']['year']} {sale['vehicle']['make']} {sale['vehicle']['model']}")
                    st.write(f"**Registration:** {sale['vehicle']['registration']}")
                    st.write(f"**Total Price:** £{sale['financial']['total_price']:,}")
                
                progress = sale['pipeline']['progress_percentage'] / 100
                st.progress(progress)
    else:
        st.info("📋 No sales data available. Create customer journeys from TradeSnap to see them here!")

# ============================================================================
# CUSTOMER TRACKER PAGE
# ============================================================================

def render_customer_tracker_page():
    """Customer-facing tracking page"""
    st.markdown("""
    <div style='text-align: center; padding: 40px 20px;'>
        <h1 style='color: #0b3b6f; font-size: 42px;'>🚗 Track Your New Vehicle</h1>
        <p style='color: #666; font-size: 18px;'>
            Follow your purchase journey from deposit to collection
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tracking_id = st.text_input(
        "Enter your tracking ID",
        placeholder="ABC123XYZ456",
        help="You received this in your confirmation email/SMS"
    )
    
    if tracking_id:
        journey = get_journey_by_tracking_id(tracking_id.upper())
        
        if journey:
            render_wheel_tracker(journey.get('current_stage', 0), SALES_STAGES)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Purchase details in a nice card
            st.markdown(f"""
            <div style='background-color: white; padding: 24px; border-radius: 12px; 
                        box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin: 24px 0;'>
                <h3 style='color: {PRIMARY}; margin-top: 0;'>👤 Your Purchase Details</h3>
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 20px;'>
                    <div>
                        <div style='color: #999; font-size: 12px; text-transform: uppercase; margin-bottom: 4px;'>Customer</div>
                        <div style='font-size: 16px; font-weight: 600; color: {PRIMARY};'>{journey['customer']['name']}</div>
                    </div>
                    <div>
                        <div style='color: #999; font-size: 12px; text-transform: uppercase; margin-bottom: 4px;'>Tracking ID</div>
                        <div style='font-size: 16px; font-weight: 600; color: {PRIMARY};'>{journey['tracking_id']}</div>
                    </div>
                    <div>
                        <div style='color: #999; font-size: 12px; text-transform: uppercase; margin-bottom: 4px;'>Vehicle</div>
                        <div style='font-size: 16px; font-weight: 600; color: {PRIMARY};'>
                            {journey['vehicle']['year']} {journey['vehicle']['make']} {journey['vehicle']['model']}
                        </div>
                    </div>
                    <div>
                        <div style='color: #999; font-size: 12px; text-transform: uppercase; margin-bottom: 4px;'>Expected Collection</div>
                        <div style='font-size: 16px; font-weight: 600; color: {PRIMARY};'>
                            {datetime.datetime.fromisoformat(journey['collection_date']).strftime('%d %B %Y')}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Stage timeline
            st.markdown("### 📅 Journey Timeline")
            current_stage_idx = journey.get('current_stage', 0)
            
            for idx, stage in enumerate(SALES_STAGES):
                if idx < current_stage_idx:
                    status = "✅ Completed"
                    status_color = "#4caf50"
                elif idx == current_stage_idx:
                    status = "📍 Current Stage"
                    status_color = ACCENT
                else:
                    status = "⏳ Upcoming"
                    status_color = "#bbb"
                
                st.markdown(f"""
                <div style='background-color: #f8f9fa; padding: 16px; border-radius: 8px; 
                            margin-bottom: 12px; border-left: 4px solid {status_color};'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-size: 18px; font-weight: 600;'>{stage['icon']} {stage['name']}</div>
                            <div style='font-size: 13px; color: #666; margin-top: 4px;'>Stage {idx + 1} of {len(SALES_STAGES)}</div>
                        </div>
                        <div style='font-size: 14px; font-weight: 600; color: {status_color};'>{status}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("📞 **Questions?** Contact your salesperson or visit your local Sytner dealership")
            
            # Share this tracker
            st.markdown("---")
            with st.expander("📤 Share This Tracker", expanded=False):
                st.markdown("**Share your vehicle progress with family & friends**")
                
                share_url = f"https://your-app.streamlit.app/?track={journey['tracking_id']}"
                
                col_share1, col_share2 = st.columns(2)
                
                with col_share1:
                    if st.button("📧 Email This Link", use_container_width=True):
                        st.session_state[f"share_email_{tracking_id}"] = True
                        st.rerun()
                
                with col_share2:
                    if st.button("📱 SMS This Link", use_container_width=True):
                        st.session_state[f"share_sms_{tracking_id}"] = True
                        st.rerun()
                
                # Email share form
                if st.session_state.get(f"share_email_{tracking_id}", False):
                    with st.form("customer_share_email"):
                        st.markdown("##### Send via Email")
                        recipient_email = st.text_input("Recipient Email", placeholder="friend@email.com")
                        recipient_name = st.text_input("Recipient Name (optional)", placeholder="John")
                        
                        col_x, col_y = st.columns(2)
                        with col_x:
                            if st.form_submit_button("✉️ Send", type="primary"):
                                if recipient_email:
                                    st.success(f"✅ Tracking link sent to {recipient_email}")
                                    st.info("💡 Email service integration required in production")
                                    del st.session_state[f"share_email_{tracking_id}"]
                        with col_y:
                            if st.form_submit_button("❌ Cancel"):
                                del st.session_state[f"share_email_{tracking_id}"]
                                st.rerun()
                
                # SMS share form
                if st.session_state.get(f"share_sms_{tracking_id}", False):
                    with st.form("customer_share_sms"):
                        st.markdown("##### Send via SMS")
                        recipient_phone = st.text_input("Recipient Phone", placeholder="07700 900000")
                        
                        col_x, col_y = st.columns(2)
                        with col_x:
                            if st.form_submit_button("📲 Send", type="primary"):
                                if recipient_phone:
                                    st.success(f"✅ Tracking link sent to {recipient_phone}")
                                    st.info("💡 SMS service integration required in production")
                                    del st.session_state[f"share_sms_{tracking_id}"]
                        with col_y:
                            if st.form_submit_button("❌ Cancel"):
                                del st.session_state[f"share_sms_{tracking_id}"]
                                st.rerun()
                
                # Copy link option
                st.markdown("---")
                st.markdown("**Or copy this link:**")
                st.code(share_url, language=None)
            
        else:
            st.error("❌ Tracking ID not found. Please check and try again.")
    else:
        st.markdown("""
        <div style='background-color: #e3f2fd; padding: 20px; border-radius: 12px; margin-top: 40px;'>
            <p style='margin: 0; color: #0b3b6f;'>
                <strong>📧 Check your email or SMS</strong><br>
                Your unique tracking ID was sent to you after your deposit.<br>
                Example format: <code>ABC123XYZ456</code>
            </p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Sytner Complete Journey",
        page_icon="🚗",
        layout="centered"
    )
    
    init_session_state()
    apply_custom_css()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🎯 Navigation")
        page = st.radio(
            "Select Feature",
            ["🚗 TradeSnap - Vehicle Lookup", 
             "📊 Sales Pipeline - Track Sales", 
             "🔍 Customer Tracker"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("""
        **TradeSnap**: Vehicle lookup and trade-in valuation
        
        **Sales Pipeline**: View all active sales and progress
        
        **Customer Tracker**: Customer-facing progress view
        """)
    
    render_header()
    
    # Route to appropriate page
    if "TradeSnap" in page:
        render_reset_button()
        
        if st.session_state.show_summary and st.session_state.reg:
            render_summary_page()
        else:
            render_input_page()
    
    elif "Sales Pipeline" in page:
        render_sales_pipeline_page()
    
    else:
        render_customer_tracker_page()

if __name__ == "__main__":
    main()
