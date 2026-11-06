// The game day is the calendar date in São Paulo, whatever the device's time zone.
const parts = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/Sao_Paulo",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

export function gameDate(now = new Date()) {
  const p = Object.fromEntries(parts.formatToParts(now).map(({ type, value }) => [type, value]));
  return `${p.year}-${p.month}-${p.day}`;
}

// The generated schedule in site/days/. Keep in step with `generator build --start --days`.
export const SCHEDULE_START = "2026-11-05";
export const SCHEDULE_DAYS = 85;

// A date outside the schedule replays it from the start: day 85 after the start is the start again.
export function cycledDate(iso) {
  const offset = Math.round((Date.parse(`${iso}T00:00:00Z`) - Date.parse(`${SCHEDULE_START}T00:00:00Z`)) / 86400000);
  const index = ((offset % SCHEDULE_DAYS) + SCHEDULE_DAYS) % SCHEDULE_DAYS;
  return new Date(Date.parse(`${SCHEDULE_START}T00:00:00Z`) + index * 86400000).toISOString().slice(0, 10);
}
