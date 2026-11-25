# AGENTS.md

doorcfg is a small, fictional garage door configurator: can a door be built, and what does it
cost. Same answer on the command line, as a web page and as a JSON API. `README.md` explains
every module - read the section you need, not the whole file.

## Commands

Use the Python of the virtual environment: `.venv/bin/python` (Windows:
`.\.venv\Scripts\python.exe`). Do not install anything globally.

- Tests: `python -m pytest`, one file: `python -m pytest tests/test_pricing.py`
- Lint: `python -m ruff check .`
- Page: `python -m doorcfg serve --port 8080` - blocks the terminal, start it in the background

## Architecture

```
cli.py ─┐
        ├─> evaluate.py ─┬─> rules.py    validate(): list of violations
web.py ─┘                └─> pricing.py  net_price_cents(): integer cents
models.py    dataclasses without logic        messages.py   texts per language
```

Front ends only parse input, call `evaluate()` and format the answer. The core never imports a
front end. `tests/test_architecture.py` enforces this - do not relax it without asking.

## Rules for every change

1. Rules are data: limits, allowed values and prices live in `data/rules.json`, not in Python.
2. Money is integer cents: no `float`, no `round()`. Round with `divide_half_up()`.
3. Standard library only. Ask before adding a dependency.
4. Texts for people live in `data/messages/<language>.json`. English is the reference.
5. Violation codes are stable: add new ones, never rename one.
6. Escape user input on the page with `html.escape()`.
7. Test first. Never delete or weaken a test to get to green; if a test looks wrong, ask.
8. Keep the README true in the same change.

## Read only when the task needs it

- Skill `spec`: before every feature - interview the user, write `docs/specs/<feature>.md`
- Skill `add-rule-entry`: a new surface, insulation, drive or option
- Skill `check-page`: look at the page in a real browser after a change of `web.py`
- Skill `commit`: every commit (message format, ticket number)
- Subagent `translator`: new language or new texts, one call per language
- MCP server `context7`: current documentation instead of guessing an API

## Before you say "done"

- ruff and pytest are green, and you say how many tests ran.
- You list what you changed and what you did not check.

## Git

Never commit to `main`: work on `feature/<name>` or `fix/<name>`. Do not commit or push unless
you are asked to. Never use `--no-verify` and never edit `.githooks/` to get through.
