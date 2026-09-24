# ragd-mcp

An MCP (Model Context Protocol) adapter that exposes [ragd](https://github.com/dan-arnold/ragd)'s
`POST /query` endpoint as a `query_codebase` tool, so Claude Code can call
it for fuzzy/semantic codebase search alongside its built-in Grep/Glob.

ragd speaks plain REST/JSON, not MCP, so this exists purely to bridge the
two protocols. It's a single tool, resolved automatically:

- If a `resource` name isn't given, it looks up ragd's `/resources` list
  and picks whichever registered resource's directory contains the
  current working directory (deepest match wins).
- Otherwise it queries the given resource directly.

## Requirements

- `ragd` running and reachable (default `http://localhost:20250`,
  override with `RAGD_URL`)
- [`uv`](https://docs.astral.sh/uv/)

## Register with Claude Code

```sh
claude mcp add --transport stdio ragd --scope user -- uv run --project /home/dan/src/ragd-mcp main.py
```

`--scope user` makes it available in every project on this machine, since
ragd itself already scopes results per-repo. Verify with `claude mcp list`
or `/mcp` in a session.
