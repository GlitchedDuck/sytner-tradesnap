import streamlit as st
from PIL import Image, ImageOps
import datetime, re, json
import io

# -------------------------
# Mock / helper functions
# -------------------------
def lookup_vehicle_basic(reg):
    return {
        "reg": reg.upper().replace(" ", ""),
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

def lookup_recalls(reg):
    return [{"id": "R-2023-001", "summary": "Airbag inflator recall — replace module", "open": True}]

def lookup_history_flags(reg):
    return {
        "write_off": False,
        "theft": False,
        "mileage_anomaly": True,
        "note": "Mileage shows a 5,000‑mile jump in 2021 record"
    }

def estimate_value(make, model, year, mileage, condition="good"):
    age = datetime.date.today().year - year
    base = 25000 - (age * 2000) - (mileage / 10)
    cond_multiplier = {"excellent": 1.05, "good": 1.0, "fair": 0.9, "poor": 0.8}
    return max(100, int(base * cond_multiplier.get(condition, 1.0)))

# -------------------------
# Session state setup
# -------------------------
if "reg" not in st.session_state:
    st.session_state.reg = None
if "image" not in st.session_state:
    st.session_state.image = None
if "show_summary" not in st.session_state:
    st.session_state.show_summary = False

st.set_page_config(page_title="Sytner AutoSense", page_icon="🚗", layout="centered")

# -------------------------
# Input page
# -------------------------
if not st.session_state.show_summary:
    st.title("AutoSense — Vehicle Check")
    st.write("Enter vehicle registration/VIN or take a photo of the number plate.")

    option = st.radio("Input method", ["Manual entry", "Take photo"], index=0)

    if option == "Manual entry":
        manual_reg = st.text_input("Registration / VIN", placeholder="KT68XYZ or VIN…")
        if manual_reg:
            st.session_state.reg = manual_reg.strip().upper().replace(" ", "")
            st.session_state.show_summary = True
            st.experimental_rerun()  # immediately show summary

    elif option == "Take photo":
        img = st.camera_input("Snap number plate photo")
        if img:
            st.session_state.image = img
            # TODO: replace with real OCR to get reg
            st.session_state.reg = "KT68XYZ"  # mock reg
            st.session_state.show_summary = True
            st.experimental_rerun()  # immediately show summary

    st.stop()  # stop here until reg is provided

# -------------------------
# Summary page
# -------------------------
reg = st.session_state.reg
image = st.session_state.image

# Centered column layout
_, center_col, _ = st.columns([1, 2, 1])

with center_col:
    st.header(f"Vehicle: {reg}")

    if image:
        st.image(ImageOps.exif_transpose(Image.open(image)), use_column_width=True)

    # Fetch data
    vehicle = lookup_vehicle_basic(reg)
    mot_tax = lookup_mot_and_tax(reg)
    recalls = lookup_recalls(reg)
    flags = lookup_history_flags(reg)

    # Vehicle summary
    st.subheader("Vehicle Summary")
    st.write(f"**Make / Model:** {vehicle['make']} {vehicle['model']}")
    st.write(f"**Year:** {vehicle['year']}")
    st.write(f"**VIN:** {vehicle['vin']}")
    st.write(f"**Mileage:** {vehicle['mileage']:,} miles")
    st.write(f"**Next MOT due:** {mot_tax['mot_next_due']}")

    # Flags
    if flags.get("write_off"):
        st.error("⚠️ Write‑off record detected")
    if flags.get("theft"):
        st.error("⚠️ Theft record detected")
    if flags.get("mileage_anomaly"):
        st.warning(f"⚠️ {flags.get('note')}")

    # MOT history
    with st.expander("MOT History"):
        for rec in mot_tax["mot_history"]:
            st.write(f"- {rec['date']}: **{rec['result']}** — {rec['mileage']} miles")

    # Recalls
    with st.expander("Recalls"):
        for r in recalls:
            status = "Open ⚠️" if r.get("open") else "Closed ✅"
            st.write(f"- {r['summary']} — ID: {r['id']} ({status})")

    # Valuation
    st.subheader("Valuation")
    condition = st.selectbox("Condition", ["excellent", "good", "fair", "poor"], index=1)
    value = estimate_value(vehicle["make"], vehicle["model"], vehicle["year"], vehicle["mileage"], condition)
    st.write(f"**Estimated Value:** £{value:,}")

    # Send to Buyer
    if st.button("Send to Buyer"):
        st.success("✅ Sent to buyer — Buyer: John Smith | 01234 567890")

    # Reset / Change registration
    if st.button("New / Change Registration"):
        st.session_state.reg = None
        st.session_state.image = None
        st.session_state.show_summary = False
        st.experimental_rerun()
