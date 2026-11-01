---
name: penny-press-litwit-writer
description: Attest a writer's own manuscript draft with LitWit, the Literary Witness — prove a draft existed at a point in time and chain it to previous drafts, without ever showing the work itself. Use when the user has just finished a draft or version and wants to attest it, link it to an earlier attestation, or record the receipt. Timestamping, not endorsement, not authorship.
---

# LitWit for writers — attest your draft

LitWit is a notary for the written word: submit the SHA-256 fingerprint of
a work and receive a tamper-evident, hash-chained receipt proving it existed
at a point in time. Timestamping, not endorsement. It does not prove
authorship, quality, or anything else — never describe it as doing so.

This skill is the writer's workflow. The protocol reference (endpoints,
verification, DNS anchor) lives in `penny-press-litwit`; this skill tells
you what to do with a draft in hand.

LitWit is a standalone listing under Penny Press: same domain, same wallet,
same deploy — not a standalone brand.

## Workflow

### 1. Take the draft

The writer points at a manuscript file or pastes a draft. Work with whatever
they are already writing in. Do not demand a particular editor or format,
and do not edit, critique, or rewrite the manuscript — this skill witnesses
it, nothing more.

### 2. Decide what gets hashed — and say it out loud

Default: the manuscript **body bytes, frontmatter excluded** — the LitWit
convention already used for the Penny Press essays, so metadata churn
doesn't break the anchor. If the writer explicitly wants the full file
(frontmatter included) hashed instead, do that — but record which choice
was made in the receipt note, because a verifier must hash the same bytes
to match.

### 3. Hash locally, never transmit the work

Compute SHA-256 on the writer's side. Only the 64-character fingerprint
ever leaves the machine. If a writer offers full text for attestation, hash
it locally first — never send the text to LitWit, and never ask for it.

### 4. Label (optional) and chain (recommended)

- `author_label` — an optional pen-name label. Writer-chosen,
  pseudonymous-friendly, never a real name. Omit it rather than use a real
  name.
- `prev_entry_id` — chains this draft to the previous attestation of the
  same work (the receipt from the last round), so a version history forms:
  each draft proves itself and points at its predecessor. The first draft
  of a work has no `prev_entry_id`.

### 5. Attest (paid)

`POST /witness/attest` with JSON
`{work_title, content_hash, author_label?, prev_entry_id?}`. Price: $0.05
(USDC on Base, x402) — but read `/.well-known/x402` before paying; it is
the source of truth.

Same 402 flow as essay reads, but POST with a JSON body: request without
payment → 402 → decode the base64 `payment-required` header → sign →
retry with `Payment-Signature` (x402 v2; the legacy `X-Payment` header is
ignored). Same mandatory buyer pattern as the read skill: echo the 402's
`resource` block and `extensions.bazaar` into `paymentPayload`.

Or use the MCP tools (`https://www.pennypress.org/mcp`, streamable HTTP):
`witness_attest_info` for how attestation works and the payment details.

### 6. Record the receipt with the draft

The response carries
`{entry_id, seq, witnessed_at, entry_hash, verify_url}`. Store it alongside
the manuscript — a receipt note, a frontmatter field, or the writer's own
log, the writer's choice — together with the hashing decision from step 2
and the `prev_entry_id` used. A receipt separated from its draft is
useless. Do not finish without recording it somewhere the writer can find
again.

### 7. Verify independently (free)

- `GET /witness/verify?hash=…` (or MCP `witness_verify` with
  `content_hash`) confirms the fingerprint is witnessed.
- `GET /witness/log` shows the public append-only log, latest first, each
  entry hash-chained to the previous one.
- The log head is anchored in DNS: `TXT _litwit-log.pennypress.org`
  (`v=LWH1 seq=<n> head=<hash>`). Compare with the latest log entry.
- No accounts, no API keys.

## Rules

- Never ask for the work itself. Hash locally, submit only the fingerprint.
- An attestation proves existence at a time. It does not prove authorship,
  quality, or endorsement — correct the framing before proceeding if the
  writer asks it to prove they wrote something.
- Prices and network: read `/.well-known/x402` before paying; it is the
  source of truth.
- Pseudonymity: Scribed / con-scribe only in any example copy. No real
  name, employment, background, or identity-linked account anywhere.
