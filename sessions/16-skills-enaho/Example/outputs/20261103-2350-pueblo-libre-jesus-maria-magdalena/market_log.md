# Market log: 20261103-2350-pueblo-libre-jesus-maria-magdalena

Collected 2026-11-03 23:50 to 2026-11-04 00:10 (America/Lima). Source mode: **live** (no `data/listings.csv` exists, so there is no CSV fallback).

Search: sale apartments S/ 450,000–550,000, ≥ 60 m², ≥ 2 bedrooms, building < 10 years (`max_age_years` = 10), in Pueblo Libre, Jesús María and Magdalena del Mar, plus comparable rentals.

## Portals tried

| Portal | Result | Action |
| --- | --- | --- |
| Urbania (urbania.pe/buscar/venta-de-departamentos-en-pueblo-libre--lima--lima) | HTTP 403 | Blocked; not used again |
| Adondevivir (adondevivir.com/departamentos-en-venta-en-pueblo-libre.html) | HTTP 403 | Blocked; not used again |
| Properati (properati.com.pe/s/pueblo-libre/departamento/venta) | HTTP 403 | Blocked; not used again |
| MercadoLibre (departamento.mercadolibre.com.pe/venta/lima/pueblo-libre/) | HTTP 403 | Blocked; not used again |
| Babilonia (babilonia.pe/venta/departamentos/lima/pueblo-libre) | HTTP 403 | Blocked; not used again |
| Nestoria (nestoria.pe/pueblo-libre/departamentos/venta/dormitorios-2) | HTTP 401 | Blocked; not used again |
| Trovit (casas.trovit.com.pe/departamento-pueblo-libre-dos-dormitorios) | HTTP 401 | Blocked; not used again |
| Nexo Inmobiliario (nexoinmobiliario.pe/busqueda/venta-de-departamentos-en-lima-lima-pueblo-libre) | 200 | Only featured projects with "desde" prices (no unit prices); not used for listings |
| **InfoCasas (infocasas.com.pe)** | 200 | robots.txt (`User-agent: *`) allows the search pages; **only source of listings** |

Web-search queries (used only to find portals; search-engine summaries were **not** used as listings because they do not tie prices to listing URLs):
`departamento venta Pueblo Libre 2 dormitorios estreno S/ 500,000`; `alquiler departamento Jesús María 2 dormitorios 70 m2`;
`infocasas.com.pe venta departamentos lima "hasta" soles 2 dormitorios jesus-maria`.

## InfoCasas pages fetched (one curl request each, about 6–10 s apart, no parallel requests)

Data were read from the page's embedded JSON (`__NEXT_DATA__`): price and currency, built m², bedrooms, bathrooms, parking, construction year, construction state, maintenance fee, publication date and listing link.
The guessed price-filter URL returned 403, so the site's own bedroom-filter pages (2 and 3 bedrooms) were paged instead. That made 44 InfoCasas requests (≤ 10 per district and operation; 52 fetches in the run including the portal probes, under the 80 cap).

| Fetched at | URL | HTTP | (rows on page, total results) |
| --- | --- | --- | --- |
| 2026-11-03T23:52:44 | https://www.infocasas.com.pe/venta/departamentos/lima/pueblo-libre | 200 | (21, 677) |
| 2026-11-03T23:53:23 | https://www.infocasas.com.pe/venta/departamentos/lima/pueblo-libre/2-dormitorios/desde-450000/hasta-550000 | 403 | noparse |
| 2026-11-03T23:53:31 | https://www.infocasas.com.pe/venta/departamentos/lima/pueblo-libre/2-dormitorios | 200 | (21, 214) |
| 2026-11-03T23:54:15 | https://www.infocasas.com.pe/venta/departamentos/lima/pueblo-libre/2-dormitorios/pagina2 | 200 | (21, 214) |
| 2026-11-03T23:54:25 | https://www.infocasas.com.pe/venta/departamentos/lima/pueblo-libre/2-dormitorios/pagina3 | 200 | (21, 214) |
| 2026-11-03T23:54:34 | https://www.infocasas.com.pe/venta/departamentos/lima/pueblo-libre/2-dormitorios/pagina4 | 200 | (21, 214) |
| 2026-11-03T23:54:44 | https://www.infocasas.com.pe/venta/departamentos/lima/pueblo-libre/2-dormitorios/pagina5 | 200 | (21, 214) |
| 2026-11-03T23:54:53 | https://www.infocasas.com.pe/venta/departamentos/lima/pueblo-libre/3-dormitorios | 200 | (21, 342) |
| 2026-11-03T23:55:02 | https://www.infocasas.com.pe/venta/departamentos/lima/pueblo-libre/3-dormitorios/pagina2 | 200 | (21, 342) |
| 2026-11-03T23:55:12 | https://www.infocasas.com.pe/venta/departamentos/lima/pueblo-libre/3-dormitorios/pagina3 | 200 | (21, 342) |
| 2026-11-03T23:55:22 | https://www.infocasas.com.pe/venta/departamentos/lima/pueblo-libre/3-dormitorios/pagina4 | 200 | (21, 342) |
| 2026-11-03T23:55:31 | https://www.infocasas.com.pe/alquiler/departamentos/lima/pueblo-libre/2-dormitorios | 200 | (19, 19) |
| 2026-11-03T23:55:39 | https://www.infocasas.com.pe/alquiler/departamentos/lima/pueblo-libre/2-dormitorios/pagina2 | 200 | (0, 19) |
| 2026-11-03T23:55:47 | https://www.infocasas.com.pe/alquiler/departamentos/lima/pueblo-libre/2-dormitorios/pagina3 | 200 | (0, 19) |
| 2026-11-03T23:55:56 | https://www.infocasas.com.pe/alquiler/departamentos/lima/pueblo-libre/3-dormitorios | 200 | (21, 30) |
| 2026-11-03T23:56:04 | https://www.infocasas.com.pe/alquiler/departamentos/lima/pueblo-libre/3-dormitorios/pagina2 | 200 | (9, 30) |
| 2026-11-03T23:56:13 | https://www.infocasas.com.pe/venta/departamentos/lima/jesus-maria/2-dormitorios | 200 | (21, 290) |
| 2026-11-03T23:56:22 | https://www.infocasas.com.pe/venta/departamentos/lima/jesus-maria/2-dormitorios/pagina2 | 200 | (21, 290) |
| 2026-11-03T23:56:45 | https://www.infocasas.com.pe/venta/departamentos/lima/jesus-maria/2-dormitorios/pagina3 | 200 | (21, 290) |
| 2026-11-03T23:57:04 | https://www.infocasas.com.pe/venta/departamentos/lima/jesus-maria/2-dormitorios/pagina4 | 200 | (21, 290) |
| 2026-11-03T23:57:14 | https://www.infocasas.com.pe/venta/departamentos/lima/jesus-maria/2-dormitorios/pagina5 | 200 | (21, 290) |
| 2026-11-03T23:57:24 | https://www.infocasas.com.pe/venta/departamentos/lima/jesus-maria/3-dormitorios | 200 | (21, 368) |
| 2026-11-03T23:57:33 | https://www.infocasas.com.pe/venta/departamentos/lima/jesus-maria/3-dormitorios/pagina2 | 200 | (21, 368) |
| 2026-11-03T23:57:44 | https://www.infocasas.com.pe/venta/departamentos/lima/jesus-maria/3-dormitorios/pagina3 | 200 | (21, 368) |
| 2026-11-03T23:57:53 | https://www.infocasas.com.pe/venta/departamentos/lima/jesus-maria/3-dormitorios/pagina4 | 200 | (21, 368) |
| 2026-11-03T23:58:02 | https://www.infocasas.com.pe/alquiler/departamentos/lima/jesus-maria/2-dormitorios | 200 | (21, 27) |
| 2026-11-03T23:58:10 | https://www.infocasas.com.pe/alquiler/departamentos/lima/jesus-maria/2-dormitorios/pagina2 | 200 | (6, 27) |
| 2026-11-03T23:58:18 | https://www.infocasas.com.pe/alquiler/departamentos/lima/jesus-maria/2-dormitorios/pagina3 | 200 | (0, 27) |
| 2026-11-03T23:58:27 | https://www.infocasas.com.pe/alquiler/departamentos/lima/jesus-maria/3-dormitorios | 200 | (21, 46) |
| 2026-11-03T23:58:35 | https://www.infocasas.com.pe/alquiler/departamentos/lima/jesus-maria/3-dormitorios/pagina2 | 200 | (21, 46) |
| 2026-11-03T23:58:44 | https://www.infocasas.com.pe/venta/departamentos/lima/magdalena-del-mar/2-dormitorios | 200 | (21, 251) |
| 2026-11-03T23:58:54 | https://www.infocasas.com.pe/venta/departamentos/lima/magdalena-del-mar/2-dormitorios/pagina2 | 200 | (21, 251) |
| 2026-11-03T23:59:03 | https://www.infocasas.com.pe/venta/departamentos/lima/magdalena-del-mar/2-dormitorios/pagina3 | 200 | (21, 251) |
| 2026-11-03T23:59:13 | https://www.infocasas.com.pe/venta/departamentos/lima/magdalena-del-mar/2-dormitorios/pagina4 | 200 | (21, 251) |
| 2026-11-03T23:59:22 | https://www.infocasas.com.pe/venta/departamentos/lima/magdalena-del-mar/2-dormitorios/pagina5 | 200 | (21, 251) |
| 2026-11-03T23:59:32 | https://www.infocasas.com.pe/venta/departamentos/lima/magdalena-del-mar/3-dormitorios | 200 | (21, 458) |
| 2026-11-03T23:59:41 | https://www.infocasas.com.pe/venta/departamentos/lima/magdalena-del-mar/3-dormitorios/pagina2 | 200 | (21, 458) |
| 2026-11-03T23:59:51 | https://www.infocasas.com.pe/venta/departamentos/lima/magdalena-del-mar/3-dormitorios/pagina3 | 200 | (21, 458) |
| 2026-11-04T00:00:01 | https://www.infocasas.com.pe/venta/departamentos/lima/magdalena-del-mar/3-dormitorios/pagina4 | 200 | (21, 458) |
| 2026-11-04T00:00:11 | https://www.infocasas.com.pe/alquiler/departamentos/lima/magdalena-del-mar/2-dormitorios | 200 | (21, 34) |
| 2026-11-04T00:00:19 | https://www.infocasas.com.pe/alquiler/departamentos/lima/magdalena-del-mar/2-dormitorios/pagina2 | 200 | (13, 34) |
| 2026-11-04T00:00:28 | https://www.infocasas.com.pe/alquiler/departamentos/lima/magdalena-del-mar/2-dormitorios/pagina3 | 200 | (0, 34) |
| 2026-11-04T00:00:37 | https://www.infocasas.com.pe/alquiler/departamentos/lima/magdalena-del-mar/3-dormitorios | 200 | (21, 46) |
| 2026-11-04T00:00:46 | https://www.infocasas.com.pe/alquiler/departamentos/lima/magdalena-del-mar/3-dormitorios/pagina2 | 200 | (21, 46) |

## Selection rules applied to the raw file (`raw_listings_live.csv`)

- **Sale**: kept only listings matching the search (price converted at 3.466 for the check only; the engine recomputes), ≥ 60 m², ≥ 2 bedrooms, and
  either construction state "A estrenar"/"En construcción" (new, `is_new = true`) or a known construction year ≤ 10 years old.
  Used units with no construction year were **skipped** (age cannot be verified against the < 10-year filter). Cap: first 30 matching listings per district, in page order.
- **Rent**: every rental seen on the 2- and 3-bedroom pages is kept. The engine marks as comparable those with ≥ 2 bedrooms and an area within ±15% of the sale median area.
  The rent rows seen exceed 30 per district (44/68/75) because the engine, not the agent, picks the comparables. Comparables used: 25/36/21.
- Skipped at extraction (21 total): 9 projects with "desde" prices only (not a unit), 5 listings without price, 7 without area.
- `address_hint` = street name without number (approximate). No personal names.

Sale listings skipped (by district and reason):

| District | Price out of range | Area < 60 | Age > 10 | Used, age unverifiable | Over 30 cap |
| --- | --- | --- | --- | --- | --- |
| Pueblo Libre | 137 | 2 | 2 | 6 | 3 |
| Jesús María | 118 | 15 | 0 | 8 | 6 |
| Magdalena del Mar | 129 | 21 | 0 | 9 | 0 |

## Data-quality notes

- Many kept sale units are **off-plan / under construction** (Pueblo Libre 17 of 30, Jesús María 14 of 30, Magdalena 2 of 19); they are marked in `notes`.
- Magdalena `venta-de-dpto-76m2-magdalena-del-mar/194359552` lists 763 m² (its title says 76 m²). It is kept as listed and flagged as an outlier by the engine.
- `super-duplex-en-venta-en-juan-de-aliaga-magdalena/188551390` appears on the rental pages although its slug says "venta". It is kept as seen and flagged as an outlier.
- One InfoCasas listing (Pueblo Libre, 3 bedrooms) shows US$ in the structured price but says soles in its description; the structured price was used.
- No cross-portal duplicates are possible (single portal); 8 outliers were flagged by the engine (IQR 1.5×).

## Housing parameters

- SBS active rates by credit type (MN, last 30 business days to 03/11/2026). The first request got an Incapsula cookie page; the second request with that cookie returned the public table (no CAPTCHA, no login).
- BCRP API series: PD04639PD/PD04640PD (FX), PN01273PM (CPI), PN01305PM (CPI rents), PD38030PQ (S/ per m², Sector Medio), PD17464PQ/PD17466PQ/PD17467PQ (US$ per m² by district).
- UIT 2026 = S/ 5,500 (DS 301-2025-EF, El Peruano); alcabala rule from gob.pe.
- Not sourced (null): buy_cost_pct total (notary, SUNARP, appraisal), sell_cost_pct, property_tax_pct, insurance_pct, price/rent growth by district.

## Final counts (clean, in-range, used for statistics)

| District | Sale n (found) | Realistic price (P25–P75) | Rent n (found) | Realistic rent (P25–P75) | Index check |
| --- | --- | --- | --- | --- | --- |
| Pueblo Libre | 30 (30) | S/ 496,302 (467,245–509,495) | 25 (44) | S/ 2,200 (2,000–2,400) | +2.0% vs BCRP |
| Jesús María | 30 (30) | S/ 488,170 (466,700–514,704) | 36 (68) | S/ 2,500 (2,400–3,013) | +0.7% vs BCRP |
| Magdalena del Mar | 16 (19) | S/ 528,352 (517,985–535,280) | 21 (75) | S/ 2,500 (2,300–2,772) | −1.2% vs BCRP |

No district has fewer than 8 listings per side.
