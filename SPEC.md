# Spec: Futrivia

Status: approved 2026-11-05. Product background and test evidence: [docs/ideas/futrivia.md](docs/ideas/futrivia.md).

## Objective
A daily Brazilian football trivia game in Portuguese. Every player gets the same 7 prompts each day, types one player per prompt, and scores more for valid answers that are harder to remember. All content is generated from data, so nobody edits prompts.

**First users:** Felipe and about 5 friends, sharing results in a WhatsApp group.

**Outcome this moves:** a daily habit. In a 7-day trial with 5 friends, most still play on day 7 without being reminded, counted from results shared in the group. The game has no analytics.

### Player stories
- I open the page and see today's game, the same one my friends see, without signing up.
- For each prompt I have 25 seconds to type a valid player. A wrong guess costs only time, so I can keep trying until the timer ends.
- After each prompt I see my points, and at the end I see my total and every prompt's answers, from most obvious to rarest.
- I copy a spoiler-free result and paste it in the group.
- If I close the tab mid-game, I resume where I stopped. If I already finished, I see my result and can't replay today.

### Game rules
| Rule | Value |
|---|---|
| Prompts per day | 7 |
| Time per prompt | 25 seconds, continuing to count if the tab is closed |
| Game day | Calendar date in `America/Sao_Paulo`, changing at midnight there |
| Maximum score | 700 |

**Rarity tiers:** valid answers in a prompt are ranked by Wikidata language-page count and split into five equal groups. Tied players always share the rarer group.

| Tier | Points |
|---|---|
| Arquibancada (most obvious) | 10 |
| Torcedor | 30 |
| Raiz | 60 |
| Resenha | 85 |
| Enciclopédia (rarest) | 100 |

- Players with no trusted identity match are valid answers in the Raiz tier and don't count in the ranking.
- A blank or timed-out prompt scores 0.

**Name matching** runs only against the current prompt's answers:
1. Lowercase, remove accents and punctuation.
2. Accept the player's dataset name or any Wikidata or override alias.
3. Accept a single name word, such as a surname, if it identifies one answer in this prompt.
4. Accept one typo (edit distance 1) in names of 5 or more letters, if that identifies one answer.
5. If several answers match, show "Seja mais específico" and keep the timer running.

### Prompt rules
- Every prompt states its data window, for example "no Brasileirão, 2014–2024", so a true answer from outside the data isn't implied to be valid.
- A prompt needs 5–40 valid answers. The generator may adjust a template's threshold or filter to reach that range, and otherwise drops the prompt.
- Own goals never count as goals. A hat-trick means 3 or more goals by one player in one match. A clean-sheet run means consecutive league games in a season, started by the same goalkeeper, without conceding.
- No prompt repeats within the schedule. A day has at most 2 prompts from one template.
- Prompts contain no Wikidata-only facts. Facts come from the match data only.

## Tech Stack
No runtime dependencies and no build step.

| Part | Choice |
|---|---|
| Generator | Python 3.12, standard library |
| Game | Plain HTML, CSS and JavaScript modules |
| Device storage | `localStorage` |
| Hosting | GitHub Pages, public URL shared only with the trial group |

**Inputs:**

| Source | Provides | Calendar window |
|---|---|---|
| `adaoduque/Brasileirao_Dataset`, pinned commit | Scorers, cards | Brasileirão 2014–2024 |
| `dcaribou/transfermarkt-datasets`, checksummed | Lineups, goals, cards | Brasileirão 2025, and 2026 to 1 June |
| Wikidata | Language-page counts, aliases, identity | Not a source of facts |

- Transfermarkt labels each season with the year before: its `2024` season is Brasileirão 2025. The generator must convert this, and a test must prove it.
- Collection stopped in July 2026, so no later matches will arrive.
- Prompts may cover 2014 to 2026, but must name the window they use, such as "2014–2024" or "2025".

## Commands
The project doesn't exist yet, so these are the commands it must support.

```bash
python3 -m generator fetch            # download pinned sources into .cache/
python3 -m generator build --start 2027-01-01 --days 365   # write site/days/*.json and a report
python3 -m unittest discover -s tests/generator            # generator tests
node --test tests/game/                                    # game logic tests
python3 -m http.server --directory site 8000               # play locally
```

## Project Structure
```
generator/            Python package: fetch, identity, templates, rarity, schedule
data/overrides.csv    One-time identity and alias corrections
site/index.html       Game page
site/game/            JavaScript modules: game state, matching, scoring, sharing
site/days/            Generated YYYY-MM-DD.json, one file per day, committed
tests/generator/      Python tests
tests/game/           Node tests
reports/              Generator reports, committed
.cache/               Downloaded sources, git-ignored
```

### Contract: `site/days/YYYY-MM-DD.json`
This file is the only link between the generator and the game.

```json
{
  "version": 1,
  "date": "2027-01-01",
  "prompts": [
    {
      "id": "hat-trick-2014-2024",
      "text": "Diga um jogador que marcou um hat-trick no Brasileirão, 2014–2024",
      "answers": [
        {
          "id": "Q26517",
          "name": "Luis Suárez",
          "aliases": ["luis alberto suarez"],
          "tier": "torcedor",
          "points": 30,
          "evidence": "Grêmio, 2023"
        }
      ]
    }
  ]
}
```

The values above illustrate the format and aren't computed output. `id` is a Wikidata ID, or `dataset:<name>` for a player without a trusted match.

### Generator report
Each build writes `reports/build.json` with: prompts generated and dropped per template, answer-count distribution, identity match counts, and players on the Raiz default. Every metric in Success Criteria must be readable from this report or a test.

## Code Style
Small pure functions, with file and network access kept in `fetch`. Names are English; player-facing text is Portuguese.

```python
def hat_trick_scorers(goals: list[Goal]) -> set[str]:
    """Players with 3+ goals in one match; own goals don't count."""
    per_match = Counter(
        (goal.match_id, goal.player) for goal in goals if not goal.own_goal
    )
    return {player for (_, player), count in per_match.items() if count >= 3}
```

## Testing Strategy
Tests are written before the code they cover, and each test must be able to fail for a real bug. No snapshot tests of generated output.

| Level | Covers | Runs |
|---|---|---|
| Generator unit | Template facts on small hand-made data, own-goal exclusion, streak breaks, tier cut-offs and ties, the 5–40 rule, no repeats | Every commit, under 2 seconds |
| Game unit | Name matching, scoring, timer resume, date in São Paulo time, share text | Every commit, under 2 seconds |
| Generated data | Every day file: 7 prompts, valid schema, points match tier, no empty aliases | After each build |
| Fact check | 20 random prompts and 3 answers each, checked by hand against an outside source | Before the trial |
| Answer test | 50 realistic typed answers with nicknames, surnames and typos | Before the trial |
| Browser | One full game at phone width, including resume and sharing | Before the trial |

The game has no LLM calls, so it has no evals.

## Boundaries
- **Always:** state the data window in prompts; pin source versions; write tests first; regenerate through the generator; test at phone width.
- **Ask first:** adding any dependency or backend; scraping any source; adding prompt templates outside the listed data; publishing anywhere public; changing the day-file contract.
- **Never:** edit `site/days/` by hand; use Wikidata club history as prompt facts; let an LLM write prompts or answers; offer autocomplete; commit `.cache/` or secrets.

## Build Gates
These run inside the build, in this order. None is a prerequisite for this spec.

1. **Identity check:** hand-check 50 random name-only matches.
   - At least 90% correct: name-only matches keep their rarity tier.
   - Below 90%: all name-only players go to the Raiz default.
2. **Override file:** one-time `data/overrides.csv` for about 30 unresolved or ambiguous players with the most goals, such as Keno and Hulk. Claude drafts it from sources, and Felipe reviews it once.
3. **Prompt count:** the generator must produce enough prompts for 365 days. If it can't, stop and report the real number with options before adding data sources.

## Success Criteria
Before the trial:
- [ ] `build` produces 365 day files from a fresh clone and a clean `.cache/`, and running it twice gives identical files.
- [ ] Every day has 7 prompts with 5–40 answers each, at most 2 from one template, and no repeats in the 365 days.
- [ ] At least 90% of hand-checked answers in the fact check are correct, with every error traced and fixed in the generator or override file.
- [ ] At least 90% of the 50 test answers are handled as expected.
- [ ] Two different devices show identical prompts on the same São Paulo date.
- [ ] A game can be finished on a phone-width screen, resumed after closing the tab, and shared as text with no answers in it.
- [ ] The shared result pastes into WhatsApp readably.
- [ ] Page and day file load in under 1 second locally, excluding hosting.

After the trial:
- [ ] Of 5 friends, at least 3 share a result on day 7 without being reminded.

## Not In Scope
Accounts, leaderboards, autocomplete, archive or unlimited mode, seasons before 2014, single-match prompts for older games, English text, native apps. Reasons are in the [idea doc](docs/ideas/futrivia.md).

## Decisions
| Date | Decision |
|---|---|
| 2026-11-05 | Host the friends trial on GitHub Pages. Felipe accepts the risk of the unlicensed dataset for the trial; review this before any wider launch. |
| 2026-11-05 | The name is **futrivia**, lowercase, in the title and share text. |
| 2026-11-05 | Pre-2014 legends such as Ronaldinho are accepted as missing. Neymar is in the 2025–2026 data, with 12 goals and 28 lineup appearances. |

## Open Questions
None blocking.
