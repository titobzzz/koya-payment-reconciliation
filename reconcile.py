#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py

Rules (from README):
  * Skip lines that can't be read, and events without a txn_id.
  * A txn_id can have several attempts; only the latest one (by ts) counts.
  * A payment is collected only if its latest attempt is "success".
  * Amounts are sometimes strings with thousands separators ("4,804.15").
"""
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


def parse_amount(value):
    """Return the amount as a Decimal, handling strings like '4,804.15'."""
    if isinstance(value, str):
        value = value.replace(",", "").strip()
    return Decimal(str(value))


def parse_ts(value):
    """Parse an ISO-8601 UTC timestamp such as 2026-09-21T15:30:26Z."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# txn_id -> (timestamp, event) for the latest attempt seen so far.
# The file is NOT in time order, so compare timestamps instead of
# trusting line order.
latest = {}

with open("payments.jsonl", encoding="utf-8", errors="replace") as f:
    for line in f:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue 
        if not isinstance(event, dict):
            continue

        txn_id = event.get("txn_id")
        if not txn_id:
            continue  # no txn_id: ignore

        ts = parse_ts(event["ts"])
        if txn_id not in latest or ts >= latest[txn_id][0]:
            latest[txn_id] = (ts, event)

total = Decimal(0)
count = 0
for _, event in latest.values():
    if event["status"] == "success":
        total += parse_amount(event["amount"])
        count += 1

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{int(total.quantize(Decimal(1), rounding=ROUND_HALF_UP))}")