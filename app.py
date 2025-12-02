"""
Sytner TradeSnap - Vehicle Trade-In Valuation Tool
===================================================
A Streamlit application for instant vehicle lookups, valuations, and deal processing.

Architecture:
- Config: All constants and configuration in one place
- Models: Data classes for type safety
- Services: Mock API layer (swap for real implementations)
- Components: Reusable UI components
- Pages: Page-level rendering logic
- Main: Application entry point
"""

import streamlit as st
from PIL import Image, ImageOps
import datetime
import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from abc import ABC, abstractmethod


# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Application configuration - single source of truth"""
    
    # Branding
    APP_NAME = "Sytner TradeSnap"
    APP_TAGLINE = "Snap it. Value it. Done."
    
    # Colors
    PRIMARY = "#0a2f4f"
    PRIMARY_LIGHT = "#1a4a6e"
    ACCENT = "#00b4d8"
    ACCENT_HOVER = "#0096b7"
    SUCCESS = "#06d6a0"
    WARNING = "#ffd166"
    ERROR = "#ef476f"
    PAGE_BG = "#f0f4f8"
    CARD_BG = "#ffffff"
    TEXT_PRIMARY = "#1a1a2e"
    TEXT_MUTED = "#6b7280"
    
    # Validation
    PLATE_MIN_LENGTH = 5
    PLATE_MAX_LENGTH = 10
    PHONE_MIN_LENGTH = 10
    
    # Business rules
    BOOKING_ADVANCE_DAYS_MIN = 1
    BOOKING_ADVANCE_DAYS_MAX = 60
    INSPECTION_ADVANCE_DAYS_MAX = 7
    VALUATION_VALIDITY_HOURS = 48
    STOCK_PRIORITY_BONUS = 500
    SAME_DAY_BONUS = 200
    
    # Locations
    GARAGES = [
        "Sytner BMW Birmingham - High St",
        "Sytner BMW Manchester - Oxford Rd",
        "Sytner BMW London - Park Lane",
        "Sytner BMW Bristol - Temple Way",
        "Sytner BMW Solihull - Stratford Rd",
        "Sytner BMW Coventry - Ring Road",
    ]
    
    TIME_SLOTS = ["09:00 AM", "11:00 AM", "02:00 PM", "04:00 PM"]
    INSPECTION_SLOTS = ["Next Available (30 mins)", "11:00 AM", "02:00 PM", "04:00 PM"]


# ============================================================================
# DATA MODELS
# ============================================================================

class VehicleCondition(Enum):
    """Vehicle condition ratings"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    
    @property
    def multiplier(self) -> float:
        multipliers = {
            VehicleCondition.EXCELLENT: 1.05,
            VehicleCondition.GOOD: 1.0,
            VehicleCondition.FAIR: 0.9,
            VehicleCondition.POOR: 0.8,
        }
        return multipliers[self]


@dataclass
class Vehicle:
    """Vehicle information"""
    reg: str
    make: str
    model: str
    year: int
    vin: str
    mileage: int
    
    @property
    def age(self) -> int:
        return datetime.date.today().year - self.year
    
    @property
    def display_name(self) -> str:
        return f"{self.make} {self.model}"


@dataclass
class MOTEntry:
    """Single MOT test record"""
    date: str
    result: str
    mileage: int
    
    @property
    def is_pass(self) -> bool:
        return self.result.lower() == "pass"


@dataclass
class MOTAndTax:
    """MOT and tax information"""
    mot_next_due: str
    tax_expiry: str
    mot_history: list[MOTEntry] = field(default_factory=list)


@dataclass
class Recall:
    """Vehicle recall information"""
    id: str
    summary: str
    is_open: bool


@dataclass
class HistoryFlags:
    """Vehicle history check flags"""
    write_off: bool = False
    theft: bool = False
    mileage_anomaly: bool = False
    note: Optional[str] = None
    
    @property
    def has_issues(self) -> bool:
        return self.write_off or self.theft or self.mileage_anomaly
    
    @property
    def issue_count(self) -> int:
        return sum([self.write_off, self.theft, self.mileage_anomaly])


@dataclass
class Valuation:
    """Vehicle valuation result"""
    base_value: int
    condition: VehicleCondition
    stock_bonus: int = 0
    same_day_bonus: int = 0
    
    @property
    def total_value(self) -> int:
        return self.base_value + self.stock_bonus + self.same_day_bonus


@dataclass
class Booking:
    """Booking information"""
    reference: str
    garage: str
    date: datetime.date
    time_slot: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None


# ============================================================================
# SERVICE LAYER (Abstract base + Mock implementation)
# ============================================================================

class VehicleService(ABC):
    """Abstract base class for vehicle data services"""
    
    @abstractmethod
    def lookup_vehicle(self, reg: str) -> Vehicle:
        pass
    
    @abstractmethod
    def lookup_mot_and_tax(self, reg: str) -> MOTAndTax:
        pass
    
    @abstractmethod
    def lookup_recalls(self, reg_or_vin: str) -> list[Recall]:
        pass
    
    @abstractmethod
    def get_history_flags(self, reg: str) -> HistoryFlags:
        pass
    
    @abstractmethod
    def estimate_value(self, vehicle: Vehicle, condition: VehicleCondition) -> int:
        pass
    
    @abstractmethod
    def extract_plate_from_image(self, image) -> Optional[str]:
        pass


class MockVehicleService(VehicleService):
    """Mock implementation for development/demo"""
    
    def lookup_vehicle(self, reg: str) -> Vehicle:
        reg_clean = reg.upper().replace(" ", "")
        return Vehicle(
            reg=reg_clean,
            make="BMW",
            model="3 Series",
            year=2018,
            vin="WBA8BFAKEVIN12345",
            mileage=54000
        )
    
    def lookup_mot_and_tax(self, reg: str) -> MOTAndTax:
        today = datetime.date.today()
        return MOTAndTax(
            mot_next_due=(today + datetime.timedelta(days=120)).isoformat(),
            tax_expiry=(today + datetime.timedelta(days=30)).isoformat(),
            mot_history=[
                MOTEntry(date="2024-08-17", result="Pass", mileage=52000),
                MOTEntry(date="2023-08-10", result="Advisory", mileage=48000),
                MOTEntry(date="2022-08-05", result="Pass", mileage=41000),
            ]
        )
    
    def lookup_recalls(self, reg_or_vin: str) -> list[Recall]:
        return [
            Recall(id="R-2023-001", summary="Airbag inflator recall - replace module", is_open=True),
            Recall(id="R-2022-012", summary="Steering column check", is_open=False),
        ]
    
    def get_history_flags(self, reg: str) -> HistoryFlags:
        return HistoryFlags(
            write_off=False,
            theft=False,
            mileage_anomaly=True,
            note="Mileage shows a 5,000 jump in 2021 record"
        )
    
    def estimate_value(self, vehicle: Vehicle, condition: VehicleCondition) -> int:
        base = 25000 - (vehicle.age * 2000) - (vehicle.mileage / 10)
        return max(100, int(base * condition.multiplier))
    
    def extract_plate_from_image(self, image) -> Optional[str]:
        # Mock OCR - returns a sample plate
        return "KT68XYZ"


# Service instance (swap for real implementation in production)
vehicle_service: VehicleService = MockVehicleService()


# ============================================================================
# VALIDATION
# ============================================================================

class Validator:
    """Input validation utilities"""
    
    @staticmethod
    def is_valid_registration(reg: Optional[str]) -> bool:
        if not reg:
            return False
        reg_clean = reg.upper().replace(" ", "")
        return (
            Config.PLATE_MIN_LENGTH <= len(reg_clean) <= Config.PLATE_MAX_LENGTH
            and re.match(r'^[A-Z0-9]+$', reg_clean) is not None
        )
    
    @staticmethod
    def is_valid_phone(phone: Optional[str]) -> bool:
        if not phone:
            return False
        digits = re.sub(r'\D', '', phone)
        return len(digits) >= Config.PHONE_MIN_LENGTH
    
    @staticmethod
    def is_valid_email(email: Optional[str]) -> bool:
        if not email:
            return True  # Email is optional
        return re.match(r'^[^@]+@[^@]+\.[^@]+$', email) is not None
    
    @staticmethod
    def clean_registration(reg: str) -> str:
        return reg.strip().upper().replace(" ", "")


# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================

class SessionState:
    """Centralized session state management"""
    
    DEFAULTS = {
        "reg": None,
        "image": None,
        "show_summary": False,
        "vehicle_data": None,
        "booking_forms": {},
        "show_inspection_booking": False,
    }
    
    @classmethod
    def initialize(cls):
        """Initialize all session state variables"""
        for key, value in cls.DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @classmethod
    def reset(cls):
        """Reset all session state to defaults"""
        for key, value in cls.DEFAULTS.items():
            st.session_state[key] = value
    
    @classmethod
    def set_vehicle(cls, reg: str, image=None):
        """Set vehicle lookup state"""
        st.session_state.reg = reg
        st.session_state.image = image
        st.session_state.show_summary = True
    
    @classmethod
    def toggle_booking_form(cls, recall_key: str):
        """Toggle a recall booking form"""
        if recall_key in st.session_state.booking_forms:
            del st.session_state.booking_forms[recall_key]
        else:
            st.session_state.booking_forms = {recall_key: True}
    
    @classmethod
    def close_booking_form(cls, recall_key: str):
        """Close a specific booking form"""
        if recall_key in st.session_state.booking_forms:
            del st.session_state.booking_forms[recall_key]


# ============================================================================
# STYLING
# ============================================================================

class Styles:
    """CSS styling for the application"""
    
    @staticmethod
    def get_css() -> str:
        return f"""
        <style>
        /* Import distinctive fonts */
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Mono:wght@700&display=swap');
        
        /* Global styles */
        [data-testid="stAppViewContainer"] {{
            background: linear-gradient(180deg, {Config.PAGE_BG} 0%, #e2e8f0 100%);
            font-family: 'DM Sans', sans-serif;
        }}
        
        [data-testid="stAppViewContainer"] * {{
            font-family: 'DM Sans', sans-serif;
        }}
        
        .block-container {{
            padding-top: 1.5rem;
            max-width: 800px;
        }}
        
        /* Header card */
        .header-card {{
            background: linear-gradient(135deg, {Config.PRIMARY} 0%, {Config.PRIMARY_LIGHT} 100%);
            color: white;
            padding: 20px 28px;
            border-radius: 16px;
            text-align: center;
            margin-bottom: 28px;
            box-shadow: 0 8px 32px rgba(10, 47, 79, 0.25);
        }}
        
        .header-title {{
            font-family: 'Space Mono', monospace;
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin: 0;
        }}
        
        .header-tagline {{
            font-size: 14px;
            opacity: 0.9;
            margin-top: 6px;
            font-weight: 400;
        }}
        
        /* Content cards */
        .content-card {{
            background: {Config.CARD_BG};
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
            margin-bottom: 20px;
            border: 1px solid rgba(0, 0, 0, 0.04);
        }}
        
        .content-card h4 {{
            color: {Config.PRIMARY};
            font-weight: 600;
            margin: 0 0 16px 0;
            font-size: 18px;
        }}
        
        /* Number plate display */
        .numberplate {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border: 3px solid {Config.PRIMARY};
            border-radius: 10px;
            padding: 14px 28px;
            font-family: 'Space Mono', monospace;
            font-size: 32px;
            font-weight: 700;
            color: {Config.PRIMARY};
            text-align: center;
            margin: 0 auto 28px;
            max-width: 280px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            letter-spacing: 2px;
        }}
        
        /* Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, {Config.ACCENT} 0%, {Config.ACCENT_HOVER} 100%);
            color: white;
            font-weight: 600;
            border-radius: 10px;
            border: none;
            padding: 0.6rem 1.2rem;
            font-size: 15px;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(0, 180, 216, 0.3);
        }}
        
        .stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(0, 180, 216, 0.4);
        }}
        
        .stButton > button:active {{
            transform: translateY(0);
        }}
        
        .stButton > button:disabled {{
            background: #d1d5db;
            box-shadow: none;
            color: #9ca3af;
        }}
        
        /* Status badges */
        .badge {{
            padding: 5px 12px;
            border-radius: 20px;
            color: white;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
            margin: 2px 4px 2px 0;
            letter-spacing: 0.3px;
        }}
        
        .badge-success {{
            background: linear-gradient(135deg, {Config.SUCCESS} 0%, #05c793 100%);
        }}
        
        .badge-warning {{
            background: linear-gradient(135deg, {Config.WARNING} 0%, #f5c842 100%);
            color: {Config.TEXT_PRIMARY};
        }}
        
        .badge-error {{
            background: linear-gradient(135deg, {Config.ERROR} 0%, #dc2f5a 100%);
        }}
        
        /* Hero section */
        .hero {{
            background: linear-gradient(135deg, {Config.PRIMARY} 0%, {Config.ACCENT} 100%);
            padding: 48px 32px;
            border-radius: 20px;
            margin-bottom: 36px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        
        .hero::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 100%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
            pointer-events: none;
        }}
        
        .hero h1 {{
            color: white;
            font-size: 38px;
            font-weight: 700;
            margin: 0 0 12px 0;
            position: relative;
        }}
        
        .hero p {{
            color: rgba(255, 255, 255, 0.95);
            font-size: 18px;
            margin: 0 0 32px 0;
            font-weight: 400;
        }}
        
        /* Stats row */
        .stats-row {{
            display: flex;
            justify-content: center;
            gap: 48px;
            flex-wrap: wrap;
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-value {{
            font-family: 'Space Mono', monospace;
            font-size: 36px;
            font-weight: 700;
            color: white;
        }}
        
        .stat-label {{
            font-size: 13px;
            color: rgba(255, 255, 255, 0.85);
            margin-top: 4px;
        }}
        
        /* Feature cards */
        .feature-card {{
            text-align: center;
            padding: 24px 16px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }}
        
        .feature-title {{
            font-weight: 600;
            color: {Config.PRIMARY};
            margin-bottom: 8px;
            font-size: 16px;
        }}
        
        .feature-desc {{
            font-size: 14px;
            color: {Config.TEXT_MUTED};
            line-height: 1.5;
        }}
        
        /* Valuation highlight */
        .valuation-box {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            padding: 20px;
            border-radius: 12px;
            border-left: 5px solid {Config.WARNING};
            margin: 20px 0;
        }}
        
        .valuation-label {{
            font-size: 14px;
            color: {Config.TEXT_MUTED};
            margin-bottom: 4px;
        }}
        
        .valuation-value {{
            font-family: 'Space Mono', monospace;
            font-size: 42px;
            font-weight: 700;
            color: {Config.PRIMARY};
        }}
        
        .valuation-note {{
            font-size: 13px;
            color: {Config.TEXT_MUTED};
            margin-top: 8px;
        }}
        
        /* Deal accelerator */
        .bonus-item {{
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            padding: 14px 18px;
            border-radius: 10px;
            border-left: 4px solid {Config.SUCCESS};
            margin: 8px 0;
        }}
        
        .bonus-label {{
            font-weight: 600;
            color: {Config.PRIMARY};
            font-size: 14px;
        }}
        
        .bonus-value {{
            color: {Config.SUCCESS};
            font-weight: 700;
            font-size: 16px;
        }}
        
        /* Network comparison */
        .network-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f1f5f9;
        }}
        
        .network-row:last-child {{
            border-bottom: none;
        }}
        
        .network-location {{
            font-weight: 500;
            color: {Config.TEXT_PRIMARY};
        }}
        
        .network-best {{
            background: {Config.SUCCESS};
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 8px;
        }}
        
        .network-price {{
            font-family: 'Space Mono', monospace;
            font-weight: 700;
            color: {Config.PRIMARY};
        }}
        
        .network-distance {{
            color: {Config.TEXT_MUTED};
            font-size: 13px;
        }}
        
        /* Trust indicators */
        .trust-section {{
            background: white;
            padding: 28px;
            border-radius: 16px;
            text-align: center;
            margin-top: 48px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
        }}
        
        .trust-label {{
            color: {Config.TEXT_MUTED};
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 600;
            margin-bottom: 16px;
        }}
        
        .trust-items {{
            display: flex;
            justify-content: center;
            gap: 36px;
            flex-wrap: wrap;
        }}
        
        .trust-item {{
            color: {Config.PRIMARY};
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        .trust-check {{
            color: {Config.SUCCESS};
            font-weight: 700;
        }}
        
        /* Input styling */
        .stTextInput input {{
            font-size: 16px;
            padding: 14px 16px;
            border-radius: 10px;
            border: 2px solid #e2e8f0;
            transition: border-color 0.2s ease;
        }}
        
        .stTextInput input:focus {{
            border-color: {Config.ACCENT};
            box-shadow: 0 0 0 3px rgba(0, 180, 216, 0.1);
        }}
        
        .stTextInput input::placeholder {{
            color: #9ca3af;
        }}
        
        /* Upgrade option cards */
        .upgrade-card {{
            background: #f8fafc;
            padding: 18px;
            border-radius: 10px;
            margin: 14px 0;
            border-left: 4px solid {Config.PRIMARY};
            transition: transform 0.2s ease;
        }}
        
        .upgrade-card:hover {{
            transform: translateX(4px);
        }}
        
        .upgrade-title {{
            font-size: 17px;
            font-weight: 600;
            color: {Config.PRIMARY};
            margin-bottom: 8px;
        }}
        
        .upgrade-details {{
            font-size: 14px;
            color: {Config.TEXT_MUTED};
        }}
        
        .upgrade-coverage {{
            font-size: 13px;
            color: {Config.ACCENT};
            margin-top: 8px;
            font-weight: 500;
        }}
        
        /* Hide empty elements */
        .element-container:has(> .stMarkdown > div:empty) {{
            display: none !important;
        }}
        </style>
        """


# ============================================================================
# UI COMPONENTS
# ============================================================================

class Components:
    """Reusable UI components"""
    
    @staticmethod
    def header():
        """Render application header"""
        st.markdown(f"""
        <div class="header-card">
            <div class="header-title">{Config.APP_NAME}</div>
            <div class="header-tagline">{Config.APP_TAGLINE}</div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def numberplate(reg: str):
        """Render number plate display"""
        st.markdown(f'<div class="numberplate">{reg}</div>', unsafe_allow_html=True)
    
    @staticmethod
    def status_badges(history_flags: HistoryFlags, open_recall_count: int):
        """Render status badges"""
        badges = []
        
        if history_flags.write_off:
            badges.append('<span class="badge badge-error">Write-off</span>')
        if history_flags.theft:
            badges.append('<span class="badge badge-error">Theft Record</span>')
        if history_flags.mileage_anomaly:
            badges.append('<span class="badge badge-warning">Mileage Anomaly</span>')
        if open_recall_count > 0:
            badges.append(f'<span class="badge badge-warning">{open_recall_count} Open Recall(s)</span>')
        
        if not badges:
            badges.append('<span class="badge badge-success">No Issues Found</span>')
        
        st.markdown(f'<p><strong>Status:</strong> {" ".join(badges)}</p>', unsafe_allow_html=True)
    
    @staticmethod
    def valuation_display(value: int, condition: str, total_with_bonuses: int):
        """Render valuation display"""
        st.markdown(f"""
        <div class="valuation-box">
            <div class="valuation-label">Total Offer Value</div>
            <div class="valuation-value">£{total_with_bonuses:,}</div>
            <div class="valuation-note">
                Base: £{value:,} ({condition}) + bonuses | 
                Valid for {Config.VALUATION_VALIDITY_HOURS} hours
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def bonus_item(label: str, value: int, description: str):
        """Render a bonus item"""
        st.markdown(f"""
        <div class="bonus-item">
            <span class="bonus-label">{label}:</span>
            <span class="bonus-value"> +£{value:,}</span>
            <div style="font-size: 13px; color: #6b7280; margin-top: 4px;">{description}</div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def network_comparison(offers: list[dict], trade_in_value: int):
        """Render network price comparison"""
        for offer in offers:
            best_badge = '<span class="network-best">BEST OFFER</span>' if offer.get('is_best') else ''
            st.markdown(f"""
            <div class="network-row">
                <div>
                    <span class="network-location">{offer['location']}</span>
                    {best_badge}
                </div>
                <div>
                    <span class="network-price">£{offer['value']:,}</span>
                    <span class="network-distance"> · {offer['distance']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def upgrade_option(model: str, year: int, price: int, monthly: int, trade_in_value: int):
        """Render upgrade option card"""
        deposit_needed = max(0, price - trade_in_value)
        coverage_pct = min(100, int((trade_in_value / price) * 100))
        
        st.markdown(f"""
        <div class="upgrade-card">
            <div class="upgrade-title">{model} ({year})</div>
            <div class="upgrade-details">
                <strong>£{price:,}</strong> · 
                £{deposit_needed:,} additional · 
                From <strong>£{monthly}/month</strong>
            </div>
            <div class="upgrade-coverage">
                Your trade-in covers {coverage_pct}% of the price
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def trust_indicators():
        """Render trust indicators"""
        st.markdown(f"""
        <div class="trust-section">
            <div class="trust-label">Trusted by Sytner Staff Nationwide</div>
            <div class="trust-items">
                <div class="trust-item">
                    <span class="trust-check">✓</span> Full DVLA Integration
                </div>
                <div class="trust-item">
                    <span class="trust-check">✓</span> Real-time MOT Data
                </div>
                <div class="trust-item">
                    <span class="trust-check">✓</span> Secure & Compliant
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def feature_cards():
        """Render feature highlight cards"""
        col1, col2, col3 = st.columns(3)
        
        features = [
            ("⚡ Instant Check", "Full vehicle history in seconds"),
            ("💰 Best Offers", "Compare across network"),
            ("🚗 Same Day", "Complete deal today"),
        ]
        
        for col, (title, desc) in zip([col1, col2, col3], features):
            with col:
                st.markdown(f"""
                <div class="feature-card">
                    <div class="feature-title">{title}</div>
                    <div class="feature-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)


# ============================================================================
# BOOKING FORMS
# ============================================================================

class BookingForms:
    """Booking form components"""
    
    @staticmethod
    def recall_booking(recall: Recall, recall_key: str):
        """Render recall repair booking form"""
        st.markdown("##### Book Recall Repair")
        
        garage = st.selectbox("Select Sytner Garage", Config.GARAGES, key=f"garage_{recall_key}")
        
        col_a, col_b = st.columns(2)
        with col_a:
            min_date = datetime.date.today() + datetime.timedelta(days=Config.BOOKING_ADVANCE_DAYS_MIN)
            max_date = datetime.date.today() + datetime.timedelta(days=Config.BOOKING_ADVANCE_DAYS_MAX)
            booking_date = st.date_input(
                "Preferred Date",
                min_value=min_date,
                max_value=max_date,
                value=min_date,
                key=f"date_{recall_key}"
            )
        with col_b:
            time_slot = st.selectbox("Time Slot", Config.TIME_SLOTS, key=f"time_{recall_key}")
        
        col_c, col_d = st.columns(2)
        with col_c:
            customer_name = st.text_input("Customer Name *", key=f"name_{recall_key}", placeholder="John Smith")
        with col_d:
            customer_phone = st.text_input("Phone Number *", key=f"phone_{recall_key}", placeholder="07700 900000")
        
        customer_email = st.text_input("Email (optional)", key=f"email_{recall_key}", placeholder="customer@example.com")
        
        col_x, col_y = st.columns(2)
        with col_x:
            if st.button("✅ Confirm Booking", key=f"confirm_{recall_key}", use_container_width=True):
                if not customer_name or not Validator.is_valid_phone(customer_phone):
                    st.error("⚠️ Please fill in all required fields with valid information")
                else:
                    booking_ref = f"RCL-{recall.id}-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
                    st.success(f"""
                    ✅ **Booking Confirmed!**
                    
                    **Reference:** {booking_ref}  
                    **Garage:** {garage}  
                    **Date & Time:** {booking_date.strftime('%d %B %Y')} at {time_slot}  
                    **Customer:** {customer_name} | {customer_phone}
                    """)
                    SessionState.close_booking_form(recall_key)
                    st.balloons()
        
        with col_y:
            if st.button("Cancel", key=f"cancel_{recall_key}", use_container_width=True):
                SessionState.close_booking_form(recall_key)
                st.rerun()
    
    @staticmethod
    def inspection_booking(vehicle: Vehicle, offer_value: int):
        """Render inspection booking form"""
        st.markdown("---")
        st.markdown("### 📅 Book Instant Inspection")
        
        col1, col2 = st.columns(2)
        with col1:
            today = datetime.date.today()
            inspection_date = st.date_input(
                "Inspection Date",
                min_value=today,
                max_value=today + datetime.timedelta(days=Config.INSPECTION_ADVANCE_DAYS_MAX),
                value=today,
                key="inspection_date"
            )
        with col2:
            time_slot = st.selectbox("Available Slots", Config.INSPECTION_SLOTS, key="inspection_time")
        
        col3, col4 = st.columns(2)
        with col3:
            customer_name = st.text_input("Your Name *", placeholder="John Smith", key="inspection_name")
        with col4:
            customer_phone = st.text_input("Phone *", placeholder="07700 900000", key="inspection_phone")
        
        customer_email = st.text_input("Email *", placeholder="customer@example.com", key="inspection_email")
        
        st.info("""
        **What happens next:**
        - Inspection takes 15-20 minutes
        - Instant offer confirmation
        - Payment within 24 hours (or immediate bank transfer)
        - All paperwork handled on-site
        """)
        
        col_x, col_y = st.columns(2)
        with col_x:
            if st.button("✅ Confirm Inspection", key="confirm_inspection", use_container_width=True, type="primary"):
                if customer_name and Validator.is_valid_phone(customer_phone) and customer_email:
                    booking_ref = f"INS-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
                    st.success(f"""
                    ✅ **Inspection Booked!**
                    
                    **Reference:** {booking_ref}  
                    **Vehicle:** {vehicle.display_name} ({vehicle.reg})  
                    **Offer Value:** £{offer_value:,}  
                    **Date:** {inspection_date.strftime('%d %B %Y')} at {time_slot}  
                    
                    📧 Confirmation sent to {customer_email}
                    """)
                    st.session_state.show_inspection_booking = False
                    st.balloons()
                else:
                    st.error("⚠️ Please fill in all required fields with valid information")
        
        with col_y:
            if st.button("Cancel", key="cancel_inspection", use_container_width=True):
                st.session_state.show_inspection_booking = False
                st.rerun()


# ============================================================================
# PAGE SECTIONS
# ============================================================================

class Sections:
    """Page section renderers"""
    
    @staticmethod
    def vehicle_summary(vehicle: Vehicle, mot_tax: MOTAndTax, history_flags: HistoryFlags, open_recalls: int):
        """Render vehicle summary card"""
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("<h4>📋 Vehicle Summary</h4>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Make & Model:** {vehicle.display_name}")
            st.markdown(f"**Year:** {vehicle.year}")
            st.markdown(f"**Mileage:** {vehicle.mileage:,} miles")
        with col2:
            st.markdown(f"**VIN:** {vehicle.vin}")
            st.markdown(f"**Next MOT:** {mot_tax.mot_next_due}")
            st.markdown(f"**Tax Expiry:** {mot_tax.tax_expiry}")
        
        st.markdown("---")
        Components.status_badges(history_flags, open_recalls)
        
        if history_flags.note:
            st.warning(f"ℹ️ {history_flags.note}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def mot_history(mot_history: list[MOTEntry]):
        """Render MOT history expander"""
        with st.expander("📜 MOT History"):
            if mot_history:
                for entry in mot_history:
                    icon = "✅" if entry.is_pass else "⚠️"
                    st.markdown(f"{icon} **{entry.date}**: {entry.result} — {entry.mileage:,} miles")
            else:
                st.info("No MOT history available")
    
    @staticmethod
    def recalls(recalls: list[Recall]):
        """Render recalls section"""
        open_count = sum(1 for r in recalls if r.is_open)
        
        with st.expander(f"🔔 Recalls ({len(recalls)} total, {open_count} open)"):
            if not recalls:
                st.success("✅ No recalls found for this vehicle")
                return
            
            for idx, recall in enumerate(recalls):
                recall_key = f"recall_{recall.id}"
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    status = "⚠️ **OPEN**" if recall.is_open else "✅ Closed"
                    st.markdown(f"**{recall.summary}**")
                    st.caption(f"ID: `{recall.id}` — Status: {status}")
                
                with col2:
                    if recall.is_open:
                        if st.button("📅 Book", key=f"book_btn_{recall_key}"):
                            SessionState.toggle_booking_form(recall_key)
                            st.rerun()
                
                if recall.is_open and st.session_state.booking_forms.get(recall_key):
                    BookingForms.recall_booking(recall, recall_key)
                
                if idx < len(recalls) - 1:
                    st.markdown("---")
    
    @staticmethod
    def valuation(vehicle: Vehicle):
        """Render valuation section"""
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("<h4>💰 Instant Trade-In Valuation</h4>", unsafe_allow_html=True)
        
        condition_str = st.radio(
            "Vehicle Condition",
            [c.value for c in VehicleCondition],
            index=1,
            horizontal=True,
            help="Select the overall condition of the vehicle"
        )
        condition = VehicleCondition(condition_str)
        
        base_value = vehicle_service.estimate_value(vehicle, condition)
        total_value = base_value + Config.STOCK_PRIORITY_BONUS + Config.SAME_DAY_BONUS
        
        Components.valuation_display(base_value, condition.value.capitalize(), total_value)
        
        # Deal accelerator
        st.markdown("---")
        st.markdown("#### ⚡ Deal Accelerator")
        
        col1, col2 = st.columns(2)
        with col1:
            Components.bonus_item("Stock Priority", Config.STOCK_PRIORITY_BONUS, "We need this model!")
        with col2:
            Components.bonus_item("Same-Day", Config.SAME_DAY_BONUS, "Complete today")
        
        # Network comparison
        st.markdown("---")
        st.markdown("#### 🏢 Best Offers Across Network")
        
        network_offers = [
            {"location": "Sytner BMW Birmingham", "value": total_value, "distance": "Current", "is_best": True},
            {"location": "Sytner BMW Solihull", "value": total_value - 300, "distance": "8 miles", "is_best": False},
            {"location": "Sytner BMW Coventry", "value": total_value - 500, "distance": "15 miles", "is_best": False},
        ]
        Components.network_comparison(network_offers, total_value)
        
        # Assigned buyer
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Assigned Vehicle Buyer:** John Smith")
            st.caption("📞 01234 567890 | 📧 john.smith@sytner.co.uk")
        with col2:
            if st.button("📅 Book Inspection", key="book_inspection", use_container_width=True, type="primary"):
                st.session_state.show_inspection_booking = True
                st.rerun()
        
        if st.session_state.get("show_inspection_booking"):
            BookingForms.inspection_booking(vehicle, total_value)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def upgrade_options(vehicle: Vehicle):
        """Render upgrade options"""
        st.markdown("#### 🚗 What Could You Drive Away In?")
        st.markdown("*Based on your trade-in value + typical finance options*")
        
        trade_in_value = vehicle_service.estimate_value(vehicle, VehicleCondition.GOOD)
        
        upgrades = [
            ("BMW 5 Series 530e M Sport", 2023, 45000, 520),
            ("BMW X3 xDrive30e", 2024, 52000, 580),
            ("BMW 4 Series 420i Coupe", 2023, 38000, 420),
        ]
        
        for model, year, price, monthly in upgrades:
            Components.upgrade_option(model, year, price, monthly, trade_in_value)
        
        st.info("💬 Speak to our sales team about part-exchange deals and finance options")
    
    @staticmethod
    def additional_details(vehicle: Vehicle, mot_tax: MOTAndTax, history_flags: HistoryFlags, open_recalls: int):
        """Render additional details expander"""
        with st.expander("🔍 View All Details"):
            tab1, tab2, tab3, tab4 = st.tabs(["Specifications", "History", "Alerts", "Upgrades"])
            
            with tab1:
                st.markdown(f"""
                - **Registration:** {vehicle.reg}
                - **Make & Model:** {vehicle.display_name}
                - **Year:** {vehicle.year}
                - **VIN:** {vehicle.vin}
                - **Mileage:** {vehicle.mileage:,} miles
                - **Next MOT:** {mot_tax.mot_next_due}
                - **Tax Expiry:** {mot_tax.tax_expiry}
                """)
            
            with tab2:
                st.markdown("**MOT Test History:**")
                for entry in mot_tax.mot_history:
                    st.markdown(f"- {entry.date}: **{entry.result}** at {entry.mileage:,} miles")
                if history_flags.note:
                    st.warning(f"⚠️ {history_flags.note}")
            
            with tab3:
                total_alerts = history_flags.issue_count + (1 if open_recalls > 0 else 0)
                if total_alerts > 0:
                    st.warning(f"⚠️ {total_alerts} alert(s) found")
                    if history_flags.write_off:
                        st.error("🚨 Vehicle has a write-off record")
                    if history_flags.theft:
                        st.error("🚨 Vehicle has a theft record")
                    if history_flags.mileage_anomaly:
                        st.warning("⚠️ Mileage discrepancy detected")
                    if open_recalls > 0:
                        st.warning(f"⚠️ {open_recalls} open safety recall(s)")
                else:
                    st.success("✅ No alerts found")
            
            with tab4:
                Sections.upgrade_options(vehicle)


# ============================================================================
# PAGES
# ============================================================================

class Pages:
    """Page renderers"""
    
    @staticmethod
    def input_page():
        """Render the vehicle input page"""
        # Hero section
        st.markdown(f"""
        <div class="hero">
            <h1>Instant Trade-In Valuation</h1>
            <p>Get competitive offers in seconds · Complete deals in minutes</p>
            <div class="stats-row">
                <div class="stat-item">
                    <div class="stat-value">30 min</div>
                    <div class="stat-label">Average completion</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">15+</div>
                    <div class="stat-label">Network locations</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">£500+</div>
                    <div class="stat-label">Bonus opportunities</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature cards
        Components.feature_cards()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Input section
        st.markdown(f"""
        <div style="text-align: center; margin: 32px 0 24px;">
            <h2 style="color: {Config.PRIMARY}; margin: 0 0 8px;">Get Started</h2>
            <p style="color: {Config.TEXT_MUTED};">Enter registration or scan the number plate</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Input method selector
        col_spacer1, col_radio, col_spacer2 = st.columns([1, 2, 1])
        with col_radio:
            input_method = st.radio(
                "Input method",
                ["Enter Registration", "Scan Plate"],
                horizontal=True,
                label_visibility="collapsed"
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if input_method == "Enter Registration":
            manual_reg = st.text_input(
                "Registration",
                placeholder="e.g. KT68XYZ or WBA8BFAKEVIN12345",
                label_visibility="collapsed"
            )
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔍 Look Up Vehicle", disabled=not manual_reg, use_container_width=True, type="primary"):
                    if Validator.is_valid_registration(manual_reg):
                        SessionState.set_vehicle(Validator.clean_registration(manual_reg))
                        st.rerun()
                    else:
                        st.error("Please enter a valid registration (5-10 alphanumeric characters)")
            
            st.markdown(f"""
            <div style="text-align: center; margin-top: 16px;">
                <p style="color: {Config.TEXT_MUTED}; font-size: 13px;">
                    <strong>Try:</strong> KT68XYZ · AB12CDE · WBA8B12345
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        else:  # Scan Plate
            st.info("📸 Position the plate clearly in frame with good lighting")
            
            image = st.camera_input("Scan plate", label_visibility="collapsed")
            
            if image:
                try:
                    extracted_reg = vehicle_service.extract_plate_from_image(image)
                    if extracted_reg and Validator.is_valid_registration(extracted_reg):
                        SessionState.set_vehicle(extracted_reg, image)
                        st.rerun()
                    else:
                        st.error("Could not read plate. Please try again or enter manually.")
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")
        
        # Trust indicators
        Components.trust_indicators()
    
    @staticmethod
    def summary_page():
        """Render the vehicle summary page"""
        reg = st.session_state.reg
        image = st.session_state.image
        
        # Show captured image if available
        if image:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(ImageOps.exif_transpose(Image.open(image)), use_container_width=True)
        
        # Number plate display
        Components.numberplate(reg)
        
        # Fetch data
        try:
            with st.spinner("Fetching vehicle information..."):
                vehicle = vehicle_service.lookup_vehicle(reg)
                mot_tax = vehicle_service.lookup_mot_and_tax(reg)
                recalls = vehicle_service.lookup_recalls(reg)
                history_flags = vehicle_service.get_history_flags(reg)
        except Exception as e:
            st.error(f"⚠️ Error fetching vehicle data: {str(e)}")
            st.stop()
        
        open_recalls = sum(1 for r in recalls if r.is_open)
        
        # Render sections
        Sections.vehicle_summary(vehicle, mot_tax, history_flags, open_recalls)
        Sections.mot_history(mot_tax.mot_history)
        Sections.recalls(recalls)
        
        # Insurance quote (simplified)
        with st.expander("🛡️ Insurance Quote"):
            st.info("Insurance quotes available through partner aggregators")
            if st.button("Get Sample Quote", key="insurance_quote"):
                st.success("""
                **Sample Quote:** £320/year (Third Party, Fire & Theft)  
                Excess: £250 | No Claims: Year 1 | Mileage: 10,000/year
                """)
        
        Sections.valuation(vehicle)
        Sections.additional_details(vehicle, mot_tax, history_flags, open_recalls)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Application entry point"""
    st.set_page_config(
        page_title=Config.APP_NAME,
        page_icon="⚡",
        layout="centered"
    )
    
    # Initialize
    SessionState.initialize()
    st.markdown(Styles.get_css(), unsafe_allow_html=True)
    
    # Header
    Components.header()
    
    # Reset button (only on summary page)
    if st.session_state.show_summary:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⚡ New Vehicle Lookup", use_container_width=True):
                SessionState.reset()
                st.rerun()
    
    # Route to appropriate page
    if st.session_state.show_summary and st.session_state.reg:
        Pages.summary_page()
    else:
        Pages.input_page()


if __name__ == "__main__":
    main()
