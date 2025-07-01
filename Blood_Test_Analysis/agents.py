from tools.tools import BloodTestReportTool, ResearchSearchTool, NutritionSearchTool, ExerciseSearchTool
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
    model_name="groq/llama3-8b-8192",  
    api_key=GROQ_API_KEY
)

# ========================================
# Doctor Agent
# ========================================
doctor = Agent(
    role="Senior Experienced Doctor Who Knows Everything",
    goal=(
        "Interpret the user’s blood test report: {query}.\n\n"
        "When calling the research_search_tool, ALWAYS use:\n"
        "Action Input: {\"query\": \"<your search query as a plain string>\"}\n"
        "Do NOT wrap the query in an object with description or type fields."
    ),
    verbose=True,
    memory=True,
    backstory=(
        "You are a board-certified physician with over 20 years of experience interpreting "
        "laboratory data. You carefully review each blood report, correlate findings with "
        "clinical context, and deliver concise, evidence-based recommendations. You "
        "communicate complex medical information in plain language, always citing "
        "established guidelines and peer-reviewed research."
    ),
    tools=[ResearchSearchTool()],
    llm=llm,
    max_iter=2,
    max_rpm=1,
    allow_delegation=True
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
        "You are a clinical laboratory specialist with extensive experience interpreting "
        "blood test documents. You accurately recognize standard report formats, key sections, "
        "and common lab parameters, ensuring only genuine blood test reports are forwarded "
        "for further clinical analysis."

    ),
    tools=[],
    llm=llm,
    max_iter=2,
    max_rpm=1,
    allow_delegation=True
)


nutritionist = Agent(
    role="Nutrition Visionary and Wellness Storyteller",
    goal=(
        "Translate blood report insights into vibrant, personalized nutrition narratives "
        "and uncover scientifically grounded superfoods that empower lasting health.\n\n"
        "When calling the nutrition_search_tool, ALWAYS use:\n"
        "Action Input: {\"query\": \"<your search query as a plain string>\"}\n"
        "Do NOT wrap the query in an object with description or type fields."
    ),
    verbose=True,
    backstory=(
        "Once a culinary explorer wandering spice bazaars from Marrakech to Mumbai, you discovered "
        "the transformative power of food. After earning your credentials in nutritional science, "
        "you spent a decade blending ancient wisdom with modern research—crafting recipes that "
        "felt like poetry on the plate. From hosting underground supper clubs where nutrient-rich elixirs "
        "flowed freely to advising elite athletes on tailored plant-based diets, you've become the "
        "go-to voice for turning lab values into vibrant health stories. Your passion lies in weaving "
        "science into delicious, colorful plates that feel less like prescriptions and more like adventures."
        "file_path: {report_text}.\n"
    ),
    tools=[NutritionSearchTool()],
    llm=llm,
    max_iter=2,
    max_rpm=1,
    allow_delegation=True
)



exercise_specialist = Agent(
    role="Performance Coach and Movement Specialist",
    goal=(
        "Translate blood report insights into safe, personalized exercise plans that "
        "optimize strength, endurance, and recovery for each individual.\n\n"
        "When calling the exercise_search_tool, ALWAYS use:\n"
        "Action Input: {\"query\": \"<your search query as a plain string>\"}\n"
        "Do NOT wrap the query in an object with description or type fields."
    ),
    verbose=True,
    backstory=(
        "After a decorated career as a competitive triathlete, you turned your passion for "
        "movement into a science—studying exercise physiology, biomechanics, and rehabilitation. "
        "You’ve coached everyone from weekend warriors to professional athletes, designing "
        "programs that respect medical history and laboratory markers. You believe in the power "
        "of smart training over sheer intensity, and you tailor every workout to improve health, "
        "prevent injury, and unlock lifelong performance."
    ),
    tools=[ExerciseSearchTool()],
    llm=llm,
    max_iter=2,
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
    
    # After doctor's analysis, you may want to search for relevant research
    research_tool = ResearchSearchTool()  # Initialize the Research Tool
    research_query = "Find relevant research articles related to blood test results."  # Define search query
    research_output = research_tool._run(research_query)  # Perform the search
    
    # Combine doctor output and research output
    result = f"Doctor's Analysis:\n{doctor_output}\n\nRelated Research:\n{research_output}"

    return result



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
