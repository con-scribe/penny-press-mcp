#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# The Literary Witness - provenance-as-a-service for writers and publishers.
#
# A writer hashes their manuscript locally (SHA-256 - we never see the work
# itself) and submits the fingerprint. The witness appends it to a public,
# hash-chained, append-only log and returns a receipt. Anyone can verify a
# hash and validate the chain, free, forever.
#
# Timestamping, not endorsement: we witness THAT bytes existed at a time,
# never WHAT they are worth. Not copyright registration, not legal advice.
#
# Human home:  GET /witness              (free HTML page + how-to guide)
#              GET /witness/attest       (free HTML - how to submit)
# Machine:     POST /witness/attest      (x402, $0.05 - submit an attestation)
#              GET /witness/log          (free JSON - the public log)
#              GET /witness/verify?hash= (free JSON - look up + chain check)
#              GET /witness/verify       (free HTML form when no hash given)
#
# The log lives in SQLite under WITNESS_DATA_DIR (default /data), which the
# deployment mounts as a persistent host volume - container rebuilds never
# touch it.
# ---------------------------------------------------------------------------

import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone

TITLE = "The Literary Witness"
TAGLINE = "A notary for the written word."
ATTEST_PRICE = "$0.05"

# Author-approved page copy (2026-10-11).
LEDE = (
    "The Literary Witness (LitWit) is a notary tool for writers and "
    "publishers. Submit the fingerprint of your work; receive a witnessed, "
    "tamper-evident record of its existence — no account, no legal name, "
    "no one reading your manuscript. Built for the pseudonymous age: "
    "independent writers, small publishers, and the AI agents who buy and "
    "sell their words."
)
HOW_IT_WORKS = (
    "Make a fingerprint of your work. Send the fingerprint, a title, and an "
    "optional pen name — five cents, paid through your AI agent. Get your "
    "receipt; anyone can verify it forever, free."
)
WHAT_IT_IS_NOT = (
    "Timestamping, not endorsement: we witness <em>that</em> these bytes "
    "existed at this time, never <em>what</em> they are worth. It is not "
    "copyright registration, and it is not legal advice. We never see your "
    "manuscript — only its fingerprint."
)

DATA_DIR = os.environ.get("WITNESS_DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "witness.db")

GENESIS_PREV = "GENESIS"
ANCHOR_RECORD = "_litwit-log.pennypress.org"
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
NL = chr(10)


def _db():
    os.makedirs(DATA_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = _db()
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id TEXT UNIQUE NOT NULL,
            witnessed_at TEXT NOT NULL,
            work_title TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            author_label TEXT,
            prev_entry_id TEXT,
            log_prev_hash TEXT NOT NULL,
            entry_hash TEXT NOT NULL,
            meta TEXT
        )
        """
    )
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_entries_hash ON entries(content_hash)"
    )
    con.commit()
    con.close()


def _entry_id(seq):
    return "lw-%06d" % seq


def _canonical(seq, entry_id, witnessed_at, work_title, content_hash,
               author_label, prev_entry_id, log_prev_hash):
    return json.dumps(
        {
            "seq": seq,
            "entry_id": entry_id,
            "witnessed_at": witnessed_at,
            "work_title": work_title,
            "content_hash": content_hash,
            "author_label": author_label,
            "prev_entry_id": prev_entry_id,
            "log_prev_hash": log_prev_hash,
        },
        sort_keys=True,
        ensure_ascii=False,
    )


def _hash_entry(*args):
    return hashlib.sha256(_canonical(*args).encode("utf-8")).hexdigest()


def _normalize_hash(h):
    if not isinstance(h, str):
        raise ValueError("content_hash must be a hex SHA-256 string")
    h = h.strip().lower()
    if h.startswith("sha256:"):
        h = h[7:]
    if not _HASH_RE.match(h):
        raise ValueError("content_hash must be a 64-character hex SHA-256 digest")
    return h


def attest(work_title, content_hash, author_label=None, prev_entry_id=None,
           meta=None):
    """Append one attestation to the log. Raises ValueError on bad input."""
    if not isinstance(work_title, str) or not work_title.strip():
        raise ValueError("work_title is required")
    work_title = work_title.strip()
    if len(work_title) > 200:
        raise ValueError("work_title must be 200 characters or fewer")
    content_hash = _normalize_hash(content_hash)
    if author_label is not None:
        author_label = str(author_label).strip() or None
        if author_label and len(author_label) > 80:
            raise ValueError("author_label must be 80 characters or fewer")
    if prev_entry_id is not None:
        prev_entry_id = str(prev_entry_id).strip() or None

    init_db()
    con = _db()
    try:
        if prev_entry_id:
            row = con.execute(
                "SELECT seq FROM entries WHERE entry_id = ?", (prev_entry_id,)
            ).fetchone()
            if row is None:
                raise ValueError("prev_entry_id does not exist")
        last = con.execute(
            "SELECT seq, entry_hash FROM entries ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        log_prev_hash = last["entry_hash"] if last else GENESIS_PREV
        witnessed_at = datetime.now(timezone.utc).isoformat()
        # Reserve the seq first so entry_id and hash commit to it.
        cur = con.execute(
            "INSERT INTO entries (entry_id, witnessed_at, work_title, "
            "content_hash, author_label, prev_entry_id, log_prev_hash, "
            "entry_hash, meta) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("pending", witnessed_at, work_title, content_hash, author_label,
             prev_entry_id, log_prev_hash, "pending",
             json.dumps(meta) if meta else None),
        )
        seq = cur.lastrowid
        entry_id = _entry_id(seq)
        entry_hash = _hash_entry(seq, entry_id, witnessed_at, work_title,
                                 content_hash, author_label, prev_entry_id,
                                 log_prev_hash)
        con.execute(
            "UPDATE entries SET entry_id = ?, entry_hash = ? WHERE seq = ?",
            (entry_id, entry_hash, seq),
        )
        con.commit()
    finally:
        con.close()
    return {
        "witness": TITLE,
        "entry_id": entry_id,
        "seq": seq,
        "work_title": work_title,
        "content_hash": content_hash,
        "author_label": author_label,
        "prev_entry_id": prev_entry_id,
        "witnessed_at": witnessed_at,
        "entry_hash": entry_hash,
        "verify_url": "/witness/verify?hash=" + content_hash,
    }


def get_log(limit=100):
    init_db()
    con = _db()
    try:
        rows = con.execute(
            "SELECT seq, entry_id, witnessed_at, work_title, content_hash, "
            "author_label, prev_entry_id, log_prev_hash, entry_hash "
            "FROM entries ORDER BY seq DESC LIMIT ?",
            (max(1, min(limit, 1000)),),
        ).fetchall()
        total = con.execute("SELECT COUNT(*) AS n FROM entries").fetchone()["n"]
    finally:
        con.close()
    return {"witness": TITLE, "total_entries": total,
            "entries": [dict(r) for r in rows]}


def find_by_hash(content_hash):
    content_hash = _normalize_hash(content_hash)
    init_db()
    con = _db()
    try:
        rows = con.execute(
            "SELECT seq, entry_id, witnessed_at, work_title, content_hash, "
            "author_label, prev_entry_id, log_prev_hash, entry_hash "
            "FROM entries WHERE content_hash = ? ORDER BY seq",
            (content_hash,),
        ).fetchall()
    finally:
        con.close()
    return [dict(r) for r in rows]


def verify_chain():
    """Recompute every entry hash from genesis. Returns a validity report."""
    init_db()
    con = _db()
    try:
        rows = con.execute(
            "SELECT seq, entry_id, witnessed_at, work_title, content_hash, "
            "author_label, prev_entry_id, log_prev_hash, entry_hash "
            "FROM entries ORDER BY seq"
        ).fetchall()
    finally:
        con.close()
    prev = GENESIS_PREV
    checked = 0
    for r in rows:
        if r["log_prev_hash"] != prev:
            return {"chain_valid": False, "entries_checked": checked,
                    "failed_at_seq": r["seq"], "reason": "log_prev_hash mismatch"}
        expect = _hash_entry(r["seq"], r["entry_id"], r["witnessed_at"],
                             r["work_title"], r["content_hash"],
                             r["author_label"], r["prev_entry_id"],
                             r["log_prev_hash"])
        if expect != r["entry_hash"]:
            return {"chain_valid": False, "entries_checked": checked,
                    "failed_at_seq": r["seq"], "reason": "entry_hash mismatch"}
        prev = r["entry_hash"]
        checked += 1
    head = dict(rows[-1]) if rows else None
    return {"chain_valid": True, "entries_checked": checked, "head": head}


def register_x402_routes(x402_routes, pay_to, network, publication_name):
    from x402.extensions.bazaar import OutputConfig, declare_discovery_extension

    x402_routes["POST /witness/attest"] = {
        "accepts": {
            "scheme": "exact",
            "payTo": pay_to,
            "price": ATTEST_PRICE,
            "network": network,
            # NOTE: the description is PUBLIC (agents read it before
            # deciding to pay).
            "extra": {
                "name": "USD Coin",
                "version": "2",
                "title": "The Literary Witness - attest a work",
                "description": (
                    "Witness the SHA-256 fingerprint of a literary work: "
                    "submit a title, content hash, and optional pen name; "
                    "receive a tamper-evident, hash-chained receipt. "
                    "Timestamping, not endorsement. We never see the work itself."
                ),
                "type": "attestation",
                "format": "json",
            },
        },
        "extensions": declare_discovery_extension(
            input={
                "work_title": "Title of the work (required, max 200 chars).",
                "content_hash": "Hex SHA-256 of the work (required).",
                "author_label": "Optional pen name or label (max 80 chars).",
                "prev_entry_id": "Optional entry_id of the previous version.",
            },
            input_schema={
                "type": "object",
                "properties": {
                    "work_title": {"type": "string"},
                    "content_hash": {"type": "string"},
                    "author_label": {"type": "string"},
                    "prev_entry_id": {"type": "string"},
                },
                "required": ["work_title", "content_hash"],
            },
            body_type="json",
            output=OutputConfig(
                example={
                    "witness": TITLE,
                    "entry_id": "lw-000001",
                    "entry_hash": "(sha256 of the canonical entry)",
                    "verify_url": "/witness/verify?hash=...",
                },
                schema={
                    "type": "object",
                    "properties": {
                        "witness": {"type": "string"},
                        "entry_id": {"type": "string"},
                        "seq": {"type": "integer"},
                        "work_title": {"type": "string"},
                        "content_hash": {"type": "string"},
                        "witnessed_at": {"type": "string"},
                        "entry_hash": {"type": "string"},
                        "verify_url": {"type": "string"},
                    },
                    "required": ["witness", "entry_id", "entry_hash"],
                },
            ),
        ),
    }


def get_head_anchor():
    """Return (seq, head_hash) of the current log head for DNS anchoring.
    The head entry_hash commits to the entire chain, so publishing it
    anchors the full history."""
    init_db()
    con = _db()
    try:
        total = con.execute("SELECT COUNT(*) AS n FROM entries").fetchone()["n"]
        if total == 0:
            return 0, GENESIS_PREV
        head = con.execute(
            "SELECT entry_hash FROM entries ORDER BY seq DESC LIMIT 1"
        ).fetchone()["entry_hash"]
    finally:
        con.close()
    return total, head


def _anchor_html():
    seq, head = get_head_anchor()
    txt_value = "v=LWH1 seq=%d head=%s" % (seq, head)
    return NL.join([
        "<h2>Anchoring</h2>",
        "<p>The log lives on our server. So that no one — not even us — can "
        "quietly rewrite its history, the fingerprint of the latest entry is "
        "also published in the domain's DNS records, which live outside the "
        "server.</p>",
        "<p>We publish this TXT record on the domain (updated after every attestation):</p>",
        '<p>Host: <code id="lw-anchor-host">_litwit-log</code> '
        '<button type="button" id="lw-anchor-copy-host">Copy</button></p>',
        '<p>Value: <code id="lw-anchor-txt">' + txt_value + "</code> "
        '<button type="button" id="lw-anchor-copy-txt">Copy</button></p>',
        "<p>Anyone can check it: look up the "
        "<code>_litwit-log.pennypress.org</code> TXT record, then compare it "
        "with the newest entry in "
        '<a href="/witness/log">the public log</a>. If they do not match, '
        "the log was changed after the anchor was published.</p>",
        "<script>",
        'document.getElementById("lw-anchor-copy-host").addEventListener("click", function() {',
        '  var t = document.getElementById("lw-anchor-host").textContent;',
        "  if (navigator.clipboard) navigator.clipboard.writeText(t);",
        "});",
        'document.getElementById("lw-anchor-copy-txt").addEventListener("click", function() {',
        '  var t = document.getElementById("lw-anchor-txt").textContent;',
        "  if (navigator.clipboard) navigator.clipboard.writeText(t);",
        "});",
        "</script>",
    ])


def _api_docs_html():
    parts = [
        "<h2>For machines</h2>",
        "<p>Programmatic access is pay-per-call via "
        '<a href="https://x402.org">x402</a> micropayments '
        "(USDC on Base, no account needed). Verification is always free.</p>",
        "<ul>",
        "<li><code>POST /witness/attest</code> — $0.05, submit "
        "<code>{work_title, content_hash, author_label?, "
        "prev_entry_id?}</code>; receive a witnessed receipt.</li>",
        "<li><code>GET /witness/log</code> — free, the public "
        "append-only log (latest first).</li>",
        "<li><code>GET /witness/verify?hash=</code> — free, look up a "
        "content hash and validate the chain.</li>",
        "</ul>",
    ]
    return NL.join(parts) + NL


def _hasher_html():
    return NL.join([
        '<h3>Step 1 — Fingerprint your work</h3>',
        "<p>Think of it like a fingerprint for your writing: a short code "
        "made from your exact words. Change even one comma and the code comes "
        "out completely different. That is what makes it proof.</p>",
        "<p>Your manuscript never leaves your hands — nothing is uploaded "
        "anywhere. Paste your text into the box below, or choose the file on "
        "your computer, and this page will make the fingerprint right here, "
        "inside your browser.</p>",
        '<textarea id="lw-text" rows="6" style="width:100%" '
        'placeholder="Paste your text here..."></textarea>',
        '<p><input type="file" id="lw-file"></p>',
        '<p>Fingerprint: <code id="lw-hash">—</code> '
        '<button type="button" id="lw-copy">Copy</button></p>',
        '<p class="read-meta">Keep the exact file or text you fingerprinted — '
        "checking only works on identical words.</p>",
        "<script>",
        "async function lwDigest(buf) {",
        '  var d = await crypto.subtle.digest("SHA-256", buf);',
        "  var b = new Uint8Array(d);",
        '  var h = "";',
        "  for (var i = 0; i < b.length; i++) {",
        "    var s = b[i].toString(16);",
        '    h += (s.length < 2 ? "0" + s : s);',
        "  }",
        "  return h;",
        "}",
        'var lwTa = document.getElementById("lw-text");',
        'var lwOut = document.getElementById("lw-hash");',
        'lwTa.addEventListener("input", async function() {',
        "  var v = lwTa.value;",
        '  lwOut.textContent = v ? await lwDigest(new TextEncoder().encode(v)) : "—";',
        "});",
        'document.getElementById("lw-file").addEventListener("change", async function(e) {',
        "  var f = e.target.files[0];",
        "  if (!f) return;",
        "  lwOut.textContent = await lwDigest(await f.arrayBuffer());",
        '  lwTa.value = "";',
        "});",
        'document.getElementById("lw-copy").addEventListener("click", function() {',
        "  if (navigator.clipboard) navigator.clipboard.writeText(lwOut.textContent);",
        "});",
        "</script>",
    ])


def _guide_html():
    return NL.join([
        "<h2>How to use</h2>",
        "<p>New here? Here is the whole thing in plain English, in four "
        "steps. No accounts, no software to install, no technical background "
        "needed.</p>",
        _hasher_html(),
        "<h3>Step 2 — Submit the fingerprint</h3>",
        "<p>Give the fingerprint — never your manuscript; the witness never "
        "sees your actual writing — to the Literary Witness, along with your "
        "title and, if you like, a pen name. It costs five cents, paid "
        "through your AI agent or any tool set up for small online payments. "
        "That small payment is what keeps the witness independent: no "
        "advertisers, no sponsors, no one to please but you. "
        '<a href="/witness/attest">How to submit</a>.</p>',
        "<h3>Step 3 — Keep your receipt</h3>",
        "<p>You will get back a receipt: an ID number for your entry (it "
        "looks like <code>lw-000007</code>), the exact date and time it was "
        "witnessed, and a web link anyone can use to check it. Save it with "
        "your manuscript — that receipt is your proof.</p>",
        "<h3>Step 4 — Anyone can check, free, forever</h3>",
        "<p>If someone wants to confirm a work is really yours — a reader, "
        "a publisher, another writer — they paste its fingerprint into the "
        "box below. The witness looks it up in its public record book and "
        "shows exactly when it was recorded. Free, no account needed.</p>",
        '<form action="/witness/verify" method="get">',
        '<input type="text" name="hash" size="64" '
        'placeholder="paste a 64-character fingerprint">',
        '<button type="submit">Verify</button>',
        "</form>",
        "<h3>The pages</h3>",
        "<ul>",
        '<li><a href="/witness/">/witness/</a> — this guide</li>',
        '<li><a href="/witness/attest">/witness/attest</a> — how to submit '
        "a fingerprint ($0.05)</li>",
        '<li><a href="/witness/log">/witness/log</a> — the public log, '
        "latest first</li>",
        '<li><a href="/witness/verify">/witness/verify</a> — verify '
        "a fingerprint</li>",
        "</ul>",
    ])


def _attest_info_html():
    return NL.join([
        '<a class="back" href="/witness">&larr; The Literary Witness</a>',
        '<h1 class="read-title">Attest a work</h1>',
        '<p class="read-meta">Submit a fingerprint. $0.05.</p>',
        '<div class="prose">',
        "<p>Attesting is done by software, not by hand. Your AI agent — or "
        "any tool set up for small online payments — sends your fingerprint "
        "to <code>POST /witness/attest</code> with a five-cent payment. The "
        "payment is handled by your agent; you never touch passwords or "
        "private keys on this page.</p>",
        "<p>First, make your fingerprint with the tool on "
        '<a href="/witness/">the guide</a> — your manuscript never leaves '
        "your browser. Then your agent sends a message like this:</p>",
        "<pre>{",
        '  "work_title": "My Essay",',
        '  "content_hash": "9f2c…e1",',
        '  "author_label": "Scribed",',
        '  "prev_entry_id": "lw-000006"',
        "}</pre>",
        "<p><code>author_label</code> is an optional pen name. "
        "<code>prev_entry_id</code> is optional too — use it to link a new "
        "version to the previous one. You will receive a receipt with your "
        "entry ID, the witness timestamp, and a verification link.</p>",
        "</div>",
    ])


def _verify_form_html():
    return NL.join([
        '<a class="back" href="/witness">&larr; The Literary Witness</a>',
        '<h1 class="read-title">Verify a fingerprint</h1>',
        '<div class="prose">',
        "<p>Paste a 64-character SHA-256 fingerprint to check it against "
        "the public log.</p>",
        '<form action="/witness/verify" method="get">',
        '<input type="text" name="hash" size="64" placeholder="fingerprint">',
        '<button type="submit">Verify</button>',
        "</form>",
        "</div>",
    ])


def register_routes(app, page_fn, publication_name, network):
    from fastapi import Request
    from fastapi.responses import HTMLResponse, JSONResponse

    init_db()

    @app.get("/witness", response_class=HTMLResponse)
    async def witness_home():
        body = (
            '<a class="back" href="/">&larr; Main page</a>' + NL
            + '<h1 class="read-title">The Literary Witness (LitWit)</h1>' + NL
            + '<p class="read-meta">' + TAGLINE + "</p>" + NL
            + '<div class="prose">' + NL
            + "<p>" + LEDE + "</p>" + NL
            + "<h2>How it works</h2>" + NL
            + "<p>" + HOW_IT_WORKS + "</p>" + NL
            + "<h2>What it is not</h2>" + NL
            + "<p>" + WHAT_IT_IS_NOT + "</p>" + NL
            + _guide_html() + NL
            + _anchor_html() + NL
            + "</div>" + NL
            + '<div class="note">' + _api_docs_html() + "</div>" + NL
        )
        return page_fn("The Literary Witness (LitWit) - " + publication_name, body)

    @app.get("/witness/attest", response_class=HTMLResponse)
    async def witness_attest_info():
        return page_fn(
            "Attest a work - " + publication_name, _attest_info_html()
        )

    @app.post("/witness/attest")
    async def witness_attest(request: Request):
        # Paid machine call. Gated by the x402 middleware - this handler
        # only runs after a valid payment has been verified and settled.
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid JSON body"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "JSON object required"}, status_code=400)
        try:
            receipt = attest(
                work_title=body.get("work_title", ""),
                content_hash=body.get("content_hash", ""),
                author_label=body.get("author_label"),
                prev_entry_id=body.get("prev_entry_id"),
            )
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        return receipt

    @app.get("/witness/log")
    async def witness_log():
        return get_log()

    @app.get("/witness/verify")
    async def witness_verify(hash: str = ""):
        if not hash.strip():
            result = page_fn(
                "Verify a fingerprint - " + publication_name,
                _verify_form_html(),
            )
            if isinstance(result, str):
                return HTMLResponse(content=result)
            return result
        try:
            matches = find_by_hash(hash)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        chain = verify_chain()
        return {
            "witness": TITLE,
            "query": hash.strip().lower(),
            "matches": matches,
            "chain_valid": chain["chain_valid"],
            "entries_checked": chain["entries_checked"],
        }
