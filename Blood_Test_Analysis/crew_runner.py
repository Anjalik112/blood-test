# crew_runner.py

from crewai import Crew
from agents import verifier, doctor, nutritionist, exercise_specialist
from task import verification, help_patients, nutrition_analysis, exercise_planning
from tools.tools import BloodTestReportTool
import logging
import time

logger = logging.getLogger(__name__)

def run_crew_pipeline(query: str, file_path: str) -> dict:
    # 1) Extract PDF text once at the top level
    try:
        loader = BloodTestReportTool()
        pdf_text = getattr(loader, "run", loader._run)(file_path)
    except Exception as e:
        logger.exception("PDF extraction failed")
        return {"error": f"Error extracting PDF: {e}"}

    inputs = {"query": query, "report_text": pdf_text}
    pipeline = [
        (verification, verifier),
        (help_patients, doctor),
        (nutrition_analysis, nutritionist),
        (exercise_planning, exercise_specialist),
    ]

    results = {}
    for task, agent in pipeline:
        role = agent.role
        try:
            # spin up a one-agent, one-task Crew each time
            crew = Crew(agents=[agent], tasks=[task], process="sequential")
            time.sleep(1)  # throttle to avoid TPM spikes
            out = crew.kickoff(inputs).dict()
            raw = (out.get("tasks_output") or [{}])[0].get("raw", "").strip()
            results[role] = raw or "⚠️ No output."
        except Exception as e:
            logger.warning(f"{role} step failed: {e}")
            results[role] = f"⚠️ Error in {role}: {e}"

    return results
