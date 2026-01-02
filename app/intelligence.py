import requests
from typing import Optional, Tuple
from langsmith import traceable
from app.config import JINA_API_KEY

JINA_URL = "https://api.jina.ai/v1/embeddings"


@traceable(
    name="emotion_detection",
    run_type="tool"
)
def detect_emotion(text: str) -> Tuple[str, float]:
    t = text.lower()
    if any(w in t for w in ["lost", "empty", "hopeless"]):
        return "distress", 0.8
    if any(w in t for w in ["happy", "excited"]):
        return "positive", 0.6
    return "neutral", 0.4


@traceable(
    name="jina_embedding",
    run_type="tool"
)
def embed_text(text: str) -> Optional[list]:
    payload = {
        "model": "jina-embeddings-v2-base-en",
        "input": text.strip(),
    }

    r = requests.post(
        JINA_URL,
        headers={"Authorization": f"Bearer {JINA_API_KEY}"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()

    return r.json()["data"][0]["embedding"]
