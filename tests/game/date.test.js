import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { gameDate } from "../../site/game/date.js";

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
