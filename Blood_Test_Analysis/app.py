import time
import streamlit as st
import requests

# FastAPI endpoint URL
api_url = "http://127.0.0.1:8000/analyze"  # FastAPI URL for triggering analysis task

st.title("Blood Test Report Analyzer")

# Upload file and input query
uploaded_file = st.file_uploader("Upload your blood test report (PDF)", type="pdf")
query = st.text_area("Enter query", placeholder="Ask something about the blood test report")

if st.button("Analyze Report"):
    if uploaded_file is None:
        st.warning("⚠️ Please upload a PDF file first.")
    elif not query.strip():
        st.warning("⚠️ Please enter a query.")
    else:
        file_bytes = uploaded_file.read()

        files = {"file": (uploaded_file.name, file_bytes, "application/pdf")}
        data = {"query": query}

        # Add a progress bar for the analysis
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Send the file to FastAPI to initiate the task
            response = requests.post(api_url, files=files, data=data)

            if response.status_code == 200:
                result = response.json()
                st.write("Analysis started. Please wait for the results.")

                # Simulating the background task processing time
                progress_bar.progress(50)
                status_text.text("🔄 Processing... Please wait.")

                time.sleep(5)  # For demonstration purposes, replace this with actual polling logic.

                st.success("✅ Analysis Completed!")
                st.markdown(f"**User Name:** {result.get('user_name', 'N/A')}")
                st.markdown(f"**Query:** {result.get('query', 'N/A')}")
                st.markdown(f"**Report ID:** `{result.get('report_id', 'N/A')}`")
                st.subheader("Analysis Text:")
                st.write(result.get('analysis', 'No analysis returned.'))
            else:
                st.error(f"❌ Error from FastAPI: {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
            st.stop()
