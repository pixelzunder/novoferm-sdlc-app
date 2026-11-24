"""Command line entry point.

python -m doorcfg --width 2500 --height 2125 --surface smooth    prints JSON
python -m doorcfg serve                                          starts the local web page
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from doorcfg.evaluate import evaluate
from doorcfg.models import DoorConfiguration
from doorcfg.rules import load_rules
from doorcfg.web import serve

SERVE_COMMAND = "serve"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="doorcfg",
        description="Fictional door configurator",
        epilog="Web page instead of JSON: python -m doorcfg serve [--port 8080]",
    )
    parser.add_argument("--width", type=int, required=True, help="width in mm")
    parser.add_argument("--height", type=int, required=True, help="height in mm")
    parser.add_argument("--surface", required=True)
    parser.add_argument("--drive", default="manual")
    parser.add_argument("--insulation", default="single")
    parser.add_argument("--option", action="append", default=[], help="repeatable")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments[:1] == [SERVE_COMMAND]:
        return serve(arguments[1:])

    args = build_parser().parse_args(arguments)
    config = DoorConfiguration(
        width_mm=args.width,
        height_mm=args.height,
        surface=args.surface,
        drive=args.drive,
        options=frozenset(args.option),
        insulation=args.insulation,
    )
    result = evaluate(config, load_rules())
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1
