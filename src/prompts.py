import textwrap

WELCOME_PROMPT = "Welcome to the Village Status Report Generator. How can I assist you today?"

def make_nofound_message(user_input: str) -> str:
    return f"Sorry, I couldn't find a village named '{user_input}'. Please check the spelling."

def make_classify_prompt(user_input: str) -> str:
    return textwrap.dedent(f"""
            You are a village status report assistant.
            Classify the user's intent as one of:
            - status_report: User wants a village's status report. Extract village_name. 
              (CRITICAL: If the user simply types a standalone noun or location name like "baluana", treat it as a status_report intent).
            - salutation: Greeting, thanks, or polite courtesies.
            - help_request: Asking how you can help or asking about your scope.
            - other: Something else.

            Return ONLY a raw, valid JSON dictionary. Do not include markdown blocks (```json) and do not include conversational text.
            Schema: {{"intent": "status_report|salutation|help_request|other", "village_name": "extracted_name_or_null"}}
            
            --- EXAMPLES ---
            User message: "show me baluana" 
            {{"intent": "status_report", "village_name": "baluana"}}
            
            User message: "bangi nehal singh" 
            {{"intent": "status_report", "village_name": "bangi nehal singh"}}
            
            User message: "hi there" 
            {{"intent": "salutation", "village_name": null}}
            
            User message: "what do you do?" 
            {{"intent": "help_request", "village_name": null}}
            ----------------
            
            User message: {user_input}
            """).strip()

def make_suggestions(text: str) -> str:
    return textwrap.dedent(f"""
                You are a Rural Development Specialist.
                Provide a single sentence, clear, actionable suggestion for this village metric:
                ```{text}```
                Output ONLY the suggestion. No formatting, no extra text.
                """).strip()


VILLAGE_ANALYSIS_PROMPT = """
You are an expert rural development analyst. Analyze the following village data and provide a structured evaluation.

Village Data:
{village_data}

Please provide exactly three sections:
1. **Key Insights:** 3-4 bullet points highlighting the most notable positive and negative aspects from the data.
2. **Recommended Solutions:** 2-3 highly actionable, practical solutions addressing the specific areas that need the most improvement based on the data.
3. **Conclusion:** A brief summary explicitly stating which domains the village is performing well in, and which domains require immediate focus.

Format the output clearly using Markdown. Be objective, precise, and base your analysis strictly on the provided data.
"""

VILLAGE_COMPARISON_PROMPT = """
You are an expert rural development analyst. Compare the following two villages based on their data.

Village 1 Data ({v1_name}):
{v1_data}

Village 2 Data ({v2_name}):
{v2_data}

Please provide exactly three sections:
1. **Head-to-Head Comparison:** 3-4 bullet points comparing their performance across major domains (Sanitation, Governance, Water Security, Employment). Explicitly highlight who is outperforming the other and cite the specific scores.
2. **Shared Weaknesses:** 1-2 bullet points identifying areas where BOTH villages are struggling and could benefit from a shared block-level intervention.
3. **Strategic Conclusion:** A brief summary determining which village requires more immediate administrative attention and funding based on the data.

Format the output clearly using Markdown. Be objective, precise, and base your analysis strictly on the provided data.
"""