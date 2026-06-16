# aspriter.am — Wayback Machine Restoration Plan

This document outlines how to restore **aspriter.am** (Aspriter Armenia — natural cosmetics & organic beauty e-shop) using the [Internet Archive Wayback Machine](https://web.archive.org).

---

## 1. Executive summary

| Item | Detail |
|------|--------|
| **Site** | [aspriter.am](https://aspriter.am) — e-commerce for natural/organic products from Armenia, Europe, and the Middle East |
| **Platform** | **PrestaShop** with the **Transformer** theme (StackThemes) |
| **Archive coverage** | ~16,030 unique URLs; 31 homepage snapshots from **2021-03-05** through **2024-10-10** |
| **Best snapshot** | `20230321042548` (March 2023) — full homepage, product listings, theme assets |
| **Current live state** | Domain resolves but is behind **Cloudflare bot protection**; storefront is not publicly usable |
| **Restoration goal** | Recover catalog content, branding, and customer-facing pages; decide separately whether to restore full e-commerce functionality |

**Recommended approach:** A **hybrid restoration** — scrape and mirror static/catalog content from Wayback, then either (a) rebuild on a fresh PrestaShop install with imported data, or (b) publish a static/read-only catalog site first while e-commerce is rebuilt.

---

## 2. What the archive contains

### 2.1 Technology stack (from archived HTML)

From snapshot `https://web.archive.org/web/20230321042548/https://aspriter.am/`:

- **CMS / shop:** PrestaShop (confirmed via `prestashop` JS object, URL patterns, `robots.txt`)
- **Theme:** `themes/transformer/` — StackThemes “Transformer”
- **Custom modules:** `stinstagram`, `stlovedproduct`, `stshoppingcart`, `stcompare`
- **Currency:** EUR (€)
- **Languages:** English GB (`gb`), plus `en` and `de` URL prefixes in `robots.txt`
- **Fonts:** Google Fonts — Fjalla One, Vollkorn, Radley
- **Related domains:** `aspriter.art`, `info.aspriter.am` (also partially archived)

### 2.2 Archive inventory (CDX API, June 2025)

| Metric | Count |
|--------|-------|
| Unique URLs (`aspriter.am/*`) | ~16,030 |
| Product/category `.html` pages | ~968 |
| Friendly URL paths (`/category-slug`, `/product-slug.html`) | ~2,212 |
| Homepage snapshots | 31 |
| First capture | 2021-03-05 |
| Last capture | 2024-10-10 |

Most archived URLs are **product images** at multiple PrestaShop image sizes (`cart_default`, `home_default`, `large_default`, `_2x` variants, etc.).

### 2.3 Key archived pages

| Page | Example archived URL |
|------|----------------------|
| Homepage | `https://web.archive.org/web/20230321042548/https://aspriter.am/` |
| Sitemap (HTML) | `https://web.archive.org/web/20230321042548/https://aspriter.am/sitemap` |
| Sitemap (XML) | `https://web.archive.org/web/20230321042548/https://aspriter.am/sitemap.xml` |
| Category example | `https://web.archive.org/web/20230321042548/https://aspriter.am/3-beauty-shop-category` |
| Product example | `https://web.archive.org/web/20230321042548/https://aspriter.am/diverse/912-harisma-olive-oil-castile-soap-100-g.html` |
| CMS / legal | `https://web.archive.org/web/20230321042548/https://aspriter.am/content/10-aeu-legal-shipping-and-payment` |

### 2.4 What Wayback cannot restore

- **Database** (products, prices, stock, orders, customers, admin config)
- **PHP backend** and server-side PrestaShop logic
- **Payment gateways**, shipping rules, tax configuration
- **Admin panel** and module licenses (StackThemes modules are commercial)
- **Dynamic features:** cart, checkout, login, search autocomplete, Instagram feed module
- **Email** (`mail.aspriter.am`, `mail.info.aspriter.am` were crawled but are not useful for shop restore)

---

## 3. Restoration strategy options

### Option A — Full PrestaShop rebuild (best for live e-commerce)

Reinstall PrestaShop, re-import catalog data extracted from archives, reconfigure payments/shipping.

| Pros | Cons |
|------|------|
| Working cart, checkout, admin | Requires DB reconstruction from HTML |
| Familiar stack for original owners | Transformer theme + modules must be re-purchased |
| SEO-friendly URLs can be preserved | Highest effort and ongoing maintenance |

### Option B — Static mirror (fastest public restore)

Use `wget` / `waybackpack` to download HTML, CSS, JS, and images; rewrite links; host on static hosting (Netlify, Cloudflare Pages, S3).

| Pros | Cons |
|------|------|
| Quick to deploy | No cart/checkout |
| Low cost | Product data frozen at snapshot date |
| Good for “we’re back” presence | Search/filter may break without JS backend |

### Option C — Hybrid (recommended)

1. **Phase 1:** Static/read-only catalog from Wayback (days, not weeks).
2. **Phase 2:** New PrestaShop (or modern headless shop) with structured data import.
3. **Phase 3:** Cut over DNS when e-commerce is validated.

---

## 4. Phase-by-phase implementation

### Phase 0 — Prerequisites and legal

- [ ] Confirm **domain ownership** of `aspriter.am` (registrar/DNS access)
- [ ] Confirm **rights** to restore site content (original site owner or authorized party)
- [ ] Review [Internet Archive terms](https://help.archive.org/help/using-the-wayback-machine/) — owners may use archives to recover lost sites
- [ ] Inventory any **existing backups** (hosting panel, cPanel, PrestaShop export, `dump.sql`) — these supersede Wayback if found

### Phase 1 — Archive discovery and snapshot selection

**1.1 Browse the calendar**

```
https://web.archive.org/web/*/aspriter.am
```

**1.2 Query the CDX API for all URLs**

```bash
curl -s "https://web.archive.org/cdx/search/cdx?url=aspriter.am/*&matchType=domain&collapse=urlkey&output=text&fl=original,timestamp,statuscode,mimetype" \
  > archive-url-list.txt
```

**1.3 Pick a canonical snapshot timestamp**

Recommended: **`20230321042548`** (2023-03-21) — stable 200 responses, complete theme CSS, rich homepage.

Alternative: **`20241010011605`** (2024-10-10) — most recent homepage capture.

**1.4 Export product URL list**

```bash
grep -E '\.html$' archive-url-list.txt | grep -v 'web.archive.org' > product-pages.txt
grep -E '/[0-9]+-' archive-url-list.txt | grep -vE '\.(jpg|png|gif|webp|css|js)$' > category-pages.txt
```

### Phase 2 — Bulk download from Wayback

**2.1 Using `waybackpack` (Python)**

```bash
pip install waybackpack
waybackpack https://aspriter.am/ \
  -d ./mirror \
  --timestamp 20230321042548 \
  --raw \
  --no-raw
```

**2.2 Using `wget` (mirror with conversion)**

```bash
wget --mirror \
  --convert-links --adjust-extension --page-requisites \
  --no-parent \
  -e robots=off \
  -P ./mirror \
  "https://web.archive.org/web/20230321042548/https://aspriter.am/"
```

**2.3 Full-site crawl (larger scope)**

For all unique HTML pages, use a script that:

1. Reads URLs from `archive-url-list.txt`
2. Fetches `https://web.archive.org/web/{TIMESTAMP}/{original_url}`
3. Rate-limits to ~1 req/sec (be kind to archive.org)
4. Skips `web-static.archive.org` rewrite assets where possible

**2.4 Strip Wayback boilerplate**

Archived HTML includes Internet Archive scripts (`wombat.js`, toolbar). For a clean mirror:

- Prefer **`id_` modifier** for raw HTML:  
  `https://web.archive.org/web/20230321042548id_/https://aspriter.am/`
- Post-process: remove `<script>` tags pointing to `web-static.archive.org`
- Rewrite `https://web.archive.org/web/TIMESTAMP/im_/https://aspriter.am/...` → `/...`

### Phase 3 — Extract structured catalog data

Parse archived product pages for:

| Field | Source in HTML |
|-------|----------------|
| Product name | `<h1>`, `meta[property="og:title"]` |
| Reference/SKU | “Reference:” label |
| Price | `.current-price`, JSON-LD if present |
| Description | `.product-description` |
| Images | `og:image`, gallery `data-image-large-src` |
| Category | Breadcrumb links |
| URL slug | Original path (e.g. `/diverse/912-harisma-...html`) |

**Output format:** `products.csv` or `products.json` for import into PrestaShop / WooCommerce / Shopify.

Example extraction pipeline:

```bash
# Pseudocode workflow
for url in $(cat product-pages.txt); do
  curl -s "https://web.archive.org/web/20230321042548id_/${url}" \
    | python extract_product.py >> products.jsonl
done
```

### Phase 4 — Restore assets

Priority asset directories:

| Path | Contents |
|------|----------|
| `/img/` | Logos, favicon, PrestaShop system images |
| `/upload/stswiper/` | Homepage slider images |
| `/upload/stthemeeditor/` | Theme icons, manifest, favicons |
| `/themes/transformer/assets/` | CSS, JS, theme images |
| `/*-home_default/` | Product thumbnails |
| `/*-large_default/` | Product detail images |

Deduplicate image sizes: keep `large_default` and `home_default`; generate smaller sizes at build time if needed.

### Phase 5 — Choose deployment path

#### Path 5A — Static hosting (Phase 1 go-live)

1. Build cleaned static site in `./site/`
2. Configure `_redirects` or nginx rules for old URL patterns
3. Deploy to Cloudflare Pages / Netlify / VPS nginx
4. Point `aspriter.am` A/CNAME to host
5. Add SSL (Let’s Encrypt or Cloudflare)

**nginx snippet for legacy URLs:**

```nginx
location / {
  try_files $uri $uri/ $uri.html =404;
}
```

#### Path 5B — PrestaShop rebuild (full shop)

1. **Server:** PHP 8.1+, MySQL 8+, Apache/Nginx (typical PrestaShop 8.x requirements)
2. **Install** fresh PrestaShop 8.x
3. **Theme:** Purchase/reinstall Transformer theme from StackThemes
4. **Import** products from extracted `products.csv` via PrestaShop CSV import or API
5. **Recreate** categories from `category-pages.txt` slug patterns (`/3-beauty-shop-category` → ID 3)
6. **CMS pages:** Manually restore legal/shipping pages from archive
7. **Configure:** EUR currency, languages (EN, HY if needed), shipping zones (Armenia + international)
8. **Payments:** Wire transfer, PayPal, Stripe, or local Armenian gateways — must be set up anew
9. **Modules:** Replace or omit `stinstagram`, `stlovedproduct`, etc.

### Phase 6 — DNS and Cloudflare

Current site uses Cloudflare protection. Steps:

1. Log into Cloudflare dashboard for `aspriter.am`
2. **Development mode** or temporarily lower security while testing
3. Update origin server / Pages deployment
4. Purge CDN cache after go-live
5. Re-enable bot protection with allowlist for payment webhooks

### Phase 7 — QA and SEO

- [ ] Homepage slider and images load
- [ ] Top 20 product pages render with correct title, price, images
- [ ] Category navigation works
- [ ] `/sitemap.xml` generated and submitted to Google Search Console
- [ ] `robots.txt` allows indexing of product/category pages
- [ ] 301 redirects from any changed URLs
- [ ] Armenian and English content spot-checked
- [ ] Mobile layout verified (theme was responsive)
- [ ] Legal pages: shipping, payment, privacy, returns

---

## 5. Repository structure (proposed)

```
aspriter.am/
├── README.md
├── RESTORATION_PLAN.md          # this file
├── scripts/
│   ├── fetch-cdx-urls.sh        # CDX API export
│   ├── download-snapshot.sh     # wget/waybackpack wrapper
│   ├── strip-wayback.py         # remove IA toolbar JS
│   └── extract-products.py      # HTML → JSON catalog
├── data/
│   ├── archive-url-list.txt
│   ├── product-pages.txt
│   └── products.json
├── mirror/                      # raw Wayback download (gitignored)
└── site/                        # cleaned static output (deploy target)
```

---

## 6. Tooling reference

| Tool | Purpose | Install |
|------|---------|---------|
| [waybackpack](https://github.com/jsvine/waybackpack) | Download all archived versions of a URL | `pip install waybackpack` |
| wget | Mirror pages and assets | system package |
| [waybackpy](https://github.com/akamhy/waybackpy) | CDX API Python client | `pip install waybackpy` |
| [HTTrack](https://www.httrack.com/) | Website copier GUI/CLI | system package |
| [archivebox](https://archivebox.io/) | Self-hosted archiving (future backups) | Docker |

**CDX API examples:**

```bash
# All homepage snapshots
curl "https://web.archive.org/cdx/search/cdx?url=aspriter.am&output=json&collapse=timestamp:8"

# Only successful HTML pages
curl "https://web.archive.org/cdx/search/cdx?url=aspriter.am/*.html&matchType=domain&filter=statuscode:200&filter=mimetype:text/html&collapse=urlkey&output=text&fl=original"
```

---

## 7. Risks and mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Incomplete archives | Missing products/images | Cross-check sitemap; try multiple snapshots |
| Rate limiting by archive.org | Slow or blocked downloads | 1 req/sec, off-peak runs, cache locally |
| Wayback URL rewriting breaks assets | Broken CSS/images | Use `id_` raw URLs; run link rewriter |
| No database | Cannot restore orders/customers | Treat as fresh install; notify returning customers |
| Commercial theme license lost | Theme won’t match exactly | Re-purchase Transformer or use free PrestaShop theme |
| Outdated prices | Wrong prices shown | Mark “prices from 2023” or hide prices until manual review |
| Cloudflare lockout | Cannot update live site | Use registrar DNS to bypass if needed |
| GDPR / customer data | Legal exposure | Do not scrape or publish any customer/order data |

---

## 8. Success criteria

### Minimum viable restore (static)

- Homepage with branding and category links live on `aspriter.am`
- ≥80% of archived product pages accessible
- Images load from local or CDN copy (not hotlinked to Wayback)
- Contact information and legal pages present

### Full e-commerce restore

- PrestaShop admin accessible
- Product catalog imported with images
- Checkout flow tested end-to-end
- Payment and shipping configured for Armenia
- SSL valid; no Cloudflare infinite challenge loop

---

## 9. Immediate next steps

1. **Create branch** `cursor/wayback-restore-0e11` for implementation work.
2. **Run CDX export** — save full URL list to `data/archive-url-list.txt`.
3. **Download homepage + 10 sample products** from snapshot `20230321042548` as a proof of concept.
4. **Build `strip-wayback.py`** and verify cleaned HTML renders locally.
5. **Review extracted catalog** with site owner for price/stock accuracy.
6. **Decide:** static go-live first vs. direct PrestaShop rebuild.
7. **Secure hosting** and DNS access before public cutover.

---

## 10. Useful links

- [Wayback calendar for aspriter.am](https://web.archive.org/web/*/aspriter.am)
- [Recommended snapshot (homepage)](https://web.archive.org/web/20230321042548/https://aspriter.am/)
- [Most recent snapshot (homepage)](https://web.archive.org/web/20241010011605/https://aspriter.am/)
- [Internet Archive CDX API docs](https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server)
- [PrestaShop documentation](https://docs.prestashop-project.org/)
- [StackThemes Transformer](https://www.stackthemes.com/)

---

*Document generated from Wayback CDX API analysis and archived HTML inspection. Snapshot timestamps and URL counts should be re-verified before production restore.*
