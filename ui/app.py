"""ui/app.py - Multi-Agent Research Workflow System
----------------------------------------------
Run with:
    streamlit run ui/app.py
"""

import sys
import io
import time
import threading
import contextlib
from pathlib import Path

# ── Path setup so imports resolve from project root ──────────────────────────
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

# ── Page config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Research Agent Workflow",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Lazy project imports (after path is set) ─────────────────────────────────
from a2a.agent_communicator import COMMUNICATOR
from mcp.mcp_tools import TOOL_REGISTRY
from agents.planner_agent import PlannerAgent
from agents.researcher_agent import ResearcherAgent
from agents.executor_agent import ExecutorAgent
from chat_with_report import chat_with_report


# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Main background ── */
.stApp {
    background: linear-gradient(135deg, #0a0f1e 0%, #0d1b3e 50%, #0a1628 100%);
    color: #e8f0fe;
}

/* ── Hero header ── */
.hero-title {
    font-size: 2.6rem;
    font-weight: 700;
    background: linear-gradient(90deg, #4da6ff, #0B5ED7, #7eb8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.2rem;
}
.hero-sub {
    font-size: 1.05rem;
    color: #7eb8ff;
    letter-spacing: 0.04em;
    margin-bottom: 1.5rem;
    font-weight: 400;
}

/* ── Cards ── */
.card {
    background: rgba(11, 94, 215, 0.08);
    border: 1px solid rgba(11, 94, 215, 0.25);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
    backdrop-filter: blur(8px);
}

/* ── Status badges ── */
.badge {
    display: inline-block;
    padding: 0.35rem 0.9rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    margin: 0.25rem 0;
}
.badge-idle    { background: rgba(255,193,7,0.15);  color: #ffc107; border: 1px solid rgba(255,193,7,0.4);  }
.badge-running { background: rgba(11,94,215,0.20);  color: #4da6ff; border: 1px solid rgba(11,94,215,0.5); }
.badge-done    { background: rgba(25,195,125,0.15); color: #19c37d; border: 1px solid rgba(25,195,125,0.4); }

/* ── Log box ── */
.log-box {
    background: #050c1a;
    border: 1px solid #0B5ED7;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem;
    color: #7eb8ff;
    max-height: 340px;
    overflow-y: auto;
    white-space: pre-wrap;
    line-height: 1.6;
}

/* ── Metric cards ── */
.metric-card {
    background: rgba(11, 94, 215, 0.12);
    border: 1px solid rgba(11, 94, 215, 0.3);
    border-radius: 14px;
    padding: 1rem 1.4rem;
    text-align: center;
}
.metric-value { font-size: 2.2rem; font-weight: 700; color: #4da6ff; }
.metric-label { font-size: 0.8rem;  color: #7eb8ff; margin-top: 0.2rem; }

/* ── Tool chip ── */
.tool-chip {
    background: rgba(11,94,215,0.15);
    border: 1px solid rgba(11,94,215,0.35);
    border-radius: 8px;
    padding: 0.3rem 0.7rem;
    font-size: 0.78rem;
    color: #a8ceff;
    margin: 0.2rem 0;
    display: block;
}

/* ── Run button ── */
div.stButton > button {
    background: linear-gradient(135deg, #0B5ED7, #1a73e8);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.75rem 2.5rem;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    cursor: pointer;
    transition: all 0.2s ease;
    width: 100%;
    box-shadow: 0 4px 20px rgba(11,94,215,0.4);
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(11,94,215,0.55);
    background: linear-gradient(135deg, #1a73e8, #2196f3);
}

/* ── Divider ── */
hr { border-color: rgba(11,94,215,0.2); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080e20, #0d1b3e);
    border-right: 1px solid rgba(11,94,215,0.25);
}
[data-testid="stSidebar"] * { color: #c8dcff !important; }

/* ── Text area (report) ── */
textarea {
    background: #050c1a !important;
    color: #7eb8ff !important;
    border: 1px solid #0B5ED7 !important;
    border-radius: 12px !important;
    font-family: 'Courier New', monospace !important;
    font-size: 0.8rem !important;
}

/* ── Spinner text ── */
.stSpinner > div { color: #4da6ff !important; }
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ─────────────────────────────────────────────────
if "mcp_started"     not in st.session_state: st.session_state.mcp_started     = False
if "workflow_ran"    not in st.session_state: st.session_state.workflow_ran     = False
if "final_report"    not in st.session_state: st.session_state.final_report     = ""
if "captured_log"    not in st.session_state: st.session_state.captured_log     = ""
if "tasks_completed" not in st.session_state: st.session_state.tasks_completed  = 0
if "agent_states"    not in st.session_state:
    st.session_state.agent_states = {
        "PlannerAgent":    "idle",
        "ResearcherAgent": "idle",
        "ExecutorAgent":   "idle",
    }


# ── MCP server (start once per session) ──────────────────────────────────────
def _start_mcp_server():
    import uvicorn
    config = uvicorn.Config("mcp.mcp_server:app", host="0.0.0.0", port=8001, log_level="warning")
    uvicorn.Server(config).run()

if not st.session_state.mcp_started:
    t = threading.Thread(target=_start_mcp_server, daemon=True)
    t.start()
    time.sleep(2)
    st.session_state.mcp_started = True


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 Research Agent Workflow")
    st.markdown("---")

    # Agent status
    st.markdown("### 🔄 Agent Status")
    states = st.session_state.agent_states
    badge_class = {"idle": "badge-idle", "running": "badge-running", "done": "badge-done"}
    icons       = {"idle": "🟡", "running": "🔵", "done": "🟢"}

    for agent, state in states.items():
        icon  = icons[state]
        cls   = badge_class[state]
        label = state.upper()
        st.markdown(
            f'<span class="badge {cls}">{icon} {agent} - {label}</span>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        '<div style="font-size:0.72rem;color:#4d6a99;text-align:center;">'
        'Research Agent Workflow<br>Powered by AI'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">🤖 Multi-Agent Research Workflow</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Powered by Intelligent Multi-Agent System</div>', unsafe_allow_html=True)
st.markdown("---")


# ── Goal input ────────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([4, 1])

with col_input:
    goal = st.text_input(
        "Enter your Goal",
        placeholder="e.g. Research AI trends in healthcare",
        label_visibility="visible",
    )

with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)   # vertical align with input
    run_clicked = st.button("▶ Run Workflow")


# ── Workflow execution ────────────────────────────────────────────────────────
if run_clicked:
    if not goal.strip():
        st.warning("⚠️ Please enter a goal before running the workflow.")
    else:
        # Reset state
        COMMUNICATOR.message_bus.clear()
        COMMUNICATOR.shared_memory.clear()
        st.session_state.agent_states = {
            "PlannerAgent":    "idle",
            "ResearcherAgent": "idle",
            "ExecutorAgent":   "idle",
        }
        st.session_state.chat_history = []  # Clear previous chat history

        log_buffer = io.StringIO()

        with st.spinner("🤖 Agents are working..."):
            # ── Planner ──────────────────────────────────────────────────────
            st.session_state.agent_states["PlannerAgent"] = "running"
            with contextlib.redirect_stdout(log_buffer):
                planner = PlannerAgent()
                tasks   = planner.run(goal)
            st.session_state.agent_states["PlannerAgent"] = "done"

            # ── Researcher ───────────────────────────────────────────────────
            st.session_state.agent_states["ResearcherAgent"] = "running"
            with contextlib.redirect_stdout(log_buffer):
                researcher = ResearcherAgent()
                findings   = researcher.run()
            st.session_state.agent_states["ResearcherAgent"] = "done"

            # ── Executor ─────────────────────────────────────────────────────
            st.session_state.agent_states["ExecutorAgent"] = "running"
            with contextlib.redirect_stdout(log_buffer):
                executor = ExecutorAgent()
                report   = executor.run()
            st.session_state.agent_states["ExecutorAgent"] = "done"

        st.session_state.captured_log    = log_buffer.getvalue()
        st.session_state.final_report    = COMMUNICATOR.shared_memory.get("final_report", report or "")
        st.session_state.tasks_completed = len(findings)
        st.session_state.workflow_ran    = True
        st.rerun()


# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.workflow_ran:
    st.markdown("---")

    # Log panel + Report + Chat in tabs
    tab_log, tab_report, tab_chat = st.tabs(["📋 Agent Activity Log", "📄 Final Report", "💬 Chat with Report"])

    with tab_log:
        st.markdown("#### Live Agent Log")
        log_text = st.session_state.captured_log or "(no output captured)"
        st.markdown(f'<div class="log-box">{log_text}</div>', unsafe_allow_html=True)

    with tab_report:
        st.markdown("#### Final Report")
        report_text = st.session_state.final_report
        if report_text:
            st.text_area(
                label="Report",
                value=report_text,
                height=420,
                label_visibility="collapsed",
            )
            st.download_button(
                label="📥 Download Report",
                data=report_text,
                file_name="final_report.txt",
                mime="text/plain",
            )
        else:
            st.info("No report generated yet.")

    with tab_chat:
        st.markdown("#### Ask Questions About the Report")
        if st.session_state.final_report:
            # Chat interface
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            
            # Display chat history
            for chat_item in st.session_state.chat_history:
                with st.chat_message(chat_item["role"]):
                    st.markdown(chat_item["content"])
            
            # Chat input
            user_question = st.chat_input("Ask a question about the report...")
            
            if user_question:
                # Display user message
                with st.chat_message("user"):
                    st.markdown(user_question)
                st.session_state.chat_history.append({"role": "user", "content": user_question})
                
                # Get AI response
                with st.spinner("🤔 Thinking..."):
                    answer = chat_with_report(st.session_state.final_report, user_question)
                
                # Display assistant message
                with st.chat_message("assistant"):
                    st.markdown(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                
                st.rerun()
        else:
            st.info("📄 Generate a report first to start chatting about its content.")
