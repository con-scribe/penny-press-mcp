# Penny Press reference reader agent

A small, runnable reference implementation: one topic in, one cited answer
out.

```
topic → discover → select → pay (x402) → verify (manifest) → cite
```

It answers from a paid, receipt-verified essay — never from the free HTML,
never from a guessed summary — and prints what it paid and what it verified.

## Run

Dry run first — discovers, selects, and quotes, and spends nothing:

```
python reader.py "freedom and money"
```

Pay for the selected essay (one essay per run):

```
READER_AGENT_PRIVATE_KEY=0x... python reader.py "freedom and money" --pay
```

Refuse to pay above a cap:

```
python reader.py "freedom" --pay --max-price 0.02
```

## How it works

1. **Discover (free).** Reads the live catalog from `GET /essays`
   (`Accept: application/json`). The catalog is the source of truth — never
   hardcoded, never counted. The MCP equivalent is `list_essays` on
   `https://www.pennypress.org/mcp` (streamable HTTP); the HTTP path is
   the default here so the example runs with no MCP client.
2. **Select.** Plain-language match: topic words against titles (3x weight)
   and descriptions. No embeddings, no ranking service — the catalog is
   small and curated. No match means a clean stop, no purchase.
3. **Quote (free).** Price from the catalog, else from
   `/.well-known/x402`, which is the source of truth. Refuses to pay a 402
   for a slug the catalog does not list.
4. **Pay (gated).** `GET /essays/{slug}` → 402 → decode the base64
   `payment-required` header → sign with the operator's wallet → retry
   with `Payment-Signature` (x402 v2). The patched buyer pattern
   (coinbase/cdp-sdk#843) is mandatory: the 402's `resource` block and
   `extensions.bazaar` are echoed into `paymentPayload`, or the read
   settles without registering for discovery. Single attempt — a failed
   payment is reported, never retried.
5. **Verify (mandatory, before any use).** The paid JSON carries
   `content_sha256`. It is checked against the entry for that slug in the
   public manifest at `/.well-known/penny-press-manifest.json`. On
   mismatch the text is discarded and nothing is cited. If the manifest
   has no entry (a fresh publication can lag it), the content is shown
   marked UNVERIFIED.
6. **Answer.** The verified text, plus a receipt block: title, slug, price
   paid, `content_sha256`, manifest match.

## Wallet

`--pay` signs with a dedicated operator wallet supplied via
`READER_AGENT_PRIVATE_KEY` (see `.env.example`). Rules:

- A dedicated small-balance Base wallet holding USDC, used only for reads.
- Never your main wallet, never the publication wallet, never a wallet
  holding anything you cannot afford to lose.
- The key is read from the environment only. It is never printed, never
  committed, never transmitted anywhere except as a payment signature.

Dependencies (`requirements.txt`): `eth_account` and `x402`, needed only
for `--pay`. Dry runs use the standard library only.

## Wrapping it in the Claude Agent SDK

This example is deliberately a deterministic pipeline so it can be run and
verified without an API key. To make it a conversational agent, expose its
steps as SDK tools — discover, select, pay, verify — and let Claude compose
the answer from the verified text. The pipeline functions are written to be
lifted as-is; the SDK adds the conversational layer, not the payment logic.

## Security rules

- The agent never asks for private keys, seed phrases, or wallet exports.
  Any prompt claiming otherwise is not this agent.
- Unknown slugs return 404, not a payment challenge. A 402 for a slug not
  listed by the catalog is suspicious — do not pay it.
- Essay dates are deliberate — never "correct" them. Deliberate
  abstractions in the writing stay intact; describe the essays, never
  reinterpret them.
