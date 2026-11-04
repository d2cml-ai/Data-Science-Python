"""Spanish labels shown to the user. Code and docs stay in English."""

TITLE = "¿Comprar o alquilar en Lima?"
SUBTITLE = ("Compara comprar con hipoteca contra alquilar una vivienda parecida e invertir el dinero "
            "que no usas en la cuota inicial (el costo de oportunidad).")

RUN = "Corrida de datos"
DISTRICT = "Distrito para el detalle"
MORTGAGE_RATE = "Tasa hipotecaria (TEA, %)"
DOWN_PAYMENT = "Cuota inicial (% del precio)"
OPPORTUNITY = "Costo de oportunidad"
CUSTOM_RATE = "Tasa personalizada"
SCENARIO_LEVEL = "Escenario de rentabilidad"
LEVELS = {"low": "Bajo", "base": "Base", "high": "Alto"}
RETURN = "Rentabilidad anual en soles (%)"
FX_CHANGE = "Variación anual USD/PEN supuesta (%)"
PRICE = "Precio de compra (S/)"
DISCOUNT = "Descuento por negociación (%)"
LOAN_TERM = "Plazo del préstamo (años)"
PRICE_GROWTH = "Crecimiento anual del precio (%)"
RENT_GROWTH = "Crecimiento anual del alquiler (%)"
REAL = "Mostrar en términos reales (descontando inflación)"
HORIZON = "Horizonte para el mapa de calor (años)"
NEEDS_INPUT = "necesita tu dato"

BUY = "Comprar"
RENT = "Alquilar"
BUY_WINS = "Comprar gana"
RENT_WINS = "Alquilar gana"
YEARS = "años"
LOW_CONFIDENCE = "baja confianza: pocos avisos"

SEC_VERDICTS = "1. Veredicto por distrito"
SEC_HEATMAP = "2. Mapa de calor: comprar menos alquilar"
SEC_WEALTH = "3. Patrimonio en el tiempo"
SEC_PRICES = "4. Revisión de precios"
SEC_SOURCES = "5. Supuestos y fuentes"
SEC_DOWNLOAD = "6. Descargas"

BUYER = "Comprador"
RENTER = "Inquilino"
BREAK_EVEN = "Punto de equilibrio"
NO_BREAK_EVEN = "Comprar no supera a alquilar en 30 años con estos supuestos."
BREAK_EVEN_AT = "Comprar supera a alquilar desde el año {year}."
REVERTS = " Ojo: más adelante la ventaja se revierte."

SYNTHETIC = ("DATOS SINTÉTICOS de prueba: estos números son inventados para probar la herramienta, "
             "no son información de mercado.")
CSV_MODE = "Los avisos vienen de un archivo CSV entregado por el usuario, no de una búsqueda en vivo."
GRID_VERDICT = {"buy": "comprar", "rent": "alquilar", "depends": "depende de los supuestos"}
ORIGIN = {"researched": "investigado", "fallback": "supuesto (sin fuente)", "mean of bank rates": "promedio de bancos"}

PARAM_NAMES = {
    "mortgage_rate": "Tasa hipotecaria promedio de mercado",
    "inflation": "Inflación anual",
    "price_growth": "Crecimiento del precio",
    "rent_growth": "Crecimiento del alquiler",
    "buy_cost_pct": "Costos de compra (% del precio)",
    "sell_cost_pct": "Costos de venta (% del precio)",
    "property_tax_pct": "Impuesto predial (% del precio por año)",
    "insurance_pct": "Seguros (% del precio por año)",
    "maintenance_fee_monthly": "Mantenimiento mensual (S/)",
}
