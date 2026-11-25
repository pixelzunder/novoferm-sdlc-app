"""Local web front end: python -m doorcfg serve  ->  http://127.0.0.1:8080

Standard library only, bound to this machine, no container and no admin rights.
The page is built from the rule set, so a new surface, drive or option in data/rules.json
shows up in the form without a change here. Its texts come from data/messages/,
one file per language: /?lang=de
"""

from __future__ import annotations

import argparse
import html
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from doorcfg.evaluate import Evaluation, evaluate
from doorcfg.messages import Messages, available_languages, load_messages
from doorcfg.models import DoorConfiguration
from doorcfg.rules import MANUAL_DRIVE, RuleSet, load_rules

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
CENTS_PER_EURO = 100
DEFAULT_INSULATION = "single"
DEFAULT_QUANTITY = 1
FORM_LABELS = (
    "width",
    "height",
    "surface",
    "insulation",
    "drive",
    "quantity",
    "options",
    "submit",
)

Query = Mapping[str, Sequence[str]]


@dataclass(frozen=True)
class Response:
    status: int
    content_type: str
    body: str


class FormError(ValueError):
    """The request cannot be turned into a DoorConfiguration (missing or non-numeric field)."""


def format_eur(cents: int) -> str:
    """Formats integer cents for people. Integer arithmetic only."""
    return f"{cents // CENTS_PER_EURO:,}.{cents % CENTS_PER_EURO:02d} EUR"


def _first(query: Query, name: str) -> str | None:
    values = query.get(name)
    return values[0].strip() if values else None


def _millimetres(query: Query, name: str) -> int:
    raw = _first(query, name)
    if raw is None or not raw.lstrip("-").isdigit():
        raise FormError(f"'{name}' must be a whole number of millimetres.")
    return int(raw)


def _quantity(query: Query) -> int:
    raw = _first(query, "quantity")
    if not raw:
        return DEFAULT_QUANTITY
    if not raw.lstrip("-").isdigit():
        raise FormError("'quantity' must be a whole number of doors.")
    return int(raw)


def parse_config(query: Query) -> DoorConfiguration:
    """Turns query parameters into a configuration. Business rules are checked later."""
    surface = _first(query, "surface")
    if not surface:
        raise FormError("'surface' is required.")
    return DoorConfiguration(
        width_mm=_millimetres(query, "width"),
        height_mm=_millimetres(query, "height"),
        surface=surface,
        drive=_first(query, "drive") or MANUAL_DRIVE,
        options=frozenset(value for value in query.get("option", []) if value),
        insulation=_first(query, "insulation") or DEFAULT_INSULATION,
        quantity=_quantity(query),
    )


STYLE = """
:root { color-scheme: light; --ink:#141414; --muted:#5b554f; --line:#e4dacb; --bg:#faf4ec;
        --accent:#b82421; --ok:#1c6b3a; }
* { box-sizing: border-box; }
body { margin:0; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; color:var(--ink);
       background:var(--bg); line-height:1.5; }
main { max-width: 760px; margin: 0 auto; padding: 32px 20px 64px; }
h1 { font-size: 1.9rem; margin: 0 0 4px; }
.note { color: var(--muted); margin: 0 0 24px; }
form, .result { background:#fff; border:1px solid var(--line); border-radius:14px; padding:24px; }
.grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:16px; }
label, legend { font-weight:600; display:block; margin-bottom:6px; }
input[type=number], select { width:100%; padding:10px 12px; font:inherit; border-radius:8px;
       border:1px solid #9a9087; background:#fff; }
.hint { color:var(--muted); font-size:.9rem; margin-top:4px; }
fieldset { border:0; padding:0; margin:20px 0 0; }
.check { display:flex; gap:8px; align-items:center; font-weight:400; }
button { margin-top:24px; padding:12px 22px; font:inherit; font-weight:700; color:#fff;
       background:var(--accent); border:0; border-radius:10px; cursor:pointer; }
button:focus-visible, input:focus-visible, select:focus-visible { outline:3px solid #1f6feb;
       outline-offset:2px; }
.result { margin-top:24px; }
.result h2 { margin:0 0 8px; font-size:1.3rem; }
.result--ok h2 { color:var(--ok); }
.result--bad h2 { color:var(--accent); }
.price { font-size:2rem; font-weight:800; margin:0; }
code { background:#f1e9dc; padding:1px 6px; border-radius:6px; }
footer { color:var(--muted); font-size:.9rem; margin-top:28px; }
.lang { text-align:right; margin:0 0 8px; color:var(--muted); }
.lang a { color:var(--accent); }
"""


def _options_html(names: Sequence[str], selected: str | None) -> str:
    return "".join(
        f'<option value="{html.escape(name)}"{" selected" if name == selected else ""}>'
        f"{html.escape(name)}</option>"
        for name in names
    )


def _language_html(messages: Messages) -> str:
    links = " ".join(
        f"<strong>{html.escape(code)}</strong>"
        if code == messages.language
        else f'<a href="/?lang={html.escape(code)}">{html.escape(code)}</a>'
        for code in available_languages()
    )
    return f'<p class="lang">{html.escape(messages.t("language"))}: {links}</p>'


def _form_html(rules: RuleSet, query: Query, messages: Messages) -> str:
    width, height = rules.width_mm, rules.height_mm
    quantity_hint = messages.t("range", min=rules.quantity.min, max=rules.quantity.max)
    label = {key: html.escape(messages.t(key)) for key in FORM_LABELS}
    chosen = set(query.get("option", []))
    checks = "".join(
        f'<label class="check"><input type="checkbox" name="option" value="{html.escape(name)}"'
        f'{" checked" if name in chosen else ""}> {html.escape(name)} '
        f"(+{format_eur(rule.price_cents)})</label>"
        for name, rule in sorted(rules.options.items())
    )
    return f"""
<form method="get" action="/">
  <input type="hidden" name="lang" value="{html.escape(messages.language)}">
  <div class="grid">
    <div><label for="width">{label["width"]}</label>
      <input id="width" name="width" type="number" required
             value="{html.escape(_first(query, "width") or str(width.min))}">
      <p class="hint">{html.escape(messages.t("range", min=width.min, max=width.max))}</p></div>
    <div><label for="height">{label["height"]}</label>
      <input id="height" name="height" type="number" required
             value="{html.escape(_first(query, "height") or str(height.min))}">
      <p class="hint">{html.escape(messages.t("range", min=height.min, max=height.max))}</p></div>
    <div><label for="surface">{label["surface"]}</label>
      <select id="surface" name="surface">
        {_options_html(sorted(rules.surfaces), _first(query, "surface"))}</select></div>
    <div><label for="insulation">{label["insulation"]}</label>
      <select id="insulation" name="insulation">
        {_options_html(list(rules.insulations), _first(query, "insulation"))}</select></div>
    <div><label for="drive">{label["drive"]}</label>
      <select id="drive" name="drive">
        {_options_html(list(rules.drives), _first(query, "drive"))}</select></div>
    <div><label for="quantity">{label["quantity"]}</label>
      <input id="quantity" name="quantity" type="number" required
             value="{html.escape(_first(query, "quantity") or str(DEFAULT_QUANTITY))}">
      <p class="hint">{html.escape(quantity_hint)}</p></div>
  </div>
  <fieldset><legend>{label["options"]}</legend>{checks}</fieldset>
  <button type="submit">{label["submit"]}</button>
</form>"""


def _price_details_html(evaluation: Evaluation, price: int, messages: Messages) -> str:
    """What the large price means: one door, or an order with price per door and discount."""
    quantity = evaluation["quantity"]
    if quantity == DEFAULT_QUANTITY:
        return f'<p class="hint">{html.escape(messages.t("net_price"))}</p>'
    lines = [
        messages.t("net_total", quantity=quantity),
        messages.t("per_door", price=format_eur(price)),
    ]
    discount = evaluation["discount_cents"]
    if discount:
        percent = evaluation["discount_percent"]
        lines.append(messages.t("discount", percent=percent, amount=format_eur(discount)))
    return "".join(f'<p class="hint">{html.escape(line)}</p>' for line in lines)


def _result_html(evaluation: Evaluation | None, error: str | None, messages: Messages) -> str:
    if error is not None:
        return (
            '<section class="result result--bad" role="alert">'
            f"<h2>{html.escape(messages.t('input_title'))}</h2>"
            f"<p>{html.escape(error)}</p></section>"
        )
    if evaluation is None:
        return ""
    price, total = evaluation["net_price_cents"], evaluation["total_net_price_cents"]
    if price is not None and total is not None:
        return (
            '<section class="result result--ok" role="status">'
            f"<h2>{html.escape(messages.t('ok_title'))}</h2>"
            f'<p class="price">{format_eur(total)}</p>'
            f"{_price_details_html(evaluation, price, messages)}</section>"
        )
    items = "".join(
        f"<li><code>{html.escape(v['code'])}</code> "
        f"{html.escape(messages.violation(v['code'], v['message']))}</li>"
        for v in evaluation["violations"]
    )
    return (
        '<section class="result result--bad" role="alert">'
        f"<h2>{html.escape(messages.t('bad_title'))}</h2><ul>{items}</ul></section>"
    )


def render_page(
    rules: RuleSet,
    query: Query,
    messages: Messages,
    evaluation: Evaluation | None = None,
    error: str | None = None,
) -> str:
    width, height, surface = rules.width_mm.min, rules.height_mm.min, min(rules.surfaces)
    api_example = f"/api/quote?width={width}&height={height}&surface={surface}"
    cli_example = f"python -m doorcfg --width {width} --height {height} --surface {surface}"
    title = html.escape(messages.t("title"))
    return f"""<!doctype html>
<html lang="{html.escape(messages.language)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{STYLE}</style>
</head>
<body>
<main>
  {_language_html(messages)}
  <h1>{title}</h1>
  <p class="note">{html.escape(messages.t("note"))}</p>
  {_form_html(rules, query, messages)}
  {_result_html(evaluation, error, messages)}
  <footer>{html.escape(messages.t("same_as_json"))} <code>{html.escape(api_example)}</code><br>
  {html.escape(messages.t("same_on_cli"))} <code>{html.escape(cli_example)}</code></footer>
</main>
</body>
</html>
"""


def _json(status: int, payload: object) -> Response:
    return Response(status, "application/json; charset=utf-8", json.dumps(payload, indent=2))


def handle(target: str, rules: RuleSet) -> Response:
    """Answers one GET request. Pure function: no sockets, easy to test."""
    parts = urlsplit(target)
    query = parse_qs(parts.query)
    html_type = "text/html; charset=utf-8"

    if parts.path == "/api/quote":
        try:
            return _json(200, evaluate(parse_config(query), rules))
        except FormError as error:
            return _json(400, {"error": str(error)})

    if parts.path == "/":
        messages = load_messages(_first(query, "lang"))
        if not set(query) - {"lang"}:
            return Response(200, html_type, render_page(rules, query, messages))
        try:
            evaluation = evaluate(parse_config(query), rules)
        except FormError as error:
            return Response(400, html_type, render_page(rules, query, messages, error=str(error)))
        return Response(200, html_type, render_page(rules, query, messages, evaluation))

    return Response(404, "text/plain; charset=utf-8", "Not found. The page lives at /")


class Handler(BaseHTTPRequestHandler):
    server: DoorServer

    def do_GET(self) -> None:
        response = handle(self.path, self.server.rules)
        body = response.body.encode("utf-8")
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class DoorServer(ThreadingHTTPServer):
    """HTTP server that carries the loaded rule set for its handlers."""

    daemon_threads = True

    def __init__(self, address: tuple[str, int], rules: RuleSet) -> None:
        super().__init__(address, Handler)
        self.rules = rules


def serve(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="doorcfg serve", description="Local web page for the fictional door configurator"
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="default: this machine only")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="default: 8080")
    args = parser.parse_args(argv)

    try:
        server = DoorServer((args.host, args.port), load_rules())
    except OSError as error:
        print(f"Cannot start on port {args.port}: {error}. Try another one: --port 8081")
        return 1

    with server:
        print(f"Door configurator: http://{args.host}:{server.server_port}/   (Ctrl+C stops it)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
    return 0
