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
            "temperature": 0.6,
            "max_output_tokens": 180,
        },
    )

    text = ""

    #  SAFE Gemini extraction (no response.text)
    if response.candidates:
        candidate = response.candidates[0]
        if candidate.content and candidate.content.parts:
            text = candidate.content.parts[0].text or ""

    # Fallback if Gemini blocks or returns empty output
    if not text.strip():
        text = (
            "Let us pause for a moment—clarity often emerges "
            "when we simplify the question to its essence."
        )

    return AIMessage(content=text.strip())
