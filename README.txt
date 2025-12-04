Sytner TradeSnap - Vehicle Trade-In System
==========================================

A revolutionary vehicle trade-in system that transforms the traditional 45-minute process into a 30-second experience.

## 🚀 Overview

Sytner TradeSnap is a complete vehicle trade-in platform featuring:
- **Instant Vehicle Lookup**: Snap a photo or enter a registration to get full vehicle history in 30 seconds
- **Comprehensive Vehicle Reports**: MOT history, recalls, write-offs, theft checks, and valuations
- **Market Intelligence**: Live trends, seasonal demand forecasts, and 6-month price predictions
- **Smart Buyer Matching**: Connect with 8 specialist buyers across 22 Sytner BMW locations
- **Deal Accelerator**: Stock priority bonuses and same-day completion incentives

## 📁 Files Included

- `app_final.py`         : Main Streamlit application with all features
- `requirements.txt`     : Python dependencies
- `Sytner_TradeSnap_Innovation_Day.pptx` : Innovation Day presentation

## 🎯 Key Features

### 1. **Quick Vehicle Check**
   - Photo capture or manual registration entry
   - UK number plate styled input
   - Automatic DVLA, MOT, and HPI integration
   - Full vehicle history in 30 seconds

### 2. **Comprehensive Reports**
   - Complete vehicle summary (make, model, year, mileage, VIN)
   - MOT history with pass/fail records
   - Outstanding recalls with booking system
   - Write-off and theft checks
   - Mileage anomaly detection

### 3. **Market Intelligence & Forecasting**
   - Current market demand levels
   - Seasonal demand trends (Winter/Spring/Summer/Autumn)
   - 6-month price forecasts with depreciation
   - Local market insights (30-mile radius)
   - Hot sellers and best value opportunities
   - Competition analysis

### 4. **Smart Valuation System**
   - Estimated value ranges (Fair/Good/Excellent condition)
   - Deal accelerator bonuses (up to £700)
   - Network comparison across locations
   - Market-based pricing

### 5. **Sytner Buyer Network**
   - 8 expert vehicle buyers
   - 22 Sytner BMW locations across UK
   - Specialist matching by vehicle type
   - One-click "ping" system
   - 2-hour guaranteed response time
   - Full booking form with urgency levels

### 6. **Recall Management**
   - View all safety recalls
   - Book recall repairs directly
   - Select preferred location and time
   - Automatic confirmation system

## 🏢 Sytner BMW Locations

The system covers 22 Sytner BMW dealerships:
- Cardiff, Chigwell, Coventry, Harold Wood
- High Wycombe, Leicester, Luton, Maidenhead
- Newport, Nottingham, Oldbury, Sheffield
- Shrewsbury, Solihull, Stevenage, Sunningdale
- Swansea, Tamworth, Tring, Warwick
- Wolverhampton, Worcester

## 👥 Vehicle Buyers

8 specialist buyers with expertise in:
- 3 Series, 5 Series, Estate Cars
- X Series, SUV, 4x4
- M Sport, Performance, Diesel
- Saloon, Hybrid models
- Premium, Executive, Family cars

## ⚡ Quick Start (Local Development)

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install streamlit pillow pytesseract pandas datetime
```

### 3. Optional: Enhanced OCR (Recommended)
```bash
pip install easyocr
# EasyOCR requires PyTorch - follow instructions at https://pytorch.org/get-started/locally/
```

### 4. Install Tesseract OCR Binary
- **Ubuntu/Debian**: `sudo apt install tesseract-ocr`
- **macOS (Homebrew)**: `brew install tesseract`
- **Windows**: Download from https://github.com/tesseract-ocr/tesseract/wiki

### 5. Run the Application
```bash
streamlit run app_final.py
```

The app will open in your browser at `http://localhost:8501`

## 📱 Mobile Access

For best camera functionality:
- Deploy to Streamlit Cloud for HTTPS access
- Or access via network URL from mobile device on same network
- Camera input works best over HTTPS

## ☁️ Deploy to Streamlit Cloud

1. Create a GitHub repository
2. Push this folder to the repository
3. Go to [Streamlit Cloud](https://streamlit.io/cloud)
4. Connect your GitHub repo
5. Set main file to `app_final.py`
6. Deploy!

## 🔧 Configuration

### Mock APIs (Replace in Production)
The following functions use mock data and should be replaced with real APIs:

- `lookup_vehicle_basic(reg)` → Vehicle lookup API
- `lookup_mot_and_tax(reg)` → DVLA MOT API
- `lookup_recalls(reg_or_vin)` → DVSA Recall API
- `get_history_flags(reg)` → HPI/Experian API
- `estimate_value(...)` → CAP/Glass's valuation API
- `mock_ocr_numberplate(image)` → ANPR service

### Real Locations
All 22 Sytner BMW locations and 8 buyer profiles are included with realistic data.

## 🎨 Design Features

- BMW-inspired color scheme (Dark Blue #0b3b6f, Electric Blue #1e90ff)
- UK number plate styled inputs (Yellow background, black border)
- Responsive card-based layouts
- Professional gradients and shadows
- Mobile-optimized interface

## 📊 Business Impact

Expected results from pilot program:
- **95% faster** processing time (45 min → 2 min)
- **+40%** conversion rate improvement
- **£700** average bonus per vehicle
- **+500** additional vehicles per year
- **£350K+** annual revenue increase
- **4.8+** customer satisfaction score

## 🗓️ Rollout Plan

- **Q1 2025**: Pilot launch at 3 high-volume locations
- **Q2 2025**: Full network rollout to 22 sites

## 📋 Notes

### OCR Implementation
- App prefers EasyOCR if available (better accuracy for natural images)
- Falls back to pytesseract if EasyOCR not installed
- EasyOCR requires PyTorch (CPU-only is fine for demos)

### Browser Compatibility
- Works on all modern browsers
- Mobile camera requires HTTPS (use Streamlit Cloud)
- Desktop and tablet fully supported

### Data Privacy
- No data is stored permanently in this POC
- Session state resets between users
- Implement proper data handling in production

## 🤝 Support

For questions or issues:
- Internal: innovation@sytner.co.uk
- Project ID: TSNAP-2025

## 📄 License

Internal use only - Sytner Group Ltd.

---

**Built for Innovation Day 2025**  
*Revolutionizing the trade-in experience*
