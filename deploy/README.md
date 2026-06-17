# Deploy aspriter.am static restore

The `site/` directory is the deploy target (~359 MB, 2,658 files).

> **Important:** `mirror/` and `site/` are in `.gitignore` and are **not** in the repository.
> Cloudflare Pages cannot rebuild the site from Git alone without a multi-hour Wayback download.
> Use **Direct Upload** or **Wrangler** with a locally built `site/` folder.

---

## Cloudflare Pages — recommended (Direct Upload)

Best for this project: upload the pre-built static folder.

### Dashboard

1. [Cloudflare Dashboard](https://dash.cloudflare.com/) → **Workers & Pages** → **Create**
2. Choose **Upload assets** (not “Connect to Git”)
3. Project name: `aspriter-am`
4. Drag-and-drop the contents of local `site/` (or upload a zip of `site/`)

### Settings after upload

| Field | Value |
|-------|-------|
| **Framework preset** | None (not applicable for Direct Upload) |
| **Build command** | *(empty — no build step)* |
| **Build output directory** | *(empty — files are served as uploaded)* |
| **Root directory** | `/` |
| **Production branch** | *(n/a for Direct Upload)* |

### Custom domain

1. Pages project → **Custom domains** → **Set up a custom domain**
2. Enter `aspriter.am` and `www.aspriter.am`
3. If the domain is already on Cloudflare, DNS records are added automatically
4. Temporarily lower **Bot Fight Mode** / **Under Attack** while testing (the old site used aggressive protection)

### Headers & redirects

`_headers` and `_redirects` from `deploy/` are copied into `site/` by `build-site.sh` and work on Cloudflare Pages.

---

## Cloudflare Pages — via Wrangler CLI

Build locally, then deploy:

```bash
# 1. Build site locally (requires mirror/ from Wayback download)
bash scripts/build-site.sh

# 2. Deploy
npx wrangler pages deploy site --project-name=aspriter-am
```

Wrangler settings:

| Field | Value |
|-------|-------|
| **Framework preset** | None |
| **Project name** | `aspriter-am` |
| **Deploy directory** | `site` |

---

## Cloudflare Pages — Connect to Git (not recommended yet)

Only use Git integration if `site/` is committed to the repo or the build is changed to download from Wayback in CI (20+ minutes, may hit build timeout).

If you still connect Git for a **future** pipeline:

| Field | Value |
|-------|-------|
| **Production branch** | `main` |
| **Framework preset** | **None** |
| **Build command** | `bash scripts/build-site.sh` |
| **Build output directory** | `site` |
| **Root directory** | `/` (leave empty) |
| **Build watch paths** | `scripts/*`, `deploy/*` |

### Environment variables (Git build with full Wayback pipeline)

Only needed if you implement a full download in CI:

| Variable | Value |
|----------|-------|
| `SNAPSHOT_TIMESTAMP` | `20230321042548` |
| `REQUEST_DELAY` | `0.75` |
| `PYTHON_VERSION` | `3.11` |

Example full CI build command (slow, ~30–60 min):

```bash
pip install -r requirements.txt
bash scripts/fetch-cdx-urls.sh
python3 scripts/download-snapshot.py --list data/product-pages.txt --delay 0.75
python3 scripts/download-snapshot.py --list data/site-pages.txt --delay 0.6
python3 scripts/download-images.py --delay 0.4
python3 scripts/download-assets.py --delay 0.35
bash scripts/build-site.sh
```

Cloudflare Pages build timeout: **20 minutes** (paid) — this pipeline will likely fail. Prefer Direct Upload.

---

## Build locally before any deploy

```bash
pip install -r requirements.txt

# If mirror/ does not exist yet, run the full restore pipeline first
# (see README.md), then:

bash scripts/build-site.sh
```

---

## DNS (if domain is on Cloudflare)

| Type | Name | Content |
|------|------|---------|
| CNAME | `@` | `aspriter-am.pages.dev` (or your Pages subdomain) |
| CNAME | `www` | `aspriter-am.pages.dev` |

If apex CNAME is not supported on your plan, use Cloudflare **CNAME flattening** (automatic on proxied records).

---

## Limitations

- Cart, checkout, and search require a live PrestaShop backend.
- Import `data/products-prestashop.csv` when rebuilding full e-commerce.
- Product images use `home_default` size (available in Wayback archive).
