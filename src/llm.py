import json
import re
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import settings
from src import prompts

client = genai.Client(api_key=settings.API_KEY)

from tenacity import retry, stop_after_attempt, wait_exponential

# This tells Python: "Try 4 times. Wait 2 seconds, then 4 seconds, then 8 seconds between tries."
@retry(
    stop=stop_after_attempt(4), 
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)

def call_gemini_api(prompt: str):
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL_NAME,
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )
        return response.text
    except genai.errors.ClientError as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("Quota hit... retrying safely.")
            raise e 
        return f"Permanent Error: {e}"

def classify_and_extract(user_input: str) -> dict:
    prompt = prompts.make_classify_prompt(user_input)
    response = call_gemini_api(prompt)
    
    # ⬅️ NEW: Catch API-level errors before trying to parse JSON
    if response.startswith("Permanent Error"):
        print(f"API Connection Failed: {response}")
        # Return 'other' so the app doesn't crash, but you see it in the terminal
        return {"intent": "other", "village_name": None} 
    
    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            clean_json = match.group(0)
            return json.loads(clean_json)
        else:
            print(f"Failed to find JSON braces in response: {response}")
            return {"intent": "other", "village_name": None}
            
    except json.JSONDecodeError as e:
        print(f"JSON Parsing Error: {e}. Raw response was: {response}")
        return {"intent": "other", "village_name": None}

def improvment_suggestion(text: str) -> str:
    prompt = prompts.make_suggestions(text)
    suggestion = call_gemini_api(prompt)
    return suggestion.strip()

def analyze_village_data(village_data, lang: str = 'en') -> str:
    """Passes single or multiple village datasets to Gemini to generate insights."""
    
    # --- Check if we are in Comparison Mode ---
    if isinstance(village_data, list) and len(village_data) == 2:
        v1, v2 = village_data
        v1_str = json.dumps(v1, indent=2, default=str)
        v2_str = json.dumps(v2, indent=2, default=str)
        
        prompt = prompts.VILLAGE_COMPARISON_PROMPT.format(
            v1_name=v1.get('village_name', 'Village 1'), v1_data=v1_str,
            v2_name=v2.get('village_name', 'Village 2'), v2_data=v2_str
        )
    # --- Otherwise, Single Village Mode ---
    else:
        # Just in case a single village gets passed as a 1-item list
        if isinstance(village_data, list):
            village_data = village_data[0]
            
        data_str = json.dumps(village_data, indent=2, default=str)
        prompt = prompts.VILLAGE_ANALYSIS_PROMPT.format(village_data=data_str)
    
    # Handle Translation
    if lang == 'pa':
        prompt += "\n\nIMPORTANT: Please provide your entire response in the Punjabi language."
        
    try:
        response = call_gemini_api(prompt) 
        return response
    except Exception as e:
        return f"⚠️ Could not generate insights at this time. Error: {e}"