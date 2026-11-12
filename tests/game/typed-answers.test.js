// T16: realistic typed answers against generated days. Expectations follow SPEC.md "Name matching".
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { matchAnswer } from "../../site/game/match.js";

// Real prompts from a build, extracted by id with tools/extract_prompts.py so the cases don't depend on the schedule.
const prompts = JSON.parse(readFileSync(new URL("../fixtures/real/prompts.json", import.meta.url), "utf8"));

// [day, prompt id, typed, expected status, expected answer name when correct]
const CASES = [
  ["2026-11-09", "marcou-contra-corinthians-2014", "fred", "correct", "Fred"],
  ["2026-11-09", "marcou-contra-corinthians-2014", "luis fabiano", "correct", "Luís Fabiano"],
  ["2026-11-09", "marcou-contra-corinthians-2014", "Conca", "correct", "Darío Conca"],
  ["2026-11-09", "marcou-contra-corinthians-2014", "barcos", "correct", "Hernán Barcos"],
  ["2026-11-09", "marcou-contra-corinthians-2014", "Nilmarr", "correct", "Nilmar"],
  ["2026-11-09", "marcou-contra-corinthians-2014", "Ronaldinho", "wrong"],
  ["2026-11-09", "marcou-contra-corinthians-2014", "Alex", "correct", "Alexsandro de Souza"],
  // Fred's legal name contains "Guedes", so the surname alone is shared with Róger Guedes.
  ["2026-11-09", "marcou-contra-corinthians-2014", "Guedes", "ambiguous"],
  ["2026-11-09", "marcou-contra-corinthians-2014", "Edson", "ambiguous"],
  ["2026-11-09", "marcou-por-corinthians-2018", "Rodriguinho", "correct", "Rodriguinho"],
  ["2026-11-09", "marcou-por-corinthians-2018", "Romero", "correct", "Ángel Romero"],
  ["2026-11-09", "marcou-por-corinthians-2018", "angel romero", "correct", "Ángel Romero"],
  ["2026-11-09", "marcou-por-corinthians-2018", "Danilo", "correct", "Danilo"],
  ["2026-11-09", "marcou-por-corinthians-2018", "Avelar", "correct", "Danilo Avelar"],
  ["2026-11-09", "marcou-por-corinthians-2018", "Jô", "wrong"],
  ["2026-11-09", "expulso-santos-2020-2026", "Neymar", "correct", "Neymar"],
  ["2026-11-09", "expulso-santos-2020-2026", "Gabigol", "correct", "Gabigol"],
  ["2026-11-09", "expulso-santos-2020-2026", "gabriel barbosa", "correct", "Gabigol"],
  ["2026-11-09", "expulso-santos-2020-2026", "Soteldo", "correct", "Yeferson Soteldo"],
  ["2026-11-09", "expulso-santos-2020-2026", "Rincon", "correct", "Tomás Rincón"],
  ["2026-11-09", "expulso-santos-2020-2026", "Lucas", "ambiguous"],
  ["2026-11-09", "expulso-santos-2020-2026", "Lucas Lima", "correct", "Lucas Lima"],
  ["2026-11-09", "marcou-contra-santos-2021", "Veiga", "correct", "Raphael Veiga"],
  ["2026-11-09", "marcou-contra-santos-2021", "Calleri", "correct", "Jonathan Calleri"],
  ["2026-11-09", "marcou-contra-santos-2021", "Yuri Alberto", "correct", "Yuri Alberto"],
  ["2026-11-09", "marcou-contra-santos-2021", "Gustavo Gomes", "correct", "Gustavo Gómez"],
  ["2026-11-09", "marcou-contra-santos-2021", "Willian Bigode", "correct", "Willian Bigode"],
  ["2026-11-09", "marcou-contra-santos-2021", "Bigode", "correct", "Willian Bigode"],
  ["2026-11-09", "marcou-contra-santos-2021", "Ze Roberto", "correct", "Zé Roberto"],
  ["2026-11-09", "expulso-palmeiras-2014-2019", "Felipe Melo", "correct", "Felipe Melo"],
  ["2026-11-09", "expulso-palmeiras-2014-2019", "Valdivia", "correct", "Jorge Valdivia"],
  ["2026-11-09", "expulso-palmeiras-2014-2019", "Dudu", "correct", "Dudu"],
  ["2026-11-09", "expulso-palmeiras-2014-2019", "Mago Valdivia", "correct", "Jorge Valdivia"],
  // Player reports: nicknames from data/overrides.csv, and players once split in two by club.
  ["2026-11-09", "marcou-por-flamengo-e-gremio", "Everton cebolinha", "correct", "Everton Cebolinha"],
  ["2026-11-09", "marcou-por-flamengo-e-gremio", "Cebolinha", "correct", "Everton Cebolinha"],
  ["2026-11-09", "marcou-por-flamengo-e-gremio", "Éverton", "correct", "Everton Cebolinha"],
  ["2026-11-09", "marcou-por-flamengo-e-gremio", "Everton Cardoso", "correct", "Everton"],
  ["2026-11-05", "marcou-por-ceara-2020", "vina", "correct", "Vina"],
  ["2026-11-05", "marcou-por-ceara-2020", "Vinícius", "correct", "Vina"],
  // A word naming one answer counts next to words the data lacks.
  ["2026-11-09", "expulso-palmeiras-2014-2019", "Luis Valdivia", "correct", "Jorge Valdivia"],
  // Player report 2026-11-11: a shared first name next to another player's surname is not that player.
  ["2026-11-11", "expulso-goias-2020-2026", "Rafael Moura", "wrong"],
  ["2026-11-11", "expulso-goias-2020-2026", "Rafael Vaz", "correct", "Rafael Vaz"],
  ["2026-11-11", "expulso-goias-2020-2026", "Bruno Henrique", "wrong"],
  // "henrique" is in another answer's legal name, so the two known words point at different players.
  ["2026-11-11", "marcou-contra-fluminense-2023", "Bruno Henrique", "ambiguous"],
  ["2026-11-11", "marcou-contra-fluminense-2023", "Bruno Praxedes", "correct", "Praxedes"],
  ["2026-11-09", "marcou-por-cruzeiro-e-internacional", "Damiao", "correct", "Leandro Damião"],
  ["2026-11-09", "marcou-por-cruzeiro-e-internacional", "Sobis", "correct", "Rafael Sóbis"],
  ["2026-11-20", "marcou-contra-flamengo-2025", "Vitor Roque", "correct", "Vitor Roque"],
  ["2026-11-20", "marcou-contra-flamengo-2025", "Borre", "correct", "Rafael Borré"],
  ["2026-11-20", "marcou-contra-flamengo-2025", "Lucho Acosta", "correct", "Luciano Acosta"],
  ["2026-11-20", "marcou-contra-flamengo-2025", "Kaio Jorge", "correct", "Kaio Jorge"],
  ["2026-11-20", "marcou-contra-flamengo-2025", "Pedro Raul", "correct", "Pedro Raul"],
  ["2026-11-20", "marcou-contra-flamengo-2025", "Arrascaeta", "wrong"],
  ["2026-11-20", "expulso-flamengo-2014-2019", "Paqueta", "correct", "Lucas Paquetá"],
  ["2026-11-20", "expulso-flamengo-2014-2019", "Guerrero", "correct", "Paolo Guerrero"],
  ["2026-11-20", "expulso-flamengo-2014-2019", "Arão", "correct", "Willian Arão"],
  ["2026-11-20", "expulso-flamengo-2014-2019", "Everton", "correct", "Everton"],
  ["2026-11-20", "expulso-flamengo-2014-2019", "Diego", "correct", "Diego Ribas"],
  ["2026-11-20", "marcou-contra-atletico-mg-2015", "Pato", "correct", "Alexandre Pato"],
  ["2026-11-20", "marcou-contra-atletico-mg-2015", "Vagner Love", "correct", "Vágner Love"],
  ["2026-11-20", "marcou-contra-atletico-mg-2015", "Love", "correct", "Vágner Love"],
  ["2026-12-01", "marcou-por-gremio-2026", "Carlos Vinicius", "correct", "Carlos Vinícius"],
  ["2026-12-01", "marcou-por-gremio-2026", "Nardoni", "correct", "Juan Nardoni"],
  ["2026-12-01", "marcou-por-gremio-2026", "Amuzu", "correct", "Francis Amuzu"],
  ["2026-12-01", "marcou-contra-internacional-2021", "Marcos Leonard", "correct", "Marcos Leonardo"],
  ["2026-12-01", "marcou-contra-internacional-2021", "Pikachu", "correct", "Yago Pikachu"],
  ["2026-12-01", "marcou-contra-internacional-2021", "Thiago Nevez", "correct", "Thiago Neves"],
];

const prompt = (_date, id) => prompts.find((p) => p.id === id);

test("at least 50 typed-answer cases", () => assert.ok(CASES.length >= 50));

for (const [date, id, typed, status, name] of CASES) {
  test(`${id}: "${typed}" is ${status}${name ? ` (${name})` : ""}`, () => {
    const result = matchAnswer(typed, prompt(date, id).answers);
    assert.equal(result.status, status);
    if (name) assert.equal(result.answer.name, name);
  });
}
