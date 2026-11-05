// futrivia page: renders the screens and wires the game modules to the DOM. All rules live in the sibling modules.
import { PROMPT_MS, newGame, nextPrompt, guess, refresh, restore, timeLeft, totalScore } from "./state.js";
import { gameDate } from "./date.js";
import { shareText, maxScore } from "./share.js";

const TIERS = { arquibancada: "Arquibancada", torcedor: "Torcedor", raiz: "Raiz", resenha: "Resenha", enciclopedia: "Enciclopédia" };
const URGENT_MS = 5000;
const app = document.getElementById("app");
const sr = document.getElementById("sr");
let day = null;
let game = null;
let storageKey = "";

// ---------- helpers ----------
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === false || v == null) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  el.append(...kids.flat().filter((k) => k != null && k !== false));
  return el;
}
const announce = (text) => { sr.textContent = ""; setTimeout(() => { sr.textContent = text; }, 30); };
const answerOf = (result) => (result.answerId ? day.prompts.find((p) => p.id === result.promptId).answers.find((a) => a.id === result.answerId) : null);
const byRarity = (answers) => answers.map((a, i) => [a, i]).sort((x, y) => x[0].points - y[0].points || x[1] - y[1]).map(([a]) => a);
const MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const shortDate = (iso) => { const [, m, d] = iso.split("-").map(Number); return `${d === 1 ? "1º" : d} ${MONTHS[m - 1]}`; };
const reduceMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const pointsText = (n) => `${n} ${n === 1 ? "ponto" : "pontos"}`;

function load() {
  try {
    return restore(JSON.parse(localStorage.getItem(storageKey)), day);
  } catch { /* no storage or corrupt: start fresh */ }
  return null;
}
function save() {
  try { localStorage.setItem(storageKey, JSON.stringify(game)); } catch { /* storage unavailable: the game still works */ }
}
function set(next) {
  game = next;
  save();
}

// ---------- shared pieces ----------
function slots(current) {
  return h("div", { class: "slots", "aria-hidden": "true" }, day.prompts.map((p, i) => {
    const r = game.results[i];
    const a = r && answerOf(r);
    if (a) return h("span", { class: "slot filled", "data-tier": a.tier });
    if (r) return h("span", { class: "slot miss" });
    return h("span", { class: i === current ? "slot now" : "slot" });
  }));
}
function chip(tier) { return h("span", { class: "chip", "data-tier": tier }, TIERS[tier]); }

function sticker(result, extra = "") {
  const a = answerOf(result);
  if (!a) {
    return h("div", { class: `sticker miss ${extra}` }, h("span", { class: "nm" }, "Tempo esgotado"), h("span", { class: "pts" }, "0", h("small", {}, " pts")));
  }
  return h("div", { class: `sticker ${extra}`, "data-tier": a.tier },
    chip(a.tier), h("span", { class: "nm" }, a.name), h("span", { class: "pts" }, `+${a.points}`, h("small", {}, " pts")),
    a.evidence ? h("span", { class: "ev" }, a.evidence) : null);
}

// ---------- screens ----------
function tierPoints() {
  const seen = {};
  for (const p of day.prompts) for (const a of p.answers) seen[a.tier] = a.points;
  return Object.keys(TIERS).filter((t) => t in seen).map((t) => [t, seen[t]]);
}

function showStart() {
  const date = new Date(`${day.date}T12:00:00Z`).toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" });
  app.replaceChildren(h("section", { class: "page hero" },
    h("h1", {}, "Complete o álbum de hoje"),
    h("p", { class: "date" }, date),
    slots(-1),
    h("ul", { class: "legend", "aria-label": "Categorias e pontos" }, tierPoints().map(([t, pts]) => h("li", { "data-tier": t }, h("span", { class: "sw" }), h("span", {}, TIERS[t]), h("b", {}, `${pts} pts`)))),
    h("ol", { class: "how" },
      h("li", {}, h("b", {}, "1"), h("span", {}, `${day.prompts.length} perguntas, ${PROMPT_MS / 1000} segundos cada. Digite um jogador que se encaixe.`)),
      h("li", {}, h("b", {}, "2"), h("span", {}, `Quanto mais raro o jogador, mais pontos. Máximo: ${maxScore(day)} pts.`))),
    h("button", { class: "btn", type: "button", onclick: () => { set(nextPrompt(game, Date.now())); render(); } }, "Começar")));
}

let clockEl, barEl, timerEl, warned;
function updateTimer() {
  const left = timeLeft(game, Date.now());
  const secs = Math.ceil(left / 1000);
  clockEl.textContent = `${secs}s`;
  timerEl.setAttribute("aria-label", `${secs} segundos restantes`);
  if (left <= URGENT_MS && left > 0 && !warned) { warned = true; announce("5 segundos"); }
  barEl.style.transform = `scaleX(${left / PROMPT_MS})`;
  timerEl.toggleAttribute("data-urgent", left <= URGENT_MS);
}

function showPrompt() {
  const prompt = day.prompts[game.index];
  const input = h("input", { type: "text", id: "guess", name: "guess", autocomplete: "off", autocorrect: "off", spellcheck: "false", autocapitalize: "words", enterkeyhint: "send", maxlength: "60", placeholder: "Jogador" });
  const feedback = h("p", { class: "feedback", "aria-live": "assertive", id: "feedback" });
  warned = false;
  clockEl = h("div", { class: "clock", "aria-hidden": "true" });
  barEl = h("i");
  timerEl = h("div", { class: "timer", role: "timer" }, clockEl, h("div", { class: "bar", "aria-hidden": "true" }, barEl));
  const say = (kind, text) => {
    feedback.dataset.kind = kind;
    feedback.textContent = "";
    feedback.textContent = text;
    if (kind === "wrong" && !reduceMotion()) feedback.animate([{ transform: "translateX(0)" }, { transform: "translateX(-7px)" }, { transform: "translateX(7px)" }, { transform: "translateX(0)" }], { duration: 350 });
  };
  const submit = (e) => {
    e.preventDefault();
    if (!input.value.trim()) return say("ambiguous", "Digite o nome de um jogador.");
    const { game: next, outcome } = guess(game, day, input.value, Date.now());
    if (next !== game) set(next);
    if (outcome.status === "wrong") { say("wrong", `Errou: “${input.value.trim().slice(0, 30)}” não vale aqui. Tente outro!`); input.value = ""; input.focus(); return; }
    if (outcome.status === "ambiguous") { say("ambiguous", "Quase! Seja mais específico: tem mais de um com esse nome."); input.select(); return; }
    render();
  };
  app.replaceChildren(h("section", { class: "page" },
    h("div", { class: "meta" }, h("div", { class: "count" }, `Figurinha ${game.index + 1} de ${day.prompts.length}`), slots(game.index)),
    h("h2", { class: "prompt", id: "prompt" }, prompt.text),
    timerEl,
    h("form", { onsubmit: submit, autocomplete: "off", novalidate: true },
      h("label", { for: "guess" }, "Sua resposta"),
      h("div", { class: "field" }, input, h("button", { class: "btn", type: "submit" }, "Enviar"))),
    feedback));
  updateTimer();
  input.focus();
}

// After a time-out: a few answers that would have counted, from the most obvious to the rarest.
function missHint(prompt) {
  const sorted = byRarity(prompt.answers);
  const picks = [...new Set([sorted[0], sorted[Math.floor(sorted.length / 2)], sorted.at(-1)])];
  return h("div", { class: "hint" }, h("p", {}, "Valia, por exemplo:"),
    h("ul", {}, picks.map((x) => h("li", {}, h("span", { class: "sw", "data-tier": x.tier }), h("span", {}, x.name), h("b", {}, `${x.points} pts`)))));
}

function showReveal() {
  const result = game.results.at(-1);
  const last = game.index >= day.prompts.length - 1;
  const a = answerOf(result);
  const shownAt = Date.now();
  const advance = (e) => { if (e.repeat || Date.now() - shownAt < 400) return e.preventDefault(); set(nextPrompt(game, Date.now())); render(); };
  app.replaceChildren(h("section", { class: "page" },
    h("div", { class: "meta" }, h("div", { class: "count" }, `Figurinha ${game.index + 1} de ${day.prompts.length}`), slots(-1)),
    h("p", { class: "prompt" }, day.prompts[game.index].text),
    sticker(result, "pop"),
    a ? null : missHint(day.prompts[game.index]),
    h("div", { class: "reveal-actions" },
      h("button", { class: "btn", id: "next", type: "button", onclick: advance, onkeydown: (e) => { if (e.repeat) e.preventDefault(); } }, last ? "Ver meu álbum" : "Próxima figurinha"))));
  announce(a ? `${a.name}. ${TIERS[a.tier]}. ${pointsText(a.points)}.` : "Tempo esgotado. Zero pontos.");
  document.getElementById("next").focus();
}

async function share(note) {
  const text = shareText(day, game.results);
  const done = (msg) => { note.textContent = msg; note.toggleAttribute("data-ok", true); announce(msg); };
  let copied = false;
  try { await navigator.clipboard.writeText(text); copied = true; } catch { /* try the fallback below */ }
  if (!copied) {
    const ta = h("textarea", { "aria-hidden": "true", style: "position:fixed;opacity:0" }, text);
    document.body.append(ta);
    ta.select();
    copied = !!(document.execCommand && document.execCommand("copy"));
    ta.remove();
  }
  if (navigator.share) {
    try { await navigator.share({ text }); return done(copied ? "Copiado e compartilhado!" : "Compartilhado!"); } catch { /* cancelled or unsupported: fall through to the copy confirmation or the textarea */ }
  }
  if (copied) return done("Copiado! Cole no grupo.");
  const box = h("textarea", { class: "sharebox", readonly: true, rows: "4", "aria-label": "Resultado para copiar" }, text);
  note.replaceChildren("Não deu para copiar. Toque no texto abaixo, selecione e copie.", box);
  box.focus();
  box.select();
}

function showResults() {
  const total = totalScore(game);
  const note = h("p", { class: "note", role: "status" });
  const rows = day.prompts.map((p, i) => {
    const r = game.results[i];
    const a = answerOf(r);
    return h("details", { class: "row" },
      h("summary", {},
        h("span", { class: "rk" }, `${i + 1}`),
        h("span", { class: "who" }, a ? a.name : "Tempo esgotado"),
        a ? chip(a.tier) : h("span", { class: "chip none" }, "Sem resposta"),
        h("strong", { class: "pt" }, `${r.points} pts`),
        h("span", { class: "sq" }, p.text)),
      h("div", { class: "detail" },
        h("ol", { class: "ranking", "aria-label": "Todas as respostas, da mais óbvia à mais rara" }, byRarity(p.answers).map((x, k, all) => {
          const rank = all.findIndex((y) => y.points === x.points) + 1; // equal points share a rank
          return h("li", { class: x.id === r.answerId ? "pick" : "", "aria-current": x.id === r.answerId ? "true" : false },
            h("span", { class: "rk" }, `${rank}º`),
            h("span", {}, x.name, x.id === r.answerId ? [" ", h("span", { class: "sua" }, "sua")] : null,
              h("span", { class: "sub" }, h("span", { class: "sw", "data-tier": x.tier }), TIERS[x.tier], x.evidence ? [" · ", h("span", { class: "ev" }, x.evidence)] : "")),
            h("span", { class: "p" }, `${x.points} pts`));
        }))));
  });
  app.replaceChildren(
    h("section", { class: "page score" },
      h("h1", {}, "Seu álbum de hoje"),
      h("p", { class: "big", id: "total" }, `${total}`, h("small", {}, `/${maxScore(day)}`)),
      slots(-1)),
    h("div", { class: "share-box" },
      h("button", { class: "btn", type: "button", id: "share", onclick: () => share(note) }, "Compartilhar resultado"),
      note),
    h("section", { class: "page rows" }, rows,
      h("p", { class: "note foot" }, "Toque em uma linha para ver todas as respostas. Volte amanhã para um álbum novo.")));
  announce(`Álbum completo: ${total} de ${maxScore(day)} pontos.`);
  app.focus();
  scrollTo(0, 0);
}

function showError(title, text) {
  app.replaceChildren(h("section", { class: "page msg" }, h("h1", {}, title), h("p", {}, text)));
}

function render() {
  try {
    document.getElementById("edition").textContent = shortDate(day.date);
    if (game.phase === "ready") showStart();
    else if (game.phase === "playing") showPrompt();
    else if (game.phase === "reveal") showReveal();
    else showResults();
  } catch (e) {
    console.error(e);
    showError("Algo deu errado", "Não conseguimos mostrar o álbum. Recarregue a página.");
  }
}

// ---------- boot ----------
function tick() {
  if (game.phase !== "playing") return;
  const next = refresh(game, Date.now());
  if (next !== game) { set(next); render(); } else updateTimer();
}

async function boot() {
  const test = new URLSearchParams(location.search).has("teste");
  try {
    const res = await fetch(test ? "../tests/fixtures/days/2027-01-01.json" : `days/${gameDate()}.json`, { cache: "no-cache" });
    if (!res.ok) throw new Error(String(res.status));
    day = await res.json();
    if (!Array.isArray(day.prompts) || !day.prompts.length) throw new Error("empty");
  } catch {
    return showError("Ainda não saiu o álbum de hoje", "Não encontramos as perguntas de hoje. Tente de novo daqui a pouco.");
  }
  document.querySelector(".logo").setAttribute("href", `./${location.search}`);
  storageKey = `futrivia:${day.date}`;
  game = load() || newGame(day);
  game = refresh(game, Date.now());
  save();
  render();
  setInterval(tick, 250);
}
boot();
