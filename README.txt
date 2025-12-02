Sytner Tradesnap - Full POC (Streamlit)
======================================

Files included:
- app.py                 : main Streamlit application
- helpers/ocr.py         : image preprocessing helper for OCR
- requirements.txt       : suggested pip dependencies

Quick start (local):
1. Create and activate a virtual environment:
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate

2. Install lightweight deps:
   pip install streamlit pillow pytesseract

3. Optional: EasyOCR (recommended for better OCR accuracy but requires PyTorch):
   pip install easyocr
   # Installing PyTorch: follow instructions at https://pytorch.org/get-started/locally/

4. Install Tesseract-OCR binary (for pytesseract):
   - Ubuntu/Debian: sudo apt install tesseract-ocr
   - macOS (Homebrew): brew install tesseract
   - Windows: install from https://github.com/tesseract-ocr/tesseract/wiki

5. Run the app:
   streamlit run app.py

Notes on OCR:
- The app prefers EasyOCR if available (better for natural images) and falls back to pytesseract.
- Mobile camera input works best over HTTPS (deploy to Streamlit Cloud) or run locally and access from phone via network URL.
- EasyOCR requires PyTorch; CPU-only installs are fine for small demos but can be slow.

Deploy to Streamlit Cloud:
- Create a GitHub repo and push this folder.
- On Streamlit Cloud, connect the repo and set the main file to app.py.
- Ensure requirements.txt includes 'easyocr' if you want EasyOCR on the cloud (be mindful of torch installation).

