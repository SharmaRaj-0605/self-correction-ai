import os
import requests
import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Self-Correcting AI",
    layout="wide",
)

st.title("Self-Correcting Multi-Agent AI")
st.caption("Planner → Researcher → Analyst → Synthesizer → Critic → Fact Checker → Judge → Correction")

prompt = st.text_area(
    "What do you want the agents to work on?",
    height=150,
    placeholder="Example: Compare REST APIs and GraphQL for a college project.",
)

run = st.button("Run agents", type="primary")

if run:
    if not prompt.strip():
        st.warning("Enter a task first.")
        st.stop()

    with st.spinner("The agents are working..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/tasks",
                json={"prompt": prompt},
                timeout=900,
            )
        except requests.RequestException as exc:
            st.error(f"Could not reach the backend: {exc}")
            st.stop()

    if response.status_code != 200:
        st.error(response.text)
        st.stop()

    data = response.json()

    if data["cached"]:
        st.info("This request was served from cache.")

    left, right = st.columns(2)
    with left:
        st.metric("Quality score", f"{data['score']:.1f}/10")
    with right:
        st.metric("Correction rounds", data["iterations"])

    st.subheader("Agent activity")

    for log in data["logs"]:
        icon = "✓" if log["status"] in {"completed", "approved"} else "↻"
        st.write(f"{icon} **{log['agent']}** — {log['summary']}")

    st.subheader("Final answer")
    st.markdown(data["answer"])

    with st.expander("Task ID"):
        st.code(data["task_id"])
