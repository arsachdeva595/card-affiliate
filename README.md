# StartWith Carrd: pSEO affiliate site

A static site generator for Carrd guides, comparisons and plan pages. Every page sends visitors to carrd.co through your referral link. Read [STRATEGY.md](STRATEGY.md) for the reasoning and roadmap.

## Quick start

```bash
python3 generator/build.py          # writes dist/ (no dependencies)
python3 -m http.server -d dist 8000 # preview at http://localhost:8000
```

The build prints warnings for anything still unconfigured.

## Configure: `site.config.json`

| Key | What to put |
|---|---|
| `base_url` | Your domain, e.g. `https://startwithcarrd.com` |
| `affiliate_url` | Your Carrd referral link |
| `carrd_hub_url` | Your existing Carrd site (linked from the footer) |
| `ga4_measurement_id` | `G-…`. Then mark the `affiliate_click` event as a Key event in GA4 |
| `indexnow_key` | Any 8–128 character hex string, e.g. from `python3 -c "import secrets;print(secrets.token_hex(16))"` |

## Add pages

Edit the JSON in `data/` and rebuild:

- `howto.json` → `/how-to/{slug}/`
- `usecases.json` → `/for/{slug}/`
- `compare.json` → `/vs/{slug}/` (also listed on `/alternatives/`)
- `plans.json` → `/pricing/` and `/is-carrd-free/` (set `verified: true` after checking carrd.co/pro)

## Deploy (GitHub Pages)

1. Repo → Settings → Pages → Source: **GitHub Actions**.
2. Merge to `main`. `.github/workflows/deploy.yml` builds, deploys, and pings IndexNow.
3. Settings → Pages → Custom domain → enter your domain and follow the DNS instructions.

Cloudflare Pages or Netlify work too: build command `python3 generator/build.py`, output directory `dist`.
