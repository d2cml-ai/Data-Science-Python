"""Text shown to the user in the dashboard."""

TITLE = "Buy or rent in Lima?"
SUBTITLE = ("Compares buying with a mortgage against renting a similar home and investing the cash you would "
            "otherwise put into the down payment (the opportunity cost).")

RUN = "Run"
DISTRICT = "District for the detail view"
MORTGAGE_RATE = "Mortgage rate (annual effective, %)"
DOWN_PAYMENT = "Down payment (% of price)"
OPPORTUNITY = "Opportunity cost"
CUSTOM_RATE = "Custom rate"
SCENARIO_LEVEL = "Return scenario"
LEVELS = {"low": "Low", "base": "Base", "high": "High"}
RETURN = "Annual return in soles (%)"
FX_CHANGE = "Assumed yearly USD/PEN change (%)"
PRICE = "Purchase price (S/)"
DISCOUNT = "Negotiation discount (%)"
LOAN_TERM = "Loan term (years)"
PRICE_GROWTH = "Yearly price growth (%)"
RENT_GROWTH = "Yearly rent growth (%)"
REAL = "Show in real terms (inflation-adjusted)"
HORIZON = "Horizon for the heat map (years)"
NEEDS_INPUT = "needs your input"

BUY_WINS = "Buying wins"
RENT_WINS = "Renting wins"
YEARS = "years"
LOW_CONFIDENCE = "low confidence: few listings"

SEC_VERDICTS = "1. Verdict by district"
SEC_HEATMAP = "2. Heat map: buy minus rent"
SEC_WEALTH = "3. Wealth over time"
SEC_PRICES = "4. Price check"
SEC_SOURCES = "5. Assumptions and sources"
SEC_DOWNLOAD = "6. Downloads"

BUYER = "Buyer"
RENTER = "Renter"
BREAK_EVEN = "Break-even"
NO_BREAK_EVEN = "Buying does not beat renting within 30 years under these assumptions."
BREAK_EVEN_AT = "Buying beats renting from year {year}."
REVERTS = " Note: the advantage reverses later."

SYNTHETIC = "SYNTHETIC test data: these numbers are made up to test the tool and are not market information."
CSV_MODE = "Listings come from a CSV file supplied by the user, not from a live search."
GRID_VERDICT = {"buy": "buy", "rent": "rent", "depends": "depends on assumptions"}
ORIGIN = {"researched": "researched", "fallback": "assumption (no source)", "mean of bank rates": "mean of bank rates"}

PARAM_NAMES = {
    "mortgage_rate": "Average market mortgage rate",
    "inflation": "Yearly inflation",
    "price_growth": "Price growth",
    "rent_growth": "Rent growth",
    "buy_cost_pct": "Buying costs (% of price)",
    "sell_cost_pct": "Selling costs (% of price)",
    "property_tax_pct": "Property tax (% of price per year)",
    "insurance_pct": "Insurance (% of price per year)",
    "maintenance_fee_monthly": "Monthly building fee (S/)",
}
