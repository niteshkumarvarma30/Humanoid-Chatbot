from datetime import datetime
from typing import List, Optional
from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_KEY
from app.intelligence import embed_text

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def ensure_thread(thread_id: str, user_id: str):
    if not supabase.table("threads").select("thread_id").eq(
        "thread_id", thread_id
    ).execute().data:
        supabase.table("threads").insert({
            "thread_id": thread_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()


def store_message(thread_id: str, role: str, content: str):
    supabase.table("messages").insert({
        "thread_id": thread_id,
        "role": role,
        "content": content,
        "metadata": {},
        "created_at": datetime.utcnow().isoformat(),
    }).execute()


def build_conversation_memory(user: str, assistant: str) -> str:
    return f"User said:\n{user}\n\nAssistant replied:\n{assistant}"


def store_episodic_memory(*, thread_id, user_id, memory_text, emotion, intensity):
    embedding = embed_text(memory_text)
    supabase.table("memories").insert({
        "thread_id": thread_id,
        "user_id": user_id,
        "role": "conversation",
        "content": memory_text,
        "embedding": embedding,
        "metadata": {
            "emotion": emotion,
            "intensity": intensity,
            "retrieval_count": 0,
        },
        "created_at": datetime.utcnow().isoformat(),
    }).execute()


def retrieve_memories(
    thread_id: str,
    query_embedding: Optional[List[float]],
    k: int = 5,
) -> List[str]:
    if not query_embedding:
        return []

    res = supabase.rpc("match_memories", {
        "query_embedding": query_embedding,
        "match_count": k,
        "thread_id": thread_id,
    }).execute()

    return [r["content"] for r in (res.data or [])]


def load_history(thread_id: str):
    res = (
        supabase
        .table("messages")
        .select("role, content")
        .eq("thread_id", thread_id)
        .order("created_at")
        .execute()
    )
    return res.data or []
