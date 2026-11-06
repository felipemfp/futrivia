import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { shareText, maxScore } from "../../site/game/share.js";

const day = JSON.parse(readFileSync(new URL("../fixtures/days/2027-01-01.json", import.meta.url), "utf8"));
const results = day.prompts.map((p, i) =>
  i === 3 ? { promptId: p.id, answerId: null, points: 0, wrong: 2 } : { promptId: p.id, answerId: p.answers[i % p.answers.length].id, points: p.answers[i % p.answers.length].points, wrong: 0 },
);

test("share text has the name, date, score and one square per prompt", () => {
  const text = shareText(day, results);
  const total = results.reduce((s, r) => s + r.points, 0);
  assert.match(text, /^futrivia 01\/01\/2027/);
  assert.ok(text.includes(`${total}/700`));
  assert.equal([...text.matchAll(/[⬛⬜🟨🟧🟥🟪]/gu)].length, 7);
});

test("a missed prompt shows as black", () => {
  assert.equal([...shareText(day, results).matchAll(/⬛/gu)].length, 1);
});

test("share text never contains a player name or prompt text", () => {
  const text = shareText(day, results).toLowerCase();
  for (const p of day.prompts) {
    assert.ok(!text.includes(p.text.toLowerCase()));
    for (const a of p.answers) {
      assert.ok(!text.includes(a.name.toLowerCase()), a.name);
      for (const alias of a.aliases) assert.ok(!text.includes(alias), alias);
    }
  }
});

test("share text ends with the site address", () => {
  assert.match(shareText(day, results), /https:\/\/futrivia\.felipemfp\.dev$/);
});

test("max score is 100 per prompt and matches the share text denominator", () => {
  assert.equal(maxScore(day), 700);
  assert.equal(maxScore({ prompts: [{}, {}, {}] }), 300);
  assert.ok(shareText({ ...day, prompts: day.prompts.slice(0, 3) }, results.slice(0, 3)).endsWith("/300\nhttps://futrivia.felipemfp.dev"));
});
