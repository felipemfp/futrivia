// Game state as plain JSON, so it can be saved and restored. Functions never modify their input.
import { matchAnswer } from "./match.js";

export const PROMPT_MS = 25_000;

export function newGame(day) {
  return {
    version: 1,
    date: day.date,
    promptIds: day.prompts.map((p) => p.id),
    index: -1,
    phase: "ready",
    startedAt: null,
    wrong: 0,
    results: [],
  };
}

export function nextPrompt(game, now) {
  const index = game.index + 1;
  if (index >= game.promptIds.length) return { ...game, index, phase: "done", startedAt: null };
  return { ...game, index, phase: "playing", startedAt: now, wrong: 0 };
}

export function timeLeft(game, now) {
  if (game.phase !== "playing") return 0;
  return Math.max(0, PROMPT_MS - (now - game.startedAt));
}

function finish(game, answer) {
  const result = {
    promptId: game.promptIds[game.index],
    answerId: answer ? answer.id : null,
    points: answer ? answer.points : 0,
    wrong: game.wrong,
  };
  return { ...game, phase: "reveal", results: [...game.results, result] };
}

export function guess(game, day, input, now) {
  if (game.phase !== "playing") return { game, outcome: { status: "closed" } };
  if (timeLeft(game, now) <= 0) return { game: finish(game, null), outcome: { status: "timeout" } };
  const outcome = matchAnswer(input, day.prompts[game.index].answers);
  if (outcome.status === "correct") return { game: finish(game, outcome.answer), outcome };
  if (outcome.status === "wrong") return { game: { ...game, wrong: game.wrong + 1 }, outcome };
  return { game, outcome };
}

// Call on load and on every timer tick: a prompt left open past its deadline (tab closed) scores zero.
export function refresh(game, now) {
  if (game.phase === "playing" && timeLeft(game, now) <= 0) return finish(game, null);
  return game;
}

export function totalScore(game) {
  return game.results.reduce((sum, r) => sum + r.points, 0);
}
