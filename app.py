import streamlit as st
from PIL import Image, ImageOps
import datetime
import re

# -------------------------
# Mock / Helpers
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

def validate_registration(reg):
    """Validate UK registration format"""
    if not reg:
        return False
    reg_clean = reg.upper().replace(" ", "")
    # Basic validation - at least 5 characters
    return len(reg_clean) >= 5 and re.match(r'^[A-Z0-9]+$', reg_clean)

PLATE_REGEX = re.compile(r"[A-Z0-9]{5,10}", re.I)

# -------------------------
# Streamlit config + CSS
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
.badge-success {{background-color: #4caf50;}}
.booking-form {{
    background-color: #f5f5f5;
    padding: 16px;
    border-radius: 8px;
    margin-top: 12px;
}}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Session State Initialization
# -------------------------
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "reg": None,
        "image": None,
        "show_summary": False,
        "vehicle_data": None,
        "booking_forms": {}  # Track which recall booking forms are open
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

init_session_state()

# -------------------------
# Header
# -------------------------
st.markdown(f"<div class='header-card'>Sytner AutoSense — POC</div>", unsafe_allow_html=True)

# -------------------------
# Reset / Change Registration
# -------------------------
if st.session_state.show_summary:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Reset / Change Registration", use_container_width=True):
            reset_all_state()
            st.rerun()

# -------------------------
# Input page
# -------------------------
if not st.session_state.show_summary:
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
            placeholder="e.g. KT68XYZ or VIN...",
            help="Enter a UK registration or VIN number"
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Look Up Vehicle", disabled=not manual_reg, use_container_width=True):
                if validate_registration(manual_reg):
                    st.session_state.reg = manual_reg.strip().upper().replace(" ", "")
                    st.session_state.image = None
                    st.session_state.show_summary = True
                    st.rerun()
                else:
                    st.error("⚠️ Please enter a valid registration (minimum 5 characters)")
    
    elif option == "Take Photo":
        image = st.camera_input(
            "Take photo of the number plate", 
            key="camera", 
            help="Position the number plate clearly in the frame"
        )
        
        if image:
            try:
                # Mock OCR processing
                extracted_reg = mock_ocr_numberplate(image)
                
                if extracted_reg and validate_registration(extracted_reg):
                    st.session_state.image = image
                    st.session_state.reg = extracted_reg
                    st.session_state.show_summary = True
                    st.rerun()
                else:
                    st.error("⚠️ Could not read number plate. Please try again or enter manually.")
            except Exception as e:
                st.error(f"⚠️ Error processing image: {str(e)}")

# -------------------------
# Summary page
# -------------------------
if st.session_state.show_summary and st.session_state.reg:
    reg = st.session_state.reg
    image = st.session_state.image

    # Display captured image if available
    if image:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(ImageOps.exif_transpose(Image.open(image)), use_container_width=True)

    # Display numberplate
    st.markdown(f"<div class='numberplate'>{reg}</div>", unsafe_allow_html=True)

    # Fetch mocked data with error handling
    try:
        with st.spinner("Fetching vehicle information..."):
            vehicle = lookup_vehicle_basic(reg)
            mot_tax = lookup_mot_and_tax(reg)
            recalls = lookup_recalls(reg)
            history_flags = get_history_flags(reg)
    except Exception as e:
        st.error(f"⚠️ Error fetching vehicle data: {str(e)}")
        st.stop()

    # Vehicle Summary with badges
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

    # Badges
    st.markdown("---")
    flags_html = "<p><strong>Status Flags:</strong> "
    flag_list = []
    
    if history_flags.get("write_off"):
        flag_list.append('<span class="badge badge-error">Write-off</span>')
    if history_flags.get("theft"):
        flag_list.append('<span class="badge badge-error">Theft Record</span>')
    if history_flags.get("mileage_anomaly"):
        flag_list.append('<span class="badge badge-warning">Mileage Anomaly</span>')
    
    # Open recalls badge
    open_recalls = sum(1 for r in recalls if r["open"])
    if open_recalls:
        flag_list.append(f'<span class="badge badge-warning">{open_recalls} Open Recall(s)</span>')
    
    if not flag_list:
        flag_list.append('<span class="badge badge-success">No Issues Found</span>')

    flags_html += " ".join(flag_list) + "</p>"
    st.markdown(flags_html, unsafe_allow_html=True)
    
    if history_flags.get("note"):
        st.info(f"ℹ️ {history_flags['note']}")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # MOT History
    with st.expander("📋 MOT History"):
        if mot_tax['mot_history']:
            for entry in mot_tax['mot_history']:
                result_icon = "✅" if entry['result'] == "Pass" else "⚠️"
                st.markdown(f"{result_icon} **{entry['date']}**: {entry['result']} — {entry['mileage']:,} miles")
        else:
            st.info("No MOT history available")

    # Recalls with Booking Feature
    with st.expander(f"🔔 Recalls ({len(recalls)} total, {open_recalls} open)"):
        if not recalls:
            st.success("✅ No recalls found for this vehicle")
        else:
            for idx, recall in enumerate(recalls):
                recall_key = f"recall_{recall['id']}"
                
                # Display recall info
                col1, col2 = st.columns([3, 1])
                with col1:
                    status_badge = "⚠️ **OPEN**" if recall['open'] else "✅ Closed"
                    st.markdown(f"**{recall['summary']}**")
                    st.caption(f"ID: `{recall['id']}` — Status: {status_badge}")
                
                with col2:
                    if recall['open']:
                        if st.button("📅 Book Repair", key=f"book_btn_{recall_key}"):
                            # Toggle booking form
                            if recall_key in st.session_state.booking_forms:
                                del st.session_state.booking_forms[recall_key]
                            else:
                                st.session_state.booking_forms[recall_key] = True
                            st.rerun()
                
                # Show booking form if toggled
                if recall['open'] and st.session_state.booking_forms.get(recall_key):
                    st.markdown("<div class='booking-form'>", unsafe_allow_html=True)
                    st.markdown("##### Book Recall Repair")
                    
                    # Garage selection
                    garage = st.selectbox(
                        "Select Sytner Garage",
                        [
                            "Sytner BMW Birmingham - High St",
                            "Sytner BMW Manchester - Oxford Rd",
                            "Sytner BMW London - Park Lane",
                            "Sytner BMW Bristol - Temple Way"
                        ],
                        key=f"garage_{recall_key}"
                    )
                    
                    # Date and time
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
                        time_slot = st.selectbox(
                            "Time Slot",
                            ["09:00 AM", "11:00 AM", "02:00 PM", "04:00 PM"],
                            key=f"time_{recall_key}"
                        )
                    
                    # Customer details
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
                    
                    # Action buttons
                    col_x, col_y = st.columns(2)
                    with col_x:
                        if st.button("✅ Confirm Booking", key=f"confirm_{recall_key}", use_container_width=True):
                            # Validation
                            if not customer_name or not customer_phone:
                                st.error("⚠️ Please fill in all required fields (marked with *)")
                            elif len(customer_phone) < 10:
                                st.error("⚠️ Please enter a valid phone number")
                            else:
                                # Success - create booking reference
                                booking_ref = f"RCL-{recall['id']}-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
                                
                                st.success(f"""
                                ✅ **Booking Confirmed!**
                                
                                **Reference:** {booking_ref}  
                                **Garage:** {garage}  
                                **Date & Time:** {booking_date.strftime('%d %B %Y')} at {time_slot}  
                                **Customer:** {customer_name} | {customer_phone}
                                
                                📧 Confirmation email sent to customer
                                """)
                                
                                # Clear the booking form
                                if recall_key in st.session_state.booking_forms:
                                    del st.session_state.booking_forms[recall_key]
                                
                                st.balloons()
                    
                    with col_y:
                        if st.button("❌ Cancel", key=f"cancel_{recall_key}", use_container_width=True):
                            # Close the form
                            if recall_key in st.session_state.booking_forms:
                                del st.session_state.booking_forms[recall_key]
                            st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Divider between recalls
                if idx < len(recalls) - 1:
                    st.markdown("---")

    # Insurance
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

    # Valuation card with Send to Buyer
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.markdown("<h4>💰 Valuation</h4>", unsafe_allow_html=True)
    
    # Condition selector
    condition = st.radio(
        "Select vehicle condition", 
        ["excellent", "good", "fair", "poor"], 
        index=1, 
        horizontal=True,
        help="Select the overall condition of the vehicle"
    )
    
    # Calculate value
    value = estimate_value(vehicle["make"], vehicle["model"], vehicle["year"], vehicle["mileage"], condition)
    
    st.markdown(f"""
    <p style='font-size: 20px;'><strong>Estimated Trade-In Value:</strong> 
    <span style='color: {PRIMARY}; font-size: 28px; font-weight: 700;'>£{value:,}</span></p>
    <p style='color: #666;'><em>Condition: {condition.capitalize()}</em></p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Send to buyer
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**Assigned Buyer:** John Smith")
        st.caption("📞 01234 567890 | 📧 john.smith@sytner.co.uk")
    with col2:
        if st.button("📤 Send to Buyer", key="send_buyer", use_container_width=True):
            st.success("✅ Vehicle details sent to John Smith!")
            st.info(f"📧 Email sent with valuation: £{value:,} ({condition})")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Additional details expander
    with st.expander("🔍 View Additional Details"):
        st.markdown("### Complete Vehicle Information")
        
        tab1, tab2, tab3 = st.tabs(["📊 Specifications", "📜 History", "⚠️ Alerts"])
        
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
