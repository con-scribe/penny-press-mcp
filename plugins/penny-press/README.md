# Penny Press — Claude Code plugin

Penny Press (pennypress.org) is a pseudonymous pay-per-read writing vault:
essays on freedom, economics, and philosophy. **Free for humans. Pennies for
machines.** People read the full text free in a browser — no accounts, no
signup. Programmatic access costs a few cents in USDC on Base per read,
gated by x402.

## Install

```
/plugin marketplace add con-scribe/penny-press-mcp
/plugin install penny-press@penny-press
```

This registers the `penny-press` marketplace and installs the `penny-press`
plugin, which bundles five skills and the Penny Press MCP server
(`https://www.pennypress.org/mcp`, streamable HTTP).

## Skills

- **penny-press-read** — discover, pay for, and verify essay reads. The core
  skill: catalog via `list_essays`, price via `essay_payment_info`, full text
  via x402, receipt verified against the public content manifest.
- **penny-press-lexicon** — look up author-defined terms (`lexicon_lookup`)
  and the full versioned dataset (`lexicon_snapshot_info`).
- **penny-press-common-cents** — the author-curated quotation collection
  (`common_cents_info`).
- **penny-press-litwit** — attest or verify a text's SHA-256 fingerprint
  (`witness_attest_info`, `witness_verify`). Timestamping, not endorsement.
- **penny-press-litwit-writer** — attest a writer's own manuscript draft,
  chain it to previous drafts, and record the receipt. Timestamping, not
  endorsement, not authorship.

Skills are namespaced `penny-press:<skill-name>` when the plugin is enabled.

## MCP tools (7)

`list_essays`, `essay_payment_info`, `lexicon_lookup`,
`lexicon_snapshot_info`, `common_cents_info`, `witness_verify`,
`witness_attest_info`.

## Prices (agent-facing; exact prices always at `/.well-known/x402`)

Fragments $0.01, ensembles $0.02, prose $0.05; full bundle $0.32; Lexicon
snapshot $0.25; Common Cents full set $0.01; LitWit attestation $0.05;
audio reads $0.10.

## License

Skill docs follow the repo's docs license (CC-BY-4.0). The essays themselves
are not in this repo.

## Notes

- The catalog grows. Skills never hardcode essay counts or enumerate essays;
  `list_essays` is always the source of truth.
- Known check at install-test time: the marketplace `owner` carries a name
  only (no email), by design for a pseudonymous project. If validation
  rejects that, add an owner email then — not before.
