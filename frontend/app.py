"""Streamlit chat UI for the Cybersecurity Guidelines Assistant."""
import streamlit as st

import api_client

st.set_page_config(page_title="Cybersecurity Guidelines Assistant", page_icon="🛡️")

EXAMPLES = [
    "What are the core functions of the NIST Cybersecurity Framework?",
    "What are the main phases of the incident response lifecycle?",
    "What is the difference between clearing, purging, and destroying media?",
    "What are the steps of a risk assessment?",
]

# ---------- sidebar ----------
with st.sidebar:
    st.header("About")
    st.write(
        "Ask questions about official NIST cybersecurity publications. "
        "Answers are generated only from the retrieved passages and cite their source."
    )
    health = api_client.check_health()
    if health:
        st.success(f"Backend online - {health.get('chunks', 0)} chunks indexed")
    else:
        st.error("Backend offline")
    st.subheader("Try an example")
    for example in EXAMPLES:
        if st.button(example, use_container_width=True):
            st.session_state["pending"] = example
    if st.button("Clear chat"):
        st.session_state["messages"] = []
        st.rerun()
    st.caption("For information only. Verify important details in the original documents.")

# ---------- chat ----------
st.title("🛡️ Cybersecurity Guidelines Assistant")

if "messages" not in st.session_state:
    st.session_state["messages"] = []


def render_sources(sources: list[str]) -> None:
    if sources:
        with st.expander(f"Sources ({len(sources)})"):
            for s in sources:
                st.markdown(f"- {s}")


for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            render_sources(msg.get("sources", []))

question = st.chat_input("Ask a question about the documents...")
if not question and st.session_state.get("pending"):
    question = st.session_state.pop("pending")

if question:
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching the documents and generating an answer..."):
                result = api_client.ask(question)
            st.markdown(result["answer"])
            render_sources(result.get("sources", []))
            st.session_state["messages"].append(
                {"role": "assistant", "content": result["answer"], "sources": result.get("sources", [])}
            )
        except api_client.ApiError as exc:
            st.error(f"Sorry, something went wrong: {exc}")
