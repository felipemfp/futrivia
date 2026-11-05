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
python3 -m generator build --start 2026-11-09 --days 86
```

`wikidata` caches footballers from Wikidata (about 15 minutes; progress in `/tmp/futrivia-wikidata/progress.log`). `build` writes `site/days/*.json` and `reports/build.json`, and stops if the prompts can't fill the days asked for. Play locally with `python3 -m http.server --directory site 8000`, or the test day at `http://localhost:8000/site/?teste=1` when serving the repo root.

## Deploy (Cloudflare Pages)
In the Cloudflare dashboard, create a Pages project connected to `felipemfp/futrivia`:

| Setting | Value |
|---|---|
| Production branch | `main` |
| Framework preset | None |
| Build command | `exit 0` |
| Build output directory | `site` |

Then add the custom domain `futrivia.felipemfp.dev` under the project's Custom domains tab. The subdomain currently has A records pointing at GitHub Pages (185.199.108–111.153); remove them first so Cloudflare can create its CNAME. Every PR gets a preview URL.

Settings checked against [Cloudflare's Git integration guide](https://developers.cloudflare.com/pages/get-started/git-integration/) and [static HTML guide](https://developers.cloudflare.com/pages/framework-guides/deploy-anything/) on 2026-11-05.
