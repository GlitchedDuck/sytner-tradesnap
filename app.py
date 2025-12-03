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
    "Sytner BMW Birmingham - High St",
    "Sytner BMW Manchester - Oxford Rd",
    "Sytner BMW London - Park Lane",
    "Sytner BMW Bristol - Temple Way"
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
    st.markdown("<h4>Instant Trade-In Valuation</h4>", unsafe_allow_html=True)
    
    condition = st.radio(
        "Select vehicle condition",
        ["excellent", "good", "fair", "poor"],
        index=1,
        horizontal=True,
        help="Select the overall condition of the vehicle"
    )
    
    value = estimate_value(vehicle["make"], vehicle["model"], vehicle["year"], vehicle["mileage"], condition)
    
    st.markdown(f"""
    <p style='font-size: 20px;'><strong>Instant Trade-In Value:</strong> 
    <span style='color: {PRIMARY}; font-size: 28px; font-weight: 700;'>£{value:,}</span></p>
    <p style='color: #666;'><em>Condition: {condition.capitalize()}</em></p>
    """, unsafe_allow_html=True)
    
    # Deal Accelerator
    st.markdown("---")
    st.markdown("### Deal Accelerator")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Stock Priority Bonus:**")
        st.success("+£500 - We need this model!")
    with col2:
        st.markdown("**Same-Day Completion:**")
        st.info("+£200 if completed today")
    
    total_value = value + 700
    st.markdown(f"""
    <div style='background-color: #fff3cd; padding: 16px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 16px 0;'>
        <p style='margin: 0; font-size: 16px;'><strong>Total Offer:</strong> 
        <span style='color: {PRIMARY}; font-size: 32px; font-weight: 700;'>£{total_value:,}</span></p>
        <p style='margin: 8px 0 0 0; color: #666; font-size: 14px;'><em>Valid for 48 hours | Instant payment available</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Network comparison
    st.markdown("#### Best Offers Across Sytner Network")
    network_data = [
        {"location": "Sytner BMW Birmingham", "offer": total_value, "distance": "Current", "badge": "Best Offer"},
        {"location": "Sytner BMW Solihull", "offer": total_value - 300, "distance": "8 miles", "badge": ""},
        {"location": "Sytner BMW Coventry", "offer": total_value - 500, "distance": "15 miles", "badge": ""},
    ]
    
    for loc in network_data:
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            badge = f" - {loc['badge']}" if loc['badge'] else ""
            st.markdown(f"{loc['location']}{badge}")
        with col_b:
            st.markdown(f"**£{loc['offer']:,}**")
        with col_c:
            st.markdown(f"*{loc['distance']}*")
    
    st.markdown("---")
    
    # Instant booking
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Assigned Vehicle Buyer:** John Smith")
        st.caption("📞 01234 567890 | 📧 john.smith@sytner.co.uk")
    with col2:
        if st.button("Book Inspection Slot", key="book_inspection", use_container_width=True, type="primary"):
            st.session_state.show_booking = True
            st.rerun()
    
    if st.session_state.get("show_booking"):
        render_inspection_booking(vehicle, total_value)
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_additional_details(vehicle, mot_tax, history_flags, open_recalls):
    """Render additional details expander"""
    with st.expander("🔍 View Additional Details"):
        st.markdown("### Complete Vehicle Information")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Specifications", "📜 History", "⚠️ Alerts", "🚗 Upgrade Options"])
        
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
    render_mot_history(mot_tax['mot_history'])
    render_recalls(recalls)
    
    with st.expander("🛡️ Insurance Quote"):
        st.info("💡 Insurance quotes are mocked. Integrate with aggregator APIs for live quotes.")
        if st.button('Get Mock Insurance Quote', key="insurance_quote"):
            with st.spinner("Fetching quotes..."):
                st.success("""
                **Sample Quote:**  
                💰 £320/year (Third Party, Fire & Theft)  
                🔹 Excess: £250  
                🔹 No Claims Bonus: Year 1  
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
