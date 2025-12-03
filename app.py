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

# Real Sytner BMW Locations from the provided image
GARAGES = [
    "Sytner BMW Cardiff - 285-287 Penarth Road, Cardiff",
    "Sytner BMW Chigwell - Langston Road, Loughton, Essex",
    "Sytner BMW Coventry - 128 Holyhead Road, Coventry",
    "Sytner BMW Harold Wood - A12 Colchester Road, Romford, Essex",
    "Sytner BMW High Wycombe - 575-647 London Road, High Wycombe",
    "Sytner BMW Leicester - Meridian East, Leicester",
    "Sytner BMW Luton - 501 Dunstable Road, Luton, Bedfordshire",
    "Sytner BMW Maidenhead - Bath Road, Maidenhead, Berkshire",
    "Sytner BMW Newport - Oak Way, The Old Town Dock, Newport",
    "Sytner BMW Nottingham - Lenton Lane, Nottingham",
    "Sytner BMW Oldbury - 919 Wolverhampton Road, Oldbury",
    "Sytner BMW Sheffield - Brightside Way, Sheffield, South Yorkshire",
    "Sytner BMW Shrewsbury - 70 Battlefield Road, Shrewsbury",
    "Sytner BMW Solihull - 520 Highlands Road, Shirley, Solihull",
    "Sytner BMW Stevenage - Arlington Business Park, Gunnels Wood Road",
    "Sytner BMW Sunningdale - Station Road, Sunningdale, Berkshire",
    "Sytner BMW Swansea - 375 Carmarthen Road, Cwmrhydyceirw, Swansea",
    "Sytner BMW Tamworth - Winchester Rd, Tamworth, West Midlands",
    "Sytner BMW Tring - Cow Roast, Tring, Hertfordshire",
    "Sytner BMW Warwick - Fusiliers Way, Warwick",
    "Sytner BMW Wolverhampton - Lever Street, Wolverhampton",
    "Sytner BMW Worcester - Knightsbridge Park, Wallingford Road, Worcester"
]

TIME_SLOTS = ["09:00 AM", "11:00 AM", "02:00 PM", "04:00 PM"]

# ============================================================================
# MOCK API FUNCTIONS (Replace with real APIs in production)
# ============================================================================

def lookup_vehicle_basic(reg):
    """Mock vehicle lookup - replace with real API"""
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
        "booking_forms": {}
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
        padding: 20px 24px;
        border-radius: 12px;
        font-size: 26px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    .content-card {{
        background-color: white;
        padding: 20px 24px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        color: {PRIMARY};
    }}
    .stButton>button {{
        background-color: {ACCENT} !important;
        color: white !important;
        font-weight: 600;
        border-radius: 8px;
        border: none !important;
        padding: 0.6rem 1.2rem;
        font-size: 16px;
        transition: all 0.2s ease;
    }}
    .stButton>button:hover {{
        background-color: #1873cc !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }}
    .numberplate {{
        background-color: #fff;
        border: 3px solid {PRIMARY};
        border-radius: 12px;
        padding: 16px 24px;
        font-size: 32px;
        font-weight: 700;
        color: {PRIMARY};
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        letter-spacing: 2px;
    }}
    .badge {{
        padding: 6px 12px;
        border-radius: 20px;
        color: white;
        margin-right: 8px;
        font-size: 13px;
        display: inline-block;
        font-weight: 600;
    }}
    .badge-warning {{background-color: #ff9800;}}
    .badge-success {{background-color: #4caf50;}}
    .badge-danger {{background-color: #f44336;}}
    .badge-info {{background-color: {ACCENT};}}
    .stat-box {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    .icon {{
        font-size: 24px;
        margin-right: 8px;
        vertical-align: middle;
    }}
    hr {{
        margin: 24px 0;
        border: none;
        border-top: 2px solid #e0e0e0;
    }}
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# RENDERING FUNCTIONS
# ============================================================================

def render_header():
    """Render application header"""
    st.markdown(f"""
    <div class='header-card'>
        <span class='icon'>⚡</span> Sytner TradeSnap <span class='icon'>🚗</span>
    </div>
    """, unsafe_allow_html=True)

def render_reset_button():
    """Render reset button"""
    if st.session_state.show_summary:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Check Another Vehicle", use_container_width=True):
                reset_all_state()
                st.rerun()

def render_vehicle_summary(vehicle, mot_tax, history_flags, open_recalls):
    """Render main vehicle summary section"""
    st.markdown(f"""
    <div class='content-card'>
        <h3 style='margin-top: 0; color: {PRIMARY};'>
            <span class='icon'>🚗</span> Vehicle Overview
        </h3>
        <p style='font-size: 20px; margin: 12px 0;'>
            <strong>{vehicle['year']} {vehicle['make']} {vehicle['model']}</strong>
        </p>
        <p style='color: #666; margin: 8px 0;'>
            <span class='icon'>🔢</span> <strong>VIN:</strong> {vehicle['vin']}
        </p>
        <p style='color: #666; margin: 8px 0;'>
            <span class='icon'>📏</span> <strong>Mileage:</strong> {vehicle['mileage']:,} miles
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Status badges
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='margin-top: 0; color: {PRIMARY};'><span class='icon'>✅</span> Status Checks</h3>", unsafe_allow_html=True)
    
    badges = []
    if not history_flags.get('write_off'):
        badges.append("<span class='badge badge-success'>✓ No Write-off</span>")
    else:
        badges.append("<span class='badge badge-danger'>⚠ Write-off Recorded</span>")
    
    if not history_flags.get('theft'):
        badges.append("<span class='badge badge-success'>✓ Not Stolen</span>")
    else:
        badges.append("<span class='badge badge-danger'>⚠ Theft Record</span>")
    
    if open_recalls > 0:
        badges.append(f"<span class='badge badge-warning'>⚠ {open_recalls} Open Recall(s)</span>")
    else:
        badges.append("<span class='badge badge-success'>✓ No Open Recalls</span>")
    
    if history_flags.get('mileage_anomaly'):
        badges.append("<span class='badge badge-warning'>⚠ Mileage Anomaly</span>")
    else:
        badges.append("<span class='badge badge-success'>✓ Clean Mileage</span>")
    
    st.markdown("<div style='margin: 16px 0;'>" + "".join(badges) + "</div>", unsafe_allow_html=True)
    
    # MOT and Tax info
    st.markdown("<hr>", unsafe_allow_html=True)
    mot_date = datetime.datetime.fromisoformat(mot_tax['mot_next_due']).strftime('%d %B %Y')
    tax_date = datetime.datetime.fromisoformat(mot_tax['tax_expiry']).strftime('%d %B %Y')
    
    st.markdown(f"""
    <div style='display: flex; gap: 24px; flex-wrap: wrap;'>
        <div style='flex: 1; min-width: 200px;'>
            <p style='margin: 0; color: #666; font-size: 14px;'>
                <span class='icon'>🔍</span> <strong>MOT Due:</strong>
            </p>
            <p style='margin: 4px 0 0 0; font-size: 16px; font-weight: 600; color: {PRIMARY};'>
                {mot_date}
            </p>
        </div>
        <div style='flex: 1; min-width: 200px;'>
            <p style='margin: 0; color: #666; font-size: 14px;'>
                <span class='icon'>💳</span> <strong>Tax Expiry:</strong>
            </p>
            <p style='margin: 4px 0 0 0; font-size: 16px; font-weight: 600; color: {PRIMARY};'>
                {tax_date}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_mot_history(mot_history):
    """Render MOT history section"""
    with st.expander("📋 MOT History", expanded=False):
        if mot_history:
            for record in mot_history:
                result_icon = "✅" if record['result'] == "Pass" else "⚠️"
                result_color = "#4caf50" if record['result'] == "Pass" else "#ff9800"
                st.markdown(f"""
                <div style='background-color: #f5f5f5; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid {result_color};'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <strong>{result_icon} {record['result']}</strong> - {record['date']}
                        </div>
                        <div style='color: #666;'>
                            <span class='icon'>📏</span> {record['mileage']:,} miles
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("ℹ️ No MOT history available")

def render_recalls(recalls):
    """Render recalls section"""
    with st.expander(f"⚠️ Safety Recalls ({sum(1 for r in recalls if r['open'])} Open)", expanded=False):
        if recalls:
            for recall in recalls:
                status_icon = "🔴" if recall['open'] else "✅"
                status_text = "OPEN" if recall['open'] else "COMPLETED"
                status_color = "#f44336" if recall['open'] else "#4caf50"
                
                st.markdown(f"""
                <div style='background-color: #f5f5f5; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid {status_color};'>
                    <div style='margin-bottom: 8px;'>
                        <strong>{status_icon} {status_text}</strong>
                        <span style='color: #666; margin-left: 12px;'>{recall['id']}</span>
                    </div>
                    <div style='color: #666;'>
                        {recall['summary']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No outstanding recalls found")

def render_valuation(vehicle):
    """Render valuation section with part exchange booking"""
    with st.expander("💰 Instant Valuation & Part Exchange", expanded=False):
        st.markdown(f"<p style='color: #666; margin-bottom: 16px;'><span class='icon'>💡</span> Get an instant estimate based on current market data</p>", unsafe_allow_html=True)
        
        condition = st.selectbox(
            "Vehicle Condition",
            ["Excellent", "Good", "Fair", "Poor"],
            index=1,
            key="condition_select"
        )
        
        if st.button("📊 Get Valuation", key="valuation_btn"):
            valuation = estimate_value(
                vehicle['make'],
                vehicle['model'],
                vehicle['year'],
                vehicle['mileage'],
                condition.lower()
            )
            
            st.markdown(f"""
            <div class='stat-box'>
                <div style='font-size: 18px; margin-bottom: 8px;'>Estimated Value</div>
                <div style='font-size: 42px; font-weight: 700;'>£{valuation:,}</div>
                <div style='font-size: 14px; margin-top: 8px; opacity: 0.9;'>Based on {condition} condition</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Part Exchange Booking Form
            st.markdown(f"""
            <h4 style='color: {PRIMARY}; margin: 20px 0 16px 0;'>
                <span class='icon'>📅</span> Book Part Exchange Appointment
            </h4>
            """, unsafe_allow_html=True)
            
            with st.form(key="px_form"):
                col1, col2 = st.columns(2)
                with col1:
                    customer_name = st.text_input("Customer Name", placeholder="John Smith")
                    customer_email = st.text_input("Email", placeholder="john@example.com")
                with col2:
                    customer_phone = st.text_input("Phone", placeholder="07700 900000")
                    preferred_garage = st.selectbox("Preferred Location", GARAGES)
                
                preferred_date = st.date_input("Preferred Date", min_value=datetime.date.today())
                preferred_time = st.selectbox("Preferred Time", TIME_SLOTS)
                
                notes = st.text_area("Additional Notes", placeholder="Any specific requirements or questions...")
                
                submitted = st.form_submit_button("✅ Confirm Appointment", use_container_width=True)
                
                if submitted:
                    if customer_name and customer_phone:
                        st.success(f"""
                        ✅ **Appointment Confirmed!**
                        
                        📧 Confirmation sent to: {customer_email}  
                        📍 Location: {preferred_garage}  
                        📅 Date: {preferred_date.strftime('%d %B %Y')}  
                        🕒 Time: {preferred_time}  
                        💰 Estimated Value: £{valuation:,}
                        """)
                    else:
                        st.error("❌ Please provide customer name and phone number")

def render_additional_details(vehicle, mot_tax, history_flags, open_recalls):
    """Render additional details section"""
    with st.expander("📊 Full Vehicle Report", expanded=False):
        st.markdown(f"""
        <div style='background-color: #f8f9fa; padding: 20px; border-radius: 8px;'>
            <h4 style='color: {PRIMARY}; margin-top: 0;'><span class='icon'>📄</span> Complete Summary</h4>
            
            <div style='margin: 16px 0;'>
                <strong>Vehicle Details:</strong>
                <ul style='margin: 8px 0; padding-left: 20px;'>
                    <li>Registration: {vehicle['reg']}</li>
                    <li>VIN: {vehicle['vin']}</li>
                    <li>Make & Model: {vehicle['make']} {vehicle['model']}</li>
                    <li>Year: {vehicle['year']}</li>
                    <li>Mileage: {vehicle['mileage']:,} miles</li>
                </ul>
            </div>
            
            <div style='margin: 16px 0;'>
                <strong>Status Summary:</strong>
                <ul style='margin: 8px 0; padding-left: 20px;'>
                    <li>Write-off: {'Yes ⚠️' if history_flags.get('write_off') else 'No ✅'}</li>
                    <li>Stolen: {'Yes ⚠️' if history_flags.get('theft') else 'No ✅'}</li>
                    <li>Open Recalls: {open_recalls}</li>
                    <li>Mileage Issues: {'Yes ⚠️' if history_flags.get('mileage_anomaly') else 'No ✅'}</li>
                </ul>
            </div>
            
            <div style='margin: 16px 0;'>
                <strong>MOT & Tax:</strong>
                <ul style='margin: 8px 0; padding-left: 20px;'>
                    <li>Next MOT: {mot_tax['mot_next_due']}</li>
                    <li>Tax Expiry: {mot_tax['tax_expiry']}</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# PAGE RENDERING
# ============================================================================

def render_input_page():
    """Render the input page"""
    # Hero section with stats
    st.markdown(f"""
    <div class='stat-box' style='margin-bottom: 24px;'>
        <h2 style='margin: 0 0 20px 0; font-size: 24px;'>Quick Vehicle Check & Part Exchange</h2>
        <div style='display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px;'>
            <div style='text-align: center;'>
                <div style='font-size: 32px; font-weight: 700;'>⚡ 30s</div>
                <div style='font-size: 14px; opacity: 0.9; margin-top: 4px;'>Average Check Time</div>
            </div>
            <div style='text-align: center;'>
                <div style='font-size: 32px; font-weight: 700;'>📍 22</div>
                <div style='font-size: 14px; opacity: 0.9; margin-top: 4px;'>UK Locations</div>
            </div>
            <div style='text-align: center;'>
                <div style='font-size: 32px; font-weight: 700;'>💰 £500+</div>
                <div style='font-size: 14px; opacity: 0.9; margin-top: 4px;'>Avg. Bonus Value</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick benefits
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='content-card' style='text-align: center; min-height: 120px;'>
            <div style='font-size: 32px; margin-bottom: 8px;'>⚡</div>
            <div style='font-weight: 600; color: #0b3b6f; margin-bottom: 8px;'>Instant Check</div>
            <div style='font-size: 14px; color: #666;'>Full history in seconds</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='content-card' style='text-align: center; min-height: 120px;'>
            <div style='font-size: 32px; margin-bottom: 8px;'>💰</div>
            <div style='font-weight: 600; color: #0b3b6f; margin-bottom: 8px;'>Best Offers</div>
            <div style='font-size: 14px; color: #666;'>Competitive valuations</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='content-card' style='text-align: center; min-height: 120px;'>
            <div style='font-size: 32px; margin-bottom: 8px;'>📅</div>
            <div style='font-weight: 600; color: #0b3b6f; margin-bottom: 8px;'>Same Day</div>
            <div style='font-size: 14px; color: #666;'>Complete deal today</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main input section
    st.markdown(f"""
    <div class='content-card' style='text-align: center;'>
        <h2 style='color: {PRIMARY}; margin: 0 0 12px 0; font-size: 26px;'>
            <span class='icon'>🚀</span> Get Started
        </h2>
        <p style='color: #666; font-size: 16px; margin-bottom: 20px;'>
            Enter registration or scan number plate
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Input method selection
    col_spacer1, col_radio, col_spacer2 = st.columns([1, 2, 1])
    with col_radio:
        option = st.radio(
            "Choose input method",
            ["📝 Enter Registration", "📸 Scan Number Plate"],
            index=0,
            horizontal=True,
            label_visibility="collapsed"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if "Enter Registration" in option:
        manual_reg = st.text_input(
            "Enter registration",
            placeholder="e.g. KT68XYZ or WBA8BFAKEVIN12345",
            label_visibility="collapsed"
        )
        
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔍 Look Up Vehicle", disabled=not manual_reg, use_container_width=True, type="primary"):
                if validate_registration(manual_reg):
                    st.session_state.reg = manual_reg.strip().upper().replace(" ", "")
                    st.session_state.image = None
                    st.session_state.show_summary = True
                    st.rerun()
                else:
                    st.error("❌ Please enter a valid registration")
        
        st.markdown("""
        <div style='text-align: center; margin-top: 20px;'>
            <p style='color: #999; font-size: 14px;'>
                💡 <strong>Try:</strong> KT68XYZ • AB12CDE • WBA8B12345
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    else:  # Scan Number Plate
        st.markdown(f"""
        <div style='background-color: #e3f2fd; padding: 16px; border-radius: 8px; border-left: 4px solid {ACCENT}; margin-bottom: 20px;'>
            <p style='margin: 0; font-size: 14px; color: #0b3b6f;'>
                <span class='icon'>💡</span> <strong>Tips:</strong> Clear frame • Good lighting • Hold steady
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        image = st.camera_input(
            "Scan number plate",
            key="camera",
            label_visibility="collapsed"
        )
        
        if image:
            try:
                extracted_reg = mock_ocr_numberplate(image)
                
                if extracted_reg and validate_registration(extracted_reg):
                    st.session_state.image = image
                    st.session_state.reg = extracted_reg
                    st.session_state.show_summary = True
                    st.rerun()
                else:
                    st.error("❌ Could not read plate. Try again or enter manually.")
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")
    
    # Trust indicators
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='content-card' style='text-align: center;'>
        <p style='color: #999; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 16px 0; font-weight: 600;'>
            Trusted by Sytner Staff Nationwide
        </p>
        <div style='display: flex; justify-content: center; gap: 32px; flex-wrap: wrap;'>
            <div style='color: {PRIMARY}; font-size: 14px;'>
                <span style='color: #4caf50;'>✅</span> DVLA Integrated
            </div>
            <div style='color: {PRIMARY}; font-size: 14px;'>
                <span style='color: #4caf50;'>✅</span> Real-time MOT
            </div>
            <div style='color: {PRIMARY}; font-size: 14px;'>
                <span style='color: #4caf50;'>✅</span> Secure Data
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_summary_page():
    """Render the vehicle summary page"""
    reg = st.session_state.reg
    image = st.session_state.image

    # Display captured image
    if image:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(ImageOps.exif_transpose(Image.open(image)), use_container_width=True)

    # Display number plate
    st.markdown(f"<div class='numberplate'>{reg}</div>", unsafe_allow_html=True)

    # Fetch vehicle data
    try:
        with st.spinner("🔄 Fetching vehicle information..."):
            vehicle = lookup_vehicle_basic(reg)
            mot_tax = lookup_mot_and_tax(reg)
            recalls = lookup_recalls(reg)
            history_flags = get_history_flags(reg)
    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")
        st.stop()

    # Render all sections
    open_recalls = sum(1 for r in recalls if r["open"])
    
    render_vehicle_summary(vehicle, mot_tax, history_flags, open_recalls)
    render_mot_history(mot_tax['mot_history'])
    render_recalls(recalls)
    
    with st.expander("🛡️ Insurance Quote", expanded=False):
        st.info("💡 Connect to insurance API for live quotes")
        if st.button('📊 Get Sample Quote', key="insurance_quote"):
            st.success("""
            **Sample Quote:**  
            💰 £320/year (Third Party, Fire & Theft)  
            🔹 Excess: £250  
            🔹 No Claims: Year 1  
            🔹 Mileage: 10,000/year
            """)
    
    render_valuation(vehicle)
    render_additional_details(vehicle, mot_tax, history_flags, open_recalls)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Sytner TradeSnap ⚡",
        page_icon="⚡",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    init_session_state()
    apply_custom_css()
    render_header()
    render_reset_button()
    
    if st.session_state.show_summary and st.session_state.reg:
        render_summary_page()
    else:
        render_input_page()

if __name__ == "__main__":
    main()
