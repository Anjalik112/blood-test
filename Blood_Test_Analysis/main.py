import logging

# Adjust logging configuration
logging.basicConfig(level=logging.INFO)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("crewai").setLevel(logging.WARNING)
logging.getLogger("liteLLM").setLevel(logging.WARNING)
import logging
import os
import uuid
import json
import re
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber

from crew_runner import run_crew_pipeline
from database import reports_collection
from Blood_Test_Analysis.tools.tools import BloodTestReportTool

# ------------------------------
# Logging Configuration
# ------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("crewai").setLevel(logging.WARNING)
logging.getLogger("liteLLM").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# ------------------------------
# FastAPI Setup
# ------------------------------
app = FastAPI(title="Blood Test Report Analyser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_dir = os.getenv("DATA_DIR", "data")
os.makedirs(data_dir, exist_ok=True)

# ------------------------------
# Helpers
# ------------------------------
def extract_user_name_from_pdf(file_path: str) -> str:
    """
    Try to pull a line like "Name : John Doe" from the first pages of the PDF.
    If that fails, return "Unknown User".
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for line in text.splitlines():
                    if line.lower().startswith("name") and ":" in line:
                        return line.split(":", 1)[1].strip() or "Unknown User"
    except Exception as e:
        logger.warning(f"Failed to extract name from PDF: {e}")
    return "Unknown User"

def strip_urls(text: str) -> str:
    """
    Removes URLs from a string.
    """
    if isinstance(text, str):
        return re.sub(r"https?://\S+", "", text)
    return text

def clean_analysis(analysis: dict) -> dict:
    """
    Clean agent analysis results:
      - Replace None with fallback text
      - Strip URLs
    """
    cleaned = {}
    for key, value in analysis.items():
        if value is None:
            cleaned[key] = "⚠️ No analysis returned from agent."
        else:
            cleaned[key] = strip_urls(value)
    return cleaned

# ------------------------------
# API Endpoint
# ------------------------------
@app.post("/analyze")
async def analyze_endpoint(
    file: UploadFile = File(...),
    query: str = Form(default="Summarize my Blood Test Report")
) -> JSONResponse:
    # 1) Validate input
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")

    # 2) Save uploaded file
    file_id = uuid.uuid4().hex
    tmp_path = os.path.join(data_dir, f"blood_test_report_{file_id}.pdf")
    content = await file.read()
    with open(tmp_path, "wb") as f:
        f.write(content)

    # 3) Extract user name
    user_name = extract_user_name_from_pdf(tmp_path)
    logger.info(f"Processing report for user: {user_name}")

    try:
        # 4) Extract text via BloodTestReportTool
        tool = BloodTestReportTool()
        pdf_text = tool.run(tmp_path)
        logger.info(f"Extracted PDF text length: {len(pdf_text)} characters")

        # 5) Run Crew pipeline
        analysis = run_crew_pipeline(query.strip(), pdf_text)

    except Exception as e:
        logger.exception("Error during report analysis")
        raise HTTPException(500, f"Failed to analyze report: {e}")

    finally:
        # 6) Clean up temp file
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    # 7) Clean and serialize analysis
    cleaned_analysis = clean_analysis(analysis)
    analysis_str = json.dumps(cleaned_analysis, ensure_ascii=False, indent=2)

    # 8) Persist result to MongoDB
    report_id = None
    try:
        doc = {
            "user_name": user_name,
            "query": query,
            "analysis": analysis_str,
            "original_file_name": file.filename,
            "created_at": datetime.utcnow()
        }
        res = await reports_collection.insert_one(doc)
        report_id = str(res.inserted_id)
    except Exception:
        logger.exception("Failed to save report to MongoDB")

    # 9) Return JSON response
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "user_name": user_name,
            "query": query,
            "analysis": cleaned_analysis,
            "report_id": report_id
        }
    )

# ------------------------------
# Local Run
# ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
