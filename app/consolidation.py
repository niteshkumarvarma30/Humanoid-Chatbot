from app.supabase_client import supabase
from app.intelligence import embed_text
from app.llm import llm
from app.beliefs import infer_belief_from_summary, upsert_belief

CONSOLIDATION_THRESHOLD = 3
MIN_CONTENT_LENGTH = 100


def run_consolidation(user_id: str):
    """
    Phase-3 consolidation:
    - Identify reinforced episodic memories
    - Create semantic memory (summary)
    - Infer long-term belief
    """

    # 1️⃣ Fetch episodic memories
    res = (
        supabase
        .table("memories")
        .select("id, content, metadata")
        .eq("user_id", user_id)
        .execute()
    )

    memories = res.data or []
    if not memories:
        return

    # 2️⃣ Filter recurrent, meaningful memories
    recurrent = []
    for m in memories:
        metadata = m.get("metadata") or {}
        retrieval_count = metadata.get("retrieval_count", 0)
        content = m.get("content", "")

        if (
            retrieval_count >= CONSOLIDATION_THRESHOLD
            and "Assistant replied" in content
            and len(content) >= MIN_CONTENT_LENGTH
        ):
            recurrent.append(m)

    if not recurrent:
        return

    # 3️⃣ Prevent duplicate consolidation
    latest_summary = (
        supabase
        .table("memory_summaries")
        .select("id")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
    )

    if latest_summary:
        return  # Already consolidated recently

    # 4️⃣ Build consolidation prompt
    joined_text = "\n\n".join(m["content"] for m in recurrent)

    prompt = f"""
Summarize the recurring emotional and cognitive patterns in the following experiences.
Avoid dialogue, names, or advice.
Write ONE neutral psychological insight.

Experiences:
{joined_text}

Insight:
""".strip()

    # 5️⃣ Generate semantic summary
    summary = llm(prompt).strip()
    if not summary:
        return

    # 6️⃣ Embed and store semantic memory
    embedding = embed_text(summary)

    supabase.table("memory_summaries").insert({
        "user_id": user_id,
        "summary": summary,
        "confidence": 0.7,
        "embedding": embedding,
    }).execute()

    # 7️⃣ Infer belief (Phase-3)
    belief_text = infer_belief_from_summary(summary)

    if belief_text:
        upsert_belief(
            user_id=user_id,
            belief_text=belief_text,
            evidence_strength=0.8,
        )
