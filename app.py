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
import random
import time
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
    "Sytner BMW Cardiff - Penarth Road",
    "Sytner BMW Chigwell - Langston Road",
    "Sytner BMW Coventry - Holyhead Road",
    "Sytner BMW Harold Wood - Colchester Road",
    "Sytner BMW High Wycombe - London Road",
    "Sytner BMW Leicester - Meridian East",
    "Sytner BMW Luton - Dunstable Road",
    "Sytner BMW Maidenhead - Bath Road",
    "Sytner BMW Newport - Usk Way",
    "Sytner BMW Nottingham - Lenton Lane",
    "Sytner BMW Oldbury - Wolverhampton Road",
    "Sytner BMW Sheffield - Brightside Way",
    "Sytner BMW Shrewsbury - Battlefield Road",
    "Sytner BMW Solihull - Highlands Road",
    "Sytner BMW Stevenage - Gunnels Wood Road",
    "Sytner BMW Sunningdale - London Road",
    "Sytner BMW Swansea - Carmarthen Road",
    "Sytner BMW Tamworth - Winchester Road",
    "Sytner BMW Tring - Cow Roast",
    "Sytner BMW Warwick - Fusiliers Way",
    "Sytner BMW Wolverhampton - Lever Street",
    "Sytner BMW Worcester - Wainwright Road",
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


class VehicleType(Enum):
    """Vehicle body type classification"""
    SPORTS = "Sports Car"
    CONVERTIBLE = "Convertible"
    SUV = "SUV"
    CROSSOVER = "Crossover"
    SALOON = "Saloon"
    ESTATE = "Estate"
    HATCHBACK = "Hatchback"
    COUPE = "Coupe"
    MPV = "MPV"
    PICKUP = "Pickup"
    
    @property
    def icon(self) -> str:
        icons = {
            VehicleType.SPORTS: "🏎️",
            VehicleType.CONVERTIBLE: "🚗",
            VehicleType.SUV: "🚙",
            VehicleType.CROSSOVER: "🚙",
            VehicleType.SALOON: "🚘",
            VehicleType.ESTATE: "🚐",
            VehicleType.HATCHBACK: "🚗",
            VehicleType.COUPE: "🚘",
            VehicleType.MPV: "🚐",
            VehicleType.PICKUP: "🛻",
        }
        return icons.get(self, "🚗")


class Season(Enum):
    """Seasons for demand forecasting"""
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"
    
    @classmethod
    def current(cls) -> "Season":
        month = datetime.date.today().month
        if month in (3, 4, 5):
            return cls.SPRING
        elif month in (6, 7, 8):
            return cls.SUMMER
        elif month in (9, 10, 11):
            return cls.AUTUMN
        else:
            return cls.WINTER
    
    @property
    def display_name(self) -> str:
        return self.value.capitalize()
    
    @property
    def icon(self) -> str:
        icons = {
            Season.SPRING: "🌸",
            Season.SUMMER: "☀️",
            Season.AUTUMN: "🍂",
            Season.WINTER: "❄️",
        }
        return icons[self]


class DemandLevel(Enum):
    """Demand level indicators"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"
    
    @property
    def display_name(self) -> str:
        return self.value.replace("_", " ").title()
    
    @property
    def color(self) -> str:
        colors = {
            DemandLevel.VERY_HIGH: "#06d6a0",
            DemandLevel.HIGH: "#4ade80",
            DemandLevel.MODERATE: "#ffd166",
            DemandLevel.LOW: "#fb923c",
            DemandLevel.VERY_LOW: "#ef476f",
        }
        return colors[self]
    
    @property
    def bonus_multiplier(self) -> float:
        multipliers = {
            DemandLevel.VERY_HIGH: 1.15,
            DemandLevel.HIGH: 1.08,
            DemandLevel.MODERATE: 1.0,
            DemandLevel.LOW: 0.95,
            DemandLevel.VERY_LOW: 0.90,
        }
        return multipliers[self]


@dataclass
class RegionalDemand:
    """Demand data for a specific region/location"""
    location: str
    demand_level: DemandLevel
    demand_score: int  # 0-100
    days_to_sell: int  # Average days to sell
    stock_level: int  # Current stock count
    buyers_waiting: int  # Number of interested buyers
    distance_miles: float
    
    @property
    def is_hotspot(self) -> bool:
        return self.demand_level in (DemandLevel.VERY_HIGH, DemandLevel.HIGH)


@dataclass
class DemandForecast:
    """Complete demand forecast for a vehicle"""
    vehicle_type: VehicleType
    current_season: Season
    national_demand: DemandLevel
    seasonal_trend: str  # "rising", "falling", "stable"
    trend_percentage: int  # e.g., +15% or -10%
    regional_demands: list[RegionalDemand]
    best_region: Optional[RegionalDemand] = None
    demand_bonus: int = 0
    
    @property
    def hotspot_count(self) -> int:
        return sum(1 for r in self.regional_demands if r.is_hotspot)


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
    
    @abstractmethod
    def get_vehicle_type(self, vehicle: Vehicle) -> VehicleType:
        pass
    
    @abstractmethod
    def get_demand_forecast(self, vehicle: Vehicle) -> DemandForecast:
        pass
    
    @abstractmethod
    def ping_network(self, vehicle: Vehicle, forecast: DemandForecast) -> dict:
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
    
    def get_vehicle_type(self, vehicle: Vehicle) -> VehicleType:
        """Determine vehicle type from make/model"""
        model_lower = vehicle.model.lower()
        
        # BMW model type mapping
        type_mapping = {
            "x1": VehicleType.CROSSOVER,
            "x2": VehicleType.CROSSOVER,
            "x3": VehicleType.SUV,
            "x4": VehicleType.SUV,
            "x5": VehicleType.SUV,
            "x6": VehicleType.SUV,
            "x7": VehicleType.SUV,
            "z4": VehicleType.CONVERTIBLE,
            "m2": VehicleType.COUPE,
            "m3": VehicleType.SPORTS,
            "m4": VehicleType.SPORTS,
            "m5": VehicleType.SPORTS,
            "m8": VehicleType.SPORTS,
            "2 series": VehicleType.COUPE,
            "3 series": VehicleType.SALOON,
            "4 series": VehicleType.COUPE,
            "5 series": VehicleType.SALOON,
            "7 series": VehicleType.SALOON,
            "8 series": VehicleType.COUPE,
            "1 series": VehicleType.HATCHBACK,
            "touring": VehicleType.ESTATE,
            "gran coupe": VehicleType.COUPE,
            "convertible": VehicleType.CONVERTIBLE,
        }
        
        for key, vtype in type_mapping.items():
            if key in model_lower:
                return vtype
        
        return VehicleType.SALOON  # Default
    
    def get_demand_forecast(self, vehicle: Vehicle) -> DemandForecast:
        """Generate demand forecast based on vehicle type and season"""
        vehicle_type = self.get_vehicle_type(vehicle)
        current_season = Season.current()
        
        # Seasonal demand patterns
        seasonal_demand = {
            Season.SUMMER: {
                VehicleType.SPORTS: DemandLevel.VERY_HIGH,
                VehicleType.CONVERTIBLE: DemandLevel.VERY_HIGH,
                VehicleType.COUPE: DemandLevel.HIGH,
                VehicleType.SUV: DemandLevel.MODERATE,
                VehicleType.CROSSOVER: DemandLevel.MODERATE,
                VehicleType.SALOON: DemandLevel.MODERATE,
                VehicleType.HATCHBACK: DemandLevel.MODERATE,
                VehicleType.ESTATE: DemandLevel.LOW,
                VehicleType.MPV: DemandLevel.LOW,
                VehicleType.PICKUP: DemandLevel.MODERATE,
            },
            Season.WINTER: {
                VehicleType.SUV: DemandLevel.VERY_HIGH,
                VehicleType.CROSSOVER: DemandLevel.VERY_HIGH,
                VehicleType.PICKUP: DemandLevel.HIGH,
                VehicleType.ESTATE: DemandLevel.HIGH,
                VehicleType.SALOON: DemandLevel.MODERATE,
                VehicleType.HATCHBACK: DemandLevel.MODERATE,
                VehicleType.MPV: DemandLevel.MODERATE,
                VehicleType.SPORTS: DemandLevel.LOW,
                VehicleType.CONVERTIBLE: DemandLevel.VERY_LOW,
                VehicleType.COUPE: DemandLevel.LOW,
            },
            Season.SPRING: {
                VehicleType.CONVERTIBLE: DemandLevel.HIGH,
                VehicleType.SPORTS: DemandLevel.HIGH,
                VehicleType.COUPE: DemandLevel.MODERATE,
                VehicleType.SUV: DemandLevel.MODERATE,
                VehicleType.CROSSOVER: DemandLevel.MODERATE,
                VehicleType.SALOON: DemandLevel.MODERATE,
                VehicleType.HATCHBACK: DemandLevel.HIGH,
                VehicleType.ESTATE: DemandLevel.MODERATE,
                VehicleType.MPV: DemandLevel.MODERATE,
                VehicleType.PICKUP: DemandLevel.MODERATE,
            },
            Season.AUTUMN: {
                VehicleType.SUV: DemandLevel.HIGH,
                VehicleType.CROSSOVER: DemandLevel.HIGH,
                VehicleType.ESTATE: DemandLevel.HIGH,
                VehicleType.SALOON: DemandLevel.MODERATE,
                VehicleType.HATCHBACK: DemandLevel.MODERATE,
                VehicleType.MPV: DemandLevel.MODERATE,
                VehicleType.SPORTS: DemandLevel.MODERATE,
                VehicleType.CONVERTIBLE: DemandLevel.LOW,
                VehicleType.COUPE: DemandLevel.MODERATE,
                VehicleType.PICKUP: DemandLevel.HIGH,
            },
        }
        
        national_demand = seasonal_demand.get(current_season, {}).get(
            vehicle_type, DemandLevel.MODERATE
        )
        
        # Calculate trend based on upcoming season
        trend_data = self._calculate_trend(vehicle_type, current_season)
        
        # Generate regional demand data
        regional_demands = self._generate_regional_demands(vehicle_type, national_demand)
        
        # Find best region
        best_region = max(regional_demands, key=lambda r: r.demand_score)
        
        # Calculate demand bonus
        demand_bonus = self._calculate_demand_bonus(national_demand, best_region)
        
        return DemandForecast(
            vehicle_type=vehicle_type,
            current_season=current_season,
            national_demand=national_demand,
            seasonal_trend=trend_data["direction"],
            trend_percentage=trend_data["percentage"],
            regional_demands=regional_demands,
            best_region=best_region,
            demand_bonus=demand_bonus,
        )
    
    def _calculate_trend(self, vehicle_type: VehicleType, current_season: Season) -> dict:
        """Calculate demand trend based on upcoming season"""
        # Summer-friendly vehicles trend up in spring, down in autumn
        summer_vehicles = {VehicleType.SPORTS, VehicleType.CONVERTIBLE, VehicleType.COUPE}
        # Winter-friendly vehicles trend up in autumn, down in spring
        winter_vehicles = {VehicleType.SUV, VehicleType.CROSSOVER, VehicleType.PICKUP}
        
        if vehicle_type in summer_vehicles:
            if current_season == Season.SPRING:
                return {"direction": "rising", "percentage": 18}
            elif current_season == Season.SUMMER:
                return {"direction": "stable", "percentage": 2}
            elif current_season == Season.AUTUMN:
                return {"direction": "falling", "percentage": -15}
            else:
                return {"direction": "stable", "percentage": -5}
        elif vehicle_type in winter_vehicles:
            if current_season == Season.AUTUMN:
                return {"direction": "rising", "percentage": 22}
            elif current_season == Season.WINTER:
                return {"direction": "stable", "percentage": 3}
            elif current_season == Season.SPRING:
                return {"direction": "falling", "percentage": -12}
            else:
                return {"direction": "stable", "percentage": -3}
        else:
            return {"direction": "stable", "percentage": 0}
    
    def _generate_regional_demands(
        self, vehicle_type: VehicleType, national_demand: DemandLevel
    ) -> list[RegionalDemand]:
        """Generate regional demand data for all network locations"""
        
        # Regional characteristics affect demand
        regions = [
            {
                "location": "Sytner BMW Birmingham",
                "base_modifier": 0,
                "rural_bonus": False,
                "affluent": True,
                "distance": 0,
            },
            {
                "location": "Sytner BMW Manchester",
                "base_modifier": 5,
                "rural_bonus": False,
                "affluent": True,
                "distance": 85,
            },
            {
                "location": "Sytner BMW London - Park Lane",
                "base_modifier": 10,
                "rural_bonus": False,
                "affluent": True,
                "distance": 120,
            },
            {
                "location": "Sytner BMW Edinburgh",
                "base_modifier": -5,
                "rural_bonus": True,
                "affluent": False,
                "distance": 290,
            },
            {
                "location": "Sytner BMW Leeds",
                "base_modifier": 0,
                "rural_bonus": True,
                "affluent": False,
                "distance": 120,
            },
            {
                "location": "Sytner BMW Bristol",
                "base_modifier": 5,
                "rural_bonus": True,
                "affluent": True,
                "distance": 90,
            },
            {
                "location": "Sytner BMW Newcastle",
                "base_modifier": -10,
                "rural_bonus": True,
                "affluent": False,
                "distance": 200,
            },
            {
                "location": "Sytner BMW Cardiff",
                "base_modifier": -5,
                "rural_bonus": True,
                "affluent": False,
                "distance": 110,
            },
        ]
        
        regional_demands = []
        base_score = {
            DemandLevel.VERY_HIGH: 90,
            DemandLevel.HIGH: 75,
            DemandLevel.MODERATE: 55,
            DemandLevel.LOW: 35,
            DemandLevel.VERY_LOW: 20,
        }[national_demand]
        
        for region in regions:
            # Calculate regional score
            score = base_score + region["base_modifier"]
            
            # Rural areas prefer SUVs/4x4s
            if region["rural_bonus"] and vehicle_type in {
                VehicleType.SUV, VehicleType.CROSSOVER, VehicleType.PICKUP
            }:
                score += 15
            
            # Affluent areas prefer sports/luxury
            if region["affluent"] and vehicle_type in {
                VehicleType.SPORTS, VehicleType.CONVERTIBLE, VehicleType.COUPE
            }:
                score += 12
            
            # Add some randomness
            score += random.randint(-8, 8)
            score = max(10, min(98, score))
            
            # Determine demand level from score
            if score >= 85:
                demand_level = DemandLevel.VERY_HIGH
            elif score >= 70:
                demand_level = DemandLevel.HIGH
            elif score >= 50:
                demand_level = DemandLevel.MODERATE
            elif score >= 30:
                demand_level = DemandLevel.LOW
            else:
                demand_level = DemandLevel.VERY_LOW
            
            # Calculate days to sell (inversely related to demand)
            days_to_sell = max(3, int(60 - (score * 0.5)))
            
            regional_demands.append(RegionalDemand(
                location=region["location"],
                demand_level=demand_level,
                demand_score=score,
                days_to_sell=days_to_sell,
                stock_level=random.randint(0, 5),
                buyers_waiting=random.randint(0, 12) if score > 60 else random.randint(0, 3),
                distance_miles=region["distance"],
            ))
        
        return sorted(regional_demands, key=lambda r: -r.demand_score)
    
    def _calculate_demand_bonus(
        self, national_demand: DemandLevel, best_region: RegionalDemand
    ) -> int:
        """Calculate bonus value based on demand"""
        base_bonus = {
            DemandLevel.VERY_HIGH: 800,
            DemandLevel.HIGH: 500,
            DemandLevel.MODERATE: 200,
            DemandLevel.LOW: 0,
            DemandLevel.VERY_LOW: 0,
        }[national_demand]
        
        # Additional bonus for hotspot regions
        if best_region.demand_score >= 85:
            base_bonus += 300
        elif best_region.demand_score >= 75:
            base_bonus += 150
        
        return base_bonus
    
    def ping_network(self, vehicle: Vehicle, forecast: DemandForecast) -> dict:
        """Simulate pinging the network with vehicle availability"""
        hotspots = [r for r in forecast.regional_demands if r.is_hotspot]
        
        # Simulate network notification
        notifications_sent = len(hotspots)
        interested_buyers = sum(r.buyers_waiting for r in hotspots)
        
        return {
            "success": True,
            "notifications_sent": notifications_sent,
            "locations_pinged": [r.location for r in hotspots],
            "interested_buyers": interested_buyers,
            "best_match": forecast.best_region.location if forecast.best_region else None,
            "estimated_sale_days": forecast.best_region.days_to_sell if forecast.best_region else 30,
            "timestamp": datetime.datetime.now().isoformat(),
        }


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
        "ping_result": None,
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
        
        /* Demand Forecast Styles */
        .demand-card {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 24px;
            border-radius: 16px;
            color: white;
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
        }}
        
        .demand-card::before {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(0, 180, 216, 0.15) 0%, transparent 70%);
            pointer-events: none;
        }}
        
        .demand-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
        }}
        
        .demand-title {{
            font-size: 18px;
            font-weight: 600;
            margin: 0 0 4px 0;
        }}
        
        .demand-subtitle {{
            font-size: 13px;
            opacity: 0.8;
        }}
        
        .demand-level {{
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .demand-meter {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            height: 12px;
            margin: 16px 0;
            overflow: hidden;
        }}
        
        .demand-meter-fill {{
            height: 100%;
            border-radius: 10px;
            transition: width 0.5s ease;
        }}
        
        .demand-stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 20px;
        }}
        
        .demand-stat {{
            text-align: center;
            padding: 12px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }}
        
        .demand-stat-value {{
            font-family: 'Space Mono', monospace;
            font-size: 24px;
            font-weight: 700;
            color: {Config.ACCENT};
        }}
        
        .demand-stat-label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            opacity: 0.7;
            margin-top: 4px;
        }}
        
        .trend-indicator {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 13px;
            font-weight: 600;
        }}
        
        .trend-up {{
            background: rgba(6, 214, 160, 0.2);
            color: #06d6a0;
        }}
        
        .trend-down {{
            background: rgba(239, 71, 111, 0.2);
            color: #ef476f;
        }}
        
        .trend-stable {{
            background: rgba(255, 209, 102, 0.2);
            color: #ffd166;
        }}
        
        /* Regional Hotspot Card */
        .hotspot-card {{
            background: white;
            border-radius: 12px;
            padding: 16px;
            margin: 10px 0;
            border-left: 4px solid;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .hotspot-card:hover {{
            transform: translateX(4px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}
        
        .hotspot-info {{
            flex: 1;
        }}
        
        .hotspot-location {{
            font-weight: 600;
            color: {Config.PRIMARY};
            font-size: 15px;
            margin-bottom: 4px;
        }}
        
        .hotspot-details {{
            font-size: 13px;
            color: {Config.TEXT_MUTED};
        }}
        
        .hotspot-score {{
            text-align: right;
        }}
        
        .hotspot-score-value {{
            font-family: 'Space Mono', monospace;
            font-size: 28px;
            font-weight: 700;
        }}
        
        .hotspot-score-label {{
            font-size: 11px;
            text-transform: uppercase;
            color: {Config.TEXT_MUTED};
        }}
        
        /* Ping Network Button */
        .ping-button {{
            background: linear-gradient(135deg, #06d6a0 0%, #05c793 100%);
            color: white;
            border: none;
            padding: 14px 28px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            width: 100%;
            transition: all 0.2s ease;
            box-shadow: 0 4px 16px rgba(6, 214, 160, 0.3);
        }}
        
        .ping-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(6, 214, 160, 0.4);
        }}
        
        .ping-result {{
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border: 2px solid {Config.SUCCESS};
            border-radius: 12px;
            padding: 20px;
            margin-top: 16px;
        }}
        
        .ping-result-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
        }}
        
        .ping-result-title {{
            font-weight: 600;
            color: {Config.PRIMARY};
            font-size: 16px;
        }}
        
        .ping-result-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }}
        
        .ping-stat {{
            background: white;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .ping-stat-value {{
            font-family: 'Space Mono', monospace;
            font-size: 20px;
            font-weight: 700;
            color: {Config.PRIMARY};
        }}
        
        .ping-stat-label {{
            font-size: 12px;
            color: {Config.TEXT_MUTED};
        }}
        
        /* Season indicator */
        .season-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
            background: rgba(255, 255, 255, 0.1);
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
        st.markdown(f"""<div style="background: linear-gradient(135deg, #0a2f4f 0%, #1a4a6e 100%); color: white; padding: 20px 28px; border-radius: 16px; text-align: center; margin-bottom: 28px; box-shadow: 0 8px 32px rgba(10, 47, 79, 0.25);"><div style="font-family: monospace; font-size: 26px; font-weight: 700; letter-spacing: -0.5px;">{Config.APP_NAME}</div><div style="font-size: 14px; opacity: 0.9; margin-top: 6px;">{Config.APP_TAGLINE}</div></div>""", unsafe_allow_html=True)
    
    @staticmethod
    def numberplate(reg: str):
        """Render number plate display"""
        st.markdown(f"""<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 3px solid #0a2f4f; border-radius: 10px; padding: 14px 28px; font-family: monospace; font-size: 32px; font-weight: 700; color: #0a2f4f; text-align: center; margin: 0 auto 28px; max-width: 280px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); letter-spacing: 2px;">{reg}</div>""", unsafe_allow_html=True)
    
    @staticmethod
    def status_badges(history_flags: HistoryFlags, open_recall_count: int):
        """Render status badges"""
        badges = []
        
        if history_flags.write_off:
            badges.append('<span style="padding: 5px 12px; border-radius: 20px; background: linear-gradient(135deg, #ef476f 0%, #dc2f5a 100%); color: white; font-size: 12px; font-weight: 600; margin-right: 4px;">Write-off</span>')
        if history_flags.theft:
            badges.append('<span style="padding: 5px 12px; border-radius: 20px; background: linear-gradient(135deg, #ef476f 0%, #dc2f5a 100%); color: white; font-size: 12px; font-weight: 600; margin-right: 4px;">Theft Record</span>')
        if history_flags.mileage_anomaly:
            badges.append('<span style="padding: 5px 12px; border-radius: 20px; background: linear-gradient(135deg, #ffd166 0%, #f5c842 100%); color: #1a1a2e; font-size: 12px; font-weight: 600; margin-right: 4px;">Mileage Anomaly</span>')
        if open_recall_count > 0:
            badges.append(f'<span style="padding: 5px 12px; border-radius: 20px; background: linear-gradient(135deg, #ffd166 0%, #f5c842 100%); color: #1a1a2e; font-size: 12px; font-weight: 600; margin-right: 4px;">{open_recall_count} Open Recall(s)</span>')
        
        if not badges:
            badges.append('<span style="padding: 5px 12px; border-radius: 20px; background: linear-gradient(135deg, #06d6a0 0%, #05c793 100%); color: white; font-size: 12px; font-weight: 600;">No Issues Found</span>')
        
        st.markdown(f'<p><strong>Status:</strong> {" ".join(badges)}</p>', unsafe_allow_html=True)
    
    @staticmethod
    def valuation_display(value: int, condition: str, total_with_bonuses: int):
        """Render valuation display"""
        st.markdown(f"""<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); padding: 20px; border-radius: 12px; border-left: 5px solid #ffd166; margin: 20px 0;"><div style="font-size: 14px; color: #6b7280; margin-bottom: 4px;">Total Offer Value</div><div style="font-family: monospace; font-size: 42px; font-weight: 700; color: #0a2f4f;">£{total_with_bonuses:,}</div><div style="font-size: 13px; color: #6b7280; margin-top: 8px;">Base: £{value:,} ({condition}) + bonuses | Valid for {Config.VALUATION_VALIDITY_HOURS} hours</div></div>""", unsafe_allow_html=True)
    
    @staticmethod
    def bonus_item(label: str, value: int, description: str):
        """Render a bonus item"""
        st.markdown(f"""<div style="background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); padding: 14px 18px; border-radius: 10px; border-left: 4px solid #06d6a0; margin: 8px 0;"><span style="font-weight: 600; color: #0a2f4f; font-size: 14px;">{label}:</span><span style="color: #06d6a0; font-weight: 700; font-size: 16px;"> +£{value:,}</span><div style="font-size: 13px; color: #6b7280; margin-top: 4px;">{description}</div></div>""", unsafe_allow_html=True)
    
    @staticmethod
    def network_comparison(offers: list[dict], trade_in_value: int):
        """Render network price comparison"""
        for offer in offers:
            col1, col2 = st.columns([3, 2])
            with col1:
                if offer.get('is_best'):
                    st.markdown(f"**{offer['location']}** <span style='background: #06d6a0; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-left: 8px;'>BEST OFFER</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"**{offer['location']}**")
            with col2:
                st.markdown(f"**£{offer['value']:,}** · {offer['distance']}")
    
    @staticmethod
    def upgrade_option(model: str, year: int, price: int, monthly: int, trade_in_value: int):
        """Render upgrade option card"""
        deposit_needed = max(0, price - trade_in_value)
        coverage_pct = min(100, int((trade_in_value / price) * 100))
        
        st.markdown(f"""<div style="background: #f8fafc; padding: 18px; border-radius: 10px; margin: 14px 0; border-left: 4px solid #0a2f4f;"><div style="font-size: 17px; font-weight: 600; color: #0a2f4f; margin-bottom: 8px;">{model} ({year})</div><div style="font-size: 14px; color: #6b7280;"><strong>£{price:,}</strong> · £{deposit_needed:,} additional · From <strong>£{monthly}/month</strong></div><div style="font-size: 13px; color: #00b4d8; margin-top: 8px; font-weight: 500;">Your trade-in covers {coverage_pct}% of the price</div></div>""", unsafe_allow_html=True)
    
    @staticmethod
    def trust_indicators():
        """Render trust indicators"""
        st.markdown("""<div style="background: white; padding: 28px; border-radius: 16px; text-align: center; margin-top: 48px; box-shadow: 0 2px 12px rgba(0,0,0,0.04);"><div style="color: #6b7280; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; margin-bottom: 16px;">Trusted by Sytner Staff Nationwide</div><div style="display: flex; justify-content: center; gap: 36px; flex-wrap: wrap;"><span style="color: #0a2f4f; font-size: 14px;"><span style="color: #06d6a0; font-weight: 700;">✓</span> Full DVLA Integration</span><span style="color: #0a2f4f; font-size: 14px;"><span style="color: #06d6a0; font-weight: 700;">✓</span> Real-time MOT Data</span><span style="color: #0a2f4f; font-size: 14px;"><span style="color: #06d6a0; font-weight: 700;">✓</span> Secure & Compliant</span></div></div>""", unsafe_allow_html=True)
    
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
                st.markdown(f"""<div style="text-align: center; padding: 24px 16px; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);"><div style="font-weight: 600; color: #0a2f4f; margin-bottom: 8px; font-size: 16px;">{title}</div><div style="font-size: 14px; color: #6b7280; line-height: 1.5;">{desc}</div></div>""", unsafe_allow_html=True)
    
    @staticmethod
    def demand_forecast_card(forecast: DemandForecast, vehicle: Vehicle):
        """Render the main demand forecast card"""
        # Determine trend styling
        if forecast.seasonal_trend == "rising":
            trend_icon = "📈"
            trend_sign = "+"
            trend_bg = "rgba(6, 214, 160, 0.2)"
            trend_color = "#06d6a0"
        elif forecast.seasonal_trend == "falling":
            trend_icon = "📉"
            trend_sign = ""
            trend_bg = "rgba(239, 71, 111, 0.2)"
            trend_color = "#ef476f"
        else:
            trend_icon = "➡️"
            trend_sign = ""
            trend_bg = "rgba(255, 209, 102, 0.2)"
            trend_color = "#ffd166"
        
        demand_color = forecast.national_demand.color
        
        meter_width = {
            DemandLevel.VERY_HIGH: 95,
            DemandLevel.HIGH: 75,
            DemandLevel.MODERATE: 55,
            DemandLevel.LOW: 35,
            DemandLevel.VERY_LOW: 15,
        }[forecast.national_demand]
        
        days_to_sell = forecast.best_region.days_to_sell if forecast.best_region else "—"
        
        # Card container
        st.markdown(f"""<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 24px; border-radius: 16px; color: white; margin-bottom: 20px;">""", unsafe_allow_html=True)
        
        # Header row using columns
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{forecast.vehicle_type.icon} {forecast.vehicle_type.value} Demand Forecast**")
            st.caption(f"{vehicle.display_name} · {vehicle.year}")
        with col2:
            st.markdown(f"<span style='background: rgba(255,255,255,0.15); padding: 6px 12px; border-radius: 20px; font-size: 13px;'>{forecast.current_season.icon} {forecast.current_season.display_name}</span>", unsafe_allow_html=True)
        
        # Demand level and trend badges
        st.markdown(f"""
<span style="display: inline-block; padding: 8px 16px; border-radius: 20px; font-weight: 600; font-size: 14px; text-transform: uppercase; background: {demand_color}; color: white; margin-right: 12px;">{forecast.national_demand.display_name}</span><span style="display: inline-block; padding: 6px 12px; border-radius: 16px; font-size: 13px; font-weight: 600; background: {trend_bg}; color: {trend_color};">{trend_icon} {trend_sign}{forecast.trend_percentage}% this season</span>
""", unsafe_allow_html=True)
        
        # Progress meter
        st.markdown(f"""
<div style="background: rgba(255, 255, 255, 0.1); border-radius: 10px; height: 12px; margin: 16px 0; overflow: hidden;"><div style="height: 100%; border-radius: 10px; width: {meter_width}%; background: linear-gradient(90deg, {demand_color} 0%, #00b4d8 100%);"></div></div>
""", unsafe_allow_html=True)
        
        # Stats row using columns
        stat1, stat2, stat3 = st.columns(3)
        with stat1:
            st.markdown(f"""
<div style="text-align: center; padding: 12px; background: rgba(255, 255, 255, 0.05); border-radius: 10px;"><div style="font-family: monospace; font-size: 24px; font-weight: 700; color: #00b4d8;">{forecast.hotspot_count}</div><div style="font-size: 11px; text-transform: uppercase; opacity: 0.7;">Hotspot Regions</div></div>
""", unsafe_allow_html=True)
        with stat2:
            st.markdown(f"""
<div style="text-align: center; padding: 12px; background: rgba(255, 255, 255, 0.05); border-radius: 10px;"><div style="font-family: monospace; font-size: 24px; font-weight: 700; color: #00b4d8;">{days_to_sell}d</div><div style="font-size: 11px; text-transform: uppercase; opacity: 0.7;">Est. Days to Sell</div></div>
""", unsafe_allow_html=True)
        with stat3:
            st.markdown(f"""
<div style="text-align: center; padding: 12px; background: rgba(255, 255, 255, 0.05); border-radius: 10px;"><div style="font-family: monospace; font-size: 24px; font-weight: 700; color: #00b4d8;">+£{forecast.demand_bonus:,}</div><div style="font-size: 11px; text-transform: uppercase; opacity: 0.7;">Demand Bonus</div></div>
""", unsafe_allow_html=True)
        
        # Close container
        st.markdown("</div>", unsafe_allow_html=True)
    
    @staticmethod
    def regional_hotspot(region: RegionalDemand, rank: int):
        """Render a regional hotspot card"""
        demand_color = region.demand_level.color
        
        # Badge for top regions
        rank_badge = ""
        if rank == 1:
            rank_badge = " 🏆 BEST MATCH"
        elif rank == 2:
            rank_badge = " (2nd)"
        elif rank == 3:
            rank_badge = " (3rd)"
        
        st.markdown(f"""<div style="background: white; border-radius: 12px; padding: 16px; margin: 10px 0; border-left: 4px solid {demand_color}; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.04);"><div style="flex: 1;"><div style="font-weight: 600; color: #0a2f4f; font-size: 15px; margin-bottom: 4px;">{region.location}{rank_badge}</div><div style="font-size: 13px; color: #6b7280;">📍 {region.distance_miles:.0f} mi · 🚗 {region.stock_level} stock · 👥 {region.buyers_waiting} waiting · ⏱️ ~{region.days_to_sell}d</div></div><div style="text-align: right;"><div style="font-family: monospace; font-size: 28px; font-weight: 700; color: {demand_color};">{region.demand_score}</div><div style="font-size: 11px; text-transform: uppercase; color: #6b7280;">Score</div></div></div>""", unsafe_allow_html=True)
    
    @staticmethod
    def ping_result(result: dict):
        """Render the ping network result"""
        best_location = result.get('best_match', 'N/A')
        if best_location and best_location != 'N/A':
            best_location = best_location.replace('Sytner BMW ', '')
        
        st.success("📡 **Network Pinged Successfully!**")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Locations Notified", result['notifications_sent'])
        with col2:
            st.metric("Interested Buyers", result['interested_buyers'])
        with col3:
            st.metric("Est. Sale Time", f"~{result['estimated_sale_days']}d")
        with col4:
            st.metric("Best Match", best_location)


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
    def demand_forecast(vehicle: Vehicle):
        """Render demand forecast section with regional hotspots"""
        # Get forecast data
        forecast = vehicle_service.get_demand_forecast(vehicle)
        
        # Render main forecast card (self-contained HTML)
        Components.demand_forecast_card(forecast, vehicle)
        
        # Seasonal insight
        season_insights = {
            (Season.SUMMER, VehicleType.SPORTS): "🔥 Peak season for sports cars! Buyers actively searching.",
            (Season.SUMMER, VehicleType.CONVERTIBLE): "☀️ Convertibles are HOT right now. Expect fast sales.",
            (Season.WINTER, VehicleType.SUV): "❄️ SUV demand peaks in winter. Great time to sell!",
            (Season.WINTER, VehicleType.CROSSOVER): "🌨️ Crossovers in high demand for winter conditions.",
            (Season.WINTER, VehicleType.CONVERTIBLE): "📉 Off-season for convertibles. Consider holding or pricing competitively.",
            (Season.WINTER, VehicleType.SPORTS): "⚠️ Sports car demand drops in winter. Target indoor showrooms.",
            (Season.AUTUMN, VehicleType.SUV): "📈 SUV demand rising as winter approaches!",
            (Season.SPRING, VehicleType.CONVERTIBLE): "🌸 Convertible interest picking up for summer.",
        }
        
        insight_key = (forecast.current_season, forecast.vehicle_type)
        if insight_key in season_insights:
            st.info(season_insights[insight_key])
        
        # Regional hotspots section
        st.markdown("#### 🗺️ Regional Demand Hotspots")
        st.caption("Locations ranked by demand score — higher scores mean faster sales")
        
        # Show top 5 regions
        for idx, region in enumerate(forecast.regional_demands[:5], 1):
            Components.regional_hotspot(region, idx)
        
        # Expandable for all regions
        with st.expander(f"View all {len(forecast.regional_demands)} regions"):
            for idx, region in enumerate(forecast.regional_demands[5:], 6):
                Components.regional_hotspot(region, idx)
        
        # Ping Network Section
        st.markdown("---")
        st.markdown("#### 📡 Ping Network")
        st.caption("Alert high-demand locations about this vehicle to find buyers faster")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            hotspot_locations = [r.location.replace("Sytner BMW ", "") for r in forecast.regional_demands if r.is_hotspot]
            if hotspot_locations:
                st.markdown(f"**Will notify:** {', '.join(hotspot_locations[:3])}{'...' if len(hotspot_locations) > 3 else ''}")
            else:
                st.markdown("**Will notify:** All network locations")
        
        with col2:
            ping_button = st.button(
                "📡 Ping Network",
                key="ping_network",
                use_container_width=True,
                type="primary"
            )
        
        if ping_button:
            with st.spinner("Pinging network locations..."):
                time.sleep(1)  # Simulate network delay
                result = vehicle_service.ping_network(vehicle, forecast)
                st.session_state.ping_result = result
        
        if st.session_state.get("ping_result"):
            Components.ping_result(st.session_state.ping_result)
            
            # Show which locations were pinged
            if st.session_state.ping_result.get("locations_pinged"):
                with st.expander("📍 Locations notified"):
                    for loc in st.session_state.ping_result["locations_pinged"]:
                        st.markdown(f"✓ {loc}")
    
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
        st.markdown("""<div style="background: linear-gradient(135deg, #0a2f4f 0%, #00b4d8 100%); padding: 48px 32px; border-radius: 20px; margin-bottom: 36px; text-align: center; position: relative; overflow: hidden;"><h1 style="color: white; font-size: 38px; font-weight: 700; margin: 0 0 12px 0;">Instant Trade-In Valuation</h1><p style="color: rgba(255, 255, 255, 0.95); font-size: 18px; margin: 0 0 32px 0;">Get competitive offers in seconds · Complete deals in minutes</p><div style="display: flex; justify-content: center; gap: 48px; flex-wrap: wrap;"><div style="text-align: center;"><div style="font-family: monospace; font-size: 36px; font-weight: 700; color: white;">30 min</div><div style="font-size: 13px; color: rgba(255,255,255,0.85); margin-top: 4px;">Average completion</div></div><div style="text-align: center;"><div style="font-family: monospace; font-size: 36px; font-weight: 700; color: white;">15+</div><div style="font-size: 13px; color: rgba(255,255,255,0.85); margin-top: 4px;">Network locations</div></div><div style="text-align: center;"><div style="font-family: monospace; font-size: 36px; font-weight: 700; color: white;">£500+</div><div style="font-size: 13px; color: rgba(255,255,255,0.85); margin-top: 4px;">Bonus opportunities</div></div></div></div>""", unsafe_allow_html=True)
        
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
        
        # Demand Forecast - NEW FEATURE
        Sections.demand_forecast(vehicle)
        
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

