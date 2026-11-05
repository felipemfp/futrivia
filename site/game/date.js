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
