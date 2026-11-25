import sys
import os
sys.path.insert(0, os.path.abspath("."))

import json
from intent_parser import IntentParser

parser = IntentParser()
mismatches = 0
total = 0

for line in open('dev.jsonl', encoding='utf-8'):
    if not line.strip():
        continue
    req = json.loads(line)
    total += 1
    gold = req.get('filters', {})
    parsed = parser.parse(req['text'])
    mismatched_fields = []
    for k in ('category', 'colour', 'size', 'brand', 'max_price'):
        gv = gold.get(k)
        pv = parsed.get(k)
        if str(gv).lower() != str(pv).lower():
            mismatched_fields.append((k, gv, pv))
    if mismatched_fields:
        mismatches += 1
        print(f"Mismatch in {req['id']}: {mismatched_fields} | Text: {req['text']}")

print(f"Total: {total}, Mismatches: {mismatches}, Accuracy: {(total-mismatches)/total:.4f}")
