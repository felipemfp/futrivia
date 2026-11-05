# futrivia tasks

Spec: [SPEC.md](../SPEC.md). Plan: [plan.md](plan.md). Tests are written before the code they cover in every task.

## Phase 1: Walking skeleton

## Task 1: Scaffold, test runners, pre-commit hook
**Description:** Create the project layout from the spec, both test runners, `.gitignore` for `.cache/`, and a pre-commit hook that runs both unit suites.

**Acceptance criteria:**
- [ ] `python3 -m unittest discover -s tests/generator` and `node --test tests/game/` each run a placeholder test and pass
- [ ] `git config core.hooksPath .githooks` enables the hook, and a failing test blocks a commit
- [ ] README explains setup in three commands

**Verification:**
- [ ] Commit with a deliberately failing test is rejected, then the test is removed
- [ ] Hook runtime under 2 seconds

**Dependencies:** None
**Files likely touched:** `generator/__init__.py`, `generator/__main__.py`, `tests/generator/test_smoke.py`, `tests/game/smoke.test.js`, `.githooks/pre-commit`, `.gitignore`, `README.md`
**Estimated scope:** Medium

## Task 2: `fetch` with pinned, checksummed sources
**Description:** `python3 -m generator fetch` downloads the adaoduque CSVs at a pinned commit and the Transfermarkt `games`, `game_lineups`, `game_events` and `players` tables into `.cache/`. It checks each file against a recorded SHA-256.

**Acceptance criteria:**
- [ ] A clean run downloads every file and verifies its checksum
- [ ] A changed checksum stops with a message naming the file, without overwriting the cached copy
- [ ] A second run uses the cache without network access

**Verification:**
- [ ] Unit tests for checksum handling, with no network in tests
- [ ] Manual: run twice, the second time offline

**Dependencies:** T1
**Files likely touched:** `generator/fetch.py`, `generator/sources.py`, `tests/generator/test_fetch.py`
**Estimated scope:** Small

## Task 3: 2014–2024 adapter and hat-trick template
**Description:** Read adaoduque goals into `Goal` records with calendar season and own-goal flag, and implement the hat-trick template from the spec.

**Acceptance criteria:**
- [ ] Own goals never count toward a hat-trick
- [ ] Two goals in each of two matches is not a hat-trick
- [ ] On the real data, the template finds 36 players with 44 hat-tricks, matching the 2026-11-05 test

**Verification:**
- [ ] Unit tests on small hand-made records
- [ ] One integration test on the cached data asserting the 36 and 44 counts

**Dependencies:** T2
**Files likely touched:** `generator/records.py`, `generator/sources/adaoduque.py`, `generator/templates/goals.py`, tests
**Estimated scope:** Medium

## Task 4: Day-file writer and validator (contract v1)
**Description:** Write the spec's day-file format, plus a validator used by the build and by tests. Commit one validated test day file for the game to use.

**Acceptance criteria:**
- [ ] The validator rejects: not 7 prompts, answers outside 5–40, points not matching tier, empty aliases, unknown tier
- [ ] Writer output is byte-identical for identical input
- [ ] `tests/game/fixtures/day.json` passes the validator

**Verification:**
- [ ] Unit tests, one per rejection rule

**Dependencies:** T1
**Files likely touched:** `generator/dayfile.py`, `tests/generator/test_dayfile.py`, `tests/game/fixtures/day.json`
**Estimated scope:** Small

## Task 5: Game logic
**Description:** Write the game's rules as pure JavaScript functions: answer matching, scoring, timer, São Paulo date, saved state, and share text.

**Acceptance criteria:**
- [ ] Matching follows the five spec rules, including the "Seja mais específico" case and no typo allowance under 5 letters
- [ ] The date is correct at 23:59 and 00:00 São Paulo time, whatever the device time zone
- [ ] A saved game restores with the right remaining time, and share text contains no player names

**Verification:**
- [ ] `node --test tests/game/`

**Dependencies:** T4
**Files likely touched:** `site/game/match.js`, `site/game/score.js`, `site/game/state.js`, `site/game/share.js`, `tests/game/*.test.js`
**Estimated scope:** Medium

## Task 6: Game page plays a test day file
**Description:** Build the page in Portuguese: the start screen, each prompt with its timer, per-prompt points, the results page with every answer ranked, resume, and share. It must work at phone width.

**Acceptance criteria:**
- [ ] A full game plays from `python3 -m http.server --directory site 8000` using the test day file
- [ ] Reloading mid-prompt resumes it; reloading after finishing shows the result
- [ ] The layout has no horizontal scroll at 360 px width

**Verification:**
- [ ] Manual run in the browser at 360 px width, with screenshots kept outside the repo

**Dependencies:** T5
**Files likely touched:** `site/index.html`, `site/style.css`, `site/game/app.js`
**Estimated scope:** Medium

### Checkpoint 1: playable skeleton
- [ ] Hook passes in under 2 seconds
- [ ] A test day file plays end to end
- [ ] Review with Felipe

## Phase 2: Identity and rarity

## Task 7: Wikidata fetch, cached
**Description:** Fetch Brazilian-club footballers with every club statement, dates, aliases, language-page counts and Transfermarkt IDs. Batch the queries, back off on errors, and cache the result.

**Acceptance criteria:**
- [ ] Uses `p:P54/ps:P54`; Rodrygo (Q42728914) appears with Santos
- [ ] A failed batch stops the run rather than saving a partial result
- [ ] Refetches only when asked

**Verification:**
- [ ] Unit tests for query building and response parsing on saved sample responses
- [ ] Manual: one live fetch

**Dependencies:** T2
**Files likely touched:** `generator/wikidata.py`, `tests/generator/test_wikidata.py`, `tests/generator/fixtures/wikidata/*.json`
**Estimated scope:** Small

## Task 8: Identity resolver and report
**Description:** Give every player one identity, with a status of club-confirmed, name only, ambiguous or unmatched. Use Transfermarkt IDs first, then the name matcher, then `data/overrides.csv`, and write identity counts to the report.

**Acceptance criteria:**
- [ ] Both Gabriel Barbosa spellings resolve to Q13646572
- [ ] The Fred who scored for Fluminense resolves by club and year, not by language-page count
- [ ] A player in both sources becomes one identity; the report states how many Transfermarkt players matched by ID

**Verification:**
- [ ] Unit tests on fixtures for each case
- [ ] Coverage on real data at least the 89.8% measured on 2026-11-05

**Dependencies:** T3, T7, T12 for Transfermarkt IDs (until T12 lands, only the 2014–2024 source is resolved)
**Files likely touched:** `generator/identity.py`, `data/overrides.csv`, `tests/generator/test_identity.py`
**Estimated scope:** Medium

## Task 9: Gate 1, hand-check 50 name-only matches
**Description:** Check 50 random name-only matches against outside sources, and record the evidence and the decision.

**Acceptance criteria:**
- [ ] `reports/identity-check.md` lists all 50 with a source for each verdict
- [ ] The decision follows the spec rule (at least 90% correct keeps tiers) and is set in generator config

**Verification:**
- [ ] Felipe spot-checks 5 of the verdicts

**Dependencies:** T8
**Files likely touched:** `reports/identity-check.md`, `generator/config.py`
**Estimated scope:** Small

## Task 10: Gate 2, draft the overrides file
**Description:** Draft identity and alias corrections for the roughly 30 unresolved or ambiguous players with the most goals, with sources.

**Acceptance criteria:**
- [ ] Each row has the dataset name, Wikidata ID or "none", aliases and a source link
- [ ] Keno, Hulk, Pedro and Róger Guedes are resolved
- [ ] Felipe has reviewed and approved the file

**Verification:**
- [ ] The identity report shows those players resolved after a rebuild

**Dependencies:** T8
**Files likely touched:** `data/overrides.csv`
**Estimated scope:** Small

## Task 11: Rarity tiers in the build
**Description:** Add a tier and points to every answer, following the spec: quintiles by language-page count, ties go to the rarer tier, and players without a trusted identity get Raiz.

**Acceptance criteria:**
- [ ] Unit tests cover 5 answers, 40 answers, all tied, and some answers unmatched
- [ ] The hat-trick prompt ranks Suárez, Rodrygo and Gabriel Barbosa in its top third

**Verification:**
- [ ] Unit tests, and a check on the real hat-trick prompt

**Dependencies:** T4, T8, T9
**Files likely touched:** `generator/rarity.py`, `tests/generator/test_rarity.py`
**Estimated scope:** Small

### Checkpoint 2: trusted rarity
- [ ] Gate 1 decision recorded; overrides file approved
- [ ] Review with Felipe

## Phase 3: Content

## Task 12: Transfermarkt adapter
**Description:** Read Transfermarkt games, events and lineups into the shared records, shifting each season label forward one year, and joining player names from the `players` table.

**Acceptance criteria:**
- [ ] A 2025-12-07 match maps to Brasileirão 2025 and a 2026-05 match to Brasileirão 2026
- [ ] Goal events per match equal the final score; own goals are flagged and excluded from player goals
- [ ] Neymar has 12 goals and 28 lineup appearances across 2025–2026

**Verification:**
- [ ] Unit tests on sample rows; integration test on cached data for the totals above

**Dependencies:** T2
**Files likely touched:** `generator/sources/transfermarkt.py`, `tests/generator/test_transfermarkt.py`
**Estimated scope:** Medium

## Task 13: Goal-based templates
**Description:** Add the goal-based templates: scored for a club in a season, hat-trick, penalty for a club, 15 or more goals in a season, and scored against a club. Thresholds adjust within set limits to reach 5–40 answers.

**Acceptance criteria:**
- [ ] Each template states its data window in the text
- [ ] Prompts outside 5–40 answers after adjustment are dropped and counted in the report
- [ ] Each template has at least one test that fails for a plausible bug, such as an off-by-one in the season

**Verification:**
- [ ] Unit tests on hand-made data

**Dependencies:** T3, T11, T12
**Files likely touched:** `generator/templates/goals.py`, `tests/generator/test_templates_goals.py`
**Estimated scope:** Medium

## Task 14: Card and lineup templates
**Description:** Add the card and lineup templates: red card for a club in a season, clean-sheet runs by goalkeepers, and started a match for a club in a season.

**Acceptance criteria:**
- [ ] A clean-sheet run breaks on a conceded goal or a change of goalkeeper
- [ ] Lineup prompts use only Brasileirão 2025–2026 and say so
- [ ] Same 5–40 answer rule and report counts as T13

**Verification:**
- [ ] Unit tests; real-data check that a 4-game run gives Everson and Agustín Rossi (Brasileirão 2025)

**Dependencies:** T11, T12
**Files likely touched:** `generator/templates/cards.py`, `generator/templates/lineups.py`, tests
**Estimated scope:** Medium

## Task 15: Schedule builder and build report (gate 3)
**Description:** `build --start --days` picks 7 prompts a day with no repeats and at most 2 per template per day, seeded by date. It writes the day files and `reports/build.json`.

**Acceptance criteria:**
- [ ] Two builds produce byte-identical output
- [ ] Every day file passes the validator
- [ ] If there are fewer prompts than needed, the build stops and reports the real number

**Verification:**
- [ ] Unit tests on a small prompt pool; full build twice and compare

**Dependencies:** T4, T13, T14
**Files likely touched:** `generator/schedule.py`, `generator/build.py`, `generator/__main__.py`, tests
**Estimated scope:** Medium

### Checkpoint 3: a full year
- [ ] 365 day files committed in `site/days/`
- [ ] Report reviewed with Felipe

## Phase 4: Trial

## Task 16: Fact check and 50-answer test
**Description:** Check 20 random prompts, 3 answers each, against outside sources. Then write 50 realistic typed answers (nicknames, surnames, typos) as a game test against real day files.

**Acceptance criteria:**
- [ ] `reports/fact-check.md` has a source per answer, with at least 90% correct and every error traced and fixed
- [ ] At least 45 of the 50 typed answers behave as expected, and failures are fixed or explained

**Verification:**
- [ ] Report reviewed; `node --test tests/game/`

**Dependencies:** T15, T5
**Files likely touched:** `reports/fact-check.md`, `tests/game/typed-answers.test.js`
**Estimated scope:** Small

## Task 17: Cloudflare Pages deploy at futrivia.felipemfp.dev
**Description:** Connect the repo to Cloudflare Pages, publishing `site/` from `main` with no build command. Then attach the custom domain `futrivia.felipemfp.dev`. Claude writes the exact settings, checked against current Cloudflare docs, and Felipe applies them in the dashboard. That includes approving replacement of the old records pointing at GitHub Pages.

**Acceptance criteria:**
- [ ] `https://futrivia.felipemfp.dev` serves today's game over HTTPS, and a PR gets a preview URL
- [ ] Two different devices show identical prompts on the same São Paulo date
- [ ] The page and day file load in under 1 second over a normal connection

**Verification:**
- [ ] `dig` shows only Cloudflare records for the subdomain; manual check on two devices

**Dependencies:** T15
**Files likely touched:** `README.md` (deploy notes only)
**Estimated scope:** Small

## Task 18: Browser pass at phone width
**Description:** Play a full live game at phone width: finish, resume mid-prompt, share, and paste into WhatsApp.

**Acceptance criteria:**
- [ ] No console errors, no horizontal scroll at 360 px
- [ ] The pasted result reads correctly in WhatsApp (Felipe checks)

**Verification:**
- [ ] Browser run with screenshots outside the repo

**Dependencies:** T17
**Files likely touched:** Fixes only, if any
**Estimated scope:** Small

### Checkpoint 4: trial ready
- [ ] All pre-trial success criteria in SPEC.md checked, with evidence
- [ ] Felipe sends the link
