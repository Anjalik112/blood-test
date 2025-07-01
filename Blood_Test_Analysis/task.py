from crewai import Task
from agents import doctor, verifier, nutritionist, exercise_specialist, analyze_blood_report
from tools.tools import ResearchSearchTool,BloodTestReportTool,NutritionSearchTool,ExerciseSearchTool
from typing import List, Optional
from celery_config import celery_app  # Import celery app instance
from time import sleep
import logging

# Initialize logger for debugging and error handling
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function to create tasks in a reusable way
def create_task(
    *,
    description: str,
    expected_output: str,
    agent,
    tools: Optional[List] = None,
) -> Task:
    return Task(
        description=description.strip(),
        expected_output=expected_output.strip(),
        agent=agent,
        tools=tools or [],  # tools the agent may call during this task
        inputs={
            "query": "{query}",
            "report_text": "{report_text}",
        },
        async_execution=False,
    )

# Task 1: Verify the input is a blood report
verification = create_task(
    description="""
        Assess whether the provided text appears to be a blood test report.

        Respond with:
        - Yes/No conclusion.
        - Any reasons for your determination.
    """,
    expected_output="Verification result indicating if the input is a blood test report.",
    agent=verifier,
    tools=[],  # allow lookup if needed
)

# Task 2: Summarize & explain for the patient
help_patients = create_task(
  description="""
  **Inputs**  
  - `report_text`: the full blood test report as plain text.  
  
  **Your Role**  
  You are a board-certified physician who **only interprets lab values** in plain language—no treatment or prescribing.  
  
  **Objectives**  
  1. Summarize the key findings.  
  2. Point out any values outside the normal range and explain their significance.  
  
  **Output**  
  A markdown summary a non-medical person can understand.
  """,
  expected_output="Patient-friendly interpretation of lab values, without advice.",
  agent=doctor,
  tools=[ResearchSearchTool()],
)


# Task 3: Evidence-based dietary recommendations
nutrition_analysis = create_task(
    description="""
    **Inputs**  
    - `report_text`: the full blood test report as plain text.  

    **Your Role**  
    You are an expert nutritionist.  
    Your job is to analyze the blood report and provide personalized dietary insights.  
    You should transform complex lab results into easy-to-understand nutritional guidance for a non-medical person.  

    **Objectives**  
    1. Identify any nutritional issues indicated by abnormal lab markers.  
    2. Recommend foods to prioritize or limit based on those markers.  
    3. Suggest any scientifically justified supplements if needed.  
    4. Summarize the rationale behind your recommendations in plain language.  
    5. Avoid listing external links or suggesting the user visit other websites. Provide actionable recommendations directly.

    **Output**  
    A concise, plain-language nutrition report summarizing how the person can adjust their diet based on their blood report.
    """,
    expected_output="A personalized nutrition guidance report, written in simple language without external URLs.",
    agent=nutritionist,
    tools=[],
)


# Task 4: Tailored exercise planning
exercise_planning = create_task(
    description="""
    **Inputs**  
    - `report_text`: the full blood test report as plain text.  

    **Your Role**  
    You are an experienced exercise physiologist and performance coach.  
    Your job is to translate blood report findings into practical fitness advice.  

    **Objectives**  
    1. Identify any exercise contraindications based on abnormal lab markers.  
    2. Recommend suitable exercise types and intensity for this individual’s health profile.  
    3. Provide practical fitness guidance that the person can safely implement.  
    4. Explain the rationale for your recommendations in plain language.  
    5. Avoid listing external links or suggesting the user visit other websites. Provide actionable recommendations directly.

    **Output**  
    A short, clear exercise plan tailored to the individual’s blood report findings, written in everyday language.
    """,
    expected_output="A safe and personalized exercise plan without external URLs, in plain language.",
    agent=exercise_specialist,
    tools=[],
)


# Celery Task to process blood report asynchronously
@celery_app.task
def process_blood_report(file_path: str, query: str):
    try:
        logger.info(f"Started async processing for {file_path} with query '{query}'")
        sleep(5)
        result = analyze_blood_report(file_path, query)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error in async blood report task: {e}")
        return {"status": "failure", "error": str(e)}
