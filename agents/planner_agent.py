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

    # ── Query optimization with spell checking ──────────────────────────────

    def _optimize_query(self, query: str) -> str:
        """Fix common spelling errors and normalize query."""
        # Clean basic formatting
        query = query.strip().replace("  ", " ")
        
        # Common tech spelling corrections
        corrections = {
            "transmision": "transmission",
            "recieve": "receive",
            "occured": "occurred",
            "seperate": "separate",
            "definately": "definitely",
            "algoritm": "algorithm",
            "datbase": "database",
            "netwrok": "network",
            "sceduled": "scheduled",
            "bussiness": "business",
            "artifical": "artificial",
            "inteligence": "intelligence",
            "blockchian": "blockchain",
            "cryptocurency": "cryptocurrency",
            "blockchane": "blockchain",
            "machne": "machine",
            "learnng": "learning",
            "automatoin": "automation",
        }
        
        words = query.lower().split()
        corrected_words = []
        
        for word in words:
            # Remove punctuation for matching
            word_clean = word.rstrip(".,;:!?")
            
            if word_clean in corrections:
                # Preserve original punctuation
                punct = word[len(word_clean):]
                corrected_words.append(corrections[word_clean] + punct)
            else:
                corrected_words.append(word)
        
        return " ".join(corrected_words)

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
        # Optimize goal first (fix spelling)
        goal_opt = self._optimize_query(goal)
        
        words = goal_opt.split()
        return [
            goal_opt,
            f"What is {' '.join(words[:2])} explained",
            f"How does {goal_opt} work",
            f"{goal_opt} tutorial and guide",
            f"{goal_opt} benefits and applications",
        ]

    def _generate_subtasks(self, goal: str) -> list[str]:
        """Use Groq to break goal into specific, searchable subtasks."""
        # Optimize goal (fix spelling, clean formatting)
        goal_clean = self._optimize_query(goal)
        
        prompt = (
            f"Create 4-5 SPECIFIC search queries for this topic:\n"
            f"Topic: {goal_clean}\n\n"
            f"Rules:\n"
            f"1. Each query should be 3-7 words, specific and clear\n"
            f"2. Use proper terminology and correct spelling\n"
            f"3. Include key terms that will return relevant results\n"
            f"4. Make each query slightly different (different angles)\n"
            f"5. Format as numbered list\n\n"
            f"Example:\n"
            f"Topic: What is Blockchain\n"
            f"1. Blockchain technology explained\n"
            f"2. How does blockchain work\n"
            f"3. Blockchain applications and uses\n"
            f"4. Blockchain security benefits\n"
            f"5. Blockchain vs traditional databases\n\n"
            f"Now create search queries for: {goal_clean}"
        )
        llm_response = self._call_llm(prompt)

        if llm_response:
            tasks = self._parse_numbered_list(llm_response)
            if tasks and len(tasks) >= 3:
                print(f"[PLANNER]: Generated {len(tasks)} specific search queries")
                return tasks[:5]
            print("[PLANNER]: Could not parse queries - using fallback.")

        return self._fallback_subtasks(goal_clean)

    # ── Main entry point ─────────────────────────────────────────────────────

    def run(self, goal: str) -> list[str]:
        """
        Process a high-level goal:
        1. Optimize goal (fix spelling).
        2. Break it into subtasks via LLM (or fallback).
        3. Send each subtask to ResearcherAgent via A2A.
        4. Write task plan to shared_memory.
        5. Return the task list.
        """
        # Optimize the goal first (fix spelling, clean)
        goal_optimized = self._optimize_query(goal)
        
        print(f"[PLANNER]: Received goal: {goal}")
        if goal_optimized != goal:
            print(f"[PLANNER]: Optimized goal: {goal_optimized}")

        subtasks = self._generate_subtasks(goal_optimized)
        print(f"[PLANNER]: Generated {len(subtasks)} subtasks")

        for task in subtasks:
            print(f"[PLANNER]: Sending task to ResearcherAgent: {task}")
            COMMUNICATOR.send_message(
                from_agent=self.name,
                to_agent="ResearcherAgent",
                message_type="TASK_ASSIGNED",
                content=task,
            )

        COMMUNICATOR.shared_memory["goal"] = goal_optimized
        COMMUNICATOR.shared_memory["task_plan"] = subtasks
        print(f"[PLANNER]: Task plan written to shared_memory.")

        return subtasks


if __name__ == "__main__":
    agent = PlannerAgent()
    tasks = agent.run("Research the benefits of multi-agent AI systems for enterprise automation")
    print("\n=== Task Plan ===")
    for i, t in enumerate(tasks, 1):
        print(f"  {i}. {t}")
