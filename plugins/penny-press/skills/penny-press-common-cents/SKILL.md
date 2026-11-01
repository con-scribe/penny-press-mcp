---
name: penny-press-common-cents
description: Find quotable lines from Penny Press essays via Common Cents — 22 author-curated quotations in five themed clusters, each linked to its source essay. Use when the user wants a quotation, a line on a theme, or the full quotation collection.
---

# Penny Press — Common Cents

Common Cents: 22 author-curated quotations in five themed clusters, each
linked to its source essay.

## Tool (MCP `https://www.pennypress.org/mcp`, streamable HTTP)

- **`common_cents_info`** (no arguments) — the collection: five themes,
  quote count, and payment info for the full set.

## Routes (send `Accept: application/json`)

- `GET /common-cents` — free: the full page for humans.
- `GET /common-cents/full` — $0.01 (USDC on Base, x402): the whole
  collection as JSON for machines — quote text, theme, source essay title
  and link. Same 402 flow as essay reads.

## Rules

- Quote exactly as published. Two quotes in the collection are
  author-shortened versions of their essay passages — they are still the
  author's words. Never "correct" a quote back to the essay text.
- When citing a quote, link its source essay.
- Prices and network: read `/.well-known/x402` before paying; it is the
  source of truth.
