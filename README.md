[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=23178784&assignment_repo_type=AssignmentRepo)
Project Instructions
==============================

This repo contains the instructions for a machine learning project. 

**Do Not Forget to mention the Python Version being used and complete the requirements.txt fil**

# Village & School Status Report Generation Tool

A unified, LLM-powered Streamlit dashboard designed to generate interactive, bilingual status reports for both schools and villages. It leverages automated insights, natural language understanding, and smart data preprocessing, supporting both English and Punjabi (ਪੰਜਾਬੀ).

---

## ✨ Key Features

* **Unified Master Portal:** An interactive Streamlit interface driven by a master orchestrator (`main.py`) that handles reporting workflows seamlessly.
* **Bilingual Support (English & Punjabi):** Features dynamic UI translation, automated data processing, and native Gurmukhi font rendering for generated assets.
* **Conversational AI & Insights:** Uses Large Language Models (LLMs) via structured prompts for natural language queries and automated comparative insights.
* **Smart Fuzzy Matching:** If a database query fails due to a typo, the system utilizes `difflib` to suggest the closest matching village or school names.
* **Robust Backend Architecture:** Utilizes structured configuration states, dedicated utility modules, and database connection wrappers.

---

## 📂 Project Organization

The repository is structured to cleanly separate the frontend presentation layer, source business logic, datasets, and generated reports:

```text
├── .gitignore
├── LICENSE
├── README.md               <- Top-level documentation for setup and testing.
├── main.py                 <- Master script to run the Streamlit application.
├── requirements.txt        <- Python dependencies required to run the environment.
├── school_data.xlsx        <- Local reference Excel dataset for metrics evaluation.
├── meetings.md             <- Logs and action items from mentor alignment meetings.
├── weekly_report.md        <- Internal weekly status and progress tracker.
│
├── notebooks/              <- Jupyter notebooks for experimental data analysis.
├── reports/                <- Target output directory for generated assets.
│   ├── figures/            <- Generated graphics and visualization exports.
│   ├── final_project_report/ <- Final definitive report PDFs and supporting documents.
│   └── presentation/        <- Supporting presentation files.
│
├── screens/                <- Presentation layer UI layouts for Streamlit.
│   ├── school_report.py    <- UI screen and controls for School data reporting.
│   └── village_report.py   <- UI screen and controls for Village data reporting.
│
└── src/                    <- Core source package containing backend business logic.
    ├── __init__.py         <- Marks src as a Python package.
    ├── config.py           <- Application configuration and dynamic settings.
    ├── constants.py        <- Global environment and application constants.
    ├── database.py         <- Database configuration and client connectivity handlers.
    ├── llm.py              <- Large Language Model integration layer.
    ├── prompts.py          <- Context-managed system prompts for LLM querying.
    ├── utils.py            <- Universal helper functions and common utilities.
    │
    ├── data/               <- Local data management.
    │   ├── processed/      <- Cleaned and transformed canonical datasets.
    │   └── raw/            <- Original immutable source data dumps.
    │
    ├── models/             <- Scripts for predictive analysis and modeling.
    │   ├── train_model.py
    │   └── predict_model.py
    │
    ├── preprocessing_data/ <- Specialized scraping and data pipeline scripts.
    │
    ├── punjabi_font/       <- Core regional assets for localized PDF generation.
    │   ├── NotoSansGurmukhi-Bold.ttf
    │   └── NotoSansGurmukhi-Regular.ttf
    │
    └── visualization/      <- Scripts for exploratory data graphics generation.
        └── visualize.py



