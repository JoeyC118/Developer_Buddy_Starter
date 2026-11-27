"""The Complex Time Saver - Streamlit front end (wise Sage, fireplace-study theme).

Run from the project folder:
    python -m streamlit run agent/frontend/app.py
"""
import os
import sys
from pathlib import Path

import streamlit as st

# On Streamlit Community Cloud the key lives in the app's Secrets settings.
# Hand it to the agent through the environment if it isn't there already.
try:
    if not os.environ.get("ANTHROPIC_API_KEY") and "ANTHROPIC_API_KEY" in st.secrets:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    pass  # no secrets configured: the agent shows a friendly "no API key" message

FRONTEND_DIR = Path(__file__).resolve().parent
AGENT_DIR = FRONTEND_DIR.parent
sys.path.insert(0, str(AGENT_DIR))      # for buddy_agent.py
sys.path.insert(0, str(FRONTEND_DIR))   # for sage.py

import buddy_agent  # noqa: E402
from sage import sage_html  # noqa: E402

DEFAULT_TASK = "Investigate this program and explain the most important result to a beginner."
CASES = ["calculator", "task_counter", "average"]
CASE_LABELS = {
    "calculator": "calculator",
    "task_counter": "task_counter",
    "average": "average (optional extra)",
}
GLOSSARY = """
- **Test**: a small program that checks one thing, e.g. "given 7 and 2, divide should return 3.5".
- **pytest**: the tool that runs the tests and reports which passed or failed.
- **assert**: the line in a test that compares the actual result with the expected one.
- **Passed / not passed**: whether every supplied test succeeded. Passing tests are evidence, not proof the code is perfect.
- **Exit code**: a number pytest returns. 0 means all tests passed; anything else means they did not.
- **Time complexity (Big-O)**: how the running time grows as the input grows.
- **O(1)**: constant time; the same amount of work no matter the input size.
- **O(n)**: linear time; the work grows in step with the number of items.
- **Refactoring**: changing how code is written without changing what it does.
"""

st.set_page_config(page_title="The Complex Time Saver", page_icon="🧐", layout="wide")

# Load the theme. Blank lines are removed so the CSS reaches the page intact.
_css = (FRONTEND_DIR / "style.css").read_text(encoding="utf-8")
st.markdown("<style>" + "\n".join(ln for ln in _css.splitlines() if ln.strip()) + "</style>",
            unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
if "task" not in st.session_state:
    st.session_state.task = DEFAULT_TASK
if "result" not in st.session_state:
    st.session_state.result = None


def reset():
    st.session_state.result = None
    st.session_state.task = DEFAULT_TASK
    st.session_state.case = CASES[0]


def clear_result():
    # A new case must never show the previous case's evidence.
    st.session_state.result = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def last_ok(result, tool_name):
    """The most recent successful raw result from a tool in this run, or None."""
    for step in reversed(result.get("trace", [])):
        raw = step.get("raw_result")
        if step["action"].startswith(tool_name + "(") and raw and "error" not in raw:
            return raw
    return None


def mood_for(result):
    if result is None:
        return "welcome"
    if result.get("error"):
        return "troubled"
    checks = last_ok(result, "run_checks")
    if not checks:
        return "troubled"
    return {"passed": "pleased", "not_passed": "concerned"}.get(checks.get("status"), "troubled")


def output_excerpt(output, max_lines=12):
    lines = [ln for ln in output.strip().splitlines() if ln.strip()]
    return "\n".join(lines[-max_lines:]) or "(no output)"


STATUS_TEXT = {
    "passed": "✅ All supplied tests passed",
    "not_passed": "❌ Some supplied tests did not pass",
    "timeout": "⏳ The tests timed out: this is neither a pass nor a confirmed bug",
}
STEP_ICONS = {"inspect_case": "🔍", "run_checks": "🧪", "final": "🕯️"}


PANEL_HEIGHT = 430  # px; long content scrolls inside its panel, never the page


def render_result(result):
    if result is None:
        with st.container(key="awaiting", height=PANEL_HEIGHT + 48):
            st.markdown("*The study is quiet. Choose a program, write your request, "
                        "and press **Run my buddy** to hear the Sage's findings.*")
        return

    if result.get("error"):
        st.error(f"**The Sage could not finish.** {result['error']}")

    tab_counsel, tab_evidence, tab_journal = st.tabs(
        ["🕯️ The Sage's counsel", "🔎 Observed evidence", "📜 The Sage's journal"])

    # 1. Journal: the activity trace
    with tab_journal, st.container(key="journal", height=PANEL_HEIGHT):
        if not result.get("trace"):
            st.markdown("*No steps were taken.*")
        else:
            st.caption("What the buddy chose to do, why, what came back, and what happened next.")
            for i, step in enumerate(result["trace"], 1):
                icon = next((v for k, v in STEP_ICONS.items() if step["action"].startswith(k)), "•")
                st.markdown(
                    f"**{i}. {icon} {step['action']}**  \n"
                    f"*Why:* {step['reason']}  \n"
                    f"*Result:* {step['result']}  \n"
                    f"*Next:* {step['next']}"
                )
            st.caption(f"{result['model_calls']} model calls (limit {buddy_agent.MAX_MODEL_CALLS}) · "
                       f"{result['tool_calls']} tool runs (limit {buddy_agent.MAX_TOOL_CALLS}) · "
                       f"model: {result['model']}")

    # 2. Observed evidence: straight from the tools, not the AI
    inspect = last_ok(result, "inspect_case")
    checks = last_ok(result, "run_checks")
    with tab_evidence, st.container(key="evidence", height=PANEL_HEIGHT):
        st.caption("Taken directly from the tools: the written requirements and the real test run. "
                   "This is not the AI's opinion.")
        st.markdown(f"**Case:** `{result['case_id']}`")
        if inspect:
            st.markdown("**Written requirements:**\n" + "\n".join(f"- {r}" for r in inspect["requirements"]))
        if checks:
            st.markdown(f"**Test status:** {STATUS_TEXT.get(checks['status'], checks['status'])}"
                        + (f" (exit code {checks['exit_code']})" if "exit_code" in checks else ""))
            if checks.get("command"):
                st.markdown(f"**Command:** `{checks['command']}`")
            st.markdown("**Test output (excerpt):**")
            st.code(output_excerpt(checks.get("output", "")), language="text")
        else:
            st.markdown("*The tests were not run successfully, so nothing can be said "
                        "about whether the program passes them.*")

    # 3. The Sage's counsel: the AI's explanation and suggestions
    with tab_counsel, st.container(key="counsel", height=PANEL_HEIGHT):
        st.caption("The AI's explanation and suggestions, based on the Observed evidence tab. "
                   "Suggestions are never applied automatically. You decide.")
        if result.get("report"):
            st.markdown(result["report"])
        else:
            st.markdown("*The Sage reached no conclusion this time. See the note above.*")


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
st.markdown('<p class="title">The Complex Time Saver</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="intro">The Complex Time Saver runs the real tests on a small Python program and tells you, '
    'in plain words, whether it works. Then it estimates how fast the code is (its Big-O time complexity) '
    'and suggests improvements, without ever changing the code itself.</p>',
    unsafe_allow_html=True,
)

# One screen: controls | the Sage | output
ctrl_col, sage_col, out_col = st.columns([1.05, 0.95, 2.4], gap="medium")
with ctrl_col:
    case = st.selectbox("Choose a program to study", CASES, key="case",
                        format_func=lambda c: CASE_LABELS[c], on_change=clear_result)
    task = st.text_area("Your request to the Sage", key="task", height=120)
    col_run, col_reset = st.columns(2)
    run_clicked = col_run.button("Run my buddy", type="primary")
    col_reset.button("Reset", on_click=reset)
    with st.expander("📖 The Sage's glossary"):
        st.markdown(GLOSSARY)
with sage_col:
    sage_slot = st.empty()

if run_clicked:
    if not task.strip():
        st.session_state.result = {"case_id": case, "error": "Please write a request for the Sage first.",
                                   "trace": []}
    else:
        sage_slot.markdown(sage_html("pondering"), unsafe_allow_html=True)
        with out_col:
            with st.spinner("The Sage is consulting the code and the tests..."):
                st.session_state.result = buddy_agent.run_buddy(case, task.strip())
    st.rerun()

result = st.session_state.result
sage_slot.markdown(sage_html(mood_for(result)), unsafe_allow_html=True)
with out_col:
    render_result(result)
