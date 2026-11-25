---
name: add-rule-entry
description: Add a new surface, insulation, drive or option to the configurator. Use when an existing kind of choice gets one more value or a price changes, not for a new kind of attribute.
---

# Add a rule entry

A new value of an existing kind is a change of data, not of code. The form, the command line
and the JSON API read `data/rules.json`, so no Python file changes.

A new *kind* of attribute (like insulation once was) is a feature, not an entry: write tests
across all modules first, see `tests/test_insulation.py`.

## Fields per kind

| Kind | Key in `rules.json` | Fields |
|---|---|---|
| surface | `surfaces` | `price_cents_per_m2` |
| insulation | `insulations` | `price_cents_per_m2` |
| drive | `drives` | `price_cents`, `max_width_mm` |
| option | `options` | `price_cents`, `requires_drive` |

Prices are integer cents: 98.00 EUR is `9800`. The drive name `manual` is special, the code
treats it as "no motor".

## Steps

1. **Confirm the numbers.** Prices and limits are business decisions. When the user did not
   name them, ask. Do not invent a price.
2. **Test first.** Add a test with the expected price of the base door (2500 x 2125 mm =
   5.3125 m2, fixture `base_config`) and write the calculation as a comment. Per-m2 prices are
   rounded half up to whole cents. Run it and see it fail.
3. **Add the entry** in `data/rules.json` with exactly the fields of its siblings. The order in
   the file is the order in the form for insulations and drives.
4. **Texts:** none. Names of entries are shown as they are and are not translated.
5. **README:** the value list in the argument table and the table under "Current values".
6. **Check:** all tests, then one quote on the command line with the new entry.

## Tests that list values exactly

`tests/test_insulation.py` expects exactly three insulations. A fourth one changes that
expectation on purpose: extend the list, and name this in your report. Do not touch any other
existing expectation.
