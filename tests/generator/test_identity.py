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

    def test_transfermarkt_name_is_shown_over_a_legal_name_label(self):
        people = dict(PEOPLE, Q47491410=person(30, ["Pedro Guilherme Abreu dos Santos"], transfermarkt=["432895"]))
        refs, ids = resolve({"transfermarkt:432895": player("transfermarkt:432895", "Pedro", ("Flamengo", 2025))}, people, [])
        self.assertEqual(ids["Q47491410"].name, "Pedro")

    def test_wikipedia_common_name_is_shown_over_a_legal_name_label(self):
        people = dict(PEOPLE, Q9=dict(person(20, ["Maicon Douglas Sisenando", "Maicon"]), common="Maicon"))
        refs, ids = resolve({"a:Maicon Douglas Sisenando": player("a:Maicon Douglas Sisenando", "Maicon Douglas Sisenando",
                                                                    ("Gremio", 2020))}, people, [])
        self.assertEqual(ids[refs["a:Maicon Douglas Sisenando"]].name, "Maicon")

    def test_long_legal_name_shortens_to_a_short_alias_drawn_from_it(self):
        people = dict(PEOPLE, Q8=person(15, ["André Luiz Paulino de Souza Motta", "Andre Paulino", "André Paulino", "Paulão Motta"],
                                         [("Santos Futebol Clube", 2015, 2016)]))
        refs, ids = resolve({"a:André Luiz Paulino de Souza Motta": player("a:André Luiz Paulino de Souza Motta",
                                                                             "André Luiz Paulino de Souza Motta", ("Santos", 2015))}, people, [])
        self.assertEqual(ids["Q8"].name, "André Paulino")

    def test_shortest_known_name_is_shown_when_the_title_is_a_legal_name(self):
        people = dict(PEOPLE, Q6=dict(person(64, ["Fred", "Frederico Chaves Guedes"], [("Fluminense Football Club", 2009, 2016)],
                                             label="Fred"), common="Frederico Chaves Guedes"))
        del people["Q312772"], people["Q999001"]
        refs, ids = resolve({"a:Fred": player("a:Fred", "Fred", ("Fluminense", 2015))}, people, [])
        self.assertEqual(ids["Q6"].name, "Fred")

    def test_vandalised_or_unrelated_aliases_are_dropped(self):
        people = dict(PEOPLE, Q5=dict(person(30, ["Juan Nardoni", "Juan Ignacio Nardoni", "Adolfo Hitler Buendía", "Nardo",
                                                  "Marquinhos futbolista nacido en 2003"], [("Grêmio Foot-Ball Porto Alegrense", 2026, None)],
                                             label="Juan Nardoni")))
        refs, ids = resolve({"tm:1": player("a:Juan Nardoni", "Juan Nardoni", ("Gremio", 2026))}, people, [])
        aliases = ids["Q5"].aliases
        self.assertIn("juan ignacio nardoni", aliases)
        self.assertIn("nardo", aliases)  # single-word nicknames are kept
        self.assertNotIn("adolfo hitler buendia", aliases)
        self.assertFalse(any("futbolista" in a for a in aliases))

    def test_candidate_too_old_for_the_season_is_rejected(self):
        people = dict(PEOPLE, Q4=dict(person(40, ["Dadá Maravilha", "Dadá"], [("Goiás Esporte Clube", None, None)]), born=1946),
                      Q3=dict(person(3, ["Dadá"]), born=1995))
        refs, ids = resolve({"a:Dadá": player("a:Dadá", "Dadá", ("Goias", 2019))}, people, [])
        self.assertEqual(refs["a:Dadá"], "Q3")

    def test_blank_source_name_never_becomes_the_shown_name(self):
        people = dict(PEOPLE, Q2=dict(person(13, ["Petros Matheus dos Santos Araujo", "الخبيث"], label="Petros Matheus dos Santos Araujo",
                                             transfermarkt=["200558"]), common="Petros"))
        refs, ids = resolve({"transfermarkt:200558": player("transfermarkt:200558", "", ("Internacional", 2025))}, people, [])
        self.assertEqual(ids["Q2"].name, "Petros")
        self.assertNotIn("", ids["Q2"].aliases)

    def test_player_split_across_sources_joins_through_the_transfermarkt_match(self):
        # Regression: Neris (Vitória 2024 in adaoduque, 2025 in Transfermarkt) became two answers.
        people = dict(PEOPLE, Q50=dict(person(8, ["Neris Augusto"], label="Neris Augusto", transfermarkt=["5"]), born=1993))
        refs, _ = resolve({"transfermarkt:5": player("transfermarkt:5", "Neris", ("Vitoria", 2025)),
                           "a:Neris": player("a:Neris", "Neris", ("Vitoria", 2024))}, people, [])
        self.assertEqual(refs["a:Neris"], refs["transfermarkt:5"])

    def test_wrong_wikidata_birth_year_does_not_reject_a_transfermarkt_confirmed_person(self):
        # Regression: Luciano's Wikidata birth year (1965) is wrong; his Transfermarkt id confirms the person.
        people = dict(PEOPLE, Q15966749=dict(person(16, ["Luciano", "Luciano da Rocha Neves"], [("São Paulo Futebol Clube", 2021, None)],
                                                    transfermarkt=["7"]), born=1965))
        refs, _ = resolve({"transfermarkt:7": player("transfermarkt:7", "Luciano", ("Sao Paulo", 2025)),
                           "a:Luciano da Rocha Neves": player("a:Luciano da Rocha Neves", "Luciano da Rocha Neves", ("Sao Paulo", 2022))},
                          people, [])
        self.assertEqual(refs["a:Luciano da Rocha Neves"], "Q15966749")

    def test_transfermarkt_confirmed_person_wins_over_an_older_namesake(self):
        # Regression: Marinho (Santos 2021) matched Mauro Sérgio, born 1978, whose Santos stint has no dates.
        people = dict(PEOPLE,
                      Q60=dict(person(25, ["Marinho", "Mario Sérgio Santos Costa"], [("Santos Futebol Clube", 2019, 2021)], transfermarkt=["8"]), born=1990),
                      Q61=dict(person(9, ["Marinho", "Mauro Sérgio da Silva"], [("Santos Futebol Clube", None, None)]), born=1978))
        refs, _ = resolve({"transfermarkt:8": player("transfermarkt:8", "Marinho", ("Fortaleza", 2025)),
                           "a:Marinho": player("a:Marinho", "Marinho", ("Santos", 2021))}, people, [])
        self.assertEqual(refs["a:Marinho"], "Q60")

    def test_short_name_joins_the_person_its_full_name_resolved_to(self):
        # Regression: "Mário Sérgio Santos Costa" (Santos 2020) resolved by club, but "Marinho" (Santos 2021) stayed
        # ambiguous between him and an undated namesake, so penalti-santos showed two Marinho answers.
        people = dict(PEOPLE,
                      Q70=dict(person(25, ["Mário Sérgio Santos Costa", "Marinho"], [("Santos Futebol Clube", 2019, 2020)]), born=1990),
                      Q71=dict(person(9, ["Marinho"], [("Santos Futebol Clube", None, None)]), born=1985))
        refs, _ = resolve({"a:Mário Sérgio Santos Costa": player("a:Mário Sérgio Santos Costa", "Mário Sérgio Santos Costa", ("Santos", 2020)),
                           "a:Marinho": player("a:Marinho", "Marinho", ("Santos", 2021))}, people, [])
        self.assertEqual(refs["a:Marinho"], "Q70")

    def test_disambiguation_suffix_is_never_shown(self):
        people = dict(PEOPLE, Q7=person(9, ["Carlos Júnior (futebolista)"], [("Santos Futebol Clube", 2018, 2019)]))
        refs, ids = resolve({"a:Carlos Júnior": player("a:Carlos Júnior", "Carlos Júnior (futebolista)", ("Santos", 2018))}, people, [])
        self.assertEqual(ids["Q7"].name, "Carlos Júnior")

    def test_legal_name_shortens_to_a_diminutive_nickname(self):
        # Rodrigo Eduardo Costa Marinho is known as Rodriguinho: a one-word alias built on a word of the full name.
        people = dict(PEOPLE, Q3940035=dict(person(20, ["Rodrigo Eduardo Costa Marinho", "Rodriguinho", "Rodriguinho Marinho"],
                                                   [("Sport Club Corinthians Paulista", 2015, 2018)], label="Rodrigo Eduardo Costa Marinho"),
                                            common="Rodrigo Eduardo Costa Marinho", born=1988))
        r = "a:Rodrigo Eduardo Costa Marinho"
        refs, ids = resolve({r: player(r, "Rodrigo Eduardo Costa Marinho", ("Corinthians", 2017))}, people, [])
        self.assertEqual(ids["Q3940035"].name, "Rodriguinho")

    def test_short_names_are_never_shortened(self):
        refs, ids = self.resolve(player("a:Gabriel Barbosa", "Gabriel Barbosa", ("Flamengo", 2019)))
        self.assertEqual(ids["Q13646572"].name, "Gabriel Barbosa")

    def test_override_name_is_shown(self):
        refs, ids = self.resolve(player("a:Wesley", "Wesley", ("Goias", 2015)),
                                 overrides=[Override("a:Wesley", "Q2", (), name="Wesley Pacheco")])
        self.assertEqual(ids["Q2"].name, "Wesley Pacheco")

    def test_override_for_a_person_not_in_the_cache_is_an_error(self):
        with self.assertRaises(KeyError):
            self.resolve(player("a:Keno", "Keno", ("Palmeiras", 2016)), overrides=[Override("a:Keno", "Q404", ())])


if __name__ == "__main__":
    unittest.main()
