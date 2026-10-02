# MCP servers in a plugin — patterns for a shared daemon

> Last audited against Claude Code docs: 2026-10-02 (v2.1.287, mirror 934d35c9)

Use this page when a plugin ships an MCP server that the author (or a power user) wants to run **once per machine as an HTTP daemon**, while ordinary recipients keep a zero-setup default. Basic plugin MCP facts (`.mcp.json`, `.mcpb` bundles, naming) are in `components.md §4`.

## 1. What the docs fix in place

- **The transport can't be switched by a variable.** `${VAR}` / `${VAR:-default}` expand only in `command`, `args`, `env`, `url`, `headers` (`mcp.md §Environment variable expansion in .mcp.json`); for plugin http/sse/ws servers also `headersHelper` (`plugins__manifest-reference.md §Where each variable resolves`). `type` never expands, so one server key is either stdio or HTTP.
- **A user-scope server can't shadow a plugin server by name.** Scopes dedupe by name; plugins and claude.ai connectors dedupe **by endpoint** — the same URL or the same command as an enabled server above them counts as a duplicate (`mcp.md §Scope hierarchy and precedence`). Scheme/host letter case, the default port and a trailing slash don't make a new endpoint; a different path, query or port does.
- **Tool names carry the plugin and server key:** `mcp__plugin_<plugin>_<server>__<tool>` (`plugins__components.md §MCP servers`). Any scheme that adds a second key renames the tools — every skill, hook matcher and permission rule that names them breaks (`pitfalls.md §4`).
- **A plugin server can be switched off without touching the plugin:** `deniedMcpServers` in user settings blocks matching servers "including plugin servers", merged from every settings scope (`settings-reference.md §deniedMcpServers`). The owner's probe (2026-10-02) found the form `{"serverName": "plugin:<plugin>:<server>"}` works and a bare server key does not. `serverCommand` matches command + args exactly, so a version bump in `args` silently lifts the block.
- **Stdio is not reconnected.** Claude Code reconnects remote servers; a stdio server that dies stays dead for the session (`mcp.md §Automatic reconnection`).
- **Idle window:** 5 minutes for HTTP/SSE/WS, 30 minutes for stdio, unless the server's `timeout` (≥1000 ms, v2.1.203+) is longer (`mcp.md`, the tips and timeout notes just before §Automatic backgrounding of long tool calls). Long tools behind a daemon need a `timeout` in the server entry.

## 2. Choosing a pattern

| Pattern | Recipient gets | Tool names | Per-session cost for the daemon user | Status |
|---|---|---|---|---|
| **U** — vendor-hosted HTTP: `"url": "${user_config.<x>_mcp_url}"`, default = vendor's URL | the vendor's remote server | unchanged | 0 | Built from documented fields; fits when the vendor hosts a remote MCP |
| **L** — launcher + relay: one stdio key runs `${CLAUDE_PLUGIN_ROOT}/bin/mcp-run <name>`; empty `*_mcp_url` → exec the normal stdio server, non-empty → exec a stdio↔HTTP relay to the daemon | the normal stdio server | unchanged | one small relay process (not measured) | **Assembled from documented parts; the pattern itself is not documented** |
| **C** — companion plugin `<plugin>-shared` with HTTP keys + the daemon user's `deniedMcpServers` on the stdio key | nothing changes (companion not installed) | new prefix `mcp__plugin_<plugin>-shared_…` | 0 | Fallback when zero processes per session matters more than stable names |

Default advice: U when the vendor hosts a remote MCP, otherwise L; C only if the relay turns out heavy. In C (or any two-key scheme) write skills against bare tool names and hook matchers as regexes over both prefixes, and never point the companion and a user-scope server at one URL — one of them silently disappears.

### `.mcp.json` for L

```json
{
  "mcpServers": {
    "brave-search": {
      "type": "stdio",
      "command": "${CLAUDE_PLUGIN_ROOT}/bin/mcp-run",
      "args": ["brave-search"],
      "env": {
        "BRAVE_API_KEY": "${user_config.BRAVE_API_KEY}",
        "SHARED_MCP_URL": "${user_config.brave_mcp_url}",
        "SHARED_MCP_BEARER": "${user_config.mcp_bearer}"
      },
      "timeout": 600000
    }
  }
}
```

`bin/mcp-run <name>`: `SHARED_MCP_URL` empty → `exec npx -y <the server package>`; non-empty → `exec` a relay to that URL with `Authorization: Bearer $SHARED_MCP_BEARER` that reconnects on its own (Claude Code won't). The relay is your own small script or an existing client — `mcp-remote` or `mcp-proxy` in client mode are **unverified examples** (not checked or measured). Keep executables out of a top-level `bin/` if the plugin may be distributed through claude.ai organization settings (`components.md §8`).

### `userConfig` for L / U

```json
"userConfig": {
  "brave_mcp_url": {
    "type": "string",
    "title": "Brave MCP: shared server (optional)",
    "description": "Empty = local stdio server in every session. Otherwise the Streamable HTTP URL of the shared daemon, e.g. http://127.0.0.1:8733/mcp",
    "default": ""
  },
  "mcp_bearer": {
    "type": "string",
    "title": "Shared MCP server token",
    "description": "Bearer token for the shared daemon or proxy. Empty = no auth.",
    "sensitive": true,
    "default": ""
  }
}
```

For U: `"type": "http", "url": "${user_config.firecrawl_mcp_url}", "headers": {"Authorization": "Bearer ${user_config.mcp_bearer}"}` with the vendor URL as `default`. Do **not** use `options` (recipients below v2.1.271 can't load the plugin) or `headersHelper` (it can't see `${user_config.*}` and runs without `*TOKEN*`/`*KEY*`/`*SECRET*` env vars — `mcp.md §Which variables a helper can read`).

## 3. Checks before release

preflight (`scripts/preflight_plugin.py`) covers the statically checkable ones (marked ✓):

1. ✓ `claude plugin validate <plugin-dir>` passes — since v2.1.281 it reports entries that would be dropped, undeclared `${user_config.*}`, invalid URLs (`plugins__manifest-reference.md §Validate the manifest`).
2. ✓ Every `${user_config.X}` in a `url` has a non-empty `default` or `required: true` — otherwise `/mcp` shows `URL is unset or invalid` (observed by probe).
3. ✓ Every `${VAR}` has `:-default` — otherwise Claude Code warns and uses the literal `${VAR}` text (`mcp.md §Unset variables without a default`); for a plugin server the 2026-10-02 probe saw `✘ Failed to connect — Missing environment variables`.
4. ✓ No `${user_config.*}` in `headersHelper` (the server is reported misconfigured).
5. Token variables in `headers` aren't on the "read as empty" credential list (`mcp.md §Credential variables that read as empty`). Prove it live: `claude --plugin-dir . mcp list` → `✔ Connected`.
6. ✓ No `options` in `userConfig` when recipients may run Claude Code < 2.1.271.
7. Tool names are identical in every mode: `rg 'mcp__plugin_<plugin>_'` across skills, agents and hooks matches the server keys.
8. ✓ (within one marketplace) No two servers share an endpoint. Across a plugin and a user-scope server the dedupe is documented; between two plugins it was only observed (one silently vanished, which one is not established).
9. Long tools: `timeout` in the server entry ≥ the expected run; HTTP idle window is 5 min.
10. Daemon mode: an `initialize` request answers on the URL before the session starts; in L the relay survives a daemon restart.
