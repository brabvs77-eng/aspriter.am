# Post-deploy audit & fix plan — aspriter.am

**Date:** 2026-06-18  
**Live URL:** https://aspriter-am.pages.dev/ (200 OK)  
**Custom domain:** https://aspriter.am/ — **403** (Cloudflare bot challenge, not Pages)

---

## 1. Audit summary

| Check | Result |
|-------|--------|
| Pages deploy (`aspriter-am.pages.dev`) | ✅ HTTP 200 |
| Custom domain `aspriter.am` | ❌ HTTP 403 — старый CF challenge / не привязан к Pages |
| HTML pages | ✅ 868 страниц в зеркале |
| Product catalog JSON | ✅ 784 товара |
| Images in `mirror-chunks` | ⚠️ 3 158 файлов |
| Images in Wayback archive | 11 228 URL |
| **Missing images** | **~8 054** уникальных путей |

### Главная проблема: неполные изображения

При восстановлении скачивались в основном `home_default` и `large_default`.  
На страницах категорий PrestaShop использует **`cart_default`**, **`small_default`**, **`medium_default`** — их **~3 229** уникальных путей отсутствуют на сайте.

Примеры битых миниатюр:
- `/46-cart_default/olive-oil-soap-levantercamomile-by-manis-rose-100-gr.jpg`
- `/1255-cart_default/nymfes-cosmetics-shertazatox-ojar-limoni-balzam.jpg`

### Ожидаемые ограничения (не баги)

| Проблема | Причина |
|----------|---------|
| Корзина, checkout, поиск | Статический сайт, нет PHP/PrestaShop |
| `module/stshoppingcart/ajax` 404 | AJAX корзины |
| Google Charts QR (`chart.googleapis.com`) | Внешний сервис, не критично |
| Pinterest/Facebook share ссылки | Внешние, не ассеты сайта |
| Cookie bar (jsdelivr) | Внешний CDN |

---

## 2. План исправлений

### Фаза A — Изображения ✅ (2026-06-18)

1. ✅ Скрипт `scripts/download-all-images.py`
2. ✅ Загружено **7 009** изображений → `mirror-chunks/00-images/` (0 miss)
3. ✅ Пересборка: 13 703 файла, **~982 MB**
4. ⏳ Commit + push → автодеплой CF Pages
5. Повторный аудит: **878** уникальных путей всё ещё отсутствуют (нет в Wayback)

**Было:** 3 229 missing → **Стало:** 878 missing (−73%)

### Фаза B — Домен aspriter.am

1. Cloudflare → **Pages** → `aspriter-am` → **Custom domains** → добавить `aspriter.am`
2. Удалить/изменить старые DNS-записи, указывающие на прежний origin с bot protection
3. SSL: Full (strict)
4. Отключить **Bot Fight Mode** / Under Attack для теста
5. Проверить: `curl -I https://aspriter.am/` → 200

### Фаза C — UX после картинок

1. Проверить главную и 5 категорий вручную
2. Убрать/заменить битые QR-коды (Google Charts deprecated)
3. Добавить баннер «Каталог архивный, заказ временно недоступен» (опционально)
4. Настроить 404-страницу для старых URL

### Фаза D — Полноценный магазин (позже)

1. Импорт `data/products-prestashop.csv` в новый PrestaShop 8.x
2. Платежи, доставка, SSL для checkout
3. Редирект статики → новый магазин или поддомен

---

## 3. Cloudflare Pages (текущие настройки)

| Поле | Значение |
|------|----------|
| Framework preset | **None** |
| Build command | `pip install -r requirements.txt && bash scripts/assemble-and-build.sh` |
| Output directory | `site` |
| URL | https://aspriter-am.pages.dev/ |

---

## 4. Команды мониторинга

```bash
# Локальный аудит битых ассетов
python3 scripts/audit-site.py

# Проверка деплоя
curl -sI https://aspriter-am.pages.dev/

# Статистика изображений
find mirror-chunks -name '*.jpg' | wc -l
```
