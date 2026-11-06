"""Gate 1 evidence: for 50 random name-only matches, does the matched person's Wikipedia article name the dataset club?

Usage: python3 -I tools/gate1_identity_check.py <repo root> <output.json>
"""
import json, random, re, sys, time, unicodedata, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from generator import build  # noqa: E402
from generator.clubs import WIKIDATA_WORDS, display  # noqa: E402
from generator.identity import resolve  # noqa: E402
from generator.sources import adaoduque, transfermarkt  # noqa: E402

UA = {"User-Agent": "futrivia/0.1 (https://github.com/felipemfp/futrivia)"}
cache = Path(sys.argv[1]) / ".cache"
out = Path(sys.argv[2])


def get(url):
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
        except Exception:
            time.sleep(5 * (attempt + 1))
    return {}


def plain(s):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", "".join(c for c in unicodedata.normalize("NFD", s.lower()) if not unicodedata.combining(c))).split())


people = json.loads((cache / "wikidata.json").read_text())
old, new = adaoduque.load(cache), transfermarkt.load(cache)
players = build.collect_players(old.goals + new.goals, old.cards + new.cards, new.lineups)
refs, ids = resolve(players, people, [])
sample_pool = sorted({r for r in players if ids[refs[r]].status == "name"})
random.Random("futrivia-gate1").shuffle(sample_pool)
sample = sample_pool[:50]
rows = []
for ref in sample:
    qid = refs[ref]
    p = players[ref]
    clubs = sorted({c for c, _ in p.seen})
    seasons = sorted({s for _, s in p.seen})
    ent = get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "wbgetentities", "ids": qid, "props": "sitelinks|descriptions", "languages": "pt|en", "format": "json"}))
    e = ent.get("entities", {}).get(qid, {})
    desc = (e.get("descriptions", {}).get("pt") or e.get("descriptions", {}).get("en") or {}).get("value", "")
    found, source = [], ""
    for wiki, host in (("ptwiki", "pt.wikipedia.org"), ("enwiki", "en.wikipedia.org")):
        title = e.get("sitelinks", {}).get(wiki, {}).get("title")
        if not title:
            continue
        page = get(f"https://{host}/w/api.php?" + urllib.parse.urlencode(
            {"action": "query", "prop": "extracts", "explaintext": 1, "titles": title, "format": "json"}))
        text = plain(" ".join(v.get("extract", "") for v in page.get("query", {}).get("pages", {}).values()))
        hits = [c for c in clubs if all(w in text.split() for w in WIKIDATA_WORDS[c] - {"esporte", "futebol", "clube", "sport", "football", "regatas", "esportiva", "porto", "alegrense", "sporting", "paulista"}) ]
        source = f"https://{host}/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
        if hits:
            found = hits
            break
        time.sleep(0.3)
    rows.append({"ref": ref, "dataset_name": p.name, "clubs": [display(c) for c in clubs], "seasons": seasons,
                 "qid": qid, "label": ids[qid].name, "description": desc, "source": source,
                 "club_in_article": [display(c) for c in found]})
    print(f"{ref:45} -> {qid:11} {ids[qid].name[:22]:22} clubs={','.join(display(c) for c in clubs)[:40]:40} hit={bool(found)} {desc[:50]}", flush=True)
    time.sleep(0.5)
out.write_text(json.dumps(rows, ensure_ascii=False, indent=1))
print("auto-confirmed", sum(1 for r in rows if r["club_in_article"]), "of", len(rows), "; pool", len(sample_pool))
