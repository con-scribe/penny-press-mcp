# LitWit — The Literary Witness

**A notary for the written word.** MIT-licensed, self-hostable provenance-as-a-service for writers and publishers.

A writer hashes their manuscript locally (SHA-256 — the service never sees the work itself) and submits the fingerprint. The witness appends it to a public, hash-chained, append-only log and returns a receipt. Anyone can verify a hash and validate the chain, free, forever.

Timestamping, not endorsement: it witnesses *that* bytes existed at a time, never *what* they are worth. Not copyright registration, not legal advice.

Live instance: [pennypress.org/witness](https://www.pennypress.org/witness)

## Endpoints

| Route | Access | Purpose |
|---|---|---|
| `GET /witness` | free | Human page: how-to guide, verify form, DNS anchor |
| `GET /witness/attest` | free | How to submit |
| `POST /witness/attest` | x402 ($0.05) | Submit `{work_title, content_hash, author_label?, prev_entry_id?}` → `{entry_id, seq, witnessed_at, entry_hash, verify_url}` |
| `GET /witness/log` | free | The public append-only log (JSON) |
| `GET /witness/verify?hash=…` | free | Look up a fingerprint + chain check |

## Self-hosting

`witness.py` is a pluggable FastAPI module (stdlib + FastAPI only):

```python
import witness

witness.register_routes(app, page_fn, publication_name, network)
witness.register_x402_routes(x402_routes, pay_to, network, publication_name)
```

- `register_routes(app, page_fn, publication_name, network)` — mounts the human pages and free JSON endpoints. `page_fn` is your site's HTML page wrapper.
- `register_x402_routes(x402_routes, pay_to, network, publication_name)` — declares the paid `POST /witness/attest` route for your x402 payment middleware, including the Bazaar discovery extension.
- The log lives in SQLite under `WITNESS_DATA_DIR` (default `/data`). Mount it as a persistent volume — container rebuilds must never touch it.
- DNS anchoring is the operator's job: after each attestation, publish the current `seq`/`head` (from `witness.get_head_anchor()`) as a TXT record so the outside world can cross-check the log head.

## License

MIT — see [LICENSE-MIT](../LICENSE-MIT). Run your own notary; the trust is in the public log, not the operator.
