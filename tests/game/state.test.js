import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { PROMPT_MS, guess, newGame, nextPrompt, refresh, timeLeft, totalScore } from "../../site/game/state.js";

const day = JSON.parse(readFileSync(new URL("../fixtures/days/2027-01-01.json", import.meta.url), "utf8"));
const T0 = Date.parse("2027-01-01T15:00:00Z");

function started() {
  return nextPrompt(newGame(day), T0);
}

test("a new game waits for the player to start", () => {
  const game = newGame(day);
  assert.equal(game.phase, "ready");
  assert.equal(game.results.length, 0);
});

test("starting a prompt gives the full 25 seconds", () => {
  assert.equal(timeLeft(started(), T0), PROMPT_MS);
  assert.equal(PROMPT_MS, 25_000);
});

test("a correct answer scores its tier points and reveals", () => {
  const { game, outcome } = guess(started(), day, "Germán Cano", T0 + 5_000);
  assert.equal(outcome.status, "correct");
  assert.equal(game.phase, "reveal");
  assert.deepEqual(game.results[0], { promptId: "teste-hat-trick", answerId: "Q3761170", points: 85, wrong: 0 });
});

test("a wrong guess keeps the prompt open and the clock running", () => {
  const { game } = guess(started(), day, "Ronaldinho", T0 + 3_000);
  assert.equal(game.phase, "playing");
  assert.equal(game.wrong, 1);
  assert.equal(timeLeft(game, T0 + 3_000), PROMPT_MS - 3_000);
});

test("an ambiguous guess is not counted as wrong", () => {
  const second = nextPrompt(guess(started(), day, "Suárez", T0).game, T0 + 10_000);
  const { game, outcome } = guess(second, day, "Gabriel", T0 + 11_000);
  assert.equal(outcome.status, "ambiguous");
  assert.equal(game.wrong, 0);
});

test("a guess after the deadline scores zero", () => {
  const { game, outcome } = guess(started(), day, "Germán Cano", T0 + PROMPT_MS + 1);
  assert.equal(outcome.status, "timeout");
  assert.equal(game.results[0].points, 0);
  assert.equal(game.results[0].answerId, null);
});

test("refreshing after the deadline, as on reopening the tab, times the prompt out", () => {
  const reopened = refresh(JSON.parse(JSON.stringify(started())), T0 + 60_000);
  assert.equal(reopened.phase, "reveal");
  assert.equal(reopened.results[0].points, 0);
});

test("refreshing within the deadline resumes with the remaining time", () => {
  const reopened = refresh(JSON.parse(JSON.stringify(started())), T0 + 10_000);
  assert.equal(reopened.phase, "playing");
  assert.equal(timeLeft(reopened, T0 + 10_000), PROMPT_MS - 10_000);
});

test("the game ends after 7 prompts with the summed score", () => {
  let game = newGame(day);
  let now = T0;
  for (const p of day.prompts) {
    game = nextPrompt(game, now);
    game = guess(game, day, p.answers[0].name, now + 1_000).game;
    now += 30_000;
  }
  game = nextPrompt(game, now);
  assert.equal(game.phase, "done");
  assert.equal(totalScore(game), day.prompts.reduce((sum, p) => sum + p.answers[0].points, 0));
});

test("state never changes in place", () => {
  const game = started();
  const before = JSON.stringify(game);
  guess(game, day, "Germán Cano", T0 + 1_000);
  assert.equal(JSON.stringify(game), before);
});
