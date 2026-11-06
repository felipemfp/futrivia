"""Copy named prompts from a build into one test fixture, so tests don't depend on which day a prompt lands on.

Usage: python3 -I tools/extract_prompts.py <days dir> <output.json> <prompt id>...
"""
import json, sys
from pathlib import Path

days_dir, out, wanted = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:]
found = {}
for day in sorted(days_dir.glob("*.json")):
    for prompt in json.loads(day.read_text(encoding="utf-8"))["prompts"]:
        if prompt["id"] in wanted:
            found[prompt["id"]] = prompt
missing = [w for w in wanted if w not in found]
if missing:
    sys.exit(f"not in this build: {', '.join(missing)}")
out.write_text(json.dumps([found[w] for w in wanted], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"{len(found)} prompts written to {out}")
