import json

import pytest

from doorcfg import cli
from doorcfg.cli import main


def test_cli_prints_price_for_valid_door(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        ["--width", "2500", "--height", "2125", "--surface", "smooth", "--drive", "standard"]
    )
    result = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert result == {"valid": True, "violations": [], "net_price_cents": 94_400}


def test_cli_reports_violations(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        ["--width", "2500", "--height", "2125", "--surface", "smooth", "--option", "smart_control"]
    )
    result = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert result["valid"] is False
    assert result["net_price_cents"] is None
    assert [violation["code"] for violation in result["violations"]] == ["OPTION_REQUIRES_DRIVE"]


def test_cli_reads_arguments_from_the_command_line(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "sys.argv", ["doorcfg", "--width", "2500", "--height", "2125", "--surface", "smooth"]
    )
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True


def test_cli_hands_the_serve_command_to_the_web_front_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: list[list[str]] = []

    def fake_serve(argv: list[str]) -> int:
        received.append(argv)
        return 0

    monkeypatch.setattr(cli, "serve", fake_serve)
    assert main(["serve", "--port", "9000"]) == 0
    assert received == [["--port", "9000"]]
