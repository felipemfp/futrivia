// Answer matching, run only against the current prompt's answers. Rules are in SPEC.md, "Name matching".

const PARTICLES = new Set(["de", "da", "do", "dos", "das", "e"]);
const MIN_WORD = 3;
const MIN_TYPO = 5;

// Must match normalize() in generator/dayfile.py; both are checked against tests/fixtures/normalize.json.
export function normalize(text) {
  return text
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .split(" ")
    .filter(Boolean)
    .join(" ");
}

function keys(answer) {
  return [...new Set([normalize(answer.name), ...answer.aliases])];
}

function withinOneEdit(a, b) {
  if (Math.abs(a.length - b.length) > 1) return false;
  let i = 0;
  let j = 0;
  let edits = 0;
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) {
      i++;
      j++;
      continue;
    }
    if (++edits > 1) return false;
    if (a.length > b.length) i++;
    else if (b.length > a.length) j++;
    else {
      i++;
      j++;
    }
  }
  return edits + (a.length - i) + (b.length - j) <= 1;
}

function decide(found) {
  if (found.length === 1) return { status: "correct", answer: found[0] };
  if (found.length > 1) return { status: "ambiguous" };
  return null;
}

export function matchAnswer(input, answers) {
  const typed = normalize(input);
  if (!typed) return { status: "wrong" };

  // Different players can share an exact name (two Dudus): every one is valid, so credit the most obvious one.
  const exactMatches = answers.filter((a) => keys(a).includes(typed));
  if (exactMatches.length) {
    const answer = exactMatches.reduce((best, a) => ((a.points ?? 0) < (best.points ?? 0) ? a : best));
    return { status: "correct", answer };
  }

  const singleWord = !typed.includes(" ");
  if (singleWord && typed.length >= MIN_WORD && !PARTICLES.has(typed)) {
    const byWord = decide(answers.filter((a) => keys(a).some((k) => k.split(" ").includes(typed))));
    if (byWord) return byWord;
  }

  if (typed.length >= MIN_TYPO) {
    const close = (key) =>
      (key.length >= MIN_TYPO && withinOneEdit(typed, key)) ||
      (singleWord && key.split(" ").some((word) => word.length >= MIN_TYPO && withinOneEdit(typed, word)));
    const byTypo = decide(answers.filter((a) => keys(a).some(close)));
    if (byTypo) return byTypo;
  }

  // Several words with a nickname the data lacks ("Everton Cebolinha"): the words that name exactly one answer decide.
  // Unknown words are ignored; known words that only point at several answers ask for more detail.
  if (!singleWord) {
    const words = typed.split(" ").filter((w) => w.length >= MIN_WORD && !PARTICLES.has(w));
    const hits = words.map((w) => answers.filter((a) => keys(a).some((k) => k.split(" ").includes(w))));
    const named = new Set(hits.filter((h) => h.length === 1).map((h) => h[0]));
    if (named.size === 1) return { status: "correct", answer: [...named][0] };
    if (named.size > 1 || hits.some((h) => h.length > 1)) return { status: "ambiguous" };
  }

  return { status: "wrong" };
}
