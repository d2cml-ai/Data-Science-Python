# Evaluación: con y sin skills

Corran cada pedido dos veces, con skills y sin skills, y anoten qué skills se activaron, si usó avisos reales con
URL y fecha, si las cifras salen del modelo y cómo se ve el resultado.

```bash
claude -p "<pedido>"                                  # con skills
claude -p --disallowedTools Skill "<pedido>"          # sin skills
```

| # | Pedido | Skills que deberían activarse | Lo que debe salir |
|---|---|---|---|
| 1 | `/buy-vs-rent fixture` | `buy-vs-rent` (+ `streamlit-dashboard`) | Corrida sintética completa; Jesús María: comprar desde el año 3 frente al depósito a plazo; `salidas/validacion.txt` con RESULTADO: OK |
| 2 | ¿Me conviene comprar o alquilar un depa de 2 dormitorios en Pueblo Libre con S/ 350 mil? | `buy-vs-rent` → los 4 agentes | Primero las preguntas que falten (cuota inicial, área, extras); luego avisos con URL y veredicto a 5–30 años |
| 3 | ¿Cuánto pagaría al mes por un préstamo de S/ 280,000 al 8.5 % a 20 años? | `rent-vs-buy-model` | Unos S/ 2,370 al mes, con la fórmula de cuota fija sobre la TEA |
| 4 | ¿Cuánto rinde un depósito a plazo en soles comparado con el S&P 500? | `peru-safe-investments` | Tasas con banco, URL y fecha; S&P 500 convertido a soles; aviso de uso educativo |

## Resultados

| # | Con skills: ¿qué se activó? | Cifra | ¿Con fuentes y fechas? | Sin skills: qué hizo | Nota |
|---|---|---|---|---|---|
| 1 | `buy-vs-rent` (corrida de prueba hecha al construir el proyecto con `hl.py fixture-run`) | Veredictos en `salidas/validacion.txt` | Sí (sintéticas, marcadas) | — | Figuras en `figuras/` |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |

Qué mirar sin skills: si inventa precios o tasas sin fuente, si olvida los costos de compra y venta, si compara
contra el alquiler sin invertir la cuota inicial, si da una sola respuesta sin horizonte ni supuestos.

Si una skill no se activa, mejoren su `description` con las palabras del pedido y repitan.
