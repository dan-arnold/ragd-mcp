"""MCP adapter exposing ragd's RAG query endpoint as a tool.

ragd (https://github.com/dan-arnold/ragd) speaks plain REST/JSON, not MCP,
so this wraps its POST /query endpoint as a single MCP tool over stdio.
"""

import os

import httpx
from mcp.server.mcpserver import MCPServer

RAGD_URL = os.environ.get("RAGD_URL", "http://localhost:20250")
REQUEST_TIMEOUT = 90.0

mcp = MCPServer("ragd")


def _resolve_resource(client: httpx.Client) -> str | None:
    """Finds the registered ragd resource whose root directory contains
    the current working directory, preferring the most specific (deepest)
    match if more than one resource's root is an ancestor of cwd.
    """
    resp = client.get("/resources")
    resp.raise_for_status()
    cwd = os.path.realpath(os.getcwd())

    best_name = None
    best_len = -1
    for resource in resp.json().get("resources", []):
        root = resource["uri"].removeprefix("file://").rstrip("/")
        if cwd == root or cwd.startswith(root + "/"):
            if len(root) > best_len:
                best_name, best_len = resource["name"], len(root)
    return best_name


@mcp.tool()
def query_codebase(query: str, resource: str | None = None, top_k: int = 5) -> str:
    """Fuzzy/semantic RAG search over a codebase indexed by ragd.

    Prefer this over Grep/Glob when the question is conceptual rather than
    an exact string/symbol match -- e.g. "where do we handle retry logic"
    or "how is auth configured" -- where you don't know the exact
    symbol/filename to search for. Returns a synthesized answer plus the
    source file excerpts it was drawn from.

    Args:
        query: Natural-language question about the codebase.
        resource: Name of the ragd resource to search. If omitted, the
            resource whose indexed directory contains the current working
            directory is used automatically.
        top_k: Number of source chunks to retrieve and ground the answer
            in (default 5, max 20).
    """
    with httpx.Client(base_url=RAGD_URL, timeout=REQUEST_TIMEOUT) as client:
        resolved = resource or _resolve_resource(client)
        if resolved is None:
            return (
                "No ragd resource is registered for the current directory. "
                "Register it first with POST /resources, or pass an explicit "
                "`resource` name."
            )

        resp = client.post(
            "/query", json={"resource": resolved, "query": query, "top_k": top_k}
        )
        resp.raise_for_status()
        data = resp.json()

    sources = "\n".join(
        f"- {s['path']} (score {s['score']:.2f})" for s in data.get("sources", [])
    )
    return f"{data['answer']}\n\nSources:\n{sources}" if sources else data["answer"]


if __name__ == "__main__":
    mcp.run()
