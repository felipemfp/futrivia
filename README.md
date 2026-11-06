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

## Build the days
```bash
python3 -m generator wikidata
python3 -m generator build --start 2026-11-05 --days 85
```

`wikidata` caches footballers from Wikidata (about 15 minutes; progress in `/tmp/futrivia-wikidata/progress.log`). `build` writes `site/days/*.json` and `reports/build.json`, and stops if the prompts can't fill the days asked for. Play locally with `python3 -m http.server --directory site 8000`, or the test day at `http://localhost:8000/site/?teste=1` when serving the repo root.

## Deploy (Cloudflare Workers)
The site is a Cloudflare Worker named `futrivia` that serves the static files in `site/`, connected to this repo with Workers Builds. `wrangler.jsonc` holds the configuration: every push to `main` deploys to `https://futrivia.felipemfp.dev`, and every pull request builds a preview with `npx wrangler preview`, which needs the `previews` block in that file.

Check the configuration locally without deploying:
```bash
npx -y wrangler@4.158.0 deploy --dry-run
```
