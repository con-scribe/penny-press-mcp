#!/usr/bin/env python3
"""Penny Press: MCP tools for Lexicon, Common Cents, and LitWit.

Adds five stateless /mcp tools alongside the existing list_essays and
essay_payment_info, following the same conventions (annotations, outputSchema,
text content + structuredContent):

  - lexicon_lookup       free term metadata + $0.01 definition payment info
  - lexicon_snapshot_info  $0.25 full-dataset payment details
  - common_cents_info    free themes overview + $0.01 full-set payment info
  - witness_verify       free SHA-256 witness lookup (real log query)
  - witness_attest_info  $0.05 attestation how-to + payment details

Surgical: every edit is anchored on exact text that must occur exactly
once; on any mismatch it aborts BEFORE writing anything. Keeps a backup.

Run:  python3 mcp-services-patch.py [/opt/scribed/server.py]
"""

import py_compile
import shutil
import sys

P = sys.argv[1] if len(sys.argv) > 1 else "/opt/scribed/server.py"
src = open(P, encoding="utf-8").read()


def replace_once(s, old, new, label):
    n = s.count(old)
    if n != 1:
        print(f"ABORT: anchor '{label}' found {n}x (expected 1). Nothing written.")
        sys.exit(1)
    print(f"ok: {label}")
    return s.replace(old, new, 1)


ANNOT = '''        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
'''

# ---------------------------------------------------------------- tools ---
TOOLS = '''    {
        "name": "lexicon_lookup",
        "description": (
            "Look up a term in the Penny Press Lexicon (the author's own "
            "definitions of his political-economy vocabulary). Returns free "
            "metadata — part of speech and the essays where the term appears — "
            "plus payment info for the $0.01 full definition."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "term": {"type": "string",
                         "description": "The term or its slug, e.g. 'fiat-order'"},
            },
            "required": ["term"],
            "additionalProperties": False,
        },
''' + ANNOT + '''        "outputSchema": {
            "type": "object",
            "properties": {
                "found": {"type": "boolean"},
                "term": {"type": "string"},
                "slug": {"type": "string"},
                "part_of_speech": {"type": "string"},
                "appears_in": {"type": "array", "items": {"type": "string"},
                               "description": "Essay slugs where the term is used"},
                "definition_price": {"type": "string"},
                "definition_url": {"type": "string",
                                   "description": "Paid machine read via x402"},
            },
            "required": ["found"],
            "additionalProperties": False,
        },
    },
    {
        "name": "lexicon_snapshot_info",
        "description": (
            "Payment details for the Penny Press Lexicon full dataset snapshot "
            "($0.25): every author-defined term with part of speech, definition, "
            "verbatim usage example, and source essays, as versioned JSON."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
''' + ANNOT + '''        "outputSchema": {
            "type": "object",
            "properties": {
                "price": {"type": "string", "description": "Price in USDC, e.g. $0.25"},
                "asset": {"type": "string", "description": "Payment asset, USDC"},
                "network": {"type": "string", "description": "Chain id, e.g. eip155:8453 (Base mainnet)"},
                "recipient": {"type": "string", "description": "Wallet receiving the payment"},
                "machine_url": {"type": "string", "description": "Paid machine read via x402"},
                "term_count": {"type": "integer"},
                "version": {"type": "string"},
            },
            "required": ["price", "asset", "network", "recipient", "machine_url"],
            "additionalProperties": False,
        },
    },
    {
        "name": "common_cents_info",
        "description": (
            "Overview of Common Cents, the Penny Press collection of 22 "
            "author-curated quotations in five themed clusters: the themes, "
            "quote count, and payment info for the $0.01 full machine-readable set."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
''' + ANNOT + '''        "outputSchema": {
            "type": "object",
            "properties": {
                "collection": {"type": "string"},
                "themes": {"type": "array", "items": {"type": "string"}},
                "quote_count": {"type": "integer"},
                "price": {"type": "string", "description": "Price in USDC, e.g. $0.01"},
                "asset": {"type": "string", "description": "Payment asset, USDC"},
                "network": {"type": "string", "description": "Chain id, e.g. eip155:8453 (Base mainnet)"},
                "recipient": {"type": "string", "description": "Wallet receiving the payment"},
                "machine_url": {"type": "string", "description": "Paid machine read via x402"},
                "human_url": {"type": "string", "description": "Free page for humans"},
            },
            "required": ["collection", "themes", "quote_count", "price", "machine_url"],
            "additionalProperties": False,
        },
    },
    {
        "name": "witness_verify",
        "description": (
            "Check whether a SHA-256 content hash has been witnessed by LitWit, "
            "the Penny Press literary notary. Free. Returns the matching "
            "attestation entries (entry id, sequence, timestamp, title) or an "
            "empty result."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content_hash": {"type": "string",
                                 "description": "Hex SHA-256 fingerprint of the work"},
            },
            "required": ["content_hash"],
            "additionalProperties": False,
        },
''' + ANNOT + '''        "outputSchema": {
            "type": "object",
            "properties": {
                "witnessed": {"type": "boolean"},
                "entries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "entry_id": {"type": "string"},
                            "seq": {"type": "integer"},
                            "witnessed_at": {"type": "string"},
                            "work_title": {"type": "string"},
                            "author_label": {"type": "string"},
                        },
                    },
                },
                "verify_url": {"type": "string"},
            },
            "required": ["witnessed", "entries"],
            "additionalProperties": False,
        },
    },
    {
        "name": "witness_attest_info",
        "description": (
            "How to attest a work's fingerprint with LitWit ($0.05): what to "
            "submit, what the tamper-evident receipt contains, and the x402 "
            "payment details. The service never sees your work — only its hash."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
''' + ANNOT + '''        "outputSchema": {
            "type": "object",
            "properties": {
                "price": {"type": "string", "description": "Price in USDC, e.g. $0.05"},
                "asset": {"type": "string", "description": "Payment asset, USDC"},
                "network": {"type": "string", "description": "Chain id, e.g. eip155:8453 (Base mainnet)"},
                "recipient": {"type": "string", "description": "Wallet receiving the payment"},
                "machine_url": {"type": "string", "description": "POST the attestation here via x402"},
                "submits": {"type": "object", "description": "JSON fields the endpoint accepts"},
                "returns": {"type": "object", "description": "Fields in the witnessed receipt"},
                "note": {"type": "string"},
            },
            "required": ["price", "machine_url", "submits", "returns"],
            "additionalProperties": False,
        },
    },
'''

old_tools = '''            "required": ["slug", "title", "price", "asset", "network", "recipient", "machine_url"],
            "additionalProperties": False,
        },
    },
]'''
new_tools = '''            "required": ["slug", "title", "price", "asset", "network", "recipient", "machine_url"],
            "additionalProperties": False,
        },
    },
''' + TOOLS + ''']'''
src = replace_once(src, old_tools, new_tools, "5 new tool dicts")

# ------------------------------------------------------------- handlers ---
HANDLERS = '''            if name == "lexicon_lookup":
                return _resp(mid, result={
                    "content": [{"type": "text",
                                 "text": _mcp_lexicon_lookup_text(args.get("term", ""))}],
                    "structuredContent":
                        _mcp_lexicon_lookup_struct(args.get("term", ""))})
            if name == "lexicon_snapshot_info":
                return _resp(mid, result={
                    "content": [{"type": "text", "text": _mcp_lexicon_snapshot_text()}],
                    "structuredContent": _mcp_lexicon_snapshot_struct()})
            if name == "common_cents_info":
                return _resp(mid, result={
                    "content": [{"type": "text", "text": _mcp_common_cents_text()}],
                    "structuredContent": _mcp_common_cents_struct()})
            if name == "witness_verify":
                return _resp(mid, result={
                    "content": [{"type": "text",
                                 "text": _mcp_witness_verify_text(args.get("content_hash", ""))}],
                    "structuredContent":
                        _mcp_witness_verify_struct(args.get("content_hash", ""))})
            if name == "witness_attest_info":
                return _resp(mid, result={
                    "content": [{"type": "text", "text": _mcp_witness_attest_info_text()}],
                    "structuredContent": _mcp_witness_attest_info_struct()})
'''

old_handler = '''            if name == "list_essays":'''
src = replace_once(src, old_handler, HANDLERS + old_handler,
                   "5 new handlers before list_essays")

# -------------------------------------------------------------- helpers ---
HELPERS = '''def _mcp_lexicon_entry(term):
    """Find a lexicon term by slug or name (case-insensitive)."""
    if not term:
        return None
    key = term.strip().lower().replace(" ", "-")
    g = lexicon.GLOSSARY
    if key in g:
        return g[key]
    for slug, e in g.items():
        if e.get("term", "").lower() == term.strip().lower():
            return e
    return None


def _mcp_lexicon_lookup_text(term):
    e = _mcp_lexicon_entry(term)
    if e is None:
        return (f"Unknown Lexicon term '{term}'. "
                f"The Lexicon holds {len(lexicon.GLOSSARY)} author-defined terms; "
                f"see {SITE_URL}/lexicon for the full index.")
    lines = [f"{e.get('term')} ({e.get('part_of_speech', '?')})",
             f"Appears in: {', '.join(e.get('essays', [])) or '—'}",
             f"Full definition ($0.01) via x402 at "
             f"{SITE_URL}/glossary/{e.get('slug')}",
             f"Full dataset snapshot ({lexicon.SNAPSHOT_PRICE}): {SITE_URL}/lexicon/snapshot"]
    return "\\n".join(lines)


def _mcp_lexicon_lookup_struct(term):
    e = _mcp_lexicon_entry(term)
    if e is None:
        return {"found": False}
    return {
        "found": True,
        "term": e.get("term"),
        "slug": e.get("slug"),
        "part_of_speech": e.get("part_of_speech"),
        "appears_in": e.get("essays", []),
        "definition_price": "$0.01",
        "definition_url": f"{SITE_URL}/glossary/{e.get('slug')}",
    }


def _mcp_lexicon_snapshot_text():
    return ("The Penny Press Lexicon snapshot: "
            f"{len(lexicon.GLOSSARY)} author-defined terms, v{lexicon.LEXICON_VERSION}, "
            f"{lexicon.SNAPSHOT_PRICE} via x402 at {SITE_URL}/lexicon/snapshot. "
            "Each term carries part of speech, definition, verbatim usage example, "
            "and source essays.")


def _mcp_lexicon_snapshot_struct():
    return {
        "price": lexicon.SNAPSHOT_PRICE,
        "asset": "USDC",
        "network": NETWORK,
        "recipient": PAY_TO,
        "machine_url": f"{SITE_URL}/lexicon/snapshot",
        "term_count": len(lexicon.GLOSSARY),
        "version": lexicon.LEXICON_VERSION,
    }


def _mcp_common_cents_text():
    themes = sorted({q[0] for q in common_cents.QUOTES})
    return ("Common Cents: "
            f"{len(common_cents.QUOTES)} author-curated quotations in "
            f"{len(themes)} themed clusters ({'; '.join(themes)}). "
            f"Full machine-readable set: {common_cents.FULL_PRICE} via x402 at "
            f"{SITE_URL}/common-cents/full. Free for humans at "
            f"{SITE_URL}/common-cents.")


def _mcp_common_cents_struct():
    return {
        "collection": common_cents.TITLE,
        "themes": sorted({q[0] for q in common_cents.QUOTES}),
        "quote_count": len(common_cents.QUOTES),
        "price": common_cents.FULL_PRICE,
        "asset": "USDC",
        "network": NETWORK,
        "recipient": PAY_TO,
        "machine_url": f"{SITE_URL}/common-cents/full",
        "human_url": f"{SITE_URL}/common-cents",
    }


def _mcp_witness_verify_text(content_hash):
    try:
        entries = witness.find_by_hash(content_hash)
    except Exception:
        entries = []
    if not entries:
        return (f"No LitWit attestation found for that fingerprint. "
                f"Attest it for {witness.ATTEST_PRICE} at {SITE_URL}/witness/attest.")
    lines = [f"Witnessed ({len(entries)} entr{'y' if len(entries) == 1 else 'ies'}):"]
    for en in entries:
        lines.append(f"- {en.get('entry_id')} (seq {en.get('seq')}, "
                     f"{en.get('witnessed_at')}): {en.get('work_title')}")
    return "\\n".join(lines)


def _mcp_witness_verify_struct(content_hash):
    try:
        entries = witness.find_by_hash(content_hash)
    except Exception:
        entries = []
    return {
        "witnessed": bool(entries),
        "entries": [{
            "entry_id": en.get("entry_id"),
            "seq": en.get("seq"),
            "witnessed_at": en.get("witnessed_at"),
            "work_title": en.get("work_title"),
            "author_label": en.get("author_label"),
        } for en in entries],
        "verify_url": f"{SITE_URL}/witness/verify?hash={content_hash}",
    }


def _mcp_witness_attest_info_text():
    return ("LitWit attestation: hash your work locally (SHA-256), then POST "
            "{work_title, content_hash, author_label?, prev_entry_id?} to "
            f"{SITE_URL}/witness/attest — {witness.ATTEST_PRICE} via x402. "
            "You receive a tamper-evident, hash-chained receipt "
            "{entry_id, seq, witnessed_at, entry_hash, verify_url}. "
            "Timestamping, not endorsement; the service never sees your work. "
            f"Verify free at {SITE_URL}/witness/verify?hash=…")


def _mcp_witness_attest_info_struct():
    return {
        "price": witness.ATTEST_PRICE,
        "asset": "USDC",
        "network": NETWORK,
        "recipient": PAY_TO,
        "machine_url": f"{SITE_URL}/witness/attest",
        "submits": {
            "work_title": "string, required, max 200 chars",
            "content_hash": "string, required, hex SHA-256",
            "author_label": "string, optional, max 80 chars",
            "prev_entry_id": "string, optional, links versions",
        },
        "returns": {
            "entry_id": "string, e.g. lw-000001",
            "seq": "integer",
            "witnessed_at": "string, ISO-8601 UTC",
            "entry_hash": "string, sha256 of the canonical entry",
            "verify_url": "string",
        },
        "note": "Timestamping, not endorsement. Hash locally; only the hash is submitted.",
    }


'''

old_card = '''@app.get("/.well-known/mcp/server-card.json", include_in_schema=False)'''
src = replace_once(src, old_card, HELPERS + old_card, "MCP helpers")

shutil.copy2(P, P + ".bak-mcp-services")
open(P, "w", encoding="utf-8").write(src)
py_compile.compile(P, doraise=True)
print("patched OK + py_compile passed; backup at " + P + ".bak-mcp-services")
