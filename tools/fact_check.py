"""T16 fact check: sample 20 generated prompts and 3 answers each, and check each answer's club against Wikipedia.

Usage: python3 -I tools/fact_check.py <days dir> <output.json>
An answer is auto-confirmed when the player's Portuguese or English Wikipedia article names a club in its evidence;
the rest are judged by hand and recorded in reports/fact-check.md.
"""
import json, random, re, sys, time, unicodedata, urllib.parse, urllib.request
from pathlib import Path

UA = {"User-Agent": "futrivia/0.1 (https://github.com/felipemfp/futrivia)"}
CLUB_WORDS = {"Atlético-MG": ["atletico", "mineiro"], "Athletico-PR": ["athletico"], "Atlético-GO": ["goianiense"],
              "América-MG": ["america"], "São Paulo": ["sao", "paulo"], "Red Bull Bragantino": ["bragantino"],
              "Ponte Preta": ["ponte", "preta"], "Santa Cruz": ["santa", "cruz"]}


def plain(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if not unicodedata.combining(c))
    return set(re.sub(r"[^a-z0-9]+", " ", s).split())


def get(url):
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
        except Exception:
            time.sleep(5 * (attempt + 1))
    return {}


def article(qid):
    e = get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "wbgetentities", "ids": qid, "props": "sitelinks", "format": "json"})).get("entities", {}).get(qid, {})
    for wiki, host in (("ptwiki", "pt.wikipedia.org"), ("enwiki", "en.wikipedia.org")):
        title = e.get("sitelinks", {}).get(wiki, {}).get("title")
        if title:
            page = get(f"https://{host}/w/api.php?" + urllib.parse.urlencode(
                {"action": "query", "prop": "extracts", "explaintext": 1, "titles": title, "format": "json"}))
            text = " ".join(v.get("extract", "") for v in page.get("query", {}).get("pages", {}).values())
            return f"https://{host}/wiki/{urllib.parse.quote(title.replace(' ', '_'))}", plain(text)
    return "", set()


days = sorted(Path(sys.argv[1]).glob("*.json"))
prompts = {p["id"]: p for d in days for p in json.loads(d.read_text())["prompts"]}
rng = random.Random("futrivia-fact-check")
sample = rng.sample(sorted(prompts), 20)
rows = []
for pid in sample:
    p = prompts[pid]
    answers = p["answers"]
    picks = [answers[0], answers[len(answers) // 2], answers[-1]]
    for a in picks:
        clubs = [c.rsplit(" ", 1)[0] for c in a["evidence"].split(" e mais")[0].split(", ")]
        source, words = article(a["id"]) if a["id"].startswith("Q") else ("", set())
        hit = [c for c in clubs if all(w in words for w in CLUB_WORDS.get(c, plain(c)))]
        rows.append({"prompt": p["text"], "prompt_id": pid, "answer": a["name"], "id": a["id"], "tier": a["tier"],
                     "evidence": a["evidence"], "source": source, "club_in_article": hit})
        print(f"{pid[:34]:34} {a['name'][:24]:24} {a['tier']:12} {a['evidence'][:34]:34} hit={bool(hit)}", flush=True)
        time.sleep(0.4)
Path(sys.argv[2]).write_text(json.dumps(rows, ensure_ascii=False, indent=1))
print("auto-confirmed", sum(1 for r in rows if r["club_in_article"]), "of", len(rows))
