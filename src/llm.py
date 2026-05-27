import json
import re
import time
from google import genai
from src.config import settings
from src import prompts

client = genai.Client(api_key=settings.API_KEY)

def call_gemini_api(prompt: str, retries=3):
    """
    Crash-proof API caller. Attempts the prompt up to 3 times with exponential backoff.
    If all retries fail, returns a safe fallback string instead of crashing Streamlit.
    """
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL_NAME,
                contents=[{"role": "user", "parts": [{"text": prompt}]}]
            )
            return response.text
        except Exception as e:
            err_str = str(e)
            # If we haven't exhausted our retries, wait and try again
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Sleeps for 1s, then 2s
                continue
            # If all retries fail, return a safe string so the app continues running
            return "⚠️ AI Service temporarily unavailable due to high server load. Please try again."

def classify_school_intent(user_input: str):
    prompt = prompts.make_school_classify_prompt(user_input=user_input)
    llm_text = call_gemini_api(prompt)
    try:
        clean_json = re.sub(r'```json|```', '', llm_text).strip()
        data = json.loads(clean_json)
        return data, data.get("intent", "other")
    except:
        return {"intent": "other", "school_name": None, "udisecode": None, "username": None}, "other"

def classify_village_intent(user_input: str) -> dict:
    prompt = prompts.make_classify_prompt(user_input)
    response = call_gemini_api(prompt)
    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        return json.loads(match.group(0)) if match else {"intent": "other", "village_names": []}
    except:
        return {"intent": "other", "village_names": []}

def llm_reply(user_input: str, intent: str) -> str:
    prompt = prompts.make_conversational_prompt(user_input, intent)
    return call_gemini_api(prompt)

def rephrase_remark(text: str) -> str:
    return re.sub(r"^\s*Output:?[\s\n]*", "", call_gemini_api(prompts.make_rephrase_prompt(text))).strip()

def improvment_suggestion(text: str) -> str:
    return call_gemini_api(prompts.make_suggestions(text)).strip()

def analyze_village_data(village_data, lang: str = 'en') -> str:
    if isinstance(village_data, list) and len(village_data) == 2:
        prompt = prompts.VILLAGE_COMPARISON_PROMPT.format(
            v1_name=village_data[0].get('village_name', 'V1'), v1_data=json.dumps(village_data[0], default=str),
            v2_name=village_data[1].get('village_name', 'V2'), v2_data=json.dumps(village_data[1], default=str)
        )
    else:
        v_data = village_data[0] if isinstance(village_data, list) else village_data
        prompt = prompts.VILLAGE_ANALYSIS_PROMPT.format(village_data=json.dumps(v_data, default=str))
    
    if lang == 'pa': 
        prompt += "\n\nIMPORTANT: Provide response entirely in Punjabi."
        
    return call_gemini_api(prompt)