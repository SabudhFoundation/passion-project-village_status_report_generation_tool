A unified, LLM-powered Streamlit dashboard designed to generate interactive, bilingual status reports for both Schools and Villages.

This portal acts as a master router, seamlessly integrating two distinct reporting tools into a single, user-friendly interface. It leverages Large Language Models (LLMs) for natural language intent classification, automated insights, and smart spell-checking, all while supporting both English and Punjabi (ਪੰਜਾਬੀ).

✨ Key Features
Unified Master Portal: A central routing hub (app.py) that allows users to seamlessly switch between the School Tool and the Village Tool without state overlap or memory leaks.

Bilingual Support (English & Punjabi): Features dynamic UI translation, automated data translation, and the ability to generate complete PDF reports in native Gurmukhi fonts.

Conversational AI Interface: Users can search for schools or villages using natural language (e.g., "Show me the report for Baluana").

Smart Fuzzy Matching: If a database query fails due to a typo, the tool uses difflib to suggest the closest matching village or school names.

Interactive Data Grids: Utilizes st-aggrid for clean, selectable, and responsive data tables.

Comparative AI Insights: Select up to two distinct villages/schools to generate automated comparative insights powered by Gemini/LLMs.

Automated PDF Generation: Compiles queried data, charts, and AI insights into downloadable, beautifully formatted PDF reports.

MongoDB Caching: Efficiently caches database calls to prevent redundant network requests and speed up UI reruns.

📂 Project Architecture
The repository is structured as a monolithic application containing sub-packages for each tool, sharing a root configuration.

Integrated_Tool/
├── .env                              # Master environment variables (API keys, Configs)
├── app.py                            # The Master Streamlit Router
├── fonts/                            # Custom fonts for PDF generation
│   ├── NotoSansGurmukhi-Regular.ttf  
│   └── NotoSansGurmukhi-Bold.ttf
│
├── school_report_gen_tool/           # 🏫 School Tool Package
│   ├── __init__.py
│   └── src/
│       ├── __init__.py
│       ├── main.py                   # School UI logic
│       ├── llm.py                    # School-specific LLM prompts/analysis
│       ├── database.py               # MongoDB fetching
│       └── utils.py                  # School PDF compilation
│
└── village_report_gen_tool/          # 🏘️ Village Tool Package
    ├── __init__.py
    ├── app.py                        # Village UI logic
    └── src/
        ├── __init__.py
        ├── llm.py
        ├── database.py
        └── utils.py

🛠️ Tech Stack

Frontend: Streamlit, streamlit-aggrid

Backend / Logic: Python 3.x, Pandas

AI / NLP: Google Gemini (LLM Analysis), deep_translator

Database: MongoDB

PDF Generation: fpdf / reportlab

Configuration: pydantic, pydantic-settings

🚀 Getting Started
Follow these steps to set up the project locally.

1. Clone the repository
git clone https://github.com/yourusername/Integrated-Data-Generation-Portal.git
cd Integrated-Data-Generation-Portal

2. Install Dependencies
Ensure you have Python 3.9+ installed, then run:
pip install -r requirements.txt

3. Setup Environment Variables
Create a .env file in the root directory (alongside the master app.py). It must include the variables defined in your Pydantic settings. Example:
PAGE_TITLE="Village Status Report Tool"
PAGE_LAYOUT="wide"
LOG_LEVEL="INFO"
MONGO_URI="mongodb+srv://<username>:<password>@<cluster-url>/"
SCHOOL_FILENAME="school_data.xlsx"
SCHOOL_LIST_PATH="school_report_gen_tool/src/data/school_data.xlsx"
API_KEY="your_google_api_key_here"
MODEL_NAME="gemini"
GEMINI_MODEL_NAME="gemini-2.5-flash-lite"
MODEL_TEMP=0.7
ENABLE_REMARK_REPHRASE=True
MAX_REPHRASE_RETRIES=3
FUZZY_SCORE_THRESHOLD=80
PUNJABI_REGULAR_FONT_PATH="fonts/NotoSansGurmukhi-Regular.ttf"
PUNJABI_BOLD_FONT_PATH="fonts/NotoSansGurmukhi-Bold.ttf"
PUNJABI_FONT_LOADED=True

5. Font Configuration (Crucial for Punjabi PDFs)
Ensure the fonts/ directory exists in the root folder and contains the required .ttf files specified in your .env. Without these, Punjabi characters will render as missing blocks in PDF exports.

6. Run the Application
Always run the application from the root directory to ensure the Python path correctly resolves the sub-modules.
streamlit run app.py

💡 Usage Guide
Home Portal: Upon launching, you will be greeted by the master routing page. Select either the School Tool or Village Tool.

Chat Interface: Type the name of the entity you are looking for (in English or Punjabi).

Selection & Comparison: If multiple results are found, use the interactive grid to select 1 or 2 rows.

Selecting one generates a standard status report.

Selecting two unlocks the Comparative AI Insights dashboard.

Download: Click the primary download button at the bottom of the report to export the compiled data and AI insights as a PDF.

Return: Click the "🔙 Back to Home Portal" button in the sidebar to securely wipe the session state and return to the main menu.
