
from crewai import Task
from agents import doctor, verifier
from tools.tools import BloodTestReportTool
from typing import List, Optional
from celery_config import celery_app  # Import celery app instance
from time import sleep

# CHANGED:
# Original task definitions were comedic and fictional.
# Rewritten for real medical analysis and production use.

# NEW:
# Helper function to create tasks in a reusable way,
# avoiding repetition and making future changes simpler.
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
        tools=tools or [],
        inputs={
            "query": "{query}",
            "report_text": "{report_text}",
        },
        async_execution=False,
    )


# CHANGED:
# Rewritten help_patients task:
# - Original task gave comedic and potentially unsafe advice.
# - Now provides real medical summary and analysis goals.
help_patients = create_task(
    description="""
        You are given this blood report text:

        {report_text}

        Your job is to:
        - Summarize key lab findings in plain language.
        - Identify any abnormal values and explain possible medical implications.
        - Provide lifestyle or dietary advice if appropriate.
    """,
    expected_output="A patient-friendly summary of the blood report.",
    agent=doctor,
    tools=[],  # Optionally add tools like [BloodTestReportTool] for PDF parsing
)


# NOTE:
# The following tasks are currently disabled.
# Original versions were comedic and token-heavy,
# and enabling them caused token overflows in the LLM.
# They can be re-enabled when using a higher-capacity model.

# nutrition_analysis = create_task(
#     description="""
#         Analyze the blood report data and:
#         - Provide evidence-based dietary recommendations.
#         - Suggest foods to prioritize or avoid based on key markers.
#         - Advise on supplements only if scientifically justified.
#     """,
#     expected_output="A personalized nutrition guidance report.",
#     agent=nutritionist,
# )


# exercise_planning = create_task(
#     description="""
#         Analyze the blood report data and:
#         - Recommend suitable exercise regimens.
#         - Tailor intensity and type of exercise to the individual's health profile.
#         - Highlight any contraindications from abnormal lab values.
#     """,
#     expected_output="A safe and personalized exercise plan.",
#     agent=exercise_specialist,
# )


# CHANGED:
# Rewritten verification task:
# - Original task simply guessed that everything was a blood report.
# - Now clearly requests a yes/no answer plus reasons for validation.
verification = create_task(
    description="""
        Assess whether the provided text appears to be a blood test report.

        Respond with:
        - Yes/No conclusion.
        - Any reasons for your determination.
    """,
    expected_output="Verification result indicating if the input is a blood test report.",
    agent=verifier,
)


# NEW:
# Added Celery task to support asynchronous processing.
# This enables running longer analysis jobs without blocking FastAPI.
@celery_app.task
def process_blood_report(file_path: str, query: str):
    # Simulating a long-running task.
    # Replace with actual call to your analysis pipeline as needed.
    sleep(5)
    print(f"Processing blood test report for file: {file_path} with query: {query}")
    return {"status": "success", "file": file_path, "query": query}
