# Changelog

## 1.1.0 — 2026-11-01

- New skill: `penny-press-litwit-writer` — attest a writer's own manuscript
  draft with LitWit, chain it to previous drafts via `prev_entry_id`, and
  record the receipt. Timestamping, not endorsement, not authorship.
- New example: `examples/reader-agent/` — a runnable reference agent
  (topic → discover → select → pay → verify → cite) with dry-run default
  and the patched x402 buyer pattern.

## 1.0.0 — 2026-11-01

- Initial pack: `penny-press` marketplace + plugin with four skills
  (`penny-press-read`, `penny-press-lexicon`, `penny-press-common-cents`,
  `penny-press-litwit`), MCP wiring to the direct `pennypress.org/mcp`
  endpoint, and the live 7-tool catalog.
- Skill copy derived from the live site skill docs, with live values
  (41 Lexicon terms, 22 Common Cents quotes) and the patched x402 buyer
  pattern and paid-receipt verification taught in the read skill.
