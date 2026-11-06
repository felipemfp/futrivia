"""Checks against the pinned real data. Needs `python3 -m generator fetch` first."""
import collections
import unittest
from pathlib import Path

from generator import clubs
from generator.sources import transfermarkt
from generator.sources.adaoduque import load
from generator.templates.goals import hat_tricks

CACHE = Path(".cache")


class AdaoduqueRealDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (CACHE / "campeonato-brasileiro-full.csv").exists():
            raise RuntimeError("run `python3 -m generator fetch` before integration tests")
        cls.data = load(CACHE)

    def test_every_season_2014_2024_has_380_matches(self):
        per_season = collections.Counter(m.season for m in self.data.matches.values())
        # 2016 has 379: Chapecoense v Atlético-MG was never played after the Chapecoense air disaster.
        expected = {season: 380 for season in range(2014, 2025)} | {2016: 379}
        self.assertEqual({s: per_season[s] for s in expected}, expected)

    def test_goals_start_in_2014(self):
        self.assertEqual(min(g.season for g in self.data.goals), 2014)

    def test_hat_trick_counts_match_the_2026_11_05_test(self):
        prompt = hat_tricks(self.data.goals, [(2014, 2024)])[0]
        # Refs are name|club, so count names: the 2026-11-05 test counted 36 players.
        self.assertEqual(len({ref.split("|")[0] for ref in prompt.answers}), 36)
        self.assertEqual(sum(len(e) for e in prompt.answers.values()), 44)

    def test_every_club_has_a_display_name(self):
        for club in {g.club for g in self.data.goals} | {c.club for c in self.data.cards}:
            self.assertTrue(clubs.display(club), club)


class IdentityRealDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        from generator import build
        from generator.identity import read_overrides, resolve
        old, new = load(CACHE), transfermarkt.load(CACHE)
        cls.players = build.collect_players(old.goals + new.goals, old.cards + new.cards, new.lineups)
        cls.people = json.loads((CACHE / "wikidata.json").read_text(encoding="utf-8"))
        cls.refs, cls.ids = resolve(cls.players, cls.people, read_overrides(Path("data/overrides.csv")))

    def test_no_identity_holds_a_record_outside_playing_age(self):
        # Regression: Paulinho (born 2000) held Flamengo 2014. Exempt only people whose Wikidata birth year is
        # provably wrong: it puts their own Transfermarkt seasons outside playing age too.
        seen = collections.defaultdict(set)
        tm_seen = collections.defaultdict(set)
        for ref, ident in self.refs.items():
            seen[ident] |= self.players[ref].seen
            if ref.startswith("transfermarkt:"):
                tm_seen[ident] |= self.players[ref].seen
        bad = []
        for ident, pairs in seen.items():
            born = self.people.get(ident, {}).get("born")
            if not born:
                continue
            wrong_birth = any(not 15 <= s - born <= 43 for _, s in tm_seen[ident])
            if not wrong_birth and any(not 15 <= s - born <= 43 for _, s in pairs):
                bad.append((ident, born, sorted(pairs)[:3]))
        self.assertEqual(bad, [])

    def test_no_adaoduque_ref_mixes_clubs(self):
        for ref, player in self.players.items():
            if ref.startswith("adaoduque:"):
                self.assertLessEqual(len({c for c, _ in player.seen}), 1, ref)


class TransfermarktRealDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = transfermarkt.load(CACHE)

    def test_seasons_are_brasileirao_2025_full_and_2026_partial(self):
        per_season = collections.Counter(m.season for m in self.data.matches.values())
        self.assertEqual(dict(per_season), {2025: 380, 2026: 177})
        self.assertEqual(max(m.date for m in self.data.matches.values() if m.season == 2025), "2025-12-07")

    def test_goal_events_add_up_to_every_final_score(self):
        per_club = collections.Counter((g.match_id, g.club) for g in self.data.goals)
        for m in self.data.matches.values():
            self.assertEqual((per_club[(m.match_id, m.home)], per_club[(m.match_id, m.away)]),
                             (m.home_goals, m.away_goals), m.match_id)

    def test_neymar_is_in_the_data(self):
        neymar = "transfermarkt:68290"
        self.assertEqual(self.data.names[neymar], "Neymar")
        self.assertEqual(sum(1 for e in self.data.lineups if e.player_ref == neymar), 28)
        self.assertEqual(sum(1 for g in self.data.goals if g.player_ref == neymar and not g.own_goal), 12)


if __name__ == "__main__":
    unittest.main()
