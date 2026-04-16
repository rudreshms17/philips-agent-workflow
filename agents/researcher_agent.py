"""
Researcher Agent
----------------
Listens for TASK_ASSIGNED messages from PlannerAgent,
calls the MCP web_search_tool directly, stores findings in shared_memory,
then notifies ExecutorAgent when all research is done.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from a2a.agent_communicator import COMMUNICATOR
from mcp.mcp_tools import web_search_tool


class ResearcherAgent:
    def __init__(self):
        self.name = "ResearcherAgent"

    # ── Main entry point ─────────────────────────────────────────────────────

    def run(self) -> dict:
        """
        Process all pending TASK_ASSIGNED messages from PlannerAgent:
        1. Fetch messages addressed to this agent.
        2. Call web_search_tool for each task.
        3. Store findings in shared_memory["research_results"].
        4. Notify ExecutorAgent when done.

        Returns the research_results dict.
        """
        messages = COMMUNICATOR.receive_messages(self.name)
        task_messages = [m for m in messages if m["message_type"] == "TASK_ASSIGNED"]

        if not task_messages:
            print("[RESEARCHER]: No pending tasks found.")
            return {}

        # Load or initialise research results in shared memory
        research_results: dict = COMMUNICATOR.shared_memory.get("research_results", {})

        for message in task_messages:
            task = message["content"]
            print(f"[RESEARCHER]: Received task: {task}")

            # Call tool directly
            finding = web_search_tool(task)
            research_results[task] = finding

            print(f"[RESEARCHER]: Research complete for task: {task}")

        # Persist back to shared memory
        COMMUNICATOR.shared_memory["research_results"] = research_results

        # Notify ExecutorAgent
        print(f"[RESEARCHER]: Notifying ExecutorAgent")
        COMMUNICATOR.send_message(
            from_agent=self.name,
            to_agent="ExecutorAgent",
            message_type="RESEARCH_DONE",
            content=f"Research complete for {len(research_results)} task(s). Results available in shared_memory.",
        )

        return research_results

