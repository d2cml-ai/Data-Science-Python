# Listing schema

## Raw file (what you write: `raw_listings_live.csv` or the fallback CSV)

| Column | Required | Meaning |
| --- | --- | --- |
| `operation` | yes | `sale` or `rent` (also accepted: `venta`, `alquiler`) |
| `district` | yes | District name; aliases like "Surco" or "SMP" are normalized |
| `address_hint` | no | Approximate area only |
| `price_original` | yes | Asking price; for rent, the monthly rent |
| `currency_original` | yes | `PEN` or `USD` (also `S/`, `US$`) |
| `area_m2` | yes | Built or total area as listed |
| `bedrooms`, `bathrooms`, `parking` | bedrooms yes | Integers |
| `age_years`, `is_new` | no | Building age when known |
| `maintenance_fee_pen` | no | Monthly building fee, soles |
| `source_portal` | yes | Site name, e.g. `urbania` |
| `source_url` | **yes** | Link to the listing page; rows without it are dropped |
| `listing_date` | no | Publication date if shown |
| `collected_at` | no | Defaults to today |
| `id`, `notes` | no | Id is generated from the URL when empty |

## Final file (`listings.csv`, written by the pipeline)

The same columns plus:

| Column | Meaning |
| --- | --- |
| `price_pen` | Price in soles (`price_original × fx_used`) |
| `fx_used` | 1 for soles, the USD/PEN rate of the collection date for dollars |
| `duplicate_of` | Id of the original when the same home appears on another portal (or the same URL twice) |
| `outlier_flag` | IQR rule (1.5 × IQR) per district and operation |
| `in_range` | Sale: within the user's range and filters. Rent: comparable to the sale sample |

Duplicate rule: same operation, district and bedrooms, different portal, price within 2% and area within 3%
(tolerances in `config/defaults.yaml`).
