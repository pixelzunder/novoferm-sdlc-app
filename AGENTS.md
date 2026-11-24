# AGENTS.md

doorcfg is a small, fictional garage door configurator: it decides whether a door can be built
and what it costs. Same answer on the command line, as a local web page and as a JSON API.
All rules and prices are invented. `README.md` explains every module in detail - read it before
larger changes.

## Commands

Use the Python of the virtual environment. Do not install anything globally.

| Task | macOS / Linux | Windows (PowerShell) |
|---|---|---|
| Install | `.venv/bin/python -m pip install -e ".[dev]"` | `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"` |
| All tests | `.venv/bin/python -m pytest` | `.\.venv\Scripts\python.exe -m pytest` |
| Lint | `.venv/bin/python -m ruff check .` | `.\.venv\Scripts\python.exe -m ruff check .` |
| One test file | `.venv/bin/python -m pytest tests/test_pricing.py` | same with the Windows path |
| Start the page | `.venv/bin/python -m doorcfg serve --port 8080` | same with the Windows path |
| One quote | `.venv/bin/python -m doorcfg --width 2500 --height 2125 --surface smooth` | same with the Windows path |

The server blocks the terminal. Start it in the background and stop it when you are done.

## Architecture

```
cli.py ─┐
        ├─> evaluate.py ─┬─> rules.py    validate(): list of violations
web.py ─┘                └─> pricing.py  net_price_cents(): integer cents
models.py    dataclasses without logic        messages.py   texts per language
```

- Front ends (`cli.py`, `web.py`) only parse input, call `evaluate()` and format the answer.
  No business rule and no price calculation lives there.
- `models.py`, `rules.py` and `pricing.py` never import `cli`, `web` or `messages`.

## Rules for every change

1. **Rules are data.** Limits, allowed values and prices live in `data/rules.json`, not in
   Python. A new surface, insulation, drive or option is a new entry there.
2. **Money is integer cents.** No `float`, no `round()`. Round with `divide_half_up()`.
3. **Standard library only.** The application has no runtime dependencies. Do not add one
   without asking. Development tools go into `[project.optional-dependencies] dev`.
4. **Texts for people live in `data/messages/<language>.json`**, not in Python. English is the
   reference. A new text needs an entry in every language file.
5. **Violation codes are stable.** Tests and other systems rely on them. Add new codes, never
   rename existing ones.
6. **Escape user input** on the web page with `html.escape()`.
7. **Test first.** Write or extend the test, see it fail, then implement. Never delete or weaken
   a test to get to green; if a test looks wrong, stop and ask.
8. **Keep the README true.** Arguments, parameters, violation codes, prices and the test table
   are documented there. Update them in the same change.

## Tools (MCP)

`.mcp.json` connects two servers. Both run with the rights of the developer.

- **context7**: current documentation of libraries and of Python itself. Use it instead of
  guessing an API, for example when a question is about a new Python version.
- **chrome-devtools**: a real browser. Use it to look at the page after a change of `web.py`:
  open `http://127.0.0.1:8080/`, submit the form, check the console for errors.

## Before you say "done"

- `python -m ruff check .` and `python -m pytest` are green, and you say how many tests ran.
- For a change of the page: you started the server and looked at the result (chrome-devtools).
- You list what you changed and what you did not check.

## Git

- Never commit to `main`. Work on a branch: `feature/<short-name>` or `fix/<short-name>`.
- The pre-commit hook runs `ruff check` and the tests. When it rejects a commit, read its
  output and fix the cause. Never use `--no-verify` and never edit `.githooks/` to get through.
- Small commits, one topic each. Do not commit or push unless you are asked to.
- Commit messages: Conventional Commits with an emoji and a ticket number. The details are in
  the skill `.claude/skills/commit/SKILL.md` - follow it for every commit.
