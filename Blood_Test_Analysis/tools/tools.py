import requests
from crewai.tools import BaseTool
import os
from langchain_community.document_loaders import PDFPlumberLoader
import logging

# Set up logging for better debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class BloodTestReportTool(BaseTool):
    name: str = "blood_test_report_tool"
    description: str = "Reads data from a PDF file and returns text (truncated to avoid token limits)."
    MAX_CHARS: int = 3000

    def _run(self, file_path: str) -> str:
        try:
            docs = PDFPlumberLoader(file_path).load()
            full_report = ""

            for data in docs:
                content = data.page_content or ""
                content = content.replace("\n\n", "\n")
                full_report += content + "\n"

                if len(full_report) > self.MAX_CHARS:
                    full_report = full_report[:self.MAX_CHARS]
                    full_report += "\n\n[...TRUNCATED DUE TO SIZE LIMIT...]"
                    break

            if not full_report:
                logger.error("No content extracted from the PDF.")
                return "Error: No content extracted from the PDF."

            logger.info(f"Extracted content preview: \n{full_report[:500]}...")
            return full_report

        except Exception as e:
            logger.error(f"Error reading PDF file at {file_path}: {str(e)}")
            return f"Error: {str(e)}"


class ResearchSearchTool(BaseTool):
    name: str = "research_search_tool"
    description: str = (
    "Searches Google via Serper.dev for authoritative information about medical or scientific questions. "
    "Returns a concise, plain-language explanation or recommendation derived from the search results. "
    "Does not include URLs or links."
)

    def _run(self, query: str) -> str:
        return run_serper_search(query)


class NutritionSearchTool(BaseTool):
    name: str = "nutrition_search_tool"
    description: str = (
        "Searches Google via Serper.dev for nutrition and dietary recommendations based on a blood marker query. "
        "Returns the top 5 relevant articles with titles and URLs."
    )

    def _run(self, query: str) -> str:
        return run_serper_search(query)


class ExerciseSearchTool(BaseTool):
    name: str = "exercise_search_tool"
    description: str = (
        "Searches Google via Serper.dev for exercise and fitness recommendations based on a blood marker query. "
        "Returns the top 5 relevant articles with titles and URLs."
    )

    def _run(self, query: str) -> str:
        return run_serper_search(query)


# ===========================
# HELPER FUNCTION
# ===========================
def run_serper_search(query: str) -> str:
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return "Error: the SERPER_API_KEY environment variable is not set."

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"Request to Serper.dev failed: {e}")
        return f"Error fetching results: {str(e)}"

    organic_results = data.get("organic", [])
    if not organic_results:
        return "No relevant results found."

    formatted = []
    for item in organic_results[:5]:
        title = item.get("title", "No title")
        link = item.get("link", "No link")
        snippet = item.get("snippet", "")
        formatted.append(f"• **{title}**\n{snippet}\n{link}")

    return "\n\n".join(formatted)


# ===========================
# EXPORTED SYMBOLS
# ===========================
__all__ = [
    "BloodTestReportTool",
    "ResearchSearchTool",
    "NutritionSearchTool",
    "ExerciseSearchTool",
]
