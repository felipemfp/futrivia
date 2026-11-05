import io
import unittest

from generator.sources.adaoduque import read_goals, read_matches

MATCHES = '''"ID","rodata","data","hora","mandante","visitante","formacao_mandante","formacao_visitante","tecnico_mandante","tecnico_visitante","vencedor","arena","mandante_Placar","visitante_Placar","mandante_Estado","visitante_Estado"
"1","38","06/12/2020","16:00","Gremio","Santos","","","","","Gremio","Arena","2","1","RS","SP"
"2","30","24/01/2021","16:00","Flamengo","Vasco","","","","","Flamengo","Maracana","3","0","RJ","RJ"
"3","1","30/05/2021","16:00","Sao Paulo","Fluminense","","","","","-","Morumbi","0","0","SP","RJ"
'''

GOALS = '''"partida_id","rodata","clube","atleta","minuto","tipo_de_gol"
"2","30","Flamengo","Pedro","10",""
"2","30","Flamengo","Pedro","90+2","Penalty"
"2","30","Flamengo","Leo Pele","50","Gol Contra"
'''


class AdaoduqueTest(unittest.TestCase):
    def setUp(self):
        self.matches = read_matches(io.StringIO(MATCHES))

    def test_dates_become_iso(self):
        self.assertEqual(self.matches["1"].date, "2020-12-06")

    def test_january_match_belongs_to_previous_season(self):
        self.assertEqual(self.matches["2"].season, 2020)

    def test_may_match_starts_new_season(self):
        self.assertEqual(self.matches["3"].season, 2021)

    def test_goal_takes_match_season_and_flags(self):
        goals = read_goals(io.StringIO(GOALS), self.matches)
        self.assertEqual([g.season for g in goals], [2020, 2020, 2020])
        self.assertEqual([g.penalty for g in goals], [False, True, False])
        self.assertEqual([g.own_goal for g in goals], [False, False, True])

    def test_player_ref_is_namespaced_by_source(self):
        goals = read_goals(io.StringIO(GOALS), self.matches)
        self.assertEqual(goals[0].player_ref, "adaoduque:Pedro")

    def test_goal_for_unknown_match_is_an_error(self):
        with self.assertRaises(KeyError):
            read_goals(io.StringIO(GOALS.replace('"2","30","Flamengo","Pedro","10"', '"99","30","Flamengo","Pedro","10"')), self.matches)


if __name__ == "__main__":
    unittest.main()
