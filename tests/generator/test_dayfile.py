import copy
import json
import tempfile
import unittest
from pathlib import Path

from generator.dayfile import DayAnswer, DayPrompt, normalize, validate, write_day

FIXTURES = Path(__file__).parent.parent / "fixtures"


def answer(n: int, tier: str = "raiz", points: int = 60) -> DayAnswer:
    return DayAnswer(id=f"Q{n}", name=f"Jogador {n}", aliases=(f"jogador {n}",), tier=tier, points=points,
                     evidence="Santos 2019")


def prompt(n: int, answers: int = 5) -> DayPrompt:
    return DayPrompt(id=f"p{n}", text=f"Prompt {n}", answers=tuple(answer(i) for i in range(answers)))


def day(prompts: int = 7) -> dict:
    return {"version": 1, "date": "2027-01-01",
            "prompts": [p.to_json() for p in (prompt(i) for i in range(prompts))]}


class NormalizeTest(unittest.TestCase):
    def test_shared_vectors(self):
        for raw, expected in json.loads((FIXTURES / "normalize.json").read_text(encoding="utf-8")):
            with self.subTest(raw=raw):
                self.assertEqual(normalize(raw), expected)


class ValidateTest(unittest.TestCase):
    def assertRejected(self, data: dict, fragment: str):
        errors = validate(data, "2027-01-01")
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_valid_day_has_no_errors(self):
        self.assertEqual(validate(day(), "2027-01-01"), [])

    def test_rejects_wrong_prompt_count(self):
        self.assertRejected(day(prompts=6), "7 prompts")

    def test_rejects_too_few_and_too_many_answers(self):
        for count in (4, 41):
            data = day()
            data["prompts"][0] = prompt(0, answers=count).to_json()
            self.assertRejected(data, "5–40 answers")

    def test_rejects_points_not_matching_tier(self):
        data = day()
        data["prompts"][0]["answers"][0]["points"] = 100
        self.assertRejected(data, "points")

    def test_rejects_unknown_tier(self):
        data = day()
        data["prompts"][0]["answers"][0]["tier"] = "lenda"
        self.assertRejected(data, "tier")

    def test_rejects_empty_or_unnormalized_alias(self):
        for alias in ("", "Jogador"):
            data = day()
            data["prompts"][0]["answers"][0]["aliases"] = [alias]
            self.assertRejected(data, "alias")

    def test_rejects_duplicate_prompt_and_answer_ids(self):
        data = day()
        data["prompts"][1]["id"] = data["prompts"][0]["id"]
        self.assertRejected(data, "duplicate prompt")
        data = day()
        data["prompts"][0]["answers"][1]["id"] = data["prompts"][0]["answers"][0]["id"]
        self.assertRejected(data, "duplicate answer")

    def test_rejects_date_not_matching_file(self):
        errors = validate(day(), "2027-01-02")
        self.assertTrue(any("date" in e for e in errors), errors)

    def test_rejects_unknown_version(self):
        data = copy.deepcopy(day())
        data["version"] = 2
        self.assertRejected(data, "version")


class WriteTest(unittest.TestCase):
    def test_writes_valid_and_byte_identical_output(self):
        prompts = [prompt(i) for i in range(7)]
        with tempfile.TemporaryDirectory() as tmp:
            first = write_day(Path(tmp), "2027-01-01", prompts).read_bytes()
            second = write_day(Path(tmp), "2027-01-01", prompts).read_bytes()
            self.assertEqual(first, second)
            self.assertEqual(validate(json.loads(first), "2027-01-01"), [])

    def test_refuses_to_write_invalid_day(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError):
            write_day(Path(tmp), "2027-01-01", [prompt(i) for i in range(6)])


class GameFixtureTest(unittest.TestCase):
    def test_game_fixture_is_a_valid_day(self):
        path = FIXTURES / "days" / "2027-01-01.json"
        self.assertEqual(validate(json.loads(path.read_text(encoding="utf-8")), "2027-01-01"), [])


if __name__ == "__main__":
    unittest.main()
