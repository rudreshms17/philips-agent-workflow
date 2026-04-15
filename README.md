# Philips Agent Workflow

A multi-agent AI workflow system built with Model Context Protocol (MCP) and Agent-to-Agent (A2A) communication, powered by Groq (Llama 3.3).

## Project Structure

```
philips-agent-workflow/
├── agents/
│   ├── planner_agent.py       # Plans and decomposes tasks using Groq
│   ├── executor_agent.py      # Compiles research and writes final report
│   └── researcher_agent.py    # Researches information via MCP tools
├── mcp/
│   ├── mcp_server.py          # FastAPI MCP server on port 8001
│   └── mcp_tools.py           # MCP tool definitions (search, summarize, report)
├── a2a/
│   └── agent_communicator.py  # Agent-to-Agent shared message bus
├── ui/
│   └── app.py                 # Streamlit dashboard UI
├── config.py                  # Centralized LLM configuration (Groq)
├── output/
│   └── final_report.txt       # Generated reports saved here
├── .env                       # Your API keys (never commit this)
├── requirements.txt
└── README.md
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get a Groq API key

Get your Groq API key from the Groq Console:

👉 **https://console.groq.com/keys**

### 4. Configure environment variables

Edit the `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

## Running the Application

### Option A — Command-line pipeline

```bash
python main.py
```

### Option B — Streamlit UI (recommended)

```bash
streamlit run ui/app.py
```

## Components

### Agents
- **Planner Agent** – Breaks down high-level goals into 3–5 subtasks using Groq (Llama 3.3).
- **Researcher Agent** – Picks up tasks from the A2A bus, calls `web_search_tool` on the MCP server.
- **Executor Agent** – Receives `RESEARCH_DONE` signal, compiles a structured report using Groq summaries, saves it via `report_writer_tool`.

### MCP (Model Context Protocol)
- **MCP Server** – FastAPI REST server on `http://localhost:8001/call-tool`.
- **MCP Tools** – `web_search_tool`, `summarizer_tool`, `task_logger_tool`, `report_writer_tool`, `file_reader_tool`.

### A2A (Agent-to-Agent)
- **A2ACommunicator** – Singleton shared message bus + shared memory used by all three agents.

### UI
- **Streamlit App** – Live agent status badges, A2A message bus counter, MCP tool list, log viewer, and downloadable report.

## Tech Stack

| Layer           | Technology                           |
|-----------------|--------------------------------------|
| LLM Provider    | Groq (Llama 3.3 70B)                 |
| MCP Server      | FastAPI + Uvicorn (port 8001)        |
| A2A Protocol    | Custom in-process message bus        |
| UI              | Streamlit                            |
| Utilities       | python-dotenv, requests, pydantic, groq |
