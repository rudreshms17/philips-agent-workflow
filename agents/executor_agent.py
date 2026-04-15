"""
Executor Agent
--------------
Waits for RESEARCH_DONE from ResearcherAgent, reads research findings
from shared_memory, generates summaries via Gemini LLM, compiles a structured
final report, saves it via MCP tools, and logs all tasks as COMPLETED.
"""

import os
import requests
from datetime import datetime
from a2a.agent_communicator import COMMUNICATOR
from config import call_llm

MCP_SERVER_URL = "http://localhost:8001/call-tool"


class ExecutorAgent:
    def __init__(self):
        self.name = "ExecutorAgent"

    # (Internal LLM calls handled via config.call_llm)

    # ── MCP helper ───────────────────────────────────────────────────────────

    def _call_mcp(self, tool_name: str, params: dict) -> str:
        """Generic MCP tool call via HTTP POST."""
        try:
            response = requests.post(
                MCP_SERVER_URL,
                json={"tool_name": tool_name, "params": params},
                timeout=10,
            )
            response.raise_for_status()
            return response.json().get("result", "")
        except Exception as e:
            return f"[MCP ERROR]: {str(e)}"

    # ── Main entry point ─────────────────────────────────────────────────────

    def run(self) -> str:
        """
        Full executor pipeline:
        1. Check for RESEARCH_DONE signal.
        2. Read research_results from shared_memory.
        3. Call summarizer_tool for each finding.
        4. Compile structured final report.
        5. Save report via report_writer_tool.
        6. Log each task via task_logger_tool.
        7. Store report in shared_memory["final_report"].

        Returns the final report text.
        """
        # Step 1 — check for RESEARCH_DONE signal
        messages = COMMUNICATOR.receive_messages(self.name)
        done_signals = [m for m in messages if m["message_type"] == "RESEARCH_DONE"]

        if not done_signals:
            print("[EXECUTOR]: No RESEARCH_DONE signal found. Nothing to process.")
            return ""

        print(f"[EXECUTOR]: Received signal: RESEARCH_DONE")

        # Step 2 — read research results
        research_results: dict = COMMUNICATOR.shared_memory.get("research_results", {})
        goal: str = COMMUNICATOR.shared_memory.get("task_plan", ["Unknown goal"])[0] \
            if COMMUNICATOR.shared_memory.get("task_plan") else "Unknown goal"

        n = len(research_results)
        print(f"[EXECUTOR]: Compiling report for {n} tasks")

        # Step 3 & 4 — summarise each finding and build report sections
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        report_lines = [
            "=" * 60,
            "  Philips Agent Workflow - Task Report",
            "=" * 60,
            f"Date       : {timestamp}",
            f"Goal       : {goal}",
            f"Total Tasks: {n}",
            "=" * 60,
            "",
        ]

        for idx, (task, finding) in enumerate(research_results.items(), 1):
            # Build a summarization prompt and call Gemini directly
            summary_prompt = (
                "You are a concise summarizer. Read the following research finding and produce "
                "a clear, bullet-pointed summary highlighting the key points.\n\n"
                f"Research finding:\n{finding}\n\nSummary:"
            )
            summary = call_llm(summary_prompt)

            # Also call the MCP summarizer_tool to get the structured prompt form
            self._call_mcp("summarizer_tool", {"text": finding})

            report_lines += [
                f"Task {idx}: {task}",
                "-" * 50,
                "Research Finding:",
                finding,
                "",
                "Groq Summary (Llama 3.3):",
                summary,
                "",
            ]

            # Step 6 — log each task as COMPLETED
            self._call_mcp(
                "task_logger_tool",
                {"task": task, "status": "COMPLETED"},
            )

        report_lines += [
            "=" * 60,
            "END OF REPORT",
            "=" * 60,
        ]

        report_text = "\n".join(report_lines)

        # Step 5 — save report via report_writer_tool
        save_result = self._call_mcp("report_writer_tool", {"content": report_text})
        print(f"[EXECUTOR]: Report saved successfully")
        print(f"[EXECUTOR]: {save_result}")

        # Step 7 — store in shared_memory
        COMMUNICATOR.shared_memory["final_report"] = report_text

        return report_text


if __name__ == "__main__":
    # Smoke-test: run full pipeline
    from agents.planner_agent import PlannerAgent
    from agents.researcher_agent import ResearcherAgent

    goal = "Research the benefits of multi-agent AI systems"
    PlannerAgent().run(goal)
    ResearcherAgent().run()

    agent = ExecutorAgent()
    report = agent.run()
    print("\n=== Final Report ===")
    print(report)
