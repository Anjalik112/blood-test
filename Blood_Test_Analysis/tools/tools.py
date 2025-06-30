import os
import crewai.tools
from crewai.tools import BaseTool
import logging
from dotenv import load_dotenv
from langchain_community.document_loaders import PDFPlumberLoader  # Single import

# Load environment variables from .env file
load_dotenv()

# Set up logging for better debugging
logging.basicConfig(level=logging.DEBUG)  # You can set to INFO or WARNING for less verbosity
logger = logging.getLogger(__name__)

# Creating custom pdf reader tool
class BloodTestReportTool(BaseTool):
    name: str = "blood_test_report_tool"
    description: str = "Reads data from a PDF file and returns text (truncated to avoid token limits)."
    MAX_CHARS: int = 3000  # Safe maximum character size to avoid token overflow

    def _run(self, file_path: str) -> str:
        try:
            # Use PDFPlumberLoader to load PDF content
            docs = PDFPlumberLoader(file_path).load()
            full_report = ""

            for data in docs:
                content = data.page_content or ""
                content = content.replace("\n\n", "\n")
                full_report += content + "\n"

                # Ensure we don't exceed MAX_CHARS
                if len(full_report) > self.MAX_CHARS:
                    full_report = full_report[:self.MAX_CHARS]
                    full_report += "\n\n[...TRUNCATED DUE TO SIZE LIMIT...]"
                    break

            # If the report is empty, log the issue and return an error message
            if not full_report:
                logger.error("No content extracted from the PDF.")
                return "Error: No content extracted from the PDF."
            logging.info("***",full_report)
            return full_report

        except Exception as e:
            logger.error(f"Error reading PDF file at {file_path}: {str(e)}")
            return f"Error: {str(e)}"


# ===========================
# EXPORTED SYMBOLS
# ===========================
__all__ = ["BloodTestReportTool"]
