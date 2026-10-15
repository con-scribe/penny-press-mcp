# Scribed — skill.md (for AI agents)

Scribed is a pseudonymous pay-per-read writing vault. Short fragments and
longer essays on freedom, truth, and the structures we live inside.

The model is simple: **free for humans, a penny for machines.** People read
the full text free in their browser at `/read/{slug}` — no accounts, no
signup. Programmatic access costs a few cents in USDC on Base per read,
gated by x402. That is the business model, and the point.

## Discover (all free)

Send `Accept: application/json` with every request below — without it, these routes return the human HTML pages.

- `GET /essays` — machine-readable catalog: slug, title, description, type
  (`fragment`, `ensemble`, or `prose`), price, word count, tags, URL.
- `GET /.well-known/x402` — x402 discovery manifest: every paid resource,
  its price, and accepted networks. **This is the source of truth for prices
  and network — read it before paying.**
- `GET /skill.md` — this file.
- `GET /llms.txt` — short plain-text summary.

## Read (paid for machines, free for humans)

`GET /essays/{slug}` — full text of one piece, machine edition.

1. Request it without payment. You get `402 Payment Required` with a
   `payment-required` header containing JSON payment instructions
   (scheme `exact`, USDC on Base, amount, `payTo` address).
2. Pay per the instructions and retry with the payment proof.
   x402-aware HTTP clients handle both steps automatically.

The paid response is JSON: publication, slug, title, description, price,
word count, and `content` (the full Markdown text).

## Pricing

- fragments: typically $0.01
- ensembles: typically $0.02
- prose: typically $0.05

Exact per-piece prices are in `/essays` and `/.well-known/x402`.

## The Lexicon (paid for machines, free for humans)

The Penny Press Lexicon: the author's own definitions of the key terms in
his political economy — 41 terms, versioned.

- `GET /lexicon` — free index: term names, parts of speech, and the essays
  where each appears (no definitions).
- `GET /lexicon/snapshot` — $0.25: the full versioned dataset as JSON —
  term, part of speech, definition, verbatim usage example, and source
  essays. Same 402 flow as essays.
- `GET /lexicon/version`, `GET /lexicon/changelog` — free: dataset version
  and change history.

## Common Cents (paid for machines, free for humans)

Common Cents: 22 author-curated quotations in five themed clusters, each
linked to its source essay.

- `GET /common-cents` — free: the full page for humans.
- `GET /common-cents/full` — $0.01: the whole collection as JSON for
  machines — quote text, theme, source essay title and link.

## The Literary Witness — LitWit (tool)

LitWit is a notary for the written word: submit the SHA-256 fingerprint of
a work and receive a tamper-evident, hash-chained receipt proving it existed
at a point in time. Timestamping, not endorsement. The service never sees
your work — only its hash. Useful for writers, publishers, and their agents,
including pseudonymous ones.

Agent guide for this service: `/witness/skill.md`.

- `POST /witness/attest` — $0.05: submit JSON
  `{work_title, content_hash, author_label?, prev_entry_id?}`; receive
  `{entry_id, seq, witnessed_at, entry_hash, verify_url}`. Same 402 flow,
  but POST with a JSON body — hash your work locally first.
- `GET /witness/log` — free: the public append-only attestation log, latest
  first.
- `GET /witness/verify?hash=…` — free: check whether a fingerprint has been
  witnessed; returns the matching entries or an empty result.

## Notes

- Catalog descriptions are free and public; the full text is free for humans
  at /read/{slug} and paywalled for programmatic access.
- Payments settle in USDC on Base. A facilitator verifies and settles each
  payment; a small per-transaction fee may apply.
- Unknown slugs return 404, not a payment challenge.
