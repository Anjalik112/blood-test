
from crewai import Crew
from task import help_patients
from agents import doctor
from Blood_Test_Analysis.tools.tools import BloodTestReportTool
import logging
import time

logger = logging.getLogger(__name__)

# NEW FILE:
# This file was not present in the original project.
# Created to:
# - encapsulate the CrewAI pipeline logic
# - orchestrate reading PDF data
# - run CrewAI tasks and agents in a single pipeline
# - simplify calling the analysis from FastAPI routes

def run_crew_pipeline(query: str, file_path: str) -> str:
    # Instantiate the custom PDF reading tool
    tool = BloodTestReportTool()

    try:
        # CHANGED:
        # Depending on the BaseTool implementation, the tool might
        # expose either .run() or ._run() as the entry point.
        # Added this logic for robustness in case CrewAI changes
        # the tool interface in future releases.
        pdf_text = tool.run(file_path)
    except AttributeError:
        # Fallback for older implementations
        pdf_text = tool._run(file_path)

    # Prepare inputs for the CrewAI pipeline
    inputs = {
        "query": query,
        "report_text": pdf_text,
    }

    # Instantiate the CrewAI pipeline
    crew = Crew(
        agents=[doctor],
        tasks=[help_patients],
        process="sequential",  # Runs tasks in sequence
    )

    try:
        # Simulate short processing delay (could be removed if not needed)
        time.sleep(1)

        # Execute the pipeline
        results = crew.kickoff(inputs)

        # Convert result object to a dictionary for easier handling
        result_dict = results.dict()
        print("Full CrewOutput dict:", result_dict)

        doctor_report = None

        # CHANGED:
        # The Crew output structure can vary depending on version.
        # Here we ensure we extract the doctor's response correctly.
        if result_dict.get("tasks_output"):
            first_task = result_dict["tasks_output"][0]
            doctor_report = first_task.get("raw")

        if not doctor_report:
            doctor_report = result_dict.get("raw")

        if not doctor_report:
            doctor_report = "No analysis generated."

    except Exception as e:
        logger.exception("Error running crew pipeline.")
        doctor_report = f"An error occurred during analysis: {str(e)}"

    print("Final doctor report text:", doctor_report)
    return doctor_report.strip()
