from config import LLM_PROVIDER

if LLM_PROVIDER == "groq":
    from ai_engine.groq import get_ai_response
else:
    from ai_engine.gemini import get_ai_response