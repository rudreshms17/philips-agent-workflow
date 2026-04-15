"""
MCP Server
----------
FastAPI REST API that exposes TOOL_REGISTRY tools via a /call-tool endpoint.

Run with:
    uvicorn mcp.mcp_server:app --reload --port 8001
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import uvicorn

from mcp.mcp_tools import TOOL_REGISTRY

app = FastAPI(title="MCP Tool Server", version="0.1.0")


class ToolCallRequest(BaseModel):
    tool_name: str
    params: dict[str, Any] = {}


@app.post("/call-tool")
def call_tool(request: ToolCallRequest):
    """Invoke a registered tool by name with the given params."""
    tool_name = request.tool_name

    if tool_name not in TOOL_REGISTRY:
        return {"result": f"ERROR: Tool '{tool_name}' not found. Available: {list(TOOL_REGISTRY.keys())}"}

    handler = TOOL_REGISTRY[tool_name]
    try:
        result = handler(**request.params)
        return {"result": result}
    except TypeError as e:
        return {"result": f"ERROR: Invalid parameters for '{tool_name}': {str(e)}"}
    except Exception as e:
        return {"result": f"ERROR: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run("mcp.mcp_server:app", host="0.0.0.0", port=8001, reload=True)
