# aspriter.am

Restoration project for [aspriter.am](https://aspriter.am) — Aspriter Armenia, a natural cosmetics and organic beauty e-shop.

The live site is currently unavailable behind Cloudflare protection. This repository will hold scripts, extracted data, and deployment artifacts to restore the site from the [Internet Archive Wayback Machine](https://web.archive.org/web/*/aspriter.am).

## Documentation

See **[RESTORATION_PLAN.md](./RESTORATION_PLAN.md)** for the full restoration plan, including:

- Archive inventory (~16,000 URLs, PrestaShop + Transformer theme)
- Recommended hybrid restore strategy (static catalog first, then full shop)
- Phase-by-phase steps, tooling, and commands
- Risks, success criteria, and next actions

## Quick reference

| Item | Value |
|------|-------|
| Platform | PrestaShop (Transformer theme) |
| Best archive snapshot | `20230321042548` (2023-03-21) |
| Wayback calendar | https://web.archive.org/web/*/aspriter.am |
