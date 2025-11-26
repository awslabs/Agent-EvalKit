import os
from typing import List, Dict

from strands import Agent, tool
from strands.telemetry import StrandsTelemetry
from tavily import TavilyClient

# --- set up telemetry for tracing ---
strands_telemetry = StrandsTelemetry()
strands_telemetry.setup_otlp_exporter()

# --- set up Tavily once ---
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise RuntimeError("Please set TAVILY_API_KEY env var (format starts with tvly-).")

tavily = TavilyClient(api_key=TAVILY_API_KEY)


@tool(name="web_search", description="Search the web with Tavily and return top results.")
def web_search(query: str, max_results: int = 5, news: bool = False) -> List[Dict]:
    """
    Run a Tavily web search and return a list of results.
    Args:
        query: search query
        max_results: number of results (0-20)
        news: if True, prefer news sources
    """
    topic = "news" if news else "general"
    # Use advanced depth for better snippets; you can switch to "basic" to save credits.
    resp = tavily.search(
        query=query,
        search_depth="basic",
        max_results=max_results,
        include_answer=False,
        include_raw_content=False,
        topic=topic,
    )
    # Tavily returns response with `results` entries containing title/url/content/score, etc.
    # We'll pass through only the essentials.
    return [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "content": r.get("content"),
            "score": r.get("score"),
        }
        for r in resp.get("results", [])
    ]


agent = Agent(
    name="QA+Search",
    tools=[web_search],
    # By default Strands uses Bedrock Claude Sonnet if your AWS creds are set.
    # To use a different provider/model, see Strands docs.
)

if __name__ == "__main__":
    # Test with a single query
    query = "recent ai news"

    print(f"Query: {query}")
    print("=" * 50)

    try:
        answer = agent(query)
        print(f"Answer: {answer}")
    except Exception as e:
        print(f"Error: {e}")
