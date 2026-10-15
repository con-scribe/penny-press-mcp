# LitWit — The Literary Witness (agent guide)

LitWit is a notary for the written word: submit the SHA-256 fingerprint of a
work and receive a tamper-evident, hash-chained receipt proving it existed at
a point in time. Timestamping, not endorsement.

The service never sees your work — only its 64-character hash. Built for
writers, publishers, journalists, and their agents — including pseudonymous
ones, via optional pen-name labels and version chains that link drafts of the
same work as it comes into being.

For pure proof-of-existence, OpenTimestamps is free and trustless. LitWit is
for writers who need a public, checkable record of their work under a name
they chose, obtainable by anyone or anything with five cents.

## Endpoints

Send `Accept: application/json` — without it you may receive HTML.

- `POST /witness/attest` — $0.05 (USDC on Base, x402). Body:
  `{work_title, content_hash, author_label?, prev_entry_id?}`. Hash your work
  locally first; only the fingerprint leaves your machine. Returns 402 with
  payment instructions on first call — pay and retry with the proof
  (x402-aware clients handle both steps). Returns
  `{entry_id, seq, witnessed_at, entry_hash, verify_url}`.
- `GET /witness/verify?hash=…` — free. Check whether a fingerprint has been
  witnessed; returns matching entries or an empty result.
- `GET /witness/log` — free. The public append-only log, latest first; each
  entry hash-chains to the previous one.
- `GET /witness` — the human page.

## Verify independently

- Every entry's hash commits to the previous entry — tampering breaks the chain.
- The log head is anchored in DNS: `TXT _litwit-log.pennypress.org`
  (`v=LWH1 seq=<n> head=<hash>`). Compare with the latest `/witness/log` entry.
- No accounts, no API keys. It stays a listing under Penny Press:
  same domain, same wallet, same deploy.
