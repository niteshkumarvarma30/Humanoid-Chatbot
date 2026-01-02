from typing import TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langsmith import traceable

# ---------------- STATE ----------------

class AgentState(TypedDict):
    user_id: str
    thread_id: str
    user_input: str
    messages: List[BaseMessage]
    emotion: str
    intensity: float
    query_embedding: list
    retrieved_memories: str


# ---------------- IMPORTS ----------------

from app.llm import llm
from app.intelligence import detect_emotion, embed_text
from app.memory import retrieve_memories
from app.prompt import build_prompt


# ---------------- NODE ----------------

@traceable(
    name="cognitive_node",
    run_type="chain"
)
def cognitive_node(state: AgentState):
    emotion, intensity = detect_emotion(state["user_input"])
    embedding = embed_text(state["user_input"])

    memories = retrieve_memories(
        state["thread_id"],
        embedding,
    )

    prompt = build_prompt(
        state["user_input"],
        "\n\n".join(memories),
    )

    ai_msg = llm([HumanMessage(content=prompt)])

    return {
        "messages": [ai_msg],
        "emotion": emotion,
        "intensity": intensity,
        "query_embedding": embedding,
        "retrieved_memories": "\n\n".join(memories),
    }


# ---------------- GRAPH ----------------

graph = StateGraph(AgentState)
graph.add_node("cognition", cognitive_node)
graph.set_entry_point("cognition")
graph.add_edge("cognition", END)

agent_graph = graph.compile()
