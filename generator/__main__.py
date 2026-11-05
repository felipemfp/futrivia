import argparse
import sys
from pathlib import Path

from generator import wikidata
from generator.fetch import SOURCES, ChecksumError, fetch_all
from generator.sources import adaoduque, transfermarkt


def dataset_players(cache: Path) -> tuple[list[str], list[str]]:
    """Every player name in the sources, and every Transfermarkt player id."""
    old, new = adaoduque.load(cache), transfermarkt.load(cache)
    names = {g.player for g in old.goals} | {c.player for c in old.cards} | set(new.names.values())
    ids = {ref.split(":", 1)[1] for ref in new.names}
    return sorted(names), sorted(ids)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m generator", description="Build futrivia daily game files.")
    parser.add_argument("--cache", type=Path, default=Path(".cache"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("fetch", help="download pinned sources into the cache")
    wd = commands.add_parser("wikidata", help="fetch footballers from Wikidata into the cache (needs fetch first)")
    wd.add_argument("--refresh", action="store_true", help="refetch even if cached")
    args = parser.parse_args(argv)

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
            people = wikidata.load_or_fetch(args.cache / "wikidata.json", wikidata.http_sparql, names, args.refresh, ids)
        except wikidata.WikidataError as error:
            print(f"wikidata failed: {error}", file=sys.stderr)
            return 1
        print(f"{len(people)} people in {args.cache / 'wikidata.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
