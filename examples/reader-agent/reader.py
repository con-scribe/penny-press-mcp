#!/usr/bin/env python3
"""Penny Press reference reader agent.

    topic -> discover -> select -> pay (x402) -> verify (manifest) -> cite

A small, runnable reference implementation, not a plugin: it shows how an
agent turns a topic into a verified Penny Press read. The discover, pay,
and verify steps are plain functions, so they can be lifted into any agent
framework — including the Claude Agent SDK, where they become tools and
Claude composes the answer from the verified text (see README.md).

Usage:
    python reader.py "freedom and money"          # dry run: no spend
    python reader.py "freedom and money" --pay    # pay for one essay
    python reader.py "freedom" --pay --max-price 0.02

Rules baked in (see the penny-press-read skill for the full story):
- The catalog is the source of truth. Never hardcoded, never counted.
- Prices come from /.well-known/x402; refuse to pay a 402 for a slug the
  catalog does not list.
- The patched buyer pattern (coinbase/cdp-sdk#843) is mandatory: echo the
  402's resource block and extensions.bazaar into paymentPayload, or the
  read settles without registering for discovery.
- The paid JSON carries content_sha256. Verify it against the public
  manifest before citing anything. On mismatch, discard and stop.
- One essay per run by default. The agent never holds keys: --pay signs
  with a dedicated operator wallet supplied via READER_AGENT_PRIVATE_KEY
  (see .env.example). Never your main wallet, never the publication wallet.
- Never retries a payment. A failed payment is reported, not repeated.
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE = "https://www.pennypress.org"
NETWORK = "eip155:8453"
USDC = "0x833589fCD6eDb6e08f4c7C32D4f71b54bdA02913"
PAYTO = "0x19ea1e953542d7ac76f042f8bdc94d81b964c53d"
RPC = "https://mainnet.base.org"
USER_AGENT = "penny-press-reader-agent/1.0"

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "by", "at", "from", "about", "what",
    "why", "how", "i", "me", "my", "we", "you", "it", "its", "this",
    "that", "as", "do", "does",
}


def http_get(url, headers=None):
    """GET returning (status, headers-dict, body-bytes); HTTP errors included."""
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "User-Agent": USER_AGENT, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def get_json(url):
    status, _, body = http_get(url)
    if status != 200:
        raise SystemExit(f"GET {url} -> HTTP {status}; expected 200")
    return json.loads(body)


def normalize_catalog(raw):
    """Accept a list or a dict wrapping one; normalize items to dicts."""
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        for key in ("essays", "items", "data", "results"):
            if isinstance(raw.get(key), list):
                items = raw[key]
                break
        else:
            items = [raw]
    else:
        items = []
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        slug = it.get("slug") or it.get("id") or it.get("name")
        if not slug:
            continue
        out.append({
            "slug": slug,
            "title": it.get("title", ""),
            "description": it.get("description") or it.get("summary")
                           or it.get("teaser") or "",
            "price_usd": _catalog_price(it),
        })
    return out


def _price_string(v):
    """Parse "$0.02" style strings; return USD float or None."""
    if isinstance(v, str):
        try:
            return float(v.strip().lstrip("$").strip())
        except ValueError:
            return None
    return None


def _catalog_price(item):
    for key in ("price_usd", "price", "usd"):
        v = item.get(key)
        if isinstance(v, (int, float)):
            return float(v)
        parsed = _price_string(v)
        if parsed is not None:
            return parsed
    v = item.get("amount")
    if isinstance(v, (int, float)):
        return float(v) / 1e6
    if isinstance(v, str) and v.isdigit():
        return int(v) / 1e6
    return None


def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def manifest_price_usd(slug, manifest):
    """Find a USD price for a slug inside /.well-known/x402, if present."""
    if not manifest:
        return None
    for node in walk(manifest):
        url = node.get("resource") or node.get("url") or ""
        if isinstance(url, str) and slug in url:
            parsed = _price_string(node.get("price"))
            if parsed is not None:
                return parsed
            if "amount" in node:
                try:
                    return int(node["amount"]) / 1e6
                except (ValueError, TypeError):
                    pass
        accepts = node.get("accepts")
        if isinstance(accepts, list):
            for acc in accepts:
                if not isinstance(acc, dict):
                    continue
                # accepts entries pair with a resource on a parent node;
                # match by slug anywhere in the enclosing node.
                if slug in json.dumps(node) and "amount" in acc:
                    try:
                        return int(acc["amount"]) / 1e6
                    except (ValueError, TypeError):
                        pass
    return None


def quote_price(slug, item, manifest):
    if item.get("price_usd") is not None:
        return item["price_usd"]
    return manifest_price_usd(slug, manifest)


def tokenize(text):
    return [w for w in re.findall(r"[a-z0-9]+", (text or "").lower())
            if w not in STOPWORDS]


def select(topic, items):
    """Plain-language match: title words weigh 3x description words."""
    topic_words = set(tokenize(topic))
    best, best_score = None, 0
    for item in items:
        score = (3 * len(topic_words & set(tokenize(item["title"])))
                 + len(topic_words & set(tokenize(item["description"]))))
        if score > best_score:
            best, best_score = item, score
    return best, best_score


def fetch_manifest_lookup():
    """slug -> content_sha256 from the public manifest (best effort)."""
    try:
        raw = get_json(BASE + "/.well-known/penny-press-manifest.json")
    except SystemExit as e:
        print(f"warning: manifest fetch failed ({e}); verification unavailable")
        return {}
    lookup = {}
    for node in walk(raw):
        slug = node.get("slug")
        sha = node.get("content_sha256") or node.get("sha256")
        if slug and sha:
            lookup[slug] = sha
    if isinstance(raw, dict):
        for slug, entry in raw.items():
            if isinstance(entry, str) and len(entry) == 64:
                lookup[slug] = entry
            elif isinstance(entry, dict):
                sha = entry.get("content_sha256") or entry.get("sha256")
                if sha:
                    lookup[slug] = sha
    return lookup


def rpc_usdc_balance(addr):
    data = "0x70a08231" + "0" * 24 + addr[2:].lower()
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                          "params": [{"to": USDC, "data": data}, "latest"]})
    req = urllib.request.Request(RPC, data=payload.encode(),
                                 headers={"Content-Type": "application/json",
                                          # mainnet.base.org rejects the
                                          # default Python UA; the buy
                                          # scripts use a browser UA too.
                                          "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())["result"]
    return int(result, 16) / 1e6


def pay_and_read(slug, max_price):
    """The 402 flow with the patched buyer pattern. Single attempt, no retry."""
    # Lazy imports: dry runs need no wallet libraries at all.
    from eth_account import Account as EthAccount
    from x402.client import x402ClientSync
    from x402.mechanisms.evm.exact.client import ExactEvmScheme
    from x402.schemas.payments import PaymentRequired

    key = os.environ.get("READER_AGENT_PRIVATE_KEY")
    if not key:
        raise SystemExit("READER_AGENT_PRIVATE_KEY is not set; refusing to pay "
                         "(see .env.example). Dry run works without it.")
    buyer = EthAccount.from_key(key).address
    if buyer.lower() == PAYTO.lower():
        raise SystemExit("ABORT: buyer is the publication wallet itself; "
                         "use a dedicated operator wallet, never the "
                         "publication wallet.")
    url = f"{BASE}/essays/{slug}"
    status, headers, _ = http_get(url)
    if status != 402:
        raise SystemExit(f"expected 402 for {slug}, got {status}; not paying")
    hdr = next((v for k, v in headers.items()
                if k.lower() == "payment-required"), None)
    if not hdr:
        raise SystemExit("402 without a payment-required header; not paying")
    # The payment details only exist after decoding the header. Never grep
    # raw 402 output for field names.
    pr_raw = json.loads(base64.b64decode(hdr))
    acc = pr_raw["accepts"][0]
    amount = int(acc["amount"])
    usd = amount / 1e6
    checks = {
        "scheme exact": acc.get("scheme") == "exact",
        "network": acc.get("network") == NETWORK,
        "asset USDC": acc.get("asset", "").lower() == USDC.lower(),
        "payTo publication": acc.get("payTo", "").lower() == PAYTO.lower(),
        "bazaar extension": bool((pr_raw.get("extensions") or {}).get("bazaar")),
    }
    print("402 terms:", checks)
    if not all(checks.values()):
        raise SystemExit("ABORT: 402 terms do not match — not paying")
    if max_price is not None and usd > max_price:
        raise SystemExit(f"ABORT: price ${usd:.2f} exceeds --max-price "
                         f"${max_price:.2f}")
    balance = rpc_usdc_balance(buyer)
    print(f"Buyer {buyer} USDC balance: ${balance:.2f} (need ${usd:.2f})")
    if balance < usd:
        raise SystemExit("insufficient buyer balance; not paying")

    pr_obj = PaymentRequired.model_validate(pr_raw)
    client = x402ClientSync()
    client.register(NETWORK, ExactEvmScheme(EthAccount.from_key(key)))
    # Mandatory: echo resource + extensions.bazaar, or the read settles
    # without registering for discovery (coinbase/cdp-sdk#843).
    payload_obj = client.create_payment_payload(
        pr_obj,
        resource=pr_obj.resource,
        extensions=dict(pr_obj.extensions) if pr_obj.extensions else None,
    )
    try:
        payload_dict = payload_obj.to_dict()
    except AttributeError:
        payload_dict = payload_obj.model_dump(by_alias=True, mode="json")
    assert payload_dict.get("resource"), "payload missing resource"
    assert (payload_dict.get("extensions") or {}).get("bazaar"), \
        "payload missing extensions.bazaar"
    pay_hdr = base64.b64encode(json.dumps(payload_dict).encode()).decode()

    status, _, body = http_get(url, {"Payment-Signature": pay_hdr})
    print("paid status:", status)
    if status != 200:
        raise SystemExit(f"payment failed ({body[:500]}); NOT retrying.")
    data = json.loads(body)
    if data.get("slug") != slug:
        raise SystemExit(f"slug mismatch: {data.get('slug')}")
    if not data.get("content"):
        raise SystemExit("empty content in paid response")
    return data


def main():
    ap = argparse.ArgumentParser(
        description="Penny Press reference reader agent (dry run by default)")
    ap.add_argument("topic", help="topic or question to find an essay for")
    ap.add_argument("--pay", action="store_true",
                    help="actually pay for the selected essay (default: dry run)")
    ap.add_argument("--max-price", type=float, default=None,
                    help="refuse to pay above this USD price")
    args = ap.parse_args()

    items = normalize_catalog(get_json(BASE + "/essays"))
    print(f"catalog loaded live: {len(items)} items")
    chosen, score = select(args.topic, items)
    if not chosen:
        print("no catalog match for this topic; stopping without purchase")
        return 0
    print(f"selected: {chosen['title']} (/{chosen['slug']}, match score {score})")

    manifest = None
    try:
        manifest = get_json(BASE + "/.well-known/x402")
    except SystemExit as e:
        print(f"warning: x402 manifest fetch failed ({e})")
    price = quote_price(chosen["slug"], chosen, manifest)
    if price is not None:
        print(f"quoted price: ${price:.2f} (exact terms at /.well-known/x402)")
    else:
        print("quoted price: unknown from catalog/manifest; "
              "the 402 itself will state the price before any payment")

    if not args.pay:
        print("dry run: stopping before payment. Re-run with --pay to buy.")
        return 0
    if price is not None and args.max_price is not None \
            and price > args.max_price:
        raise SystemExit(f"ABORT: quoted ${price:.2f} exceeds --max-price "
                         f"${args.max_price:.2f}")

    data = pay_and_read(chosen["slug"], args.max_price)

    lookup = fetch_manifest_lookup()
    sha = data.get("content_sha256")
    expected = lookup.get(chosen["slug"])
    if expected is None:
        print("manifest: no entry for this slug — content UNVERIFIED, "
              "shown with that warning")
    elif sha == expected:
        print(f"manifest: VERIFIED content_sha256 {sha}")
    else:
        print(f"manifest MISMATCH: paid {sha} vs manifest {expected}")
        raise SystemExit("discarding unverified content; not citing it")

    print(f"\n--- {data.get('title')} ---")
    print(data["content"])
    print("\n--- receipt ---")
    print(f"title: {data.get('title')}")
    print(f"slug: {chosen['slug']}")
    # The paid JSON carries price as a "$0.01" string; the quote fallback
    # is a float, which needs the $ added. Never print "$$0.01".
    paid_price = data.get("price", price)
    if isinstance(paid_price, str):
        print(f"price: {paid_price}")
    else:
        print(f"price: ${paid_price}")
    print(f"content_sha256: {sha}")
    print(f"manifest match: {'yes' if expected == sha else 'unknown (no entry)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
