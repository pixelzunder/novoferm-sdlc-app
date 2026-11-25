# Quantity discount

Status: implemented

## Goal

A customer who orders several identical doors gets a discount on the whole order. Sales asked
for it: today they calculate the discount by hand for every quote.

The request was one sentence: "Add a quantity discount." Everything below was decided in the
interview.

## Decisions

| # | Question | Decision | Reason |
|---|---|---|---|
| 1 | What is discounted? | Identical doors only: one configuration and a quantity | A basket of different doors is a different feature |
| 2 | From how many doors, and how much? | From 5 doors 5 %, from 10 doors 8 % | Named by sales; fictional like all prices here |
| 3 | On which doors? | On all doors of the order, not only on those above the threshold | Easier to explain to a customer |
| 4 | Do tiers add up? | No. The tier with the highest `min_quantity` that the quantity reaches applies | 10 doors get 8 %, not 13 % |
| 5 | Where do the tiers live? | In `data/rules.json` | Rule 1: rules are data |
| 6 | What is rounded? | The discount, once on the order, half up to whole cents | One rounding step; the total is then exact |
| 7 | Is there a limit? | 1 to 50 doors. Outside is a violation, not a silent correction | Larger orders are project business with their own prices |
| 8 | Does `net_price_cents` change? | No. It stays the price of one door without discount | Other systems read this key |
| 9 | How does the answer grow? | Four new keys, always present, also for one door | One shape for every answer |
| 10 | What about tests that compare the whole answer? | Two tests are extended by the new keys | The answer grows on purpose; no expectation is removed |
| 11 | What does the page show? | The order total as the large price; below it the price per door and the discount | The total is what the customer pays |
| 12 | Is the quantity required? | No. The default is 1 on the command line, in the API and on the page | Every request that works today keeps working |

## Behaviour

### Data

`data/rules.json` gets two entries:

```json
"quantity": { "min": 1, "max": 50 },
"quantity_discounts": [
  { "min_quantity": 5, "percent": 5 },
  { "min_quantity": 10, "percent": 8 }
]
```

`percent` is a whole number. An empty list means: no discount.

### Input

| Front end | Field | Default |
|---|---|---|
| command line | `--quantity` | 1 |
| JSON API and page | `quantity` | 1 |

The API and the page answer `400` when `quantity` is not a whole number, as they do for `width`.

### Violation

`QUANTITY_OUT_OF_RANGE` when the quantity is outside `quantity.min` to `quantity.max`. The
limits are inclusive. It is checked after all existing rules, so the order of the existing
violations does not change. An invalid order has no price and no discount.

### Calculation

```
discount percent = percent of the tier with the highest min_quantity <= quantity, else 0
discount         = net price of one door * quantity * discount percent / 100, rounded half up
order total      = net price of one door * quantity - discount
```

Integer cents only. The discount is rounded with `divide_half_up()`.

### Answer

```json
{
  "valid": true,
  "violations": [],
  "net_price_cents": 94400,
  "quantity": 5,
  "discount_percent": 5,
  "discount_cents": 23600,
  "total_net_price_cents": 448400
}
```

`net_price_cents` is the price of one door. For an invalid order, `net_price_cents`,
`discount_percent`, `discount_cents` and `total_net_price_cents` are `null`; `quantity` is the
quantity that was asked for.

### Page

A number field "Quantity" with the allowed range as a hint. For one door the result looks as
it does today. For several doors the large price is the order total, followed by the price per
door and, when there is a discount, the percentage and the amount. The new texts exist in every
language file.

## Examples

Base door: 2500 x 2125 mm, smooth, standard drive, 944.00 EUR.

| Door | Quantity | Doors without discount | Discount | Order total |
|---|---|---|---|---|
| base door | 1 | 94,400 | 0 % = 0 | 94,400 |
| base door | 4 | 377,600 | 0 % = 0 | 377,600 |
| base door | 5 | 472,000 | 5 % = 23,600 | 448,400 |
| base door | 9 | 849,600 | 5 % = 42,480 | 807,120 |
| base door | 10 | 944,000 | 8 % = 75,520 | 868,480 |
| base door | 50 | 4,720,000 | 8 % = 377,600 | 4,342,400 |
| base door with `double` insulation (103,963) | 5 | 519,815 | 5 % = 25,990.75 -> 25,991 | 493,824 |
| ribbed, manual drive (55,250) | 5 | 276,250 | 5 % = 13,812.5 -> 13,813 | 262,437 |
| base door | 0 or 51 | - | - | `QUANTITY_OUT_OF_RANGE` |

All amounts in cents.

## Acceptance criteria

1. The tiers and the allowed quantity are read from `data/rules.json`; no percentage and no
   threshold is written in Python.
2. One door costs what it costs today, with a discount of 0.
3. 4 doors get no discount, 5 and 9 doors get 5 %, 10 and 50 doors get 8 %, each on the whole
   order, with the totals of the examples.
4. The discount is rounded half up to whole cents (the two examples with a fraction).
5. A quantity of 0 or 51 gives exactly `QUANTITY_OUT_OF_RANGE`; 1 and 50 are allowed.
6. The answer has the keys `quantity`, `discount_percent`, `discount_cents` and
   `total_net_price_cents`; `net_price_cents` is still the price of one door.
7. An invalid order has `null` for every amount and for the percentage.
8. The command line accepts `--quantity`; without it the quantity is 1.
9. The API reads `quantity`, defaults to 1 and answers `400` for `quantity=many`.
10. The page has the field, keeps the entered quantity, and shows order total, price per door
    and discount for 5 doors. For one door it shows no discount line.
11. Every language file has the new texts with their placeholders and a text for the new
    violation.
12. `pricing.py` still uses no `float`, no `round()` and no `/` (existing fitness function).

## Out of scope

- Different doors in one order (a basket)
- Discounts per customer, per surface or for a period of time
- Gross prices: `vat_percent` is still unused
- Showing the next tier ("one more door and you get 8 %")

## Open questions

None.
