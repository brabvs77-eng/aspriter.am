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

- **784** product pages downloaded from Wayback snapshot `20230321042548`
- **784** product images recovered (CDX per-URL timestamps, `home_default` fallback)
- Full catalog in `data/products.json` (~1 MB)

```bash
# Re-download all products (~10 min at 0.75s delay)
python3 scripts/download-snapshot.py --list data/product-pages.txt --delay 0.75

# Download images after extraction
python3 scripts/extract-products.py --mirror mirror
python3 scripts/download-images.py --delay 0.4
```

## Quick reference

| Item | Value |
|------|-------|
| Platform | PrestaShop (Transformer theme) |
| Best archive snapshot | `20230321042548` (2023-03-21) |
| Wayback calendar | https://web.archive.org/web/*/aspriter.am |
