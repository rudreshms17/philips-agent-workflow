"""
Researcher Agent
----------------
Listens for TASK_ASSIGNED messages from PlannerAgent,
calls the MCP web_search_tool, stores findings in shared_memory,
then notifies ExecutorAgent when all research is done.
"""

import requests
from a2a.agent_communicator import COMMUNICATOR

MCP_SERVER_URL = "http://localhost:8001/call-tool"


class ResearcherAgent:
    def __init__(self):
        self.name = "ResearcherAgent"

    # ── MCP tool call ────────────────────────────────────────────────────────

    def _call_web_search(self, query: str) -> str:
        """Call web_search_tool on the MCP server via HTTP POST."""
        print(f"[RESEARCHER]: Calling MCP tool: web_search_tool")
        try:
            response = requests.post(
                MCP_SERVER_URL,
                json={"tool_name": "web_search_tool", "params": {"query": query}},
                timeout=10,
            )
            response.raise_for_status()
            return response.json().get("result", "No result returned.")
        except Exception as e:
            return f"[MCP ERROR]: {str(e)}"

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

            finding = self._call_web_search(task)
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


if __name__ == "__main__":
    # Quick smoke-test (requires MCP server running on port 8001)
    from agents.planner_agent import PlannerAgent

    goal = "Research the benefits of multi-agent AI systems"
    PlannerAgent().run(goal)

    agent = ResearcherAgent()
    results = agent.run()

    print("\n=== Research Results ===")
    for task, finding in results.items():
        print(f"\nTask: {task}\nFinding: {finding[:200]}...")
