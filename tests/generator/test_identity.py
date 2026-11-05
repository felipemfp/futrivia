import unittest

from generator.identity import Override, Player, resolve


def person(sitelinks, names, stints=(), label=None, transfermarkt=()):
    return {"sitelinks": sitelinks, "label": label or names[0], "names": list(names),
            "stints": [list(s) for s in stints], "transfermarkt": list(transfermarkt)}


PEOPLE = {
    "Q13646572": person(41, ["Gabriel Barbosa", "Gabigol", "Gabriel Barbosa Almeida"],
                        [("Clube de Regatas do Flamengo", 2019, 2024)], label="Gabriel Barbosa"),
    "Q312772": person(64, ["Fred", "Frederico Chaves Guedes"], [("Fluminense Football Club", 2009, 2016)]),
    "Q999001": person(5, ["Fred", "Frederico Rodrigues"], [("Sport Club Internacional", 2012, 2013)]),
    "Q10552615": person(22, ["Deyverson", "Deyverson Brum Silva Acosta"], [("Grêmio Mangaratibense", 2011, 2012)]),
    "Q42728914": person(61, ["Rodrygo", "Rodrygo Silva de Goes"], [("Santos Futebol Clube", 2017, 2019)], label="Rodrygo"),
    "Q142794": person(150, ["Neymar", "Neymar da Silva Santos Júnior"], label="Neymar", transfermarkt=["68290"]),
    "Q1": person(3, ["Wesley"]),
    "Q2": person(4, ["Wesley"]),
}


def player(ref, name, *seen):
    return Player(ref=ref, name=name, seen=frozenset(seen))


class ResolveTest(unittest.TestCase):
    def resolve(self, *players, overrides=()):
        return resolve({p.ref: p for p in players}, PEOPLE, list(overrides))

    def test_two_spellings_of_one_player_become_one_identity(self):
        refs, ids = self.resolve(player("a:Gabriel Barbosa", "Gabriel Barbosa", ("Flamengo", 2019)),
                                 player("a:Gabriel Barbosa Almeida", "Gabriel Barbosa Almeida", ("Flamengo", 2022)))
        self.assertEqual(refs["a:Gabriel Barbosa"], refs["a:Gabriel Barbosa Almeida"])
        self.assertEqual(ids["Q13646572"].status, "club")
        self.assertIn("gabriel barbosa almeida", ids["Q13646572"].aliases)

    def test_shared_name_is_settled_by_club_and_season_not_fame(self):
        refs, _ = self.resolve(player("a:Fred", "Fred", ("Internacional", 2013)))
        self.assertEqual(refs["a:Fred"], "Q999001")

    def test_lower_division_club_with_a_similar_name_does_not_confirm(self):
        refs, ids = self.resolve(player("a:Deyverson", "Deyverson", ("Gremio", 2023)))
        self.assertEqual(refs["a:Deyverson"], "Q10552615")
        self.assertEqual(ids["Q10552615"].status, "name")

    def test_formal_dataset_name_displays_as_the_common_name(self):
        refs, ids = self.resolve(player("a:Rodrygo Silva de Goes", "Rodrygo Silva de Goes", ("Santos", 2018)))
        self.assertEqual(ids[refs["a:Rodrygo Silva de Goes"]].name, "Rodrygo")

    def test_transfermarkt_player_resolves_by_id(self):
        refs, ids = self.resolve(player("transfermarkt:68290", "Neymar Jr", ("Santos", 2025)))
        self.assertEqual(refs["transfermarkt:68290"], "Q142794")
        self.assertEqual(ids["Q142794"].status, "transfermarkt-id")

    def test_same_player_in_both_sources_is_one_identity(self):
        refs, _ = self.resolve(player("transfermarkt:68290", "Neymar", ("Santos", 2025)),
                               player("a:Neymar", "Neymar", ("Santos", 2014)))
        self.assertEqual(refs["transfermarkt:68290"], refs["a:Neymar"])

    def test_several_candidates_with_no_club_evidence_is_untrusted(self):
        refs, ids = self.resolve(player("a:Wesley", "Wesley", ("Goias", 2015)))
        self.assertEqual(refs["a:Wesley"], "dataset:Wesley")
        self.assertEqual(ids["dataset:Wesley"].status, "ambiguous")
        self.assertIsNone(ids["dataset:Wesley"].sitelinks)

    def test_unknown_player_keeps_a_dataset_identity(self):
        refs, ids = self.resolve(player("a:Keno", "Keno", ("Palmeiras", 2016)))
        self.assertEqual(refs["a:Keno"], "dataset:Keno")
        self.assertEqual(ids["dataset:Keno"].status, "none")
        self.assertEqual(ids["dataset:Keno"].aliases, ("keno",))

    def test_override_sets_identity_and_adds_aliases(self):
        refs, ids = self.resolve(player("a:Wesley", "Wesley", ("Goias", 2015)),
                                 overrides=[Override("a:Wesley", "Q2", ("wesley pacheco",))])
        self.assertEqual(refs["a:Wesley"], "Q2")
        self.assertEqual(ids["Q2"].status, "override")
        self.assertIn("wesley pacheco", ids["Q2"].aliases)

    def test_override_can_reject_a_wrong_match(self):
        refs, ids = self.resolve(player("a:Deyverson", "Deyverson", ("Gremio", 2023)),
                                 overrides=[Override("a:Deyverson", None, ())])
        self.assertEqual(refs["a:Deyverson"], "dataset:Deyverson")
        self.assertEqual(ids["dataset:Deyverson"].status, "override")

    def test_override_for_a_person_not_in_the_cache_is_an_error(self):
        with self.assertRaises(KeyError):
            self.resolve(player("a:Keno", "Keno", ("Palmeiras", 2016)), overrides=[Override("a:Keno", "Q404", ())])


if __name__ == "__main__":
    unittest.main()
