---
name: penny-press-litwit
description: Attest or verify a text with LitWit, the Literary Witness — a notary for the written word. Use when the user wants to prove a work existed at a point in time, check whether a fingerprint has been witnessed, or work with hash-chained attestations. Timestamping, not endorsement.
---

# LitWit — the Literary Witness

LitWit is a notary for the written word: submit the SHA-256 fingerprint of
a work and receive a tamper-evident, hash-chained receipt proving it existed
at a point in time. Timestamping, not endorsement.

The service never sees your work — only its 64-character hash. Built for
writers, publishers, journalists, and their agents — including pseudonymous
ones, via optional pen-name labels and version chains that link drafts of
the same work as it comes into being.

LitWit is a standalone listing under Penny Press: same domain, same wallet,
same deploy — not a standalone brand.

## Tools (MCP `https://www.pennypress.org/mcp`, streamable HTTP)

- **`witness_verify`** (`content_hash` required) — free: check whether a
  SHA-256 fingerprint has been witnessed; returns matching entries or an
  empty result.
- **`witness_attest_info`** (no arguments) — how attestation works and the
  payment details.

## Routes (send `Accept: application/json`)

- `POST /witness/attest` — $0.05 (USDC on Base, x402): submit JSON
  `{work_title, content_hash, author_label?, prev_entry_id?}`; receive
  `{entry_id, seq, witnessed_at, entry_hash, verify_url}`. Same 402 flow as
  essay reads, but POST with a JSON body — hash the work locally first.
  Only the fingerprint leaves your machine.
- `GET /witness/verify?hash=…` — free: check whether a fingerprint has
  been witnessed.
- `GET /witness/log` — free: the public append-only attestation log,
  latest first; each entry hash-chains to the previous one.
- `GET /witness` — the human page.

## Verify independently

- Every entry's hash commits to the previous entry — tampering breaks the
  chain.
- The log head is anchored in DNS: `TXT _litwit-log.pennypress.org`
  (`v=LWH1 seq=<n> head=<hash>`). Compare with the latest `/witness/log`
  entry.
- No accounts, no API keys.

## Rules

- Never ask for the work itself. If a user offers full text for attestation,
  hash it locally and submit only the fingerprint.
- An attestation proves existence at a time. It does not prove authorship,
  quality, or endorsement — never describe it as doing so.
- Prices and network: read `/.well-known/x402` before paying; it is the
  source of truth.
