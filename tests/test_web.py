import json
import socket
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator

import pytest

from doorcfg.rules import RuleSet
from doorcfg.web import DoorServer, FormError, format_eur, handle, parse_config, serve

VALID = "width=2500&height=2125&surface=smooth&drive=standard"


def test_format_eur_uses_two_decimals_and_thousands_separator() -> None:
    assert format_eur(94_400) == "944.00 EUR"
    assert format_eur(112_336) == "1,123.36 EUR"
    assert format_eur(5) == "0.05 EUR"


def test_parse_config_defaults_to_manual_drive_and_collects_options() -> None:
    config = parse_config(
        {"width": ["2500"], "height": ["2125"], "surface": ["smooth"], "option": ["windows", ""]}
    )
    assert config.drive == "manual"
    assert config.options == frozenset({"windows"})


@pytest.mark.parametrize(
    "query",
    [
        {"height": ["2125"], "surface": ["smooth"]},
        {"width": ["wide"], "height": ["2125"], "surface": ["smooth"]},
        {"width": ["2500"], "height": ["2125"]},
    ],
)
def test_parse_config_rejects_missing_or_non_numeric_fields(query: dict[str, list[str]]) -> None:
    with pytest.raises(FormError):
        parse_config(query)


def test_empty_form_is_built_from_the_rule_set(rules: RuleSet) -> None:
    response = handle("/", rules)
    assert response.status == 200
    assert response.content_type.startswith("text/html")
    for name in [*rules.surfaces, *rules.drives, *rules.options]:
        assert f'value="{name}"' in response.body
    assert f'value="{rules.width_mm.min}"' in response.body
    assert "can be built" not in response.body


def test_page_shows_the_price_for_a_valid_door(rules: RuleSet) -> None:
    response = handle(f"/?{VALID}&option=windows", rules)
    assert response.status == 200
    assert "This door can be built" in response.body
    assert "1,163.00 EUR" in response.body
    assert 'value="windows" checked' in response.body
    assert '<option value="standard" selected>' in response.body


def test_page_lists_violations_for_an_invalid_door(rules: RuleSet) -> None:
    response = handle("/?width=2500&height=2125&surface=smooth&option=smart_control", rules)
    assert response.status == 200
    assert "This door cannot be built" in response.body
    assert "OPTION_REQUIRES_DRIVE" in response.body


def test_page_escapes_user_input(rules: RuleSet) -> None:
    response = handle("/?width=%22%3E%3Cscript%3E&height=2125&surface=%3Cscript%3E", rules)
    assert "<script>" not in response.body
    assert "&quot;&gt;&lt;script&gt;" in response.body


def test_page_reports_input_it_cannot_read(rules: RuleSet) -> None:
    response = handle("/?width=abc&height=2125&surface=smooth", rules)
    assert response.status == 400
    assert "Input not understood" in response.body


def test_api_returns_the_same_answer_as_the_cli(rules: RuleSet) -> None:
    response = handle(f"/api/quote?{VALID}", rules)
    assert response.status == 200
    assert json.loads(response.body) == {
        "valid": True,
        "violations": [],
        "net_price_cents": 94_400,
        "quantity": 1,
        "discount_percent": 0,
        "discount_cents": 0,
        "total_net_price_cents": 94_400,
    }


def test_api_reports_bad_requests(rules: RuleSet) -> None:
    response = handle("/api/quote?width=2500", rules)
    assert response.status == 400
    assert "error" in json.loads(response.body)


def test_unknown_path_is_not_found(rules: RuleSet) -> None:
    assert handle("/admin", rules).status == 404


@pytest.fixture
def running_server(rules: RuleSet) -> Iterator[str]:
    server = DoorServer(("127.0.0.1", 0), rules)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def test_server_answers_over_http(running_server: str) -> None:
    # No proxy: corporate proxy settings must not catch requests to this machine.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(f"{running_server}/api/quote?{VALID}", timeout=5) as reply:
        assert reply.status == 200
        assert json.loads(reply.read())["net_price_cents"] == 94_400
    with pytest.raises(urllib.error.HTTPError) as not_found:
        opener.open(f"{running_server}/nope", timeout=5)
    assert not_found.value.code == 404


def test_serve_prints_the_address_and_stops_on_ctrl_c(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def interrupted(self: DoorServer, poll_interval: float = 0.5) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(DoorServer, "serve_forever", interrupted)
    assert serve(["--port", "0"]) == 0
    output = capsys.readouterr().out
    assert "http://127.0.0.1:" in output
    assert "Stopped." in output


def test_serve_explains_a_port_that_is_taken(capsys: pytest.CaptureFixture[str]) -> None:
    with socket.socket() as blocker:
        blocker.bind(("127.0.0.1", 0))
        blocker.listen()
        port = blocker.getsockname()[1]
        assert serve(["--port", str(port)]) == 1
    assert "--port 8081" in capsys.readouterr().out


def test_page_speaks_the_requested_language_and_keeps_it_in_the_form(rules: RuleSet) -> None:
    response = handle(f"/?lang=de&{VALID}", rules)
    assert '<html lang="de">' in response.body
    assert "Dieses Tor kann gebaut werden" in response.body
    assert '<input type="hidden" name="lang" value="de">' in response.body
    assert '<a href="/?lang=en">en</a>' in response.body


def test_violations_are_shown_in_the_requested_language(rules: RuleSet) -> None:
    response = handle("/?lang=de&width=2500&height=2125&surface=smooth&option=smart_control", rules)
    assert "OPTION_REQUIRES_DRIVE" in response.body
    assert "Motorantrieb" in response.body


def test_only_a_language_parameter_shows_the_empty_form(rules: RuleSet) -> None:
    response = handle("/?lang=de", rules)
    assert response.status == 200
    assert "Torkonfigurator" in response.body
    assert "kann gebaut werden" not in response.body


def test_unknown_language_falls_back_to_english(rules: RuleSet) -> None:
    response = handle("/?lang=../../etc/passwd", rules)
    assert response.status == 200
    assert '<html lang="en">' in response.body
