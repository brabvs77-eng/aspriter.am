# Cloudflare Pages — Git deploy (18 chunks)

## Overview

1. **GitHub Actions** downloads the site from Wayback in **18 parallel chunks** → commits `mirror-chunks/` to git
2. **Cloudflare Pages** runs `assemble-and-build.sh` → outputs `site/`

---

## Step 1 — Run GitHub Actions restore

1. GitHub repo → **Actions** → **Restore Wayback (18 chunks)**
2. **Run workflow** (leave `chunk` empty for all 18 parts)
3. Wait ~15–25 minutes (3 chunks at a time)
4. Verify `mirror-chunks/01/` … `mirror-chunks/18/` appear on `main`

Re-run a single chunk: set `chunk` to `1`–`18`.

---

## Step 2 — Cloudflare Pages settings

| Field | Value |
|-------|-------|
| **Connect to Git** | Yes |
| **Production branch** | `main` |
| **Framework preset** | **None** |
| **Build command** | `bash scripts/assemble-and-build.sh` |
| **Build output directory** | `site` |
| **Root directory** | *(empty)* |
| **Build watch paths** | `mirror-chunks/*`, `scripts/*`, `deploy/*` |

### Environment variables

| Variable | Value | Required |
|----------|-------|----------|
| `SNAPSHOT_TIMESTAMP` | `20230321042548` | Optional |
| `PYTHON_VERSION` | `3.11` | Yes (for `pip install` if needed) |

### Build command (full)

Cloudflare may need dependencies for `download-assets.py` during assemble:

```
pip install -r requirements.txt && bash scripts/assemble-and-build.sh
```

Use this if the default build fails on `import requests`.

---

## Chunk timing (per part)

| Chunk | URLs | ~Time (Wayback) |
|-------|------|-----------------|
| 01 | 128 (site + products) | ~3 min |
| 02–18 | 43–44 products each | ~1.5 min each |

CF Pages assemble step: **under 5 minutes** (no Wayback download).

---

## Custom domain

Pages → **Custom domains** → `aspriter.am`, `www.aspriter.am`

---

## Direct Upload (alternative)

If you skip Git chunks, build locally and upload `site/`:

```bash
bash scripts/assemble-and-build.sh   # needs mirror-chunks/ locally
npx wrangler pages deploy site --project-name=aspriter-am
```
