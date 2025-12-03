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
        border: none !important;
        color: white !important;
    }}
    .stButton>button:focus {{
        background-color: #1873cc !important;
        border: none !important;
        box-shadow: none !important;
        color: white !important;
    }}
    .stButton>button:active {{
        background-color: #1565b8 !important;
        border: none !important;
        color: white !important;
    }}
    .stButton>button[kind="primary"] {{
        background-color: {ACCENT} !important;
    }}
    .stButton>button[kind="primary"]:hover {{
        background-color: #1873cc !important;
        color: white !important;
    }}
    .stButton>button[kind="primary"]:focus {{
        background-color: #1873cc !important;
        color: white !important;
    }}
    .stButton>button[kind="primary"]:active {{
        background-color: #1565b8 !important;
        color: white !important;
    }}
    .stButton>button:disabled {{
        background-color: #cccccc !important;
        color: #666666 !important;
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
    .badge-success {{background-color: #4caf50;}}
    
    /* Hide empty containers and white bars */
    .element-container:has(> .stMarkdown > div:empty),
    .element-container:has(> .stMarkdown > div:only-child:empty) {{
        display: none !important;
    }}
    
    /* Remove extra padding from empty column containers */
    [data-testid="column"]:empty {{
        display: none !important;
    }}
    
    /* Ensure content cards have no unexpected margins when empty */
    .content-card:empty {{
        display: none !important;
    }}
    
    /* Remove default Streamlit spacing that creates white bars */
    .block-container {{
        padding-top: 2rem;
    }}
    
    /* Better input styling */
    .stTextInput input {{
        font-size: 16px;
        padding: 12px;
    }}
    
    .stTextInput input::placeholder {{
        color: #888 !important;
        opacity: 1;
    }}
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
        # Use container to center button without creating empty columns
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("New Vehicle Lookup", use_container_width=True):
                reset_all_state()
                st.rerun()
        # Add empty markdown to prevent white bar rendering
        st.markdown("")

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

def render_mot_history(mot_history):
    """Render MOT history expander"""
    with st.expander("📋 MOT History"):
        if mot_history:
            for entry in mot_history:
                result_icon = "✅" if entry['result'] == "Pass" else "⚠️"
                st.markdown(f"{result_icon} **{entry['date']}**: {entry['result']} — {entry['mileage']:,} miles")
        else:
            st.info("No MOT history available")

def render_booking_form(recall, recall_key):
    """Render the booking form for a recall"""
    st.markdown("##### Book Recall Repair")
    
    garage = st.selectbox(
        "Select Sytner Garage",
        GARAGES,
        key=f"garage_{recall_key}"
    )
    
    col_a, col_b = st.columns(2)
    with col_a:
        min_date = datetime.date.today() + datetime.timedelta(days=1)
        max_date = datetime.date.today() + datetime.timedelta(days=60)
        booking_date = st.date_input(
            "Preferred Date",
            min_value=min_date,
            max_value=max_date,
            value=min_date,
            key=f"date_{recall_key}"
        )
    with col_b:
        time_slot = st.selectbox("Time Slot", TIME_SLOTS, key=f"time_{recall_key}")
    
    col_c, col_d = st.columns(2)
    with col_c:
        customer_name = st.text_input(
            "Customer Name *",
            key=f"name_{recall_key}",
            placeholder="John Smith"
        )
    with col_d:
        customer_phone = st.text_input(
            "Phone Number *",
            key=f"phone_{recall_key}",
            placeholder="07700 900000"
        )
    
    customer_email = st.text_input(
        "Email Address (optional)",
        key=f"email_{recall_key}",
        placeholder="customer@example.com"
    )
    
    col_x, col_y = st.columns(2)
    with col_x:
        if st.button("Confirm Booking", key=f"confirm_{recall_key}", use_container_width=True):
            if not customer_name or not validate_phone(customer_phone):
                st.error("⚠️ Please fill in all required fields with valid information")
            else:
                booking_ref = f"RCL-{recall['id']}-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
                st.success(f"""
                ✅ **Booking Confirmed!**
                
                **Reference:** {booking_ref}  
                **Garage:** {garage}  
                **Date & Time:** {booking_date.strftime('%d %B %Y')} at {time_slot}  
                **Customer:** {customer_name} | {customer_phone}
                
                📧 Confirmation email sent to customer
                """)
                
                if recall_key in st.session_state.booking_forms:
                    del st.session_state.booking_forms[recall_key]
                st.balloons()
    
    with col_y:
        if st.button("Cancel", key=f"cancel_{recall_key}", use_container_width=True):
            if recall_key in st.session_state.booking_forms:
                del st.session_state.booking_forms[recall_key]
            st.rerun()

def render_recalls(recalls):
    """Render recalls expander with booking functionality"""
    open_recalls = sum(1 for r in recalls if r["open"])
    
    with st.expander(f"🔔 Recalls ({len(recalls)} total, {open_recalls} open)"):
        if not recalls:
            st.success("✅ No recalls found for this vehicle")
            return
        
        for idx, recall in enumerate(recalls):
            recall_key = f"recall_{recall['id']}"
            
            col1, col2 = st.columns([3, 1])
            with col1:
                status = "⚠️ **OPEN**" if recall['open'] else "✅ Closed"
                st.markdown(f"**{recall['summary']}**")
                st.caption(f"ID: `{recall['id']}` — Status: {status}")
            
            with col2:
                if recall['open']:
                    if st.button("📅 Book Repair", key=f"book_btn_{recall_key}"):
                        if recall_key in st.session_state.booking_forms:
                            del st.session_state.booking_forms[recall_key]
                        else:
                            st.session_state.booking_forms[recall_key] = True
                        st.rerun()
            
            if recall['open'] and st.session_state.booking_forms.get(recall_key):
                render_booking_form(recall, recall_key)
            
            if idx < len(recalls) - 1:
                st.markdown("---")

def get_sytner_buyers():
    """Return list of Sytner buyers with their locations and contact info"""
    return [
        {
            "name": "Sarah Mitchell",
            "location": "Sytner BMW Cardiff",
            "area": "South Wales",
            "phone": "029 2046 8000",
            "email": "sarah.mitchell@sytner.co.uk",
            "specialties": ["3 Series", "5 Series", "Estate Cars"],
            "rating": 4.9,
            "deals_completed": 247
        },
        {
            "name": "James Thompson",
            "location": "Sytner BMW Birmingham",
            "area": "West Midlands",
            "phone": "0121 456 7890",
            "email": "james.thompson@sytner.co.uk",
            "specialties": ["X Series", "SUV", "4x4"],
            "rating": 4.8,
            "deals_completed": 312
        },
        {
            "name": "Emma Richardson",
            "location": "Sytner BMW Leicester",
            "area": "East Midlands",
            "phone": "0116 234 5678",
            "email": "emma.richardson@sytner.co.uk",
            "specialties": ["M Sport", "Performance", "Diesel"],
            "rating": 4.9,
            "deals_completed": 289
        },
        {
            "name": "David Chen",
            "location": "Sytner BMW Nottingham",
            "area": "East Midlands",
            "phone": "0115 789 0123",
            "email": "david.chen@sytner.co.uk",
            "specialties": ["3 Series", "Saloon", "Hybrid"],
            "rating": 4.7,
            "deals_completed": 198
        },
        {
            "name": "Sophie Williams",
            "location": "Sytner BMW Coventry",
            "area": "West Midlands",
            "phone": "024 7655 4321",
            "email": "sophie.williams@sytner.co.uk",
            "specialties": ["All Models", "Quick Deals", "Part Exchange"],
            "rating": 4.9,
            "deals_completed": 356
        },
        {
            "name": "Michael O'Brien",
            "location": "Sytner BMW Sheffield",
            "area": "South Yorkshire",
            "phone": "0114 567 8901",
            "email": "michael.obrien@sytner.co.uk",
            "specialties": ["X Series", "High Mileage", "Commercial"],
            "rating": 4.8,
            "deals_completed": 276
        },
        {
            "name": "Lucy Anderson",
            "location": "Sytner BMW Solihull",
            "area": "West Midlands",
            "phone": "0121 789 4561",
            "email": "lucy.anderson@sytner.co.uk",
            "specialties": ["Premium Models", "Low Mileage", "Executive"],
            "rating": 4.9,
            "deals_completed": 423
        },
        {
            "name": "Robert Taylor",
            "location": "Sytner BMW Newport",
            "area": "South Wales",
            "phone": "01633 456 789",
            "email": "robert.taylor@sytner.co.uk",
            "specialties": ["Diesel", "Estate", "Family Cars"],
            "rating": 4.7,
            "deals_completed": 234
        }
    ]

def render_sytner_buyers(vehicle, reg):
    """Render Sytner Buyers section with ping functionality"""
    with st.expander("👤 Contact Sytner Vehicle Buyer", expanded=False):
        st.markdown(f"<h4 style='color: {PRIMARY}; margin-top: 0;'>🎯 Find Your Local Sytner Buyer</h4>", unsafe_allow_html=True)
        st.markdown("Our expert buyers are ready to make you an offer within minutes")
        
        buyers = get_sytner_buyers()
        
        # Location selector
        st.markdown("##### Select Your Preferred Location")
        col1, col2 = st.columns([2, 1])
        with col1:
            location_filter = st.selectbox(
                "Filter by area",
                ["All Areas", "West Midlands", "East Midlands", "South Wales", "South Yorkshire"],
                key="buyer_location_filter"
            )
        with col2:
            sort_by = st.selectbox(
                "Sort by",
                ["Rating", "Deals Completed", "Name"],
                key="buyer_sort"
            )
        
        # Filter and sort buyers
        filtered_buyers = buyers
        if location_filter != "All Areas":
            filtered_buyers = [b for b in buyers if b["area"] == location_filter]
        
        if sort_by == "Rating":
            filtered_buyers = sorted(filtered_buyers, key=lambda x: x["rating"], reverse=True)
        elif sort_by == "Deals Completed":
            filtered_buyers = sorted(filtered_buyers, key=lambda x: x["deals_completed"], reverse=True)
        else:
            filtered_buyers = sorted(filtered_buyers, key=lambda x: x["name"])
        
        st.markdown("---")
        
        # Display buyers
        for buyer in filtered_buyers:
            # Check if this vehicle matches buyer's specialties
            is_specialty = any(spec.lower() in vehicle['model'].lower() for spec in buyer['specialties'])
            specialty_badge = " ⭐ SPECIALIST" if is_specialty else ""
            
            st.markdown(f"""
            <div style='background-color: #f8f9fa; padding: 16px; border-radius: 12px; margin-bottom: 16px; 
                        border-left: 4px solid {"#4caf50" if is_specialty else ACCENT};'>
                <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;'>
                    <div>
                        <h5 style='margin: 0; color: {PRIMARY};'>{buyer['name']}{specialty_badge}</h5>
                        <p style='margin: 4px 0; color: #666; font-size: 14px;'>
                            📍 {buyer['location']} • {buyer['area']}
                        </p>
                    </div>
                    <div style='text-align: right;'>
                        <div style='color: #ffa726; font-size: 14px;'>★ {buyer['rating']}/5.0</div>
                        <div style='color: #666; font-size: 12px;'>{buyer['deals_completed']} deals</div>
                    </div>
                </div>
                <div style='margin: 8px 0;'>
                    <strong style='font-size: 13px; color: #666;'>Specialties:</strong>
                    <div style='margin-top: 4px;'>
            """, unsafe_allow_html=True)
            
            for specialty in buyer['specialties']:
                badge_color = "#4caf50" if specialty.lower() in vehicle['model'].lower() else "#e0e0e0"
                text_color = "white" if specialty.lower() in vehicle['model'].lower() else "#666"
                st.markdown(f"""
                <span style='display: inline-block; background-color: {badge_color}; color: {text_color}; 
                            padding: 4px 10px; border-radius: 12px; font-size: 12px; margin: 2px 4px 2px 0;'>
                    {specialty}
                </span>
                """, unsafe_allow_html=True)
            
            st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Contact section
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.markdown(f"""
                <div style='font-size: 13px; color: #666; margin: 8px 0;'>
                    📞 {buyer['phone']}<br>
                    📧 {buyer['email']}
                </div>
                """, unsafe_allow_html=True)
            
            with col_b:
                if st.button(f"📲 Ping {buyer['name'].split()[0]}", key=f"ping_{buyer['email']}", use_container_width=True):
                    st.session_state[f"ping_form_{buyer['email']}"] = True
                    st.rerun()
            
            # Ping form (appears when button clicked)
            if st.session_state.get(f"ping_form_{buyer['email']}", False):
                st.markdown(f"""
                <div style='background-color: #e3f2fd; padding: 16px; border-radius: 8px; margin-top: 12px;'>
                    <h5 style='margin: 0 0 12px 0; color: {PRIMARY};'>📤 Send Request to {buyer['name']}</h5>
                </div>
                """, unsafe_allow_html=True)
                
                with st.form(key=f"ping_form_submit_{buyer['email']}"):
                    col_x, col_y = st.columns(2)
                    with col_x:
                        customer_name = st.text_input("Your Name *", placeholder="John Smith", key=f"ping_name_{buyer['email']}")
                    with col_y:
                        customer_phone = st.text_input("Your Phone *", placeholder="07700 900000", key=f"ping_phone_{buyer['email']}")
                    
                    customer_email = st.text_input("Your Email *", placeholder="customer@example.com", key=f"ping_email_{buyer['email']}")
                    
                    preferred_contact = st.radio(
                        "Preferred Contact Method",
                        ["Phone", "Email", "Either"],
                        horizontal=True,
                        key=f"ping_contact_{buyer['email']}"
                    )
                    
                    urgency = st.select_slider(
                        "How soon are you looking to sell?",
                        options=["This week", "Within 2 weeks", "Within a month", "Just exploring"],
                        key=f"ping_urgency_{buyer['email']}"
                    )
                    
                    additional_notes = st.text_area(
                        "Additional Information (optional)",
                        placeholder="Any specific questions or requirements...",
                        key=f"ping_notes_{buyer['email']}"
                    )
                    
                    col_submit, col_cancel = st.columns(2)
                    with col_submit:
                        submitted = st.form_submit_button("✅ Send Request", use_container_width=True, type="primary")
                    with col_cancel:
                        cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
                    
                    if submitted:
                        if customer_name and customer_phone and customer_email:
                            request_ref = f"REQ-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                            st.success(f"""
                            ✅ **Request Sent Successfully!**
                            
                            **Reference:** {request_ref}  
                            **Buyer:** {buyer['name']} at {buyer['location']}  
                            **Vehicle:** {vehicle['year']} {vehicle['make']} {vehicle['model']} ({reg})  
                            **Contact Method:** {preferred_contact}  
                            **Urgency:** {urgency}
                            
                            📧 Confirmation sent to: {customer_email}  
                            ⏱️ **Expected Response Time:** Within 2 hours during business hours
                            
                            {buyer['name']} will contact you shortly to arrange a valuation!
                            """)
                            st.balloons()
                            del st.session_state[f"ping_form_{buyer['email']}"]
                        else:
                            st.error("⚠️ Please fill in all required fields")
                    
                    if cancelled:
                        del st.session_state[f"ping_form_{buyer['email']}"]
                        st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        if not filtered_buyers:
            st.info("No buyers found for the selected area. Try 'All Areas' to see all available buyers.")
        
        # Summary info box
        st.markdown("---")
        st.markdown(f"""
        <div style='background-color: #fff3cd; padding: 16px; border-radius: 8px; border-left: 4px solid #ffc107;'>
            <p style='margin: 0;'><strong>💡 How it works:</strong></p>
            <ul style='margin: 8px 0 0 0; padding-left: 20px; font-size: 14px;'>
                <li>Click "Ping" to send a quick request to any buyer</li>
                <li>Buyers marked with ⭐ SPECIALIST have expertise in your vehicle type</li>
                <li>You'll receive a response within 2 hours during business hours</li>
                <li>All buyers can arrange same-day inspections if needed</li>
                <li>No obligation - compare offers from multiple buyers</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def render_market_trends(vehicle):
    """Display market trends and seasonal forecasting"""
    st.markdown("#### 📊 Market Intelligence & Trends")
    st.markdown("*Real-time insights to help you make the best deal*")
    
    # Current market demand for this vehicle type
    vehicle_type = vehicle['model'].split()[0] if vehicle['model'] else "Series"
    
    st.markdown("---")
    st.markdown("##### 🎯 Current Market Demand")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #4caf50 0%, #45a049 100%); 
                    padding: 20px; border-radius: 12px; text-align: center; color: white;'>
            <div style='font-size: 32px; font-weight: 700;'>HIGH</div>
            <div style='font-size: 14px; opacity: 0.9; margin-top: 8px;'>Demand Level</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {ACCENT} 0%, #1873cc 100%); 
                    padding: 20px; border-radius: 12px; text-align: center; color: white;'>
            <div style='font-size: 32px; font-weight: 700;'>12</div>
            <div style='font-size: 14px; opacity: 0.9; margin-top: 8px;'>Days avg. to sell</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); 
                    padding: 20px; border-radius: 12px; text-align: center; color: white;'>
            <div style='font-size: 32px; font-weight: 700;'>87%</div>
            <div style='font-size: 14px; opacity: 0.9; margin-top: 8px;'>Of asking price</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Seasonal trends
    st.markdown("---")
    st.markdown("##### 🌦️ Seasonal Demand Forecast")
    
    current_month = datetime.date.today().month
    current_season = ""
    if current_month in [12, 1, 2]:
        current_season = "Winter"
        season_icon = "❄️"
    elif current_month in [3, 4, 5]:
        current_season = "Spring"
        season_icon = "🌸"
    elif current_month in [6, 7, 8]:
        current_season = "Summer"
        season_icon = "☀️"
    else:
        current_season = "Autumn"
        season_icon = "🍂"
    
    st.markdown(f"**Current Season: {season_icon} {current_season}**")
    
    # Seasonal performance by vehicle type
    seasonal_data = {
        "Winter": {
            "SUV/4x4": {"demand": "Very High", "trend": "↑ +25%", "color": "#4caf50"},
            "Saloon": {"demand": "Moderate", "trend": "→ Stable", "color": "#ff9800"},
            "Convertible": {"demand": "Low", "trend": "↓ -40%", "color": "#f44336"},
            "Estate": {"demand": "High", "trend": "↑ +15%", "color": "#4caf50"}
        },
        "Spring": {
            "SUV/4x4": {"demand": "High", "trend": "↑ +10%", "color": "#4caf50"},
            "Saloon": {"demand": "High", "trend": "↑ +20%", "color": "#4caf50"},
            "Convertible": {"demand": "Very High", "trend": "↑ +60%", "color": "#4caf50"},
            "Estate": {"demand": "Moderate", "trend": "→ Stable", "color": "#ff9800"}
        },
        "Summer": {
            "SUV/4x4": {"demand": "Moderate", "trend": "↓ -10%", "color": "#ff9800"},
            "Saloon": {"demand": "High", "trend": "↑ +15%", "color": "#4caf50"},
            "Convertible": {"demand": "Very High", "trend": "↑ +50%", "color": "#4caf50"},
            "Estate": {"demand": "Moderate", "trend": "→ Stable", "color": "#ff9800"}
        },
        "Autumn": {
            "SUV/4x4": {"demand": "High", "trend": "↑ +15%", "color": "#4caf50"},
            "Saloon": {"demand": "High", "trend": "↑ +10%", "color": "#4caf50"},
            "Convertible": {"demand": "Low", "trend": "↓ -30%", "color": "#f44336"},
            "Estate": {"demand": "High", "trend": "↑ +20%", "color": "#4caf50"}
        }
    }
    
    season_trends = seasonal_data.get(current_season, seasonal_data["Spring"])
    
    for vehicle_type, data in season_trends.items():
        st.markdown(f"""
        <div style='background-color: #f8f9fa; padding: 12px 16px; border-radius: 8px; 
                    margin: 8px 0; border-left: 4px solid {data["color"]};'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <strong>{vehicle_type}</strong>
                </div>
                <div style='text-align: right;'>
                    <span style='color: {data["color"]}; font-weight: 600;'>{data["trend"]}</span>
                    <span style='color: #666; margin-left: 12px;'>{data["demand"]} demand</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Local market insights
    st.markdown("---")
    st.markdown("##### 📍 Local Area Insights (30 mile radius)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🔥 Hot Sellers This Month:**")
        hot_sellers = [
            "BMW 3 Series - 45 sold",
            "BMW X3 - 38 sold",
            "BMW 5 Series - 32 sold",
            "BMW X5 - 28 sold"
        ]
        for seller in hot_sellers:
            st.markdown(f"• {seller}")
    
    with col2:
        st.markdown("**💰 Best Value Opportunities:**")
        opportunities = [
            "Estate cars (+12% over book)",
            "Diesel models (High demand)",
            "2018-2020 models (Sweet spot)",
            "Full service history (+£800)"
        ]
        for opp in opportunities:
            st.markdown(f"• {opp}")
    
    # Price forecast
    st.markdown("---")
    st.markdown("##### 📈 6-Month Price Forecast")
    
    current_value = estimate_value(vehicle["make"], vehicle["model"], vehicle["year"], vehicle["mileage"])
    
    forecast_months = []
    for i in range(1, 7):
        month_date = datetime.date.today() + datetime.timedelta(days=30*i)
        # Simulate depreciation with seasonal adjustments
        base_depreciation = -2.5  # 2.5% per month base
        seasonal_adj = 0
        month_num = month_date.month
        
        # Adjust for seasons
        if month_num in [3, 4, 5, 6, 7]:  # Spring/Summer
            seasonal_adj = 1.0
        elif month_num in [12, 1, 2]:  # Winter
            seasonal_adj = -1.5
        
        total_change = base_depreciation + seasonal_adj
        projected_value = current_value * (1 + (total_change * i) / 100)
        
        forecast_months.append({
            "month": month_date.strftime("%b %Y"),
            "value": int(projected_value),
            "change": total_change * i
        })
    
    st.markdown(f"""
    <div style='background-color: #e3f2fd; padding: 16px; border-radius: 8px; margin: 12px 0;'>
        <p style='margin: 0 0 12px 0;'><strong>Current Value:</strong> £{current_value:,}</p>
    """, unsafe_allow_html=True)
    
    for forecast in forecast_months:
        change_color = "#4caf50" if forecast['change'] > 0 else "#f44336"
        change_symbol = "+" if forecast['change'] > 0 else ""
        st.markdown(f"""
        <div style='padding: 8px 0; border-bottom: 1px solid #ddd;'>
            <div style='display: flex; justify-content: space-between;'>
                <span>{forecast['month']}</span>
                <span>
                    <strong>£{forecast['value']:,}</strong>
                    <span style='color: {change_color}; margin-left: 8px; font-size: 13px;'>
                        ({change_symbol}{forecast['change']:.1f}%)
                    </span>
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.info("💡 **Tip:** Values typically peak in Spring/Summer. Current market conditions suggest selling now could maximize returns.")
    
    # Competition analysis
    st.markdown("---")
    st.markdown("##### 🏁 Competition Analysis")
    
    st.markdown(f"""
    <div style='background-color: #fff3cd; padding: 16px; border-radius: 8px; border-left: 4px solid #ffc107;'>
        <p style='margin: 0 0 8px 0;'><strong>⚡ Market Opportunity Alert</strong></p>
        <p style='margin: 0; font-size: 14px; line-height: 1.6;'>
            • Only <strong>3 similar vehicles</strong> available within 50 miles<br>
            • Average listing time: <strong>8 days</strong> (vs. 21 day average)<br>
            • Prices trending <strong>↑ +5%</strong> this month<br>
            • <strong>Recommendation:</strong> Strong seller's market - excellent time to trade
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_upgrade_options(vehicle):
    """Show what customers could upgrade to with their trade-in"""
    st.markdown("#### What Could You Drive Away In?")
    st.markdown("*Based on your trade-in value + typical finance options*")
    
    trade_in_value = estimate_value(vehicle["make"], vehicle["model"], vehicle["year"], vehicle["mileage"])
    
    # Mock upgrade vehicles
    upgrade_options = [
        {
            "model": "BMW 5 Series 530e M Sport",
            "year": 2023,
            "price": 45000,
            "monthly": 520,
            "deposit_needed": 45000 - trade_in_value
        },
        {
            "model": "BMW X3 xDrive30e",
            "year": 2024,
            "price": 52000,
            "monthly": 580,
            "deposit_needed": 52000 - trade_in_value
        },
        {
            "model": "BMW 4 Series 420i Coupe",
            "year": 2023,
            "price": 38000,
            "monthly": 420,
            "deposit_needed": 38000 - trade_in_value
        }
    ]
    
    for car in upgrade_options:
        st.markdown(f"""
        <div style='background-color: #f8f9fa; padding: 16px; border-radius: 8px; margin: 12px 0; border-left: 4px solid {PRIMARY};'>
            <p style='margin: 0; font-size: 18px;'><strong>{car['model']}</strong> ({car['year']})</p>
            <p style='margin: 8px 0; color: #666;'>
                <strong>£{car['price']:,}</strong> | 
                £{car['deposit_needed']:,} additional needed | 
                From <strong>£{car['monthly']}/month</strong>
            </p>
            <p style='margin: 8px 0 0 0; font-size: 13px; color: {ACCENT};'>
                Your £{trade_in_value:,} trade-in covers {int((trade_in_value/car['price'])*100)}% of the price
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.info("Speak to our sales team about part-exchange deals and finance options")

def render_inspection_booking(vehicle, offer_value):
    """Render instant inspection booking form"""
    st.markdown("---")
    st.markdown("### Book Instant Inspection")
    
    col1, col2 = st.columns(2)
    with col1:
        today = datetime.date.today()
        inspection_date = st.date_input(
            "Inspection Date",
            min_value=today,
            max_value=today + datetime.timedelta(days=7),
            value=today,
            key="inspection_date"
        )
    with col2:
        time_slot = st.selectbox(
            "Available Time Slots",
            ["Next Available (30 mins)", "11:00 AM", "02:00 PM", "04:00 PM"],
            key="inspection_time"
        )
    
    col3, col4 = st.columns(2)
    with col3:
        customer_name = st.text_input("Your Name *", placeholder="John Smith", key="inspection_name")
    with col4:
        customer_phone = st.text_input("Phone Number *", placeholder="07700 900000", key="inspection_phone")
    
    customer_email = st.text_input("Email *", placeholder="customer@example.com", key="inspection_email")
    
    st.markdown(f"""
    <div style='background-color: #e3f2fd; padding: 12px; border-radius: 8px; margin: 12px 0;'>
        <p style='margin: 0; font-size: 14px;'><strong>What happens next:</strong></p>
        <ul style='margin: 8px 0 0 0; font-size: 13px;'>
            <li>Inspection takes 15-20 minutes</li>
            <li>Instant offer confirmation</li>
            <li>Payment within 24 hours (or immediate bank transfer)</li>
            <li>All paperwork handled on-site</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    col_x, col_y = st.columns(2)
    with col_x:
        if st.button("✅ Confirm Inspection", key="confirm_inspection", use_container_width=True, type="primary"):
            if customer_name and customer_phone and customer_email:
                booking_ref = f"INS-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
                st.success(f"""
                ✅ **Inspection Booked!**
                
                **Reference:** {booking_ref}  
                **Vehicle:** {vehicle['make']} {vehicle['model']} ({vehicle['reg']})  
                **Offer Value:** £{offer_value:,}  
                **Date:** {inspection_date.strftime('%d %B %Y')} at {time_slot}  
                
                📧 Confirmation sent to {customer_email}
                📱 SMS reminder will be sent 1 hour before
                """)
                st.balloons()
                del st.session_state.show_booking
            else:
                st.error("⚠️ Please fill in all required fields")
    
    with col_y:
        if st.button("Cancel", key="cancel_inspection", use_container_width=True):
            del st.session_state.show_booking
            st.rerun()

def render_valuation(vehicle):
    """Render valuation card with deal accelerator"""
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.markdown("<h4>💰 Estimated Trade-In Value</h4>", unsafe_allow_html=True)
    
    st.markdown("""
    <p style='color: #666; font-size: 14px; margin-bottom: 16px;'>
        Based on current market data. Final valuation subject to vehicle inspection by Sytner buyer.
    </p>
    """, unsafe_allow_html=True)
    
    # Calculate value range
    base_value = estimate_value(vehicle["make"], vehicle["model"], vehicle["year"], vehicle["mileage"], "good")
    min_value = int(base_value * 0.85)  # Fair condition
    max_value = int(base_value * 1.05)  # Excellent condition
    mid_value = base_value
    
    # Display value range
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%); 
                padding: 24px; border-radius: 12px; text-align: center; color: white; margin-bottom: 20px;'>
        <div style='font-size: 16px; opacity: 0.9; margin-bottom: 8px;'>Your Vehicle Could Be Worth</div>
        <div style='font-size: 42px; font-weight: 700; margin: 12px 0;'>£{min_value:,} - £{max_value:,}</div>
        <div style='font-size: 14px; opacity: 0.85;'>
            Typical value: £{mid_value:,} • Based on {vehicle['year']} {vehicle['make']} {vehicle['model']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Value breakdown
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style='text-align: center; padding: 16px; background-color: #f8f9fa; border-radius: 8px;'>
            <div style='font-size: 20px; font-weight: 600; color: {PRIMARY};'>£{min_value:,}</div>
            <div style='font-size: 13px; color: #666; margin-top: 4px;'>Fair Condition</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='text-align: center; padding: 16px; background-color: #e3f2fd; border-radius: 8px;'>
            <div style='font-size: 20px; font-weight: 600; color: {PRIMARY};'>£{mid_value:,}</div>
            <div style='font-size: 13px; color: #666; margin-top: 4px;'>Good Condition</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style='text-align: center; padding: 16px; background-color: #f8f9fa; border-radius: 8px;'>
            <div style='font-size: 20px; font-weight: 600; color: {PRIMARY};'>£{max_value:,}</div>
            <div style='font-size: 13px; color: #666; margin-top: 4px;'>Excellent Condition</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Deal Accelerator
    st.markdown("---")
    st.markdown("### 🚀 Deal Accelerator Bonuses")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style='background-color: #e8f5e9; padding: 16px; border-radius: 8px; border-left: 4px solid #4caf50;'>
            <div style='font-size: 16px; font-weight: 600; color: #2e7d32; margin-bottom: 4px;'>
                📦 Stock Priority Bonus
            </div>
            <div style='font-size: 24px; font-weight: 700; color: #1b5e20;'>+£500</div>
            <div style='font-size: 13px; color: #666; margin-top: 4px;'>We need this model!</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='background-color: #e3f2fd; padding: 16px; border-radius: 8px; border-left: 4px solid {ACCENT};'>
            <div style='font-size: 16px; font-weight: 600; color: #1565c0; margin-bottom: 4px;'>
                ⚡ Same-Day Completion
            </div>
            <div style='font-size: 24px; font-weight: 700; color: #0d47a1;'>+£200</div>
            <div style='font-size: 13px; color: #666; margin-top: 4px;'>If completed today</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Total potential offer
    total_min = min_value + 700
    total_max = max_value + 700
    
    st.markdown(f"""
    <div style='background-color: #fff3cd; padding: 20px; border-radius: 12px; border-left: 4px solid #ffc107; margin: 20px 0;'>
        <div style='text-align: center;'>
            <div style='font-size: 16px; color: #666; margin-bottom: 8px;'><strong>Potential Total Offer (with bonuses)</strong></div>
            <div style='font-size: 36px; font-weight: 700; color: {PRIMARY};'>£{total_min:,} - £{total_max:,}</div>
            <div style='font-size: 14px; color: #666; margin-top: 8px;'>
                <em>Valid for 48 hours • Instant payment available</em>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Network comparison
    st.markdown("#### 🏆 Best Offers Across Sytner Network")
    
    st.markdown("""
    <p style='color: #666; font-size: 14px; margin-bottom: 16px;'>
        Estimated offers based on typical market conditions at each location
    </p>
    """, unsafe_allow_html=True)
    
    network_data = [
        {"location": "Sytner BMW Solihull", "offer_min": total_min, "offer_max": total_max, "distance": "Current Location", "badge": "🏆 Best Offer"},
        {"location": "Sytner BMW Birmingham", "offer_min": total_min - 200, "offer_max": total_max - 200, "distance": "8 miles", "badge": ""},
        {"location": "Sytner BMW Coventry", "offer_min": total_min - 400, "offer_max": total_max - 400, "distance": "15 miles", "badge": ""},
    ]
    
    for loc in network_data:
        badge_html = f"<span style='color: #ffa726; margin-left: 8px;'>{loc['badge']}</span>" if loc['badge'] else ""
        st.markdown(f"""
        <div style='background-color: #f8f9fa; padding: 12px 16px; border-radius: 8px; margin: 8px 0; 
                    display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <strong>{loc['location']}</strong>{badge_html}
                <div style='font-size: 13px; color: #666; margin-top: 4px;'>{loc['distance']}</div>
            </div>
            <div style='text-align: right;'>
                <div style='font-size: 18px; font-weight: 600; color: {PRIMARY};'>£{loc['offer_min']:,} - £{loc['offer_max']:,}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_additional_details(vehicle, mot_tax, history_flags, open_recalls):
    """Render additional details expander"""
    with st.expander("🔍 View Additional Details"):
        st.markdown("### Complete Vehicle Information")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Specifications", "📜 History", "⚠️ Alerts", "📈 Market Trends", "🚗 Upgrade Options"])
        
        with tab1:
            st.markdown(f"""
            - **Registration:** {vehicle['reg']}
            - **Make & Model:** {vehicle['make']} {vehicle['model']}
            - **Year:** {vehicle['year']}
            - **VIN:** {vehicle['vin']}
            - **Current Mileage:** {vehicle['mileage']:,} miles
            - **Next MOT Due:** {mot_tax['mot_next_due']}
            - **Tax Expiry:** {mot_tax['tax_expiry']}
            """)
        
        with tab2:
            st.markdown("**MOT Test History:**")
            for entry in mot_tax['mot_history']:
                st.markdown(f"- {entry['date']}: **{entry['result']}** at {entry['mileage']:,} miles")
            
            if history_flags.get("note"):
                st.warning(f"⚠️ {history_flags['note']}")
        
        with tab3:
            alert_count = sum([
                history_flags.get("write_off", False),
                history_flags.get("theft", False),
                history_flags.get("mileage_anomaly", False),
                open_recalls > 0
            ])
            
            if alert_count > 0:
                st.warning(f"⚠️ {alert_count} alert(s) found for this vehicle")
                if history_flags.get("write_off"):
                    st.error("🚨 Vehicle has a write-off record")
                if history_flags.get("theft"):
                    st.error("🚨 Vehicle has a theft record")
                if history_flags.get("mileage_anomaly"):
                    st.warning("⚠️ Mileage discrepancy detected")
                if open_recalls > 0:
                    st.warning(f"⚠️ {open_recalls} open safety recall(s)")
            else:
                st.success("✅ No alerts found for this vehicle")
        
        with tab4:
            render_market_trends(vehicle)
        
        with tab5:
            render_upgrade_options(vehicle)

# ============================================================================
# PAGE RENDERERS
# ============================================================================

def render_input_page():
    """Render the vehicle input page"""
    
    # Hero section with value proposition
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%); 
                padding: 40px 24px; border-radius: 16px; margin-bottom: 32px; text-align: center;'>
        <h1 style='color: white; margin: 0 0 16px 0; font-size: 36px; font-weight: 700;'>Instant Trade-In Valuation</h1>
        <p style='color: rgba(255,255,255,0.95); font-size: 18px; margin: 0 0 28px 0; font-weight: 400;'>
            Get competitive offers in seconds • Complete deals in minutes
        </p>
        <div style='display: flex; justify-content: center; gap: 32px; flex-wrap: wrap;'>
            <div style='text-align: center;'>
                <div style='font-size: 32px; font-weight: 700; color: white;'>30 mins</div>
                <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 4px;'>Average completion</div>
            </div>
            <div style='text-align: center;'>
                <div style='font-size: 32px; font-weight: 700; color: white;'>15+</div>
                <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 4px;'>Network locations</div>
            </div>
            <div style='text-align: center;'>
                <div style='font-size: 32px; font-weight: 700; color: white;'>£500+</div>
                <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 4px;'>Bonus opportunities</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick benefit cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style='text-align: center; padding: 20px 16px;'>
            <div style='font-weight: 600; color: #0b3b6f; margin-bottom: 8px; font-size: 17px;'>Instant Check</div>
            <div style='font-size: 14px; color: #666; line-height: 1.5;'>Full vehicle history in seconds</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 20px 16px;'>
            <div style='font-weight: 600; color: #0b3b6f; margin-bottom: 8px; font-size: 17px;'>Best Offers</div>
            <div style='font-size: 14px; color: #666; line-height: 1.5;'>Compare across network</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style='text-align: center; padding: 20px 16px;'>
            <div style='font-weight: 600; color: #0b3b6f; margin-bottom: 8px; font-size: 17px;'>Same Day</div>
            <div style='font-size: 14px; color: #666; line-height: 1.5;'>Complete deal today</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main input section
    st.markdown(f"""
    <div style='text-align: center; margin-bottom: 32px;'>
        <h2 style='color: {PRIMARY}; margin: 0 0 12px 0; font-size: 28px;'>Get Started</h2>
        <p style='color: #666; font-size: 16px;'>Enter the customer's registration or scan their number plate</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Center the radio buttons with more spacing
    col_spacer1, col_radio, col_spacer2 = st.columns([1, 2, 1])
    with col_radio:
        option = st.radio(
            "Choose input method",
            ["Enter Registration / VIN", "Scan Number Plate"],
            index=0,
            horizontal=True,
            label_visibility="collapsed"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if "Enter Registration" in option:
        manual_reg = st.text_input(
            "Enter registration / VIN",
            placeholder="e.g. KT68XYZ or WBA8BFAKEVIN12345",
            help="Enter a UK registration or VIN number",
            label_visibility="collapsed"
        )
        
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Look Up Vehicle", disabled=not manual_reg, use_container_width=True, type="primary"):
                if validate_registration(manual_reg):
                    st.session_state.reg = manual_reg.strip().upper().replace(" ", "")
                    st.session_state.image = None
                    st.session_state.show_summary = True
                    st.rerun()
                else:
                    st.error("Please enter a valid registration (minimum 5 characters)")
        
        # Quick examples - more prominent
        st.markdown("""
        <div style='text-align: center; margin-top: 20px;'>
            <p style='color: #999; font-size: 14px;'><strong>Try these examples:</strong> KT68XYZ • AB12CDE • WBA8B12345</p>
        </div>
        """, unsafe_allow_html=True)
    
    else:  # Scan Number Plate
        # Camera instructions
        st.markdown(f"""
        <div style='background-color: #e3f2fd; padding: 16px; border-radius: 8px; border-left: 4px solid {ACCENT}; margin-bottom: 20px;'>
            <p style='margin: 0; font-size: 14px; color: #0b3b6f;'>
                <strong>Camera Tips:</strong> Position the plate clearly in frame • Ensure good lighting • Hold steady
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        image = st.camera_input(
            "Scan customer's number plate",
            key="camera",
            help="Position the number plate clearly in the frame",
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
                    st.error("Could not read number plate. Please try again or enter manually.")
            except Exception as e:
                st.error(f"Error processing image: {str(e)}")
    
    # Trust indicators at bottom - cleaner styling
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align: center; padding: 28px 24px; background-color: white; border-radius: 12px; margin-top: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);'>
        <p style='color: #999; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 16px 0; font-weight: 600;'>Trusted by Sytner Staff Nationwide</p>
        <div style='display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;'>
            <div style='color: {PRIMARY}; font-size: 14px;'>
                <span style='font-weight: 600; color: #4caf50;'>✓</span> Full DVLA Integration
            </div>
            <div style='color: {PRIMARY}; font-size: 14px;'>
                <span style='font-weight: 600; color: #4caf50;'>✓</span> Real-time MOT Data
            </div>
            <div style='color: {PRIMARY}; font-size: 14px;'>
                <span style='font-weight: 600; color: #4caf50;'>✓</span> Secure & Compliant
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
        with st.spinner("Fetching vehicle information..."):
            vehicle = lookup_vehicle_basic(reg)
            mot_tax = lookup_mot_and_tax(reg)
            recalls = lookup_recalls(reg)
            history_flags = get_history_flags(reg)
    except Exception as e:
        st.error(f"⚠️ Error fetching vehicle data: {str(e)}")
        st.stop()

    # Render all sections
    open_recalls = sum(1 for r in recalls if r["open"])
    
    render_vehicle_summary(vehicle, mot_tax, history_flags, open_recalls)
    
    # Quick Market Insights Card
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%); 
                padding: 20px; border-radius: 12px; margin-bottom: 20px; color: white;'>
        <h4 style='margin: 0 0 12px 0;'>📊 Quick Market Insights</h4>
        <div style='display: flex; justify-content: space-around; flex-wrap: wrap; gap: 16px;'>
            <div style='text-align: center;'>
                <div style='font-size: 24px; font-weight: 700;'>HIGH</div>
                <div style='font-size: 13px; opacity: 0.9;'>Current Demand</div>
            </div>
            <div style='text-align: center;'>
                <div style='font-size: 24px; font-weight: 700;'>12 days</div>
                <div style='font-size: 13px; opacity: 0.9;'>Avg. to Sell</div>
            </div>
            <div style='text-align: center;'>
                <div style='font-size: 24px; font-weight: 700;'>↑ +5%</div>
                <div style='font-size: 13px; opacity: 0.9;'>Price Trend</div>
            </div>
        </div>
        <div style='margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.3); text-align: center; font-size: 13px;'>
            💡 See full trends analysis in Additional Details → Market Trends
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    render_mot_history(mot_tax['mot_history'])
    render_recalls(recalls)
    
    # Sytner Buyers Section
    render_sytner_buyers(vehicle, reg)
    
    render_valuation(vehicle)
    render_additional_details(vehicle, mot_tax, history_flags, open_recalls)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Sytner TradeSnap",
        page_icon="⚡",
        layout="centered"
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
