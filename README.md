# doorcfg - a (fictional) garage door configurator

A small Python application that answers two questions about a garage door: **can it be built**
and **what does it cost**. It offers the same answer three ways: on the command line, as a local
web page and as a JSON API.

> **Everything here is invented.** Rules, limits and prices have nothing to do with real Novoferm
> products.

The application uses the Python standard library only. It has no runtime dependencies, no
database and no build step.

## Setup

You need Python 3.10 or newer.

### Windows: install Python and start the app without admin rights

The following steps use **Python 3.14** on Windows 10/11 and a normal PowerShell window.
**Install Python for the current Windows user only, never for all users.** The app gets its
own environment in the repo. Download and installer options checked on 2026-11-24.

#### 1. Install Python once

If Python 3.14 is already installed, use that installation's `python.exe` in step 2.
For a new installation:

1. Download the official [Python 3.14.10 installer for Windows 64-bit (EXE)](https://www.python.org/ftp/python/3.14.10/python-3.14.10-amd64.exe).
   This is for Intel/AMD PCs. For ARM devices, use the ARM64 installer on the
   [Python 3.14.10 release page](https://www.python.org/downloads/release/python-31410/).
2. Open the downloaded file normally, without **Run as administrator**.
3. Check **Add python.exe to PATH**. Uncheck **Use admin privileges when installing py.exe**
   (or **Install launcher for all users**, depending on the installer wording).
4. Choose **Install Now** to install **only for your user**. Keep the installation in
   `%LocalAppData%\Programs\Python\Python314`; leave **Install for all users** unchecked
   if you use the custom installation screen.
5. If offered **Disable path length limit** at the end, skip it: that system setting needs
   admin rights and is not required for this app in a short project path.
6. Close and reopen PowerShell, then check:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe" --version
```

Expected output for this download: `Python 3.14.10`. If you chose a different installation
folder, adjust the executable path here and in step 2. Using the full path also avoids
conflicts with other Python versions or the Microsoft Store alias.

The [official installer documentation](https://docs.python.org/3.14/using/windows.html#installation-steps)
describes installation for the current user. Company policies can still block software
installation or require an IT-installed system prerequisite; in that case, ask IT to provide
Python rather than an administrator account.

#### 2. Set up the app once

Clone or extract the complete repository into a folder you can write to, for example
`C:\Users\YOUR_NAME\Projects\novoferm-sdlc-app`. Open a normal PowerShell window and change
to that folder (replace the example path with your actual path). It must contain
`pyproject.toml`, `src` and `data`.

```powershell
cd "$env:USERPROFILE\Projects\novoferm-sdlc-app"
& "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

The `pip` step needs internet access to download the packaging tool `setuptools`.
The app itself has no runtime dependencies. Everything is installed inside `.venv`.

#### 3. Start the app

From the same repo folder, run:

```powershell
.\.venv\Scripts\python.exe -m doorcfg serve
```

Open **<http://127.0.0.1:8080/?lang=de>** in your browser. Leave PowerShell open while using
the app; **Ctrl+C** stops it. On later starts, only change to the repo folder and run this
command again. If port 8080 is already in use, append `--port 8081` and open port 8081 instead.

These commands call the environment's Python directly. No `Activate.ps1` or PowerShell
execution-policy change is needed. For the CLI examples below, use
`.\.venv\Scripts\python.exe` wherever they say `python`.

#### Optional: run the tests on Windows

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
```

### macOS / Linux

From the repo folder, with Python 3.10 or newer installed:

```sh
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
source .venv/bin/activate
```

`[dev]` installs `pytest`, the only development dependency.

## Usage

### Command line

```
python -m doorcfg --width 2500 --height 2125 --surface smooth --drive standard
```

```json
{
  "valid": true,
  "violations": [],
  "net_price_cents": 94400
}
```

| Argument | Required | Meaning |
|---|---|---|
| `--width` | yes | width in mm |
| `--height` | yes | height in mm |
| `--surface` | yes | `woodgrain`, `smooth` or `ribbed` |
| `--drive` | no | `manual` (default), `standard` or `power` |
| `--option` | no | `windows` or `smart_control`; repeat the argument for several options |

The exit code is `0` when the door can be built and `1` when it breaks a rule. A door that
breaks a rule has no price:

```
python -m doorcfg --width 2500 --height 2125 --surface smooth --option smart_control
```

```json
{
  "valid": false,
  "violations": [
    {
      "code": "OPTION_REQUIRES_DRIVE",
      "message": "Option 'smart_control' needs a motor drive."
    }
  ],
  "net_price_cents": null
}
```

### Web page

```
python -m doorcfg serve                 # http://127.0.0.1:8080/
python -m doorcfg serve --port 8081     # another port
python -m doorcfg serve --host 0.0.0.0  # reachable from other machines
```

The page shows a form with width, height, surface, drive and options. After submitting it shows
the net price or the list of broken rules. `Ctrl+C` stops the server.

The page is available in English and German: `/?lang=de`. An unknown language code gives English.

### JSON API

The running server also answers at `/api/quote` with the same JSON as the command line:

```
curl "http://127.0.0.1:8080/api/quote?width=2500&height=2125&surface=smooth&drive=standard&option=windows"
```

| Path | Answer |
|---|---|
| `/` | the HTML page; with form parameters also the result |
| `/api/quote` | `200` with the evaluation as JSON; `400` with `{"error": ...}` when a parameter is missing or not a number |
| anything else | `404` |

Query parameters are `width`, `height`, `surface`, `drive` and `option` (repeatable). The page
additionally reads `lang`. Only `GET` is supported.

## Project layout

```
pyproject.toml           package metadata and pytest settings
data/
  rules.json             limits, allowed values and prices
  messages/en.json       texts of the web page, English (the reference)
  messages/de.json       texts of the web page, German
src/doorcfg/
  __main__.py            makes "python -m doorcfg" work
  cli.py                 command line front end
  web.py                 web page and JSON API
  evaluate.py            one function that validates and prices
  rules.py               loads rules.json, validates a configuration
  pricing.py             net price calculation
  models.py              DoorConfiguration and Violation
  messages.py            loads the texts for one language
tests/                   pytest tests, one file per module
```

## How the code works

Every front end does the same three things: it turns its input into a `DoorConfiguration`, calls
`evaluate()` and formats the answer. The decision itself lives in `rules.py` and `pricing.py`.

```
cli.py ─┐
        ├─> evaluate.evaluate(config, rules) ─┬─> rules.validate()         -> list of violations
web.py ─┘                                     └─> pricing.net_price_cents() -> price in cents
```

### `models.py`

Two frozen dataclasses without logic.

- `DoorConfiguration`: `width_mm`, `height_mm`, `surface`, `drive` and `options` (a `frozenset`
  of option names). This is what a customer asks for. It is not checked on creation.
- `Violation`: one broken rule with a stable `code` and a human-readable English `message`.

### `rules.py`

`load_rules()` reads `data/rules.json` and `parse_rules()` turns it into a typed `RuleSet`
(`Range`, `DriveRule`, `OptionRule`). A missing field raises `KeyError`.

`validate(config, rules)` returns **every** broken rule, not only the first one. An empty list
means the door can be built. The checks, in this order:

| Code | Broken when |
|---|---|
| `WIDTH_OUT_OF_RANGE` | the width is outside the allowed range (limits are inclusive) |
| `HEIGHT_OUT_OF_RANGE` | the height is outside the allowed range (limits are inclusive) |
| `UNKNOWN_SURFACE` | the surface is not in the rule set |
| `UNKNOWN_DRIVE` | the drive is not in the rule set |
| `DRIVE_TOO_WEAK` | the door is wider than the drive's `max_width_mm` |
| `UNKNOWN_OPTION` | an option is not in the rule set |
| `OPTION_REQUIRES_DRIVE` | an option with `requires_drive` is combined with the `manual` drive |

Options are checked in alphabetical order, so the result is the same on every run.

### `pricing.py`

All amounts are **integer cents**. The code uses no `float` and no `round()`.

```
net price = panel price + drive price + sum of option prices
panel price = width_mm * height_mm * price_cents_per_m2 / 1,000,000, rounded half up
```

`divide_half_up()` does the rounding with integer arithmetic. `net_price_cents()` validates
first and raises `InvalidConfigurationError` (which carries the violations) when a rule is
broken.

Example: 2500 mm x 2125 mm = 5.3125 m², smooth at 112.00 EUR per m² = 595.00 EUR, plus the
standard drive at 349.00 EUR = 944.00 EUR, which is `94400` cents.

The rule set contains `vat_percent`, but no code uses it yet. All prices are net prices.

### `evaluate.py`

`evaluate(config, rules)` combines both steps and returns a dictionary with `valid`,
`violations` and `net_price_cents`. The price is `None` when there are violations. This
dictionary is exactly what the command line and the JSON API print.

### `cli.py`

`main()` builds the configuration from the arguments, prints the evaluation as JSON and returns
the exit code. If the first argument is `serve`, it hands the remaining arguments to
`web.serve()` instead.

### `web.py`

Built on `http.server` from the standard library.

- `handle(target, rules)` answers one request and returns a `Response` (status, content type,
  body). It opens no socket, so the tests call it directly.
- `parse_config()` turns query parameters into a `DoorConfiguration`. It raises `FormError` when
  `surface` is missing or `width` or `height` is not a whole number. Whether the values are
  *allowed* is decided later by `validate()`.
- `render_page()` builds the HTML. The form is generated from the rule set: a new surface, drive
  or option in `rules.json` appears in the form without a code change. All user input is escaped
  with `html.escape()`.
- `format_eur()` formats cents for display, for example `94400` as `944.00 EUR`.
- `DoorServer` and `Handler` connect `handle()` to a real socket. `serve()` parses `--host` and
  `--port`, starts the server and reports a port that is already taken.

By default the server listens on `127.0.0.1` only.

### `messages.py`

The texts of the web page are not in Python code. `load_messages(language)` reads
`data/messages/<language>.json` on top of the English file, so a text that is missing in another
language falls back to English. `available_languages()` lists the language files, English first.

The JSON API and the command line always answer with the English `message` from `rules.py`. Only
the web page translates violations, by their `code`.

## Data files

### `data/rules.json`

```json
{
  "dimensions": {
    "width_mm":  { "min": 2000, "max": 5500 },
    "height_mm": { "min": 1875, "max": 3000 }
  },
  "surfaces": { "smooth": { "price_cents_per_m2": 11200 } },
  "drives":   { "standard": { "price_cents": 34900, "max_width_mm": 5000 } },
  "options":  { "smart_control": { "price_cents": 12900, "requires_drive": true } },
  "vat_percent": 19
}
```

Current values:

| Surface | Price per m² |
|---|---|
| `woodgrain` | 98.00 EUR |
| `ribbed` | 104.00 EUR |
| `smooth` | 112.00 EUR |

| Drive | Price | Maximum door width |
|---|---|---|
| `manual` | 0.00 EUR | 3500 mm |
| `standard` | 349.00 EUR | 5000 mm |
| `power` | 529.00 EUR | 5500 mm |

| Option | Price | Needs a motor drive |
|---|---|---|
| `windows` | 219.00 EUR | no |
| `smart_control` | 129.00 EUR | yes |

To add a surface, drive or option, add an entry here. The name `manual` is special: the code
treats it as "no motor".

### `data/messages/<language>.json`

Each file has a `language_name`, a `text` object (labels and headings of the page, with
placeholders such as `{min}`) and a `violations` object (one text per violation code). To add a
language, copy `en.json` to a new file named after the language code and translate the values.

## Tests

```
python -m pytest
```

| File | Covers |
|---|---|
| `tests/test_rules.py` | every validation rule, including the inclusive limits |
| `tests/test_pricing.py` | rounding, the price of the base door, options, invalid doors |
| `tests/test_cli.py` | output, exit codes and the `serve` command |
| `tests/test_web.py` | page, JSON API, escaping, languages and a real HTTP request |
| `tests/test_messages.py` | completeness of every language file and the fallback to English |

`tests/conftest.py` provides two fixtures: `rules` (the rule set from `data/rules.json`) and
`base_config` (a valid door: 2500 x 2125 mm, smooth, standard drive).
