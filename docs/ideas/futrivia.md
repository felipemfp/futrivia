# Futrivia

## Problem Statement
How might we give Brazilian football fans a daily 2-minute test that rewards the player nobody else would remember, with no content to manage?

## Recommended Direction
Everyone gets the same 7 stat-based prompts each day, such as "name a player who scored a hat-trick in the Brasileirão, 2014–2024". You get about 25 seconds per prompt, rarer valid answers score more, and you finish with a score to share.

A script calculates every prompt, answer list and rarity score from data, then pre-generates a year of them as static JSON. The date selects the day's 7, so there's no backend or daily editing. Answers ship to the browser, so cheating is easy, which is fine for a friends-first game.

Facts come from the match data, and fame comes from Wikidata. Rarity is a player's Wikidata language-page count, split into tiers within each prompt's answers, so a player can be obvious in one prompt and rare in another. Wikidata is not a source of facts, because its club histories are incomplete.

## Data Sources
| Source | Used for | Coverage |
|---|---|---|
| [`adaoduque/Brasileirao_Dataset`](https://github.com/adaoduque/Brasileirao_Dataset) | Scorers and carded players | Série A, 2014–2024 |
| [`dcaribou/transfermarkt-datasets`](https://github.com/dcaribou/transfermarkt-datasets) | Lineups, goals and cards | 557 Série A games: Brasileirão 2025, and 2026 to 1 June. Its season labels are one year behind (`2024` = Brasileirão 2025). Collection stopped in July 2026 |
| Wikidata | Fame, player identity, typed aliases | See test results |

## Wikidata Test Results (2026-11-05)
Pass marks were set before the first run. All 1,492 scorers in the goals data were tested.

| Check | Pass mark | Result | Verdict |
|---|---|---|---|
| Identity | ≥95% of scorers match exactly one person | 89.8% (58.7% club-confirmed, 31.1% name only) | **Fail** |
| Fame | Suárez, Rodrygo, Gabriel Barbosa in top third of hat-trick scorers (rank ≤12 of 36) | Ranks 1, 2 and 7 | Pass |
| Aliases | "Gabigol" and "Rodrygo" resolve to the right player | Both do | Pass |
| Merging | Both Gabriel Barbosa spellings become one person | Both map to Q13646572 | Pass |

The remaining scorers: 6.8% have several candidates (Pedro, Hulk, Paulinho) and 3.4% have no match (Róger Guedes, Keno).

Other findings:
- **Wrong matches aren't measured.** The 89.8% counts players with one match, not proven correct matches. Name-only matches are the most exposed. A spot check of 30 club-confirmed matches looked plausible, but one looks suspect (`Diogo de Oliveira Barbosa` → Diogo Barbosa).
- **Surnames don't resolve.** "Suarez", "Cano" and "Veiga" find nothing by exact match.
- **Club histories have gaps.** Deyverson has no Palmeiras, Lucas Pratto has no Brazilian club, and Yuri Alberto has only Santos. Career-based prompts from Wikidata would be wrong, so they are dropped.
- **Query trap.** Use `p:P54/ps:P54`, not `wdt:P54`. The latter returns only preferred-rank clubs, which hid Rodrygo and Suárez from their Brazilian clubs.

## Handling Unmatched Players
The identity failure doesn't block the game, because a player's name only has to match within one prompt's answer list:
- **Typed answers:** match against that prompt's answers only, including surnames, so "Fred" or "Pedro" rarely collide. Not tested yet.
- **Unmatched players:** remain valid answers, with a default middle rarity tier.
- **Most-scoring unresolved players:** a one-time alias and identity file, about 30 players, so names like Keno and Hulk score correctly. This is a single setup task, not ongoing content work.

## Key Assumptions to Validate
- [x] Fame ranks players correctly — passed on the hat-trick list; still needs checking on other prompt types.
- [ ] Wrong identity matches are rare — hand-check 50 name-only matches; below 90% correct means name-only players get the default tier instead.
- [ ] Typed answers are accepted — test 50 realistic answers, with nicknames, surnames and typos, against generated prompts; target at least 90% accepted.
- [ ] There are enough good prompts — at least 2,555 pass the filters (7 × 365), with 5–40 answers each and limited repeats of one template. Only 224 club-season prompts are confirmed so far.
- [ ] It's actually fun — 5 friends play for 7 days, and most come back unprompted by day 7.

## MVP Scope
**In:**
- A Python generator with tests, including checks on answer counts, that adjusts thresholds until a prompt has enough answers
- Prompts from goals and cards, 2014–2026, plus goalkeeper and lineup prompts from 2025–2026
- A prompt's data window stated in its text, so answers aren't wrong by omission
- A static web page in Portuguese, with name matching that tolerates typos and accents
- Results sharing as text for WhatsApp, and saved progress on the device

**Out:** everything below.

## Not Doing (and Why)
- **Prompts about seasons before 2014** — no open player data; scraping would put the weekend at risk.
- **Single-match lineup prompts for older games** — such as Flamengo 5 x 4 Santos (2011), for the same reason.
- **Career prompts from Wikidata** — its club histories are too incomplete to be trusted as answers.
- **Accounts or leaderboards** — sharing a score in the group chat does the job.
- **Rarity from player answers** — rarity should come from data, and a friend group is too small to measure it anyway.
- **Autocomplete** — it would reveal valid names and undercut the point of remembering them.
- **LLM-generated prompts** — templates can't invent a false fact about a player.
- **Unlimited mode or archive** — the daily habit comes first.

## Open Questions
- **Legends:** Ronaldinho has no goals in this data. Neymar appears only from 2025, through Transfermarkt. Accepted for the trial.
- **Public launch licensing:** `adaoduque/Brasileirao_Dataset` declares no licence, and the Transfermarkt data's origin needs checking. Settle this before any public launch.
- **Name:** does "Futrivia" stay as the game's name?
