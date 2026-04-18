import json
import ast
# from ollama import chat
import re
from src import prompts
from config import settings
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

client = genai.Client(api_key=settings.API_KEY)

@retry(
    retry=retry_if_exception_type(genai.errors.ClientError),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5)
)
def call_gemini_api(prompt: str):
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL_NAME,
            contents=[
                {
                    "role": "user", 
                    "parts": [{"text": prompt}]
                }
            ]
        )
        return response.text
    except genai.errors.ClientError as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print(f"Quota hit... retrying safely.")
            raise e 
        else:
            return (f"Permanent Error: {e}")
def classify_and_extract(user_input: str):
    prompt = prompts.make_classify_prompt(user_input = user_input)
    
    # llm_text = chat(model=settings.MODEL_NAME, messages=[{"role": "user", "content": prompt}]).message["content"]
    llm_text = call_gemini_api(prompt)
    try:
        data = json.loads(llm_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*?\}", llm_text, re.DOTALL)
        if match:
            json_str = match.group()
            try:
                data = json.loads(json_str) 
            except json.JSONDecodeError:
                try:
                    data = ast.literal_eval(json_str)
                except (ValueError, SyntaxError):
                    data = {"category": "other"}  
        else:
            data = {"category": "other"}

    # fill in missing keys safely
    data = {**{"category": "other", "username": None, "school_name": None, "udisecode": None}, **data}

    extracted = {
        "username": data.get("username"),
        "school_name": data.get("school_name"),
        "udisecode": data.get("udisecode"),
    }
    category = data.get("category", "other")

    return extracted, category

def llm_reply(user_input: str, intent: str) -> str:
    if intent == "help_request":
        prompt = prompts.make_help_prompt(user_input=user_input)

    elif intent == "salutation":
        prompt = prompts.make_salutation_prompt(user_input=user_input)
       
    elif intent == "status_report":
        prompt = prompts.make_report_prompt(user_input=user_input)

    else:
        # All other questions: fallback, concise, polite error
        if re.match(r"^\s*(yes|ok|okay|sure|yep|yeah)\b", user_input.strip(), re.I):
            return "Sorry, I didn’t catch your intent. Could you please clarify or provide a school name or UDISE code?"
        prompt = prompts.make_fallback_prompt(user_input=user_input)

    # response = chat(model=settings.MODEL_NAME, messages=[{"role": "user", "content": prompt}], options={"temperature": settings.MODEL_TEMP}).message["content"].strip()
    response = call_gemini_api(prompt)

    return response
 
def rephrase_remark(text: str, max_retries: int = settings.MAX_REPHRASE_RETRIES) -> str:
    """
    Ask the LLM to rephrase `remark` into a short sentence.
    """
    paraphrase_prompt = prompts.make_rephrase_prompt(text= text)

    for attempt in range(max_retries):
        try:
            # rephrased = chat(
            #     model=settings.MODEL_NAME,
            #     messages=[{"role": "user", "content": paraphrase_prompt}],
            #     options={"temperature": settings.MODEL_TEMP}
            # ).message["content"].strip()
            rephrased = call_gemini_api(paraphrase_prompt)
        except Exception:
            return text

        # Remove "Here is...", “Rephrased message:” , “Output:” or similar LLM wrappers
        cleaned = re.sub(r"^\s*Here\s(is|’s|’re| are).*?:\s*", "", rephrased, flags=re.I)
        cleaned = re.sub(r"^\s*Rephrased message:?[\s\n]*", "", cleaned, flags=re.I)
        cleaned = re.sub(r"^\s*Output:?[\s\n]*", "", cleaned, flags=re.I)

        return cleaned.strip() if cleaned.strip() else text
    
def improvment_suggestion(text: str) -> str:
    improvment_prompt = prompts.make_suggestions(text = text)

    # suggestion = chat(
    #     model = settings.MODEL_NAME,
    #     messages=[{"role": "user", "content": improvment_prompt}],
    #     options={"temperature": settings.MODEL_TEMP}
    # ).message["content"].strip()
    suggestion = call_gemini_api(improvment_prompt)

    cleaned_suggestion = re.sub(r"^\s*Here\s(is|’s|’re| are).*?:\s*", "", suggestion, flags=re.I)
    cleaned_suggestion = re.sub(r"^\s*improvement\s(message|suggestion):?[\s\n]*", "", cleaned_suggestion, flags=re.I)
    cleaned_suggestion = re.sub(r"^\s*Output:?[\s\n]*", "", cleaned_suggestion, flags=re.I)

    return cleaned_suggestion
