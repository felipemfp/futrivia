# Implementation Plan: futrivia

Status: awaiting approval. Implements [SPEC.md](../SPEC.md); detailed tasks are in [todo.md](todo.md).

## Overview
Two parts joined by one file format:
- **Generator:** a Python program that turns match data and Wikidata into 365 daily files.
- **Game:** a static page that plays the day's file.

The work starts with a thin end-to-end slice. A test day file is playable before real data arrives, so the riskiest data work runs alongside a working game.

## Architecture Decisions
- **One internal record format for both sources.** Each source gets an adapter that produces the same `Goal`, `Card` and `LineupEntry` records, each with a calendar season. Templates never see source-specific fields, and the Transfermarkt season shift is handled once, in its adapter.
- **Identity by stable IDs where possible.** Transfermarkt players match to Wikidata by Transfermarkt player ID (Wikidata property P2446). Coverage is unchecked until task 8; names are the fallback. Names from the 2014–2024 source go through the matcher tested on 2026-11-05: name with club and year, then global name lookup. One person found in both sources becomes one answer.
- **Wikidata facts are never used as answers.** It supplies language-page counts, aliases and identity only. Club history is fetched with `p:P54/ps:P54`, because `wdt:P54` hides past clubs.
- **The build is deterministic.** Inputs are pinned by commit hash or checksum, and every output is sorted. Choices are seeded from the date string, so two builds produce identical files. That makes generated files reviewable in diffs.
- **Pinned inputs, cached outside git.** Transfermarkt files aren't versioned, so `fetch` records their checksums and stops if they change. A changed checksum means a deliberate update, not a silent one.
- **The game is plain JavaScript modules.** Game logic is pure functions tested with `node --test`, and the page is a thin layer over them. The browser's `Intl` API supplies the São Paulo date.
- **Cloudflare Pages deploys from GitHub.** Cloudflare's GitHub integration publishes `site/` on each push to `main`, with no build command. Every PR gets a preview URL, which is useful for checking generated days. The repo has no CI config, and the deploy settings live in Cloudflare.
- **Fast checks gate every commit.** A pre-commit hook in `.githooks/` runs both unit suites, kept under 2 seconds.

## Dependency Graph
```
T1 scaffold + hooks
 ├─ T2 fetch (pinned sources) ─┬─ T3 adaoduque adapter + hat-trick template ─┐
 │                             ├─ T7 Wikidata fetch ─ T8 identity ─┬─ T9 identity check (gate 1)
 │                             │                                   └─ T10 overrides (gate 2)
 │                             └─ T12 Transfermarkt adapter        │
 ├─ T4 day-file contract + validator ◄────────────────────────────┘ (T3 output)
 │    ├─ T5 game logic ─ T6 game page                     [checkpoint 1]
 │    └─ T11 rarity tiers (needs T8)                      [checkpoint 2]
 └─ T13 goal templates, T14 card + lineup templates (need T11, T12)
       └─ T15 schedule + build report (gate 3)            [checkpoint 3]
            └─ T16 fact check + 50-answer test ─ T17 Pages deploy ─ T18 phone browser pass  [checkpoint 4]
```

**Can run in parallel:** after T4 fixes the contract, the game (T5–T6) and the generator (T7 onward) are independent. Parallel builders each get their own worktree.

## Task List

### Phase 1: Walking skeleton
- [ ] T1: Scaffold, test runners, pre-commit hook
- [ ] T2: `fetch` with pinned, checksummed sources
- [ ] T3: 2014–2024 adapter and hat-trick template
- [ ] T4: Day-file writer and validator (contract v1)
- [ ] T5: Game logic: matching, scoring, timer, São Paulo date, share text
- [ ] T6: Game page plays a test day file

### Checkpoint 1: playable skeleton
- [ ] Both unit suites pass in the hook, in under 2 seconds
- [ ] A test day file plays start to finish locally, with resume and share
- [ ] Review with Felipe

### Phase 2: Identity and rarity
- [ ] T7: Wikidata fetch, cached
- [ ] T8: Identity resolver and report
- [ ] T9: Gate 1, hand-check 50 name-only matches
- [ ] T10: Gate 2, draft the overrides file for Felipe's review
- [ ] T11: Rarity tiers in the build

### Checkpoint 2: trusted rarity
- [ ] Identity report produced; gate 1 decision recorded
- [ ] Felipe has reviewed the overrides file
- [ ] The hat-trick prompt ranks Suárez, Rodrygo and Gabriel Barbosa in its top third

### Phase 3: Content
- [ ] T12: Transfermarkt adapter, with the season shift proven
- [ ] T13: Goal-based templates
- [ ] T14: Card and lineup templates
- [ ] T15: Schedule builder and build report (gate 3)

### Checkpoint 3: a full year
- [ ] 365 valid day files, identical across two builds
- [ ] Report reviewed with Felipe; if the prompt count falls short, stop here with options

### Phase 4: Trial
- [ ] T16: Fact check and 50-answer test
- [ ] T17: Cloudflare Pages deploy at futrivia.felipemfp.dev
- [ ] T18: Browser pass at phone width

### Checkpoint 4: trial ready
- [ ] Every pre-trial success criterion in SPEC.md is checked off, with evidence
- [ ] Felipe sends the link to the group

## Risks and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Not enough good prompts for 365 days | High | Gate 3 stops the build with the real count and options. Adding a second year or new sources needs approval |
| Wrong identity matches give wrong rarity | Medium | Gate 1 decides whether name-only matches keep their tier, and gate 2 fixes top players by hand once |
| Transfermarkt files change or disappear | Medium | Checksums stop silent changes; keep a dated copy of `.cache/` outside the repo |
| Wikidata rate limits or timeouts | Low | Batched queries with backoff, cached results, refetch only on request |
| Season shift applied wrongly | High | One adapter owns it; a test checks a known match date maps to the right Brasileirão year |
| Own goals counted as goals in Transfermarkt events | Medium | T12 identifies own goals from event descriptions, tested against known own goals |
| Day boundary differs between devices | Medium | One function computes the date with an explicit time zone, tested at 23:59 and 00:00 São Paulo time |
| Answers visible in the public day files | Low | Accepted by spec: friends-first, no anti-cheat |
| Existing DNS records for futrivia.felipemfp.dev | Low | Records already point at GitHub Pages servers (185.199.108–111.153) but serve nothing over HTTPS. Felipe confirms they can be replaced in T17 |

## Open Questions
None blocking.
