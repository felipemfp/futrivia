"""Download pinned source files into the cache, refusing any file whose checksum differs from its pin."""
import hashlib
import os
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

ADAODUQUE = "https://raw.githubusercontent.com/adaoduque/Brasileirao_Dataset/15f027c3be337bb130d6ae94436b5cdca737377c"
TRANSFERMARKT = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data"
USER_AGENT = "futrivia/0.1 (https://github.com/felipemfp/futrivia)"


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    sha256: str


SOURCES = [
    Source("campeonato-brasileiro-full.csv", f"{ADAODUQUE}/campeonato-brasileiro-full.csv",
           "c09d03d36debfd7d7aee71da9a9f0909b5e420fc80a1705f215efc93c76e83fc"),
    Source("campeonato-brasileiro-gols.csv", f"{ADAODUQUE}/campeonato-brasileiro-gols.csv",
           "625262ca9e7301907f94a0ef235b672d803a488d1e9d8833c31e51d4ffbe5664"),
    Source("campeonato-brasileiro-cartoes.csv", f"{ADAODUQUE}/campeonato-brasileiro-cartoes.csv",
           "4376ed95901b25d6c425127bf542b7746e086e1a20116b49d7a5d87949ac95e8"),
    # Transfermarkt files are not versioned upstream; these checksums are from 2026-11-05.
    Source("games.csv.gz", f"{TRANSFERMARKT}/games.csv.gz",
           "142561989017d379bcf9e72bad0b87e0996bae0e7b710ebb3def9255f464c741"),
    Source("game_lineups.csv.gz", f"{TRANSFERMARKT}/game_lineups.csv.gz",
           "5e83d6fad28364aadfea608013700cf09990062eede1ad9ef189189b0af47ba2"),
    Source("game_events.csv.gz", f"{TRANSFERMARKT}/game_events.csv.gz",
           "80eb3b2a85c780b2caaf1e8850c3d16de7f8b1240b53aaf415bdc56b641d7d68"),
    Source("players.csv.gz", f"{TRANSFERMARKT}/players.csv.gz",
           "d22e407981d5b51a79bf8ff59835729f3526f7dc3495a6d8ed2f852ed2e86403"),
]


class ChecksumError(Exception):
    pass


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_all(sources: Iterable[Source], cache_dir: Path, download: Callable[[str], bytes] = _download) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    for source in sources:
        path = cache_dir / source.name
        if path.exists():
            if _sha256(path.read_bytes()) != source.sha256:
                raise ChecksumError(f"{source.name}: cached file does not match its pin; delete it to refetch")
            continue
        data = download(source.url)
        if _sha256(data) != source.sha256:
            raise ChecksumError(f"{source.name}: upstream file changed since it was pinned; update the pin deliberately")
        partial = path.with_suffix(path.suffix + ".partial")
        partial.write_bytes(data)
        os.replace(partial, path)
