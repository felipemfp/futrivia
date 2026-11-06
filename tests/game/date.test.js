import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readdirSync } from "node:fs";
import { gameDate, cycledDate, SCHEDULE_START, SCHEDULE_DAYS } from "../../site/game/date.js";

test("the schedule constants match the files in site/days", () => {
  const files = readdirSync(new URL("../../site/days/", import.meta.url)).filter((f) => f.endsWith(".json")).sort();
  assert.equal(files.length, SCHEDULE_DAYS);
  assert.equal(files[0], `${SCHEDULE_START}.json`);
  assert.equal(files.at(-1), `${cycledDate("2027-01-28")}.json`);
});

test("dates inside the schedule map to themselves", () => {
  assert.equal(cycledDate("2026-11-05"), "2026-11-05");
  assert.equal(cycledDate("2027-01-28"), "2027-01-28");
});

test("the day after the schedule ends starts it over", () => {
  assert.equal(cycledDate("2027-01-29"), "2026-11-05");
  assert.equal(cycledDate("2027-01-30"), "2026-11-06");
});

test("later cycles count calendar days, leap day included", () => {
  assert.equal(cycledDate("2027-04-24"), "2026-11-05");
  assert.equal(cycledDate("2028-02-29"), "2026-12-31");
  assert.equal(cycledDate("2028-03-01"), "2027-01-01");
});

test("dates before the schedule wrap backwards", () => {
  assert.equal(cycledDate("2026-11-04"), "2027-01-28");
});

test("23:59 in São Paulo is still the old day", () => {
  assert.equal(gameDate(new Date("2027-01-01T02:59:00Z")), "2026-12-31");
});

test("00:00 in São Paulo starts the new day", () => {
  assert.equal(gameDate(new Date("2027-01-01T03:00:00Z")), "2027-01-01");
});

test("the device time zone does not change the game day", () => {
  const script = `import("${new URL("../../site/game/date.js", import.meta.url)}").then(m => process.stdout.write(m.gameDate(new Date("2027-01-01T02:59:00Z"))))`;
  for (const tz of ["Pacific/Kiritimati", "Pacific/Pago_Pago", "UTC"]) {
    const out = execFileSync(process.execPath, ["--input-type=module", "-e", script], { env: { ...process.env, TZ: tz } });
    assert.equal(out.toString(), "2026-12-31", tz);
  }
});
