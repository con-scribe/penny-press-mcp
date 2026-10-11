# LitWit — The Literary Witness

**A notary for the written word.**

The Literary Witness (LitWit) is a notary tool for independent writers, small publishers, and their AI agents who require a witnessed, tamper-evident record of a body of work. At a time when power is centralizing on a global scale — threatening individual rights and freedoms through censorship, coercion, and control — freelance authors need technical tools that protect the integrity of their work.

LitWit provides provenance-as-a-service that timestamps without endorsing. The writer creates a digital fingerprint of the work's bytes using the SHA-256 cryptographic hash standard — the service never sees the work itself, only its fingerprint. That fingerprint is appended to a public, hash-chained, append-only log, and the writer receives a witnessed receipt. Anyone can then use the fingerprint, free and forever, to verify that the work existed at a point in time. No account required.

Pseudonymous writers who wish to protect their anonymity can use LitWit to establish provenance in the digital age. As the agentic economy takes shape, open-source tools like LitWit help writers strengthen trust and editorial integrity.

Scribe — 2026/10/11

---

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
