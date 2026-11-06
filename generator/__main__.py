import argparse
import datetime
import sys
import time
from pathlib import Path

from generator import build, wikidata
from generator.fetch import SOURCES, ChecksumError, fetch_all
from generator.sources import adaoduque, transfermarkt


def dataset_players(cache: Path) -> tuple[list[str], list[str]]:
    """Every player name in the sources, and every Transfermarkt player id."""
    old, new = adaoduque.load(cache), transfermarkt.load(cache)
    # Only players in Série A records: players.csv lists tens of thousands of players worldwide.
    records = [*old.goals, *old.cards, *new.goals, *new.cards, *new.lineups]
    names = {r.player for r in records}
    ids = {r.player_ref.split(":", 1)[1] for r in records if r.player_ref.startswith("transfermarkt:")}
    return sorted(names), sorted(ids)


class ProgressLog:
    """Prints one line per finished batch with percent and ETA, and appends it to a log file."""

    def __init__(self, path: Path):
        self.path = path
        self.started: dict[str, float] = {}
        path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, stage: str, done: int, total: int) -> None:
        now = time.monotonic()
        start = self.started.setdefault(stage, now - 1e-9 if done == 1 else now)
        eta = (now - start) / done * (total - done)
        line = (f"{datetime.datetime.now():%H:%M:%S} wikidata {stage}: {done}/{total} batches "
                f"({100 * done / total:.0f}%), ETA {eta / 60:.1f} min")
        print(line, file=sys.stderr, flush=True)
        with open(self.path, "a", encoding="utf-8") as log:
            log.write(line + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m generator", description="Build futrivia daily game files.")
    parser.add_argument("--cache", type=Path, default=Path(".cache"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("fetch", help="download pinned sources into the cache")
    wd = commands.add_parser("wikidata", help="fetch footballers from Wikidata into the cache (needs fetch first)")
    wd.add_argument("--refresh", action="store_true", help="refetch even if cached")
    b = commands.add_parser("build", help="write site/days/*.json and reports/build.json (needs fetch and wikidata)")
    b.add_argument("--start", type=datetime.date.fromisoformat, required=True)
    b.add_argument("--days", type=int, required=True)
    b.add_argument("--out", type=Path, default=Path("site/days"))
    b.add_argument("--report", type=Path, default=Path("reports/build.json"))
    b.add_argument("--overrides", type=Path, default=Path("data/overrides.csv"))
    args = parser.parse_args(argv)

    if args.command == "build":
        try:
            report = build.build(args.cache, args.overrides, args.out, args.report, args.start, args.days)
        except (build.ScheduleError, FileNotFoundError) as error:
            print(f"build failed: {error}; see {args.report}", file=sys.stderr)
            return 1
        print(f"{args.days} days written to {args.out}; {report['prompts_available']} prompts available")
        return 0

    if args.command == "fetch":
        try:
            fetch_all(SOURCES, args.cache)
        except ChecksumError as error:
            print(f"fetch failed: {error}", file=sys.stderr)
            return 1
        print(f"{len(SOURCES)} sources verified in {args.cache}")
    elif args.command == "wikidata":
        names, ids = dataset_players(args.cache)
        try:
            people = wikidata.load_or_fetch(args.cache / "wikidata.json", wikidata.http_sparql, names, args.refresh, ids,
                                            ProgressLog(Path("/tmp/futrivia-wikidata/progress.log")))
        except wikidata.WikidataError as error:
            print(f"wikidata failed: {error}", file=sys.stderr)
            return 1
        print(f"{len(people)} people in {args.cache / 'wikidata.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
