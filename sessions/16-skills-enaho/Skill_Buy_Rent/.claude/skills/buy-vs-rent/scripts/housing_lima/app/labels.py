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
HORIZON = "Years you plan to stay (used in sections 2 and 4)"
NEEDS_INPUT = "needs your input"

BUY_WINS = "Buying wins"
RENT_WINS = "Renting wins"
YEARS = "years"
LOW_CONFIDENCE = "low confidence: few listings"

SEC_VERDICTS = "1. The recommendation"
SEC_HOW = "2. How the recommendation was made: {district}"
SEC_WEALTH = "3. Wealth year by year"
SEC_HEATMAP = "4. Explore: mortgage rate x investment return"
SEC_PRICES = "5. Price check: the listings behind the price"
SEC_SOURCES = "6. Assumptions and sources"
SEC_DOWNLOAD = "7. Downloads"

VERDICT_INTRO = ("Each card compares two households with **the same money**: one buys a home with a mortgage, "
                 "the other rents a similar home and invests what the buyer would have put into the home. "
                 "**Buying wins** when, after that many years, the buyer's net wealth (home value after selling "
                 "costs minus what is still owed to the bank) is larger than the renter's investments. "
                 "The amount is the difference. Section 2 shows how it is calculated.")

HOW_INTRO = ("The same calculation in six steps, for this district after **{h} years**, with the controls in the "
             "sidebar. Move a control and every step updates.")
STEP1 = "Step 1 · Two comparable homes, priced from real listings"
STEP2 = "Step 2 · Both households spend exactly the same money"
STEP2_TEXT = ("On day 1 the buyer pays the down payment ({down}) plus buying costs ({costs}): **{upfront}**. "
              "The renter keeps that {upfront} and invests it. Every month the buyer pays the mortgage ({payment}), "
              "property tax, insurance and the building fee, **{total} in total**. The renter spends the same "
              "{total}: rent, the building fee, and **invests the remaining {invested}**.")
STEP2_CAPTION = ("Year-1 average per month. Colored parts build wealth (blue: the part of the mortgage that pays down "
                 "the loan; orange: the renter's investment). Gray parts are gone: interest, taxes and insurance, rent. "
                 "The building fee (light gray) is paid by both, so it cancels out. If the bar shows a negative "
                 "investment, rent is higher than the buyer's costs and the renter draws from savings.")
STEP3 = "Step 3 · What each one owns after {h} years"
STEP3_BUY = ("**Buying wins by {gap}.** The home, after paying selling costs and the rest of the loan, is worth more "
             "than the renter's investments. Over {h} years the buyer paid {interest} of interest; the renter paid "
             "{rent} of rent.")
STEP3_RENT = ("**Renting wins by {gap}.** The renter's investments are worth more than the buyer's home after selling "
              "costs and the rest of the loan. Over {h} years the buyer paid {interest} of interest; the renter paid "
              "{rent} of rent.")
STEP4 = "Step 4 · Why: the three comparisons that decide it"
STEP4_SUMMARY = "**{n} of {total} comparisons point to {side}.** They are rules of thumb; Step 3 is the full calculation."
STEP5 = "Step 5 · Is the answer robust? The scenario vote"
STEP5_TEXT = ("The market rate is uncertain and so is the investment return, so the verdict is not based on one "
              "scenario. It re-runs the calculation for **{rates} mortgage rates × {opts} investment options = {n} "
              "scenarios** (each cell above, after {h} years). Buying wins in **{wins} of {n} ({share:.0%})**. "
              "Rule: *buy* when buying wins in at least {buy:.0%} of them, *rent* when in {rent:.0%} or fewer, "
              "otherwise *it depends*. **Result: {label}.** The outlined column is today's market rate.")
STEP5_ORIGINAL = ("Original analysis (inputs of the run, before you moved any control): {label}, buying wins in "
                  "{share:.0%} of scenarios.")
STEP6 = "Step 6 · What would change the answer"
STEP6_CAPTION = ("Each row moves one input alone, keeping all others as they are now, and finds the value where "
                 "buyer and renter end up equal after {h} years. Use it to judge how close the decision is.")

METHOD_TITLE = "Method in detail"
METHOD_TEXT = """
- **Buyer:** pays the price (minus any negotiation discount) with the chosen down payment and a fixed-payment
  (French) mortgage at the annual effective rate (TEA). Each month also pays property tax, insurance (both a share
  of the price, rising with inflation) and the building fee. The home grows at the price-growth rate.
  **Buyer's wealth** = home value × (1 − selling costs) − remaining loan balance.
- **Renter:** starts with the down payment plus buying costs invested. Each month pays rent (rising once a year
  with rent growth) and the building fee, and invests the difference with the buyer's outflow (or withdraws it if
  rent is higher). The portfolio compounds monthly at the investment return. **Renter's wealth** = the portfolio.
- **Comparison:** buy minus rent, at 5, 10, 15, 20 and 30 years, month by month, in nominal soles (or deflated by
  inflation when "real terms" is on). After the loan is paid off, the buyer's outflow drops to taxes, insurance
  and fee, so the renter usually starts withdrawing.
- **Verdict:** the scenario vote of Step 5 (market rate −2 to +2 points × the three investment options at their
  base return).
"""

BUYER = "Buyer"
RENTER = "Renter"
BREAK_EVEN = "Break-even"
NO_BREAK_EVEN = "Buying does not beat renting within 30 years under these assumptions."
BREAK_EVEN_AT = "Buying beats renting from year {year} (dotted line)."
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
