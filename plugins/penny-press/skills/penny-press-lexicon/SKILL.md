---
name: penny-press-lexicon
description: Look up author-defined terms from the Penny Press Lexicon — the vocabulary of a free political economy, defined deliberately. Use when the user asks what a term means in Scribed's writing, or wants a definition with its verbatim in-essay example.
---

# Penny Press — the Lexicon

The Penny Press Lexicon: the author's own definitions of the key terms in
his political economy — 41 terms, versioned, A–Z.

## Tools (MCP `https://www.pennypress.org/mcp`, streamable HTTP)

- **`lexicon_lookup`** (`term` required) — free metadata for a term: part of
  speech and the essays where it appears.
- **`lexicon_snapshot_info`** (no arguments) — payment details for the full
  versioned dataset snapshot.

## Routes (send `Accept: application/json`)

- `GET /lexicon` — free index: term names, parts of speech, and the essays
  where each appears (no definitions).
- `GET /lexicon/snapshot` — $0.25 (USDC on Base, x402): the full versioned
  dataset as JSON — term, part of speech, definition, verbatim usage
  example, and source essays. Same 402 flow as essay reads: request, get
  402 with payment instructions, pay, retry with `Payment-Signature`.
- `GET /lexicon/version`, `GET /lexicon/changelog` — free: dataset version
  and change history.

## Rules

- Every term needs a verbatim in-essay example. When quoting a definition,
  include its example — a definition without its example is incomplete.
- Definitions are the author's own. Do not substitute dictionary definitions,
  and do not "correct" a definition toward mainstream usage.
- Prices and network: read `/.well-known/x402` before paying; it is the
  source of truth.
