import logging
import logging

# Adjust logging configuration
logging.basicConfig(level=logging.INFO)  # This will suppress debug logs globally.

# Set logging level for specific libraries (to suppress their debug logs)
logging.getLogger("pymongo").setLevel(logging.WARNING)  # This will only log warnings and errors from pymongo
logging.getLogger("httpx").setLevel(logging.WARNING)  # This will only log warnings and errors from httpx
logging.getLogger("crewai").setLevel(logging.WARNING)  # If crewai is generating logs, set it to WARNING
logging.getLogger("liteLLM").setLevel(logging.WARNING)

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import Optional
import os
import uuid
from datetime import datetime
import pdfplumber

# CHANGED: switched from original blocking crew logic to a modular pipeline
from crew_runner import run_crew_pipeline  

# NEW: integrated MongoDB for storing analysis results
from database import reports_collection  # MongoDB collection (ensure it's async)

app = FastAPI(title="Blood Test Report Analyser")

# NEW: added logging for better tracing and debugging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# NEW FUNCTION:
# This did not exist in the original code.
# Extracts the user's name from the uploaded PDF file.
def extract_user_name_from_pdf(file_path: str) -> str:
    """
    Simple function to extract 'Name' from the PDF text.
    This can be improved for more complex formats.
    """
    user_name = None

    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"

        for line in text.split("\n"):
            if "Name" in line:
                # Example: "Name : John Doe"
                parts = line.split(":")
                if len(parts) >= 2:
                    user_name = parts[1].strip()
                    break

    except Exception as e:
        logger.warning(f"Failed to extract name from PDF: {str(e)}")

    if not user_name:
        user_name = "Unknown User"

    return user_name


@app.post("/analyze")
async def analyze_blood_report(
    file: UploadFile = File(...),
    query: str = Form(default="Summarize my Blood Test Report"),
) -> JSONResponse:
    # CHANGED: added UUID to create a unique file name
    file_id = str(uuid.uuid4())
    file_path = f"data/blood_test_report_{file_id}.pdf"
    doctor_report = ""

    try:
        # CHANGED: ensures the data directory exists
        os.makedirs("data", exist_ok=True)

        # CHANGED: added robust file saving with async reading
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # NEW: extract user's name from PDF
        user_name = extract_user_name_from_pdf(file_path)

        # CHANGED: replaced original run_crew with run_crew_pipeline
        doctor_report = run_crew_pipeline(query=query.strip(), file_path=file_path)

    except Exception as e:
        logger.exception("Error during report analysis.")
        doctor_report = f"An error occurred while generating the doctor report: {str(e)}"
        user_name = "Unknown User"

    finally:
        # CHANGED: added proper cleanup logic and error logging for temp files
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as cleanup_err:
                logger.warning(f"Cleanup error: {cleanup_err}")

        inserted_id: Optional[str] = None

        try:
            # NEW: save analysis result to MongoDB
            document = {
                "user_name": user_name,
                "query": query,
                "analysis": doctor_report or "No analysis generated.",
                "original_file_name": file.filename,
                "timestamp": datetime.utcnow(),
            }

            # NEW: using async MongoDB insert for non-blocking operation
            result = await reports_collection.insert_one(document)
            inserted_id = str(result.inserted_id)

        except Exception as db_err:
            logger.exception("Error saving to MongoDB.")
            inserted_id = None
            doctor_report += f"\n\nFailed to save report to MongoDB: {str(db_err)}"

    # Simplified response with essential information for Streamlit
    return JSONResponse(
        content={
            "status": "success",
            "user_name": user_name,
            "query": query,
            "analysis": doctor_report,
            "report_id": inserted_id  # Including report_id in the response for Streamlit
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
