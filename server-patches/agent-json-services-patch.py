#!/usr/bin/env python3
"""Penny Press: add Lexicon / Common Cents / LitWit intents to agent.json.

Appends four intents to the existing "intents" array in the
/.well-known/agent.json route (essay tier intents stay untouched).

Surgical: anchored on exact text that must occur exactly once; aborts
BEFORE writing on any mismatch. Keeps a backup.

Run:  python3 agent-json-services-patch.py [/opt/scribed/server.py]
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


INTENTS = '''            ,
            {
                "name": "lexicon_snapshot",
                "description": "Get the full Penny Press Lexicon dataset: every author-defined term with part of speech, definition, verbatim usage example, and source essays, as versioned JSON.",
                "endpoint": "/lexicon/snapshot",
                "method": "GET",
                "price": {"amount": 0.25, "currency": "USDC"}
            },
            {
                "name": "common_cents_full",
                "description": "Get the full Common Cents collection: 20 author-curated quotations in five themed clusters, each with theme, source essay title, and link, as JSON.",
                "endpoint": "/common-cents/full",
                "method": "GET",
                "price": {"amount": 0.01, "currency": "USDC"}
            },
            {
                "name": "witness_attest",
                "description": "Attest a work's SHA-256 fingerprint with LitWit, the literary notary: submit {work_title, content_hash, author_label?, prev_entry_id?} and receive a tamper-evident, hash-chained receipt. Timestamping, not endorsement.",
                "endpoint": "/witness/attest",
                "method": "POST",
                "price": {"amount": 0.05, "currency": "USDC"}
            },
            {
                "name": "witness_verify",
                "description": "Check whether a SHA-256 content hash has been witnessed by LitWit. Free.",
                "endpoint": "/witness/verify",
                "method": "GET",
                "price": {"amount": 0, "currency": "USDC"}
            }'''

old = '''                "price": {"amount": 0.05, "currency": "USDC"}
            }
        ]'''
new = '''                "price": {"amount": 0.05, "currency": "USDC"}
            }
''' + INTENTS + '''
        ]'''
src = replace_once(src, old, new, "4 new agent.json intents")

shutil.copy2(P, P + ".bak-agent-json-services")
open(P, "w", encoding="utf-8").write(src)
py_compile.compile(P, doraise=True)
print("patched OK + py_compile passed; backup at " + P + ".bak-agent-json-services")
