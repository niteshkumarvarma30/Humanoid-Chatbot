from typing import TypedDict, List
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    user_id: str
    thread_id: str
    user_input: str
    messages: List[BaseMessage]
    emotion: str
    intensity: float
    query_embedding: list | None
    retrieved_memories: str
