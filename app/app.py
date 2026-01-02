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


# ---------------- HISTORY ----------------

@app.get("/chat/history")
def get_history(thread_id: str):
    return load_history(thread_id)


# ---------------- STREAM ----------------

@app.post("/chat/stream")
async def chat_stream(req: Request):
    body = await req.json()
    user_id = body["user_id"]
    thread_id = body["thread_id"]
    user_input = body["message"]

    ensure_thread(thread_id, user_id)
    store_message(thread_id, "user", user_input)

    inputs = {
        "user_id": user_id,
        "thread_id": thread_id,
        "user_input": user_input,
        "messages": [],
    }

    async def event_generator():
        full_response = ""

        # Run LangGraph once (Gemini does not stream)
        result = agent_graph.invoke(inputs)
        ai_msg: AIMessage = result["messages"][-1]
        text = ai_msg.content

        # Simulated streaming
        for token in text.split(" "):
            full_response += token + " "
            yield f"data: {token} \n\n"
            await asyncio.sleep(0.03)

        store_message(thread_id, "assistant", full_response.strip())

        store_episodic_memory(
            thread_id=thread_id,
            user_id=user_id,
            memory_text=build_conversation_memory(user_input, full_response),
            emotion=result.get("emotion", "neutral"),
            intensity=result.get("intensity", 0.4),
        )

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
