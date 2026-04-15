"""
Planner Agent
-------------
Receives a high-level goal, breaks it into subtasks via Gemini LLM,
and dispatches each subtask to ResearcherAgent via A2ACommunicator.
"""

import os
import re
from a2a.agent_communicator import COMMUNICATOR
from config import call_llm


class PlannerAgent:
    def __init__(self):
        self.name = "PlannerAgent"

    # ── LLM call ────────────────────────────────────────────────────────────

    def _call_llm(self, prompt: str) -> str:
        """Call Groq via the central config and return the response text."""
        response = call_llm(prompt)
        if "Could not get response" in response:
            return ""
        return response

    # ── Subtask generation ───────────────────────────────────────────────────

    def _parse_numbered_list(self, text: str) -> list[str]:
        """Extract numbered list items from LLM response text."""
        lines = text.strip().splitlines()
        tasks = []
        for line in lines:
            match = re.match(r"^\s*\d+[\.\)]\s+(.+)", line)
            if match:
                tasks.append(match.group(1).strip())
        return tasks

    def _fallback_subtasks(self, goal: str) -> list[str]:
        """Generate basic subtasks from the goal string when LLM is unavailable."""
        keywords = [w for w in goal.split() if len(w) > 4][:5]
        if not keywords:
            keywords = goal.split()[:3]
        return [
            f"Research information about: {goal}",
            f"Analyze key aspects related to: {', '.join(keywords)}",
            f"Summarize findings for: {goal}",
            f"Write a final report on: {goal}",
        ]

    def _generate_subtasks(self, goal: str) -> list[str]:
        """Use Gemini to break goal into subtasks; fall back if needed."""
        prompt = (
            f"Break this goal into 3-5 clear subtasks as a numbered list. "
            f"Goal: {goal}"
        )
        llm_response = self._call_llm(prompt)

        if llm_response:
            tasks = self._parse_numbered_list(llm_response)
            if tasks:
                return tasks[:5]  # cap at 5
            print("[PLANNER]: Could not parse numbered list - using fallback.")

        return self._fallback_subtasks(goal)

    # ── Main entry point ─────────────────────────────────────────────────────

    def run(self, goal: str) -> list[str]:
        """
        Process a high-level goal:
        1. Break it into subtasks via LLM (or fallback).
        2. Send each subtask to ResearcherAgent via A2A.
        3. Write task plan to shared_memory.
        4. Return the task list.
        """
        print(f"[PLANNER]: Received goal: {goal}")

        subtasks = self._generate_subtasks(goal)
        print(f"[PLANNER]: Generated {len(subtasks)} subtasks")

        for task in subtasks:
            print(f"[PLANNER]: Sending task to ResearcherAgent: {task}")
            COMMUNICATOR.send_message(
                from_agent=self.name,
                to_agent="ResearcherAgent",
                message_type="TASK_ASSIGNED",
                content=task,
            )

        COMMUNICATOR.shared_memory["task_plan"] = subtasks
        print(f"[PLANNER]: Task plan written to shared_memory.")

        return subtasks


if __name__ == "__main__":
    agent = PlannerAgent()
    tasks = agent.run("Research the benefits of multi-agent AI systems for enterprise automation")
    print("\n=== Task Plan ===")
    for i, t in enumerate(tasks, 1):
        print(f"  {i}. {t}")
