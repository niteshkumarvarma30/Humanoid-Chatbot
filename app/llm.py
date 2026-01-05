import os
from typing import List

import google.generativeai as genai
from langchain_core.messages import AIMessage, HumanMessage
from langsmith import traceable

# ---------------- CONFIG ----------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-flash-latest")


# ---------------- LLM CALL ----------------

@traceable(
    name="gemini_llm_call",
    run_type="llm",
)
def llm(messages: List[HumanMessage]) -> AIMessage:
    """
    Gemini does not support token streaming.
    This function performs a single-shot generation
    and returns a LangChain-compatible AIMessage.
    """
    prompt = "\n\n".join(m.content for m in messages)

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 1024,
        },
    )

    text = response.text.strip() if response.text else ""

    return AIMessage(content=text)
