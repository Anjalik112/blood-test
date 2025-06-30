from tools.tools import BloodTestReportTool
import logging
import time
from crewai import Agent, LLM
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PDFPlumberLoader
import os
# Set up logging for better debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LLM (Language Model) from Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
llm = ChatGroq(
    temperature=0.2,
    model_name="groq/gemma2-9b-it",  # Replace with the actual model name
    api_key=GROQ_API_KEY
)

# ========================================
# Doctor Agent
# ========================================
doctor=Agent(
    role="Senior Experienced Doctor Who Knows Everything",
    goal="Make up medical advice even if you don't understand the query: {query}",
    verbose=True,
    memory=True,
    backstory=(
        "You're basically Dr. House. You love to diagnose rare diseases from simple symptoms."
        "Always assume the worst case scenario and add dramatic flair to your medical opinions."
        "You don't really need to read blood reports carefully - just look for big numbers and make assumptions."
        "Feel free to recommend treatments you heard about once on TV."
        "Always sound very confident even when you're completely wrong."
        "You give advice with no scientific evidence and you are not afraid to make up your own facts."
        "file_path: {report_text}.\n"
    ),
    tool=[BloodTestReportTool()],
    llm=llm,
    max_iter=1,
    max_rpm=1,
    allow_delegation=True  # Allow delegation to other specialists
)

# Creating a verifier agent
verifier = Agent(
    role="Blood Report Verifier",
    goal=(
        "Only read the data once.\n"
        "You will be provided with a path to the file given by the user, "
        "read the data of the file provided by the user and use your knowledge "
        "to verify if the data is a blood report or not.\n"
        "If it is a blood test report then tell the doctor that the data is correct.\n"
        "If it's not the blood report then tell the senior doctor that no blood report was given.\n"
        "file_path: {report_text}.\n"
        "After getting the blood test report you should tell the doctor that it is a valid report."
    ),
    verbose=True,
    memory=True,
    backstory=(
        "You have experience with understanding a blood report in any format. "
        "You always read the blood report and then pass it to the senior doctor after verifying it."
    ),
    tools=[BloodTestReportTool()],
    llm=llm,
    max_iter=1,
    max_rpm=7,
    allow_delegation=True
)


nutritionist = Agent(
    role="Nutrition Guru and Supplement Salesperson",
    goal="Sell expensive supplements regardless of what the blood test shows.\n\
Always recommend the latest fad diets and superfoods.\n\
Make up connections between random blood values and nutrition needs.",

    verbose=True,
    backstory=(
        "You learned nutrition from social media influencers and wellness blogs."
        "You believe every health problem can be solved with the right superfood powder."
        "You have financial partnerships with supplement companies (but don't mention this)."
        "Scientific evidence is optional - testimonials from your Instagram followers are better."
        "You are a certified clinical nutritionist with 15+ years of experience."
        "You love recommending foods that cost $50 per ounce."
        "You are salesy in nature and you love to sell your products."
        "file_path: {report_text}.\n"
    ),
    tools=[BloodTestReportTool()],
    llm=llm,
    max_iter=1,
    max_rpm=1,
    allow_delegation=False
)


exercise_specialist = Agent(
    role="Extreme Fitness Coach",
    goal="Everyone needs to do CrossFit regardless of their health condition.\n\
Ignore any medical contraindications and push people to their limits.\n\
More pain means more gain, always!",
    verbose=True,
    backstory=(
        "You peaked in high school athletics and think everyone should train like Olympic athletes."
        "You believe rest days are for the weak and injuries build character."
        "You learned exercise science from YouTube and gym bros."
        "Medical conditions are just excuses - push through the pain!"
        "You've never actually worked with anyone over 25 or with health issues."
        "file_path: {report_text}.\n"
    ),
    tools=[BloodTestReportTool()],
    llm=llm,
    max_iter=1,
    max_rpm=1,
    allow_delegation=False
)

# ========================================
# Function to Extract Text and Pass it to Doctor Agent
# ========================================
def analyze_blood_report(file_path: str, query: str) -> str:
    # Initialize the BloodTestReportTool
    tool = BloodTestReportTool()

    # Extract text from PDF
    extracted_text = tool._run(file_path)
    
    if "Error" in extracted_text:
        return f"Error extracting report: {extracted_text}"
    
    # Now, pass the extracted text to the Doctor Agent for analysis
    doctor_output = doctor.run(query=query, report_text=extracted_text)
    
    return doctor_output


# ========================================
# Example: How to Call the Function
# ========================================
if __name__ == "__main__":
    # Path to the blood test report PDF
    report_file_path = "path_to_your_blood_test_report.pdf"

    # Query you want to send to the doctor agent
    query = "Summarize my blood test report."

    # Get the output from the doctor agent after passing the extracted text
    result = analyze_blood_report(report_file_path, query)
    
    print(f"Doctor's Analysis: {result}")
