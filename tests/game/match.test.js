import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { matchAnswer, normalize } from "../../site/game/match.js";

const vectors = JSON.parse(readFileSync(new URL("../fixtures/normalize.json", import.meta.url), "utf8"));
const day = JSON.parse(readFileSync(new URL("../fixtures/days/2027-01-01.json", import.meta.url), "utf8"));
const prompt = (id) => day.prompts.find((p) => p.id === id).answers;

test("normalize matches the Python generator on shared vectors", () => {
  for (const [raw, expected] of vectors) assert.equal(normalize(raw), expected, raw);
});

test("exact name or alias is correct, ignoring accents and case", () => {
  assert.equal(matchAnswer("LUIS SUÁREZ", prompt("teste-hat-trick")).answer.id, "Q26517");
  assert.equal(matchAnswer("gabigol", prompt("teste-hat-trick")).answer.id, "Q13646572");
});

test("unknown player is wrong", () => {
  assert.equal(matchAnswer("Ronaldinho", prompt("teste-hat-trick")).status, "wrong");
  assert.equal(matchAnswer("   ", prompt("teste-hat-trick")).status, "wrong");
});

test("a single word identifying one answer is correct", () => {
  assert.equal(matchAnswer("Suárez", prompt("teste-hat-trick")).answer.id, "Q26517");
  assert.equal(matchAnswer("Boschilia", prompt("teste-gabriel")).answer.id, "dataset:Gabriel Boschilia");
});

test("a word shared by several answers asks for more detail", () => {
  assert.equal(matchAnswer("Gabriel", prompt("teste-gabriel")).status, "ambiguous");
});

test("exact match wins over a shared word", () => {
  const answers = [...prompt("teste-curto"), { id: "x", name: "Pedro Raúl", aliases: ["pedro raul"] }];
  assert.equal(matchAnswer("Pedro", answers).answer.id, "dataset:Pedro");
});

test("name particles and short words never count as a single-word match", () => {
  assert.equal(matchAnswer("de", prompt("teste-gringos")).status, "wrong");
  assert.equal(matchAnswer("ph", [{ id: "g", name: "PH Ganso", aliases: ["ph ganso"] }]).status, "wrong");
});

test("one typo is forgiven in names of 5 or more letters", () => {
  assert.equal(matchAnswer("Geromell", prompt("teste-erro")).answer.id, "dataset:Pedro Geromel");
  assert.equal(matchAnswer("Rodrigo Moledu", prompt("teste-erro")).answer.id, "dataset:Rodrigo Moledo");
});

test("two typos, or a typo in a short name, are wrong", () => {
  assert.equal(matchAnswer("Geromelll", prompt("teste-erro")).status, "wrong");
  assert.equal(matchAnswer("Frad", prompt("teste-curto")).status, "wrong");
  assert.equal(matchAnswer("Hilk", prompt("teste-curto")).status, "wrong");
});

test("an exact name shared by different players credits the most obvious one", () => {
  const answers = [
    { id: "rare", name: "Dudu", aliases: ["dudu"], points: 85 },
    { id: "obvious", name: "Dudu", aliases: ["dudu", "eduardo pereira rodrigues"], points: 10 },
    { id: "other", name: "Rony", aliases: ["rony"], points: 30 },
  ];
  const result = matchAnswer("Dudu", answers);
  assert.equal(result.status, "correct");
  assert.equal(result.answer.id, "obvious");
});

test("a typo close to several answers asks for more detail", () => {
  const answers = [
    { id: "a", name: "Marlon", aliases: ["marlon"] },
    { id: "b", name: "Marcon", aliases: ["marcon"] },
  ];
  assert.equal(matchAnswer("Marmon", answers).status, "ambiguous");
});
