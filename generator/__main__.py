import argparse
import sys
from pathlib import Path

from generator.fetch import SOURCES, ChecksumError, fetch_all


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m generator", description="Build futrivia daily game files.")
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="download pinned sources into the cache")
    fetch.add_argument("--cache", type=Path, default=Path(".cache"))
    args = parser.parse_args(argv)

    if args.command == "fetch":
        try:
            fetch_all(SOURCES, args.cache)
        except ChecksumError as error:
            print(f"fetch failed: {error}", file=sys.stderr)
            return 1
        print(f"{len(SOURCES)} sources verified in {args.cache}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
