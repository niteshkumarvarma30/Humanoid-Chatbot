import google.generativeai as genai

from langchain_core.messages import AIMessage, HumanMessage
from langsmith import traceable
from typing import List

model = genai.GenerativeModel("gemini-flash-latest")


@traceable(
    name="gemini_llm_call",
    run_type="llm"
)
def llm(messages: List[HumanMessage]) -> AIMessage:
    prompt = "\n\n".join(m.content for m in messages)

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 1024,
        },
    )

    return AIMessage(content=response.text.strip())
