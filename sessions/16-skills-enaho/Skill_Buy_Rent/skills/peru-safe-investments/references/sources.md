# Sources

Confirm each page is public and current, and record the exact URL and date used.

| Data | Where to look |
| --- | --- |
| Deposit rates by institution | SBS rate comparator for savings and deposits (term deposits in soles); each bank's published rate sheet (tarifario) |
| Deposit insurance limit | Fondo de Seguro de Depósitos (FSD) official page |
| S&P 500 total return history | S&P Dow Jones Indices index page and factsheet; published history of a large S&P 500 index fund |
| S&P/BVL Peru General | S&P Dow Jones Indices index page and factsheet; Bolsa de Valores de Lima statistics |
| USD/PEN history | BCRP (BCRPData exchange-rate series) or SBS daily exchange rate |
| CPI inflation | BCRP, same value as `housing_params.json` |
| Taxes for individual investors | SUNAT guidance on income from capital (interest, dividends, capital gains, foreign income) |

Use a factsheet's stated annualized returns when a level series is not available; then `basis` says
"factsheet annualized returns, as of <date>" and the low/base/high rule you used (for example low = 10-year,
base = 20-year, high = 30-year annualized) instead of rolling percentiles.
