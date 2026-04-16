import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from a2a.agent_communicator import COMMUNICATOR
from mcp.mcp_tools import report_writer_tool, task_logger_tool
from config import call_llm
from datetime import datetime

class ExecutorAgent:
    def run(self):
        print(f"\n[EXECUTOR]: Received signal: RESEARCH_DONE")
        research = COMMUNICATOR.shared_memory.get("research_results", {})
        task_plan = COMMUNICATOR.shared_memory.get("task_plan", [])
        goal = COMMUNICATOR.shared_memory.get("goal", "Unknown Goal")
        if not goal or goal == "Unknown Goal":
            goal = task_plan[0] if task_plan else "Unknown Goal"

        all_research = ""
        
        for task, finding in research.items():
            all_research += f"Query: {task}\nFindings:\n{finding}\n\n"
            task_logger_tool(task, "COMPLETED")

        report_prompt = f"""You are a professional research analyst. Write a report on: {goal}

CRITICAL INSTRUCTIONS:
1. Base report ONLY on the research data provided
2. Extract actual quotes and facts from results (use URLs as citations)
3. Include the actual source URLs in citations
4. Structure the report with clear sections

FORMAT:

## {goal}

### Executive Summary
2-3 sentence overview of the topic

### Key Findings
(Extract actual findings from research with source citations)

### Sources
(List all URLs from the research results)

---

RESEARCH DATA:
{all_research}

---

Write the report now. Use facts from research data only."""
        
        print(f"[EXECUTOR]: Generating report via Groq...")
        report = call_llm(report_prompt)

        final_report = f"""Date: {datetime.now().strftime("%B %d, %Y | %I:%M %p")}
Topic: {goal}

{report}
"""
        COMMUNICATOR.shared_memory["final_report"] = final_report
        report_writer_tool(final_report)
        print(f"[EXECUTOR]: Report saved successfully")
        return final_report
