from crewai.tools import BaseTool
import requests
import os
import logging

# Optional: set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SerperDevTool(BaseTool):
    name: str = "search_tool"
    description: str = (
        "Searches the web for a query using Serper.dev Google Search API "
        "and returns the top results as text."
    )

    def _run(self, query: str) -> str:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            logger.error("SERPER_API_KEY is not set in environment variables.")
            return "Error: SERPER_API_KEY is missing."

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

        # Process results
        organic_results = data.get("organic", [])
        if not organic_results:
            return "No relevant results found."

        # Format top results nicely
        formatted_results = []
        for result in organic_results[:5]:
            title = result.get("title", "No title")
            link = result.get("link", "No link")
            snippet = result.get("snippet", "")
            formatted_results.append(f"• **{title}**\n{snippet}\n{link}")

        return "\n\n".join(formatted_results)

# For testing directly:
if __name__ == "__main__":
    tool = SerperDevTool()
    query = "What is anemia?"
    result = tool._run(query)
    print(result)
