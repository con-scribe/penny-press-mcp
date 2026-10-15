# server-patches

Synced copies of the live agent-facing docs: `skill.md` and `llms.txt`
(kept in sync with the deployed site).

## Retired patches

`mcp-services-patch.py` and `agent-json-services-patch.py` were retired
2026-10-14. They added the Lexicon / Common Cents / LitWit MCP tools and
agent.json intents to an older server base. Those features are already live
on the VPS, and the base the patches targeted no longer exists — the patches
abort against every current copy. The scripts are preserved in git history.
The live server (`server.py`) is deployed from the VPS only; the local stale
base was quarantined and is never a reference point for repo content.
