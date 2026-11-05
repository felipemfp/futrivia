# futrivia

A daily Brazilian football trivia game: 7 prompts a day, the same for everyone, and rarer valid answers score more. All content is generated from match data and Wikidata. See [SPEC.md](SPEC.md) and [tasks/plan.md](tasks/plan.md).

## Setup
Needs Python 3.12 and Node 22. No packages to install.

```bash
git config core.hooksPath .githooks
python3 -m generator fetch
python3 -m unittest discover -s tests/integration
```

The first command runs the unit tests on every commit. The second downloads the pinned sources into `.cache/` (about 220 MB). The third checks the generator against that real data.

## Tests
```bash
python3 -m unittest discover -s tests/generator
node --test 'tests/game/*.test.js'
```
