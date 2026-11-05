// Spoiler-free result for the group chat: one square per prompt, coloured by the tier of the answer given.
const SQUARES = { arquibancada: "⬜", torcedor: "🟨", raiz: "🟧", resenha: "🟥", enciclopedia: "🟪" };
const MISSED = "⬛";
const MAX_POINTS = 100;

export function shareText(day, results) {
  const [year, month, dayOfMonth] = day.date.split("-");
  const squares = results
    .map((r) => {
      if (!r.answerId) return MISSED;
      const answer = day.prompts.find((p) => p.id === r.promptId).answers.find((a) => a.id === r.answerId);
      return SQUARES[answer.tier];
    })
    .join("");
  const total = results.reduce((sum, r) => sum + r.points, 0);
  return `futrivia ${dayOfMonth}/${month}/${year}\n${squares} ${total}/${day.prompts.length * MAX_POINTS}\nfutrivia.felipemfp.dev`;
}
