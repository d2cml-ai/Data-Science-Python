# Intake questions

Ask in Spanish. Offer options where possible; the user can always answer in free text.

| # | Question (Spanish) | Options to offer | Answer field |
| --- | --- | --- | --- |
| 1 | ¿Qué rango de precio estás dispuesto a pagar? (mínimo y máximo, en soles) | S/ 200–300 mil · S/ 300–450 mil · S/ 450–650 mil · S/ 650 mil–1 millón | `price_min`, `price_max`, `currency` |
| 2 | ¿Cuál es el área mínima en m² y el número mínimo de dormitorios que aceptarías? | 50 m² / 1 dorm. · 65 m² / 2 dorm. · 80 m² / 3 dorm. · 110 m² / 3 dorm. | `min_area_m2`, `min_bedrooms` |
| 3 | ¿En qué distritos? (de uno a seis) | Multiple choice from the common list below + free text | `districts` |
| 4 | ¿Qué porcentaje del precio puedes pagar como cuota inicial? | 10% · 20% · 30% · 40% | `down_payment_pct` |
| 5 | ¿Algo más que quieras en la búsqueda? (estacionamiento, estreno o usado, piso, mascotas, cuota mensual máxima, antigüedad máxima) | Nada más · Con estacionamiento · A estrenar · Free text | `extras_text` |

Common districts to offer (AskUserQuestion allows 4 options per question, so split them over two
multi-select questions or offer the four most likely and let "Other" take the rest): Miraflores, San Isidro,
Santiago de Surco, San Borja, Barranco, Jesús María, Pueblo Libre, San Miguel, Lince, Magdalena del Mar,
La Molina, Surquillo. Any of the 43 districts of Lima or the 7 of Callao is accepted; aliases such as "SMP",
"Surco" or "Cercado" are normalized by `new-run`.

## Answers file for `new-run`

```json
{
  "price_min": 250000,
  "price_max": 400000,
  "currency": "PEN",
  "min_area_m2": 60,
  "min_bedrooms": 2,
  "districts": ["Jesús María", "Pueblo Libre", "San Miguel"],
  "down_payment_pct": 20,
  "extras_text": "con 1 estacionamiento"
}
```

If the user answers in dollars, set `"currency": "USD"` and add `fx_usd_pen`, `fx_as_of` and `fx_source_url`
with today's rate from an official source (SBS or BCRP). The rate is recorded in `inputs.json`.

## Normalization done by `new-run`

- Minimum below maximum, both positive; amounts converted to soles.
- Down payment 5–50% (`0.2` is read as 20%).
- Districts matched to official names; unknown names come back with suggestions.
- Free text becomes `parking_min`, `max_age_years`, `max_monthly_payment`, `is_new`, `pets_allowed`, `min_floor`;
  the full text stays in `notes` as a soft preference for the agents.
