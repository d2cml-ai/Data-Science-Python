# Opportunity-cost log (2026-11-03)

Educational information, not personalized investment advice.

| URL | Accessed | What was taken |
| --- | --- | --- |
| https://www.alfinbanco.pe/ahorros/depositoaplazofijo | 2026-11-03 | Soles DPF TREA: 360 d 5.65%, 540 d 5.75%, 720 d 5.85%, 1080 d 5.00%; min S/500; valid 03/11-17/11/2026 or S/20M cap |
| https://www.efectibank.pe/ahorros/deposito-a-plazo/ | 2026-11-03 | Two TEA tables (5.00/5.25% 360 d, 5.50/5.70% 720 d, 5.75/6.00% 1080 d); used the confirmed 5.00% (360 d) and stated TREA 5.75% (1080 d); min S/500; tarifario 03.08.2026; ITF 0.005%; no maintenance fee; early-cancellation penalty |
| https://andina.pe/agencia/noticia-guerra-bancos-2026-conoce-las-mejores-tasas-para-tus-depositos-a-plazos-1075245.aspx | 2026-11-03 (article 2026-11-02) | SBS average rates soles >360 d: Caja Piura 6.23%, Efectiva 5.92%, Incasur 5.91%, Los Andes 5.90%, Paita 5.76%, Confianza 5.68% (cajas June 2026, banks/financieras 2026-08-05) |
| https://elperuano.pe/noticia/304049-tus-ahorros-tienen-una-nueva-cobertura-el-fondo-de-seguro-de-depositos-fija-el-limite-en-s123000 | 2026-11-03 | FSD coverage S/ 123,000, Sep-Nov 2026 (Circular F-618-2026) |
| https://elperuano.pe/noticia/306896-presentan-proyecto-de-ley-para-que-cuentas-de-ahorros-sigan-exoneradas-de-impuestos-hasta-cuando | 2026-11-03 | Interest exemption (LIR art. 19 i) valid to 2026-12-31 (D. Leg. 1549); extension to 2029 proposed |
| https://query1.finance.yahoo.com/v8/finance/chart/%5ESP500TR?period1=0&period2=9999999999&interval=1mo | 2026-11-03 | Monthly S&P 500 Total Return closes 1988-01 to 2026-11-03 (last 16,987.20) |
| https://www.spglobal.com/spdji/en/indices/equity/sp-500/ | 2026-11-03 | Index provider reference page (figures not taken from it) |
| https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01142MM/json/1999-1/2026-12 | 2026-11-03 | Indice General BVL monthly 1999-01 to 2026-09 (last 59,831.84) |
| https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/json/2025-1/2026-12 | 2026-11-03 | Lima CPI 12-month change, Sep.2026 = 4.55% (inflation_used) |
| https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01210PM/json/2006-1/2026-12 | 2026-11-03 | USD/PEN monthly average points (2006-09 3.248 ... 2026-09 3.379) |
| https://www.cuatrecasas.com/es/latam/fiscalidad/art/ganancias-capital-enajenacion-valores-negociados-bvl | 2026-11-03 (article 2023-12-21) | BVL capital gains 5% for Peruvian securities from 2024 (exemption lapsed) |
| https://finantres.com/impuestos-sobre-trading-e-inversiones-en-peru/ | 2026-11-03 (search snippet) | 5% dividend withholding for domiciled individuals |
| https://www.ey.com/es_pe/newsroom/2024/03/aspectos-clave-ingresos-extranjero | 2026-11-03 (search snippet) | Foreign-source income added to labour income, progressive 8%-30% |

## Computation

`index_returns.py --band-window 10` on both level series; S&P with `--fx-change 0.0 --inflation 0.0455`, BVL with `--inflation 0.0455`.

- S&P 500 USD (= PEN with fx 0%): low 7.41%, base 10.39%, high 13.86%; CAGR 10y 15.01%, 20y 10.87%, 30y 9.93%; vol 15.9%; worst 12m -43.3%.
- BVL PEN: low 2.06%, base 7.74%, high 22.61%; CAGR 5y 26.8%, 10y 14.6%, 20y 9.1%; vol 43.6%; worst 12m -67.5%.
- Deposit: low (5.65+5.00)/2 = 5.325%; base (5.65+5.85+5.75)/3 = 5.75%; high 6.23%.
- Real base = (1+r)/1.0455 - 1. Risk ranking 1/2/3 confirmed by volatility (0 / 15.9% / 43.6%).

## Not found / rejected

- 1440/1800-day deposit rates; tax on deposit interest from 2027; ETF expense ratios, broker/Cavali fees; US withholding credit treatment.
- comparabancaperu.com rejected (unofficial figures inconsistent with SBS reports); SUNAT personas page returned 403.
