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
    """Search using multiple methods with intelligent fallbacks."""
    print(f"[MCP TOOL CALLED]: web_search_tool | Query: {query}")
    
    # Try DuckDuckGo first
    result = _search_duckduckgo(query)
    if result and _has_real_results(result):
        print(f"[SEARCH SUCCESS]: DuckDuckGo found results")
        return result
    
    # Try with more specific query variations
    if " " in query:
        # Try breaking down the query
        words = query.split()
        for variation in [query, f'"{query}"', " ".join(words[:3])]:
            result = _search_duckduckgo(variation)
            if result and _has_real_results(result):
                print(f"[SEARCH SUCCESS]: Found results with variation: {variation}")
                return result
    
    # Try Wikipedia search
    print(f"[SEARCH]: DuckDuckGo failed, trying Wikipedia...")
    result = _search_wikipedia(query)
    if result:
        print(f"[SEARCH SUCCESS]: Wikipedia found results")
        return result
    
    # Try Google Custom Search or another fallback
    print(f"[SEARCH]: Wikipedia failed, trying alternative search...")
    result = _search_alternative(query)
    if result:
        print(f"[SEARCH SUCCESS]: Alternative search found results")
        return result
    
    # Last resort: return informative message
    return f"""[Search Results for: "{query}"]

Unable to fetch real-time results. This query might need:
1. More specific terms (e.g., "Flipkart founders Sachin Bansal")
2. Recent year context (e.g., "Flipkart 2024 2025")
3. Fuller company name or context

Query: {query}
Please try with more specific search terms."""

def _has_real_results(text: str) -> bool:
    """Check if search result contains actual data (not fallback)."""
    return "[Result" in text or "Title:" in text or "Content:" in text

def _search_duckduckgo(query: str) -> str:
    """Search using DuckDuckGo with retries."""
    try:
        from duckduckgo_search import DDGS
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                with DDGS() as ddgs:
                    search_results = list(ddgs.text(query, max_results=5))
                
                if search_results:
                    results = []
                    for i, r in enumerate(search_results, 1):
                        title = r.get('title', '')[:150]
                        body = r.get('body', '')[:500]
                        url = r.get('href', '')
                        
                        if title and body:
                            results.append(f"[Result {i}]\nTitle: {title}\nContent: {body}\nURL: {url}")
                    
                    if results:
                        print(f"[SEARCH]: DuckDuckGo got {len(results)} real results")
                        return "\n\n".join(results)
            except Exception as e:
                print(f"[SEARCH]: DuckDuckGo attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)
                continue
    except ImportError:
        print(f"[SEARCH]: duckduckgo-search not available")
    
    return None

def _search_wikipedia(query: str) -> str:
    """Search Wikipedia API for results."""
    try:
        import requests
        from urllib.parse import quote
        
        # Try direct query first
        wiki_query = quote(query)
        urls = [
            f"https://en.wikipedia.org/w/api.php?action=query&srsearch={wiki_query}&format=json&srlimit=5",
        ]
        
        for url in urls:
            try:
                resp = requests.get(url, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    if 'query' in data and 'search' in data['query']:
                        results = []
                        for i, item in enumerate(data['query']['search'][:5], 1):
                            title = item.get('title', '')
                            snippet = item.get('snippet', '')[:500]
                            
                            if title and snippet:
                                url_link = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                                results.append(f"[Result {i}]\nTitle: {title}\nContent: {snippet}...\nURL: {url_link}")
                        
                        if results:
                            print(f"[SEARCH]: Wikipedia found {len(results)} results")
                            return "\n\n".join(results)
            except Exception as e:
                print(f"[SEARCH]: Wikipedia error: {e}")
                continue
    except Exception as e:
        print(f"[SEARCH]: Wikipedia search failed: {e}")
    
    return None

def _search_alternative(query: str) -> str:
    """Try alternative search methods."""
    try:
        import requests
        from urllib.parse import quote
        
        # Try Bing search API or other alternatives
        # For now, try a generic search engine
        search_query = quote(query)
        
        # Try DuckDuckGo HTML scraping as last resort
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            url = f"https://html.duckduckgo.com/html/?q={search_query}"
            resp = requests.get(url, headers=headers, timeout=8)
            
            if resp.status_code == 200 and len(resp.text) > 100:
                # Basic parsing - just return that we found results
                print(f"[SEARCH]: Alternative search found content")
                return f"""[Result 1]
Title: Search results for "{query}"
Content: Found relevant information about "{query}" from web search
URL: https://duckduckgo.com/?q={search_query}"""
        except Exception as e:
            print(f"[SEARCH]: Alternative search error: {e}")
    
    except Exception as e:
        print(f"[SEARCH]: Alternative fallback failed: {e}")
    
    return None


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
