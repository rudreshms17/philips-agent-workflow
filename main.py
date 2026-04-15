"""
main.py — Philips Agent Workflow Orchestrator
----------------------------------------------
Starts the MCP server in a background thread, then runs the full
Planner → Researcher → Executor pipeline for a given goal.
"""

import sys
import time
import threading
import uvicorn

# Force UTF-8 output on Windows to avoid cp1252 UnicodeEncodeError
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from agents.planner_agent import PlannerAgent
from agents.researcher_agent import ResearcherAgent
from agents.executor_agent import ExecutorAgent
from a2a.agent_communicator import COMMUNICATOR


# ── MCP Server (background thread) ──────────────────────────────────────────

def _start_mcp_server():
    """Run the MCP FastAPI server on port 8001 in a daemon thread."""
    config = uvicorn.Config(
        "mcp.mcp_server:app",
        host="0.0.0.0",
        port=8001,
        log_level="warning",   # suppress uvicorn INFO noise in the console
    )
    server = uvicorn.Server(config)
    server.run()


def start_mcp_server_background():
    """Spawn the MCP server thread and wait until it is accepting connections."""
    thread = threading.Thread(target=_start_mcp_server, daemon=True)
    thread.start()
    # Give the server a moment to bind the port before agents start calling it
    time.sleep(2)
    print("[ORCHESTRATOR]: MCP server started on http://localhost:8001")
    return thread


# ── Agent instances (shared across calls) ───────────────────────────────────

planner    = PlannerAgent()
researcher = ResearcherAgent()
executor   = ExecutorAgent()


# ── Workflow ─────────────────────────────────────────────────────────────────

def run_workflow(goal: str) -> str:
    """
    Run the full multi-agent pipeline for a given goal.

    Steps:
        1. PlannerAgent   — breaks goal into subtasks, dispatches via A2A
        2. ResearcherAgent — picks up tasks, calls MCP web_search_tool
        3. ExecutorAgent   — compiles report, saves via MCP tools

    Returns:
        The final report text from shared_memory["final_report"].
    """
    print("\n=== PHILIPS AGENT WORKFLOW STARTING ===\n")
    print(f"[ORCHESTRATOR]: Goal -> {goal}\n")

    # Step 1 — Plan
    task_list = planner.run(goal)
    print(f"\n[ORCHESTRATOR]: {len(task_list)} subtask(s) dispatched to ResearcherAgent\n")

    # Step 2 — Research
    research_results = researcher.run()
    print(f"\n[ORCHESTRATOR]: Research complete - {len(research_results)} finding(s)\n")

    # Step 3 — Execute / Compile
    report = executor.run()

    print("\n=== WORKFLOW COMPLETE ===\n")

    return COMMUNICATOR.shared_memory.get("final_report", report)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    start_mcp_server_background()

    result = run_workflow(
        "Research the latest trends in healthcare AI and write a report"
    )
    print(result)
