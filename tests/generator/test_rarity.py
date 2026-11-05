import collections
import unittest

from generator.rarity import DEFAULT_TIER, assign_tiers

ORDER = ["arquibancada", "torcedor", "raiz", "resenha", "enciclopedia"]


class RarityTest(unittest.TestCase):
    def test_five_distinct_answers_get_one_tier_each_from_obvious_to_rare(self):
        tiers = assign_tiers({f"q{i}": 100 - i for i in range(5)})
        self.assertEqual([tiers[f"q{i}"] for i in range(5)], ORDER)

    def test_forty_answers_split_into_equal_groups(self):
        tiers = assign_tiers({f"q{i}": 1000 - i for i in range(40)})
        self.assertEqual(collections.Counter(tiers.values()), {t: 8 for t in ORDER})

    def test_ties_share_the_rarer_group(self):
        tiers = assign_tiers({"a": 50, "b": 40, "c": 40, "d": 10, "e": 5})
        self.assertEqual(tiers["b"], tiers["c"])
        self.assertEqual(tiers["b"], "raiz")

    def test_all_tied_answers_are_the_rarest(self):
        tiers = assign_tiers({f"q{i}": 7 for i in range(6)})
        self.assertEqual(set(tiers.values()), {"enciclopedia"})

    def test_untrusted_answers_get_the_default_and_do_not_shift_the_ranking(self):
        tiers = assign_tiers({"a": 50, "b": 40, "c": 30, "d": 20, "e": 10, "x": None, "y": None})
        self.assertEqual(DEFAULT_TIER, "raiz")
        self.assertEqual((tiers["x"], tiers["y"]), ("raiz", "raiz"))
        self.assertEqual([tiers[k] for k in "abcde"], ORDER)

    def test_most_famous_is_never_rarer_than_less_famous(self):
        scores = {f"q{i}": (i * 37) % 23 for i in range(30)}
        tiers = assign_tiers(scores)
        for a in scores:
            for b in scores:
                if scores[a] > scores[b]:
                    self.assertLessEqual(ORDER.index(tiers[a]), ORDER.index(tiers[b]), (a, b))


if __name__ == "__main__":
    unittest.main()
