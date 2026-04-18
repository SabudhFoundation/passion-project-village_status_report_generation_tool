[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=23178784&assignment_repo_type=AssignmentRepo)
# Project Instructions

This repository contains instructions and source code for School & Village Status Report Generation Tool project.

> **Important:**  
> Python version used: **3.11.13**  
> Ensure `requirements.txt` is complete and up to date.

---

## Setup

Create and activate a Conda environment, then install dependencies:

```bash
conda create -n village-status-env python=3.11.13
conda activate village-status-env
pip install -r requirements.txt
```

---

## Project Organization

```
├── README.md              <- Top-level documentation
├── notebooks              <- Jupyter notebooks (use snake_case naming)
├── reports                <- Reports and outputs
│   ├── figures            <- Generated graphics and figures
│   ├── README.md          <- YouTube video link
│   ├── final_project_report <- Final report (PDF + supporting files)
│   └── presentation       <- Final PowerPoint presentation
│
├── requirements.txt       <- Python dependencies (`pip freeze > requirements.txt`)
│
├── src                    <- Source code
│   ├── preprocessing_data <- Data preprocessing scripts
│   ├── punjabi_font       <- Font resources (Punjabi)
│   ├── __init__.py        <- Makes src a module
│   ├── config.py          <- Configuration variables
│   ├── constants.py       <- Project constants
│   ├── llm.py             <- LLM-related logic
│   ├── main.py            <- Entry point script
│   ├── prompts.py         <- Prompt templates
│   └── utils.py           <- Utility functions
│
├── .env                   <- Environment variables
├── .env.example           <- Example env file
├── .gitignore             <- Git ignore rules
├── LICENSE                <- License information
├── meetings.md            <- Meeting notes
└── weekly_report.md       <- Weekly updates
```

---

## 🚀 Usage

Run the main script:

```bash
python -m streamlit run src/main.py
```