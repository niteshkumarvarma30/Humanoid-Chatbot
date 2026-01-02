from datetime import datetime
from app.supabase_client import supabase

CONFIDENCE_INCREMENT = 0.05
CONFIDENCE_DECAY = 0.995
MAX_CONFIDENCE = 0.95
MIN_ACTIVE_CONFIDENCE = 0.3


def _update_confidence(confidence: float, strength: float) -> float:
    return min(MAX_CONFIDENCE, confidence + CONFIDENCE_INCREMENT * strength)


def infer_belief_from_summary(summary: str) -> str | None:
    """
    Extract a stable, long-term belief from a semantic memory summary.
    This is intentionally conservative.
    """
    s = summary.lower()

    if "overwhelm" in s or "lost" in s:
        return "User struggles with emotional overwhelm under stress"

    if "reassurance" in s or "support" in s:
        return "User seeks reassurance during difficult moments"

    if "control" in s:
        return "User feels loss of control during challenges"

    return None


def upsert_belief(
    *,
    user_id: str,
    belief_text: str,
    evidence_strength: float,
):
    """
    Reinforce or create a belief based on new evidence.
    """
    existing = (
        supabase
        .table("beliefs")
        .select("*")
        .eq("user_id", user_id)
        .eq("belief", belief_text)
        .execute()
    )

    now = datetime.utcnow().isoformat()

    if existing.data:
        belief = existing.data[0]
        new_conf = _update_confidence(
            belief["confidence"], evidence_strength
        )

        supabase.table("beliefs").update({
            "confidence": round(new_conf, 3),
            "evidence_count": belief["evidence_count"] + 1,
            "last_updated": now,
        }).eq("id", belief["id"]).execute()

    else:
        supabase.table("beliefs").insert({
            "user_id": user_id,
            "belief": belief_text,
            "confidence": round(0.4 + evidence_strength * 0.3, 2),
            "evidence_count": 1,
            "last_updated": now,
        }).execute()


def decay_beliefs(user_id: str):
    """
    Gradually decay belief confidence over time.
    """
    res = (
        supabase
        .table("beliefs")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    for b in res.data or []:
        new_conf = b["confidence"] * CONFIDENCE_DECAY

        if new_conf < MIN_ACTIVE_CONFIDENCE:
            continue

        supabase.table("beliefs").update({
            "confidence": round(new_conf, 3),
            "last_updated": datetime.utcnow().isoformat(),
        }).eq("id", b["id"]).execute()


def get_active_beliefs(user_id: str, limit: int = 5) -> list[str]:
    """
    Retrieve top active beliefs for prompting or inspection.
    """
    res = (
        supabase
        .table("beliefs")
        .select("belief, confidence")
        .eq("user_id", user_id)
        .order("confidence", desc=True)
        .limit(limit)
        .execute()
    )

    return [
        f"{b['belief']} (confidence {round(b['confidence'], 2)})"
        for b in (res.data or [])
    ]
