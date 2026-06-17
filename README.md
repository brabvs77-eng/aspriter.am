# aspriter.am

Restoration project for [aspriter.am](https://aspriter.am) — Aspriter Armenia, a natural cosmetics and organic beauty e-shop.

The live site is currently unavailable behind Cloudflare protection. This repository will hold scripts, extracted data, and deployment artifacts to restore the site from the [Internet Archive Wayback Machine](https://web.archive.org/web/*/aspriter.am).

## Documentation

See **[RESTORATION_PLAN.md](./RESTORATION_PLAN.md)** for the full restoration plan, including:

- Archive inventory (~16,000 URLs, PrestaShop + Transformer theme)
- Recommended hybrid restore strategy (static catalog first, then full shop)
- Phase-by-phase steps, tooling, and commands
- Risks, success criteria, and next actions

## Quick start

```bash
# 1. Export URL index from Wayback CDX API
bash scripts/fetch-cdx-urls.sh

# 2. Download proof-of-concept snapshot (homepage, sample products, theme CSS)
pip install -r requirements.txt
python3 scripts/download-snapshot.py --poc

# 3. Clean HTML and build static site output
python3 scripts/strip-wayback.py

# 4. Extract product catalog from mirrored pages
python3 scripts/extract-products.py --mirror mirror
```

### Bulk download

```bash
# First N product pages (rate-limited, ~1 req/sec)
python3 scripts/download-snapshot.py --list data/product-pages.txt --limit 50

# Extract all products directly from Wayback (no local mirror needed)
python3 scripts/extract-products.py --list data/product-pages.txt --limit 100
```

### Bulk catalog (completed)

- **784** product pages + **84** site pages (categories, CMS, contact)
- **784** product images + **1003** theme/UI assets
- Static site build: **2,658 files**, ~359 MB in `site/`
- PrestaShop import: `data/products-prestashop.csv`

```bash
# Site pages (categories, CMS, homepage)
bash scripts/build-site-pages-list.sh
python3 scripts/download-snapshot.py --list data/site-pages.txt --delay 0.6

# Theme assets (CSS, JS, slider images)
python3 scripts/download-assets.py --delay 0.35

# Build deployable static site
bash scripts/build-site.sh

# Export for PrestaShop rebuild
python3 scripts/export-prestashop-csv.py
```

### Deploy via Git + Cloudflare Pages (18 chunks)

1. **GitHub Actions** → run `Restore Wayback (18 chunks)` workflow
2. Chunks land in `mirror-chunks/01/` … `18/` and are committed to git
3. **Cloudflare Pages** (Framework preset: **None**):

| Setting | Value |
|---------|-------|
| Build command | `pip install -r requirements.txt && bash scripts/assemble-and-build.sh` |
| Output directory | `site` |

Full details: [deploy/README.md](./deploy/README.md)

```bash
# Manual: download one chunk locally
CHUNK=1 bash scripts/download-chunk.sh

# Assemble all chunks into site/
bash scripts/assemble-and-build.sh
```

## Quick reference

| Item | Value |
|------|-------|
| Platform | PrestaShop (Transformer theme) |
| Best archive snapshot | `20230321042548` (2023-03-21) |
| Wayback calendar | https://web.archive.org/web/*/aspriter.am |
