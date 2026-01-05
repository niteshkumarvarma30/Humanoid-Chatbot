from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import asyncio

from langchain_core.messages import AIMessage

from app.graph_agent import agent_graph
from app.memory import (
    ensure_thread,
    store_message,
    store_episodic_memory,
    build_conversation_memory,
    load_history,
)

app = FastAPI()


# ---------------- HEALTH (REQUIRED FOR RENDER) ----------------

@app.get("/")
def health():
    return {"status": "ok"}


# ---------------- CHAT HISTORY ----------------

@app.get("/chat/history")
def get_history(thread_id: str):
    """
    Load full chat history for a thread.
    Always return a list (never 404).
    """
    return load_history(thread_id)


# ---------------- STREAM CHAT ----------------

@app.post("/chat/stream")
async def chat_stream(req: Request):
    body = await req.json()

    user_id = body["user_id"]
    thread_id = body["thread_id"]
    user_input = body["message"]

    # Ensure thread exists
    ensure_thread(thread_id, user_id)

    # Store user message immediately
    store_message(thread_id, "user", user_input)

    inputs = {
        "user_id": user_id,
        "thread_id": thread_id,
        "user_input": user_input,
        "messages": [],
    }

    async def event_generator():
        """
        Gemini does NOT stream tokens.
        We invoke LangGraph once, then simulate token streaming.
        """
        full_response = ""

        # ---- Run LangGraph (single call) ----
        result = agent_graph.invoke(inputs)

        ai_msg: AIMessage = result["messages"][-1]
        text: str = ai_msg.content.strip()

        # ---- Simulated streaming (word-level) ----
        for word in text.split():
            full_response += word + " "
            yield f"data: {word} \n\n"
            await asyncio.sleep(0.03)

        full_response = full_response.strip()

        # ---- Persist assistant message ----
        store_message(thread_id, "assistant", full_response)

        # ---- Store episodic memory ----
        store_episodic_memory(
            thread_id=thread_id,
            user_id=user_id,
            memory_text=build_conversation_memory(user_input, full_response),
            emotion=result.get("emotion", "neutral"),
            intensity=result.get("intensity", 0.4),
        )

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
