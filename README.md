![Penny Press logo](logo.png)
[![Listed on mcpservers.org](https://mcpservers.org/badge.svg)](https://mcpservers.org/servers/con-scribe/penny-press-mcp)

# Penny Press — MCP Server

**Free for humans. Pennies for machines.**

Penny Press ([pennypress.org](https://www.pennypress.org)) is a pseudonymous
pay-per-read writing vault: essays on freedom, economics and philosophy.
People read the full text free in a browser — no accounts, no signup.
Programmatic access costs a few cents in USDC on Base per read, gated by
the [x402](https://www.x402.org/) payment protocol.

## Connect

Remote MCP server over streamable HTTP — no installs, no Docker, no config
files. Paste the endpoint into your AI client:

- **Endpoint:** `https://www.pennypress.org/mcp`

| Client | Where to add |
|--------|--------------|
| Claude Desktop | `claude_desktop_config.json` → `url` field |
| Cursor | Settings → MCP → Add Server URL |
| Windsurf | MCP Config → Remote |

## Tools (all free)

- **`list_essays`** (no arguments) — catalog: titles, descriptions, prices,
  and reading URLs for every published piece.
- **`essay_payment_info`** (`slug` required, e.g. `river-of-time`) — the x402
  payment details for one piece: price, network, asset, and recipient wallet.
- **`lexicon_lookup`** (`term` required, e.g. `fiat-order`) — free metadata
  for a Lexicon term: part of speech, essays where it appears, plus payment
  info for the $0.01 full definition.
- **`lexicon_snapshot_info`** (no arguments) — payment details for the $0.25
  full Lexicon dataset snapshot.
- **`common_cents_info`** (no arguments) — the Common Cents collection: five
  themes, quote count, and payment info for the $0.01 full set.
- **`witness_verify`** (`content_hash` required) — check whether a SHA-256
  fingerprint has been witnessed by LitWit. Free.
- **`witness_attest_info`** (no arguments) — how LitWit attestation works and
  the $0.05 payment details.

The Literary Witness module behind `witness_*` is open source (MIT) under
[`litwit/`](./litwit/) — hash-chained, DNS-anchored timestamping for writers.

LitWit is listed on [PayAPI Market](https://payapi.market/api/litwit-the-literary-witness)
with a settlement-verified badge — PayAPI paid a real $0.05 attestation call
and received a real receipt.

## Reading (paid for machines)

`GET https://www.pennypress.org/essays/{slug}` returns the full text,
machine edition:

1. Request it without payment. You get `402 Payment Required` with payment
   instructions (x402 v2, scheme `exact`, USDC on Base).
2. Sign the payment with your own wallet tooling and retry with the payment
   proof in the **`Payment-Signature`** header.

Exact per-piece prices: `GET https://www.pennypress.org/.well-known/x402`
— the source of truth for prices and network. Payment requires a Base
wallet holding USDC. No account or signup anywhere in this flow.

Machine-readable docs: [`/llms.txt`](https://www.pennypress.org/llms.txt),
[`/skill.md`](https://www.pennypress.org/skill.md), [`/essays`](https://www.pennypress.org/essays)
(free catalog). See [SKILL.md](./SKILL.md) for the full agent skill,
including security rules.

## Security

Your wallet stays on your side. Nothing here asks for private keys, seed
phrases, or wallet exports. Sign payments only with your own trusted wallet
tooling, and verify the recipient matches the 402 instructions before
signing.

## License

Documentation in this repository is licensed under
[CC-BY-4.0](./LICENSE). Code (the `litwit/` module) is licensed under
[MIT](./LICENSE-MIT). The essays themselves remain the work of their
pseudonymous author.
