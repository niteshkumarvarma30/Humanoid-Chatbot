import requests
import streamlit as st

BACKEND_URL = "https://humanoid-chatbot.onrender.com"

st.set_page_config(
    page_title="Humanoid Memory Agent",
    layout="centered",
)

# ---------------- User Inputs ----------------
user_id = st.text_input("User ID")
thread_id = st.text_input("Thread ID")

if not user_id or not thread_id:
    st.stop()

# ---------------- Conversation Identity ----------------
conversation_key = f"{user_id}:{thread_id}"

# Reset state when conversation changes OR app reloads
if "conversation_key" not in st.session_state:
    st.session_state.conversation_key = conversation_key
    st.session_state.messages = []
    st.session_state.history_loaded = False

if st.session_state.conversation_key != conversation_key:
    st.session_state.conversation_key = conversation_key
    st.session_state.messages = []
    st.session_state.history_loaded = False

# ---------------- Load History (ALWAYS SAFE) ----------------
if not st.session_state.history_loaded:
    try:
        r = requests.get(
            f"{BACKEND_URL}/chat/history",
            params={"thread_id": thread_id},
            timeout=10,
        )
        st.session_state.messages = r.json() if r.status_code == 200 else []
    except Exception:
        st.session_state.messages = []

    st.session_state.history_loaded = True

# ---------------- Render History ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- User Input ----------------
user_input = st.chat_input("Type your message")
if not user_input:
    st.stop()

# Persist + render user message

with st.chat_message("user"):
    st.markdown(user_input)

# ---------------- Stream Assistant Response ----------------
payload = {
    "user_id": user_id,
    "thread_id": thread_id,
    "message": user_input,
}

with st.chat_message("assistant"):
    thinking = st.empty()
    thinking.markdown("_Agent is thinking…_")

    stream_box = st.empty()
    full_text = ""

    try:
        with requests.post(
            f"{BACKEND_URL}/chat/stream",
            json=payload,
            stream=True,
            timeout=120,
        ) as r:
            for line in r.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue

                token = line.replace("data: ", "")

                if token == "[DONE]":
                    break

                thinking.empty()
                full_text += token
                stream_box.markdown(full_text + "▌")

    except Exception as e:
        thinking.empty()
        st.error(f"Connection error: {e}")
        st.stop()

    stream_box.markdown(full_text)

# ---------------- Persist Assistant Message ----------------
st.session_state.messages.append(
    {"role": "assistant", "content": full_text}
)
