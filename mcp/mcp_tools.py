"""
MCP Tools Registry
------------------
MCP-style tool registry. Each tool accepts and returns plain strings,
prints a log line when called, and is registered in TOOL_REGISTRY.
"""

import os
from pathlib import Path

# In-memory task log
_task_log: list[dict] = []


# ── Tool Handlers ────────────────────────────────────────────────────────────

def web_search_tool(query: str) -> str:
    """Simulates a web search and returns mock results."""
    print("[MCP TOOL CALLED]: web_search_tool")
    mock_results = {
        "ai agents": (
            "Result 1: 'What are AI Agents?' - AI agents are autonomous programs that perceive "
            "their environment and take actions to achieve goals.\n"
            "Result 2: 'Top AI Agent Frameworks 2024' - CrewAI, AutoGen, and LangGraph are "
            "leading frameworks for building multi-agent systems.\n"
            "Result 3: 'AI Agents in Enterprise' - Companies are deploying AI agents to automate "
            "research, data analysis, and report generation workflows."
        ),
        "mcp protocol": (
            "Result 1: 'Model Context Protocol (MCP)' - MCP is a standard for exposing tools "
            "and context to LLMs in a structured, interoperable way.\n"
            "Result 2: 'MCP vs Function Calling' - MCP provides a server-client architecture "
            "that decouples tool definitions from individual LLM providers.\n"
            "Result 3: 'Getting Started with MCP' - You can build an MCP server using FastAPI "
            "and register tools that any compatible agent can consume."
        ),
        "crewai": (
            "Result 1: 'CrewAI Overview' - CrewAI is a framework for orchestrating role-based "
            "AI agents that collaborate to complete complex tasks.\n"
            "Result 2: 'CrewAI vs LangChain Agents' - CrewAI focuses on multi-agent crews with "
            "defined roles, goals, and delegation.\n"
            "Result 3: 'CrewAI Tools' - CrewAI supports custom and built-in tools like "
            "SerperDevTool, FileReadTool, and WebsiteSearchTool."
        ),
    }
    # Match query to a mock key (case-insensitive partial match)
    query_lower = query.lower()
    for key, result in mock_results.items():
        if key in query_lower or query_lower in key:
            return result
    # Default generic mock response
    return (
        f"Result 1: 'Search results for \"{query}\"' - Relevant articles and resources found.\n"
        f"Result 2: 'Latest on \"{query}\"' - Recent news and research available.\n"
        f"Result 3: 'Deep dive into \"{query}\"' - Comprehensive guide and tutorials available."
    )


def file_reader_tool(filename: str) -> str:
    """Reads a text file and returns its contents."""
    print("[MCP TOOL CALLED]: file_reader_tool")
    path = Path(filename)
    if not path.exists():
        return f"ERROR: File '{filename}' not found."
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"ERROR reading '{filename}': {str(e)}"


def summarizer_tool(text: str) -> str:
    """Returns a summary prompt string to be sent to an LLM."""
    print("[MCP TOOL CALLED]: summarizer_tool")
    prompt = (
        "You are a concise summarizer. Read the following text and produce a clear, "
        "bullet-pointed summary highlighting the key points.\n\n"
        f"Text to summarize:\n{text}\n\n"
        "Summary:"
    )
    return prompt


def task_logger_tool(task: str, status: str) -> str:
    """Logs a task name and status to the in-memory task log."""
    print("[MCP TOOL CALLED]: task_logger_tool")
    entry = {"task": task, "status": status}
    _task_log.append(entry)
    log_line = f"[TASK LOG] Task='{task}' | Status='{status}' | Total logged: {len(_task_log)}"
    return log_line


def report_writer_tool(content: str) -> str:
    """Writes content to output/final_report.txt and returns a confirmation."""
    print("[MCP TOOL CALLED]: report_writer_tool")
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "final_report.txt"
    try:
        report_path.write_text(content, encoding="utf-8")
        return f"Report successfully written to '{report_path.resolve()}'."
    except Exception as e:
        return f"ERROR writing report: {str(e)}"


# ── Tool Registry ────────────────────────────────────────────────────────────

TOOL_REGISTRY: dict = {
    "web_search_tool": web_search_tool,
    "file_reader_tool": file_reader_tool,
    "summarizer_tool": summarizer_tool,
    "task_logger_tool": task_logger_tool,
    "report_writer_tool": report_writer_tool,
}
