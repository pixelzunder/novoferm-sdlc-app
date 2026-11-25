"""Fitness functions: architecture rules as deterministic tests.

Each test protects one decision from AGENTS.md. They read the source code and the folders,
not the behaviour - so they stay green or red no matter who (or what) wrote the change.
"""

import ast
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "doorcfg"
DATA = ROOT / "data"

MODULES = sorted(path.stem for path in PACKAGE.glob("*.py"))

# Who may import whom inside the package. A module that is not listed may import nothing.
ALLOWED_IMPORTS: dict[str, set[str]] = {
    "models": set(),
    "messages": set(),
    "rules": {"models"},
    "pricing": {"models", "rules"},
    "evaluate": {"models", "rules", "pricing"},
    "web": {"models", "rules", "evaluate", "messages"},
    "cli": {"models", "rules", "evaluate", "web"},
    "__main__": {"cli"},
    "__init__": set(),
}


def imported_modules(module: str) -> set[str]:
    """Top-level names of everything a module imports, e.g. {'json', 'doorcfg.rules'}."""
    tree = ast.parse((PACKAGE / f"{module}.py").read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def internal_imports(module: str) -> set[str]:
    return {
        name.split(".")[1]
        for name in imported_modules(module)
        if name.startswith("doorcfg.") and name.split(".")[1] != module
    }


@pytest.mark.parametrize("module", MODULES)
def test_modules_only_import_what_the_architecture_allows(module: str) -> None:
    """Front ends depend on the core, never the other way round."""
    assert module in ALLOWED_IMPORTS, (
        f"New module '{module}': add it to ALLOWED_IMPORTS and decide what it may import."
    )
    forbidden = internal_imports(module) - ALLOWED_IMPORTS[module]
    assert not forbidden, (
        f"{module}.py must not import {sorted(forbidden)}. "
        f"Allowed: {sorted(ALLOWED_IMPORTS[module]) or 'nothing from doorcfg'}."
    )


@pytest.mark.parametrize("module", MODULES)
def test_the_application_uses_the_standard_library_only(module: str) -> None:
    """No runtime dependencies: every import is the standard library or doorcfg itself."""
    third_party = {
        name
        for name in imported_modules(module)
        if name.split(".")[0] not in sys.stdlib_module_names | {"doorcfg", "__future__"}
    }
    assert not third_party, (
        f"{module}.py imports {sorted(third_party)}. The application has no runtime "
        "dependencies - use the standard library or ask before adding one."
    )


def test_money_is_calculated_without_float_and_round() -> None:
    """Money is integer cents. pricing.py rounds with divide_half_up() only."""
    tree = ast.parse((PACKAGE / "pricing.py").read_text(encoding="utf-8"))
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    floats = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, float)
    ]
    divisions = [node for node in ast.walk(tree) if isinstance(node, ast.Div)]
    assert not calls & {"float", "round"}, "pricing.py must not call float() or round()."
    assert not floats, f"pricing.py must not contain float literals: {floats}"
    assert not divisions, "pricing.py must not use '/'. Use '//' or divide_half_up()."


def test_the_package_contains_python_files_only() -> None:
    """Data and texts belong in data/, not next to the code."""
    strangers = sorted(
        path.relative_to(ROOT).as_posix()
        for path in PACKAGE.rglob("*")
        if path.is_file() and path.suffix != ".py" and "__pycache__" not in path.parts
    )
    assert not strangers, f"Only .py files belong in src/doorcfg/: {strangers}"


def test_the_data_folder_contains_valid_json_only() -> None:
    """Rules and texts are data: every file in data/ is a readable JSON document."""
    files = sorted(path for path in DATA.rglob("*") if path.is_file())
    assert files, "data/ is empty."
    for path in files:
        name = path.relative_to(ROOT).as_posix()
        assert path.suffix == ".json", f"{name}: only .json files belong in data/."
        json.loads(path.read_text(encoding="utf-8"))


def test_language_files_are_named_by_a_two_letter_code() -> None:
    names = sorted(path.name for path in (DATA / "messages").iterdir())
    wrong = [name for name in names if not (len(name) == 7 and name[:2].isalpha())]
    assert not wrong, f"Language files are named <code>.json, e.g. fr.json: {wrong}"


# Context budget: what an agent reads in every session is limited, like a build size budget.
BRIEFING = ("AGENTS.md", "CLAUDE.md")
BRIEFING_BUDGET_CHARS = 3_000
DESCRIPTION_BUDGET_CHARS = 200
ON_DEMAND = sorted(
    [*(ROOT / ".claude" / "skills").glob("*/SKILL.md"), *(ROOT / ".claude" / "agents").glob("*.md")]
)


def front_matter(path: Path) -> dict[str, str]:
    """The 'key: value' lines between the two '---' lines at the top of a Markdown file."""
    lines = path.read_text(encoding="utf-8").split("---")[1].strip().splitlines()
    return {key.strip(): value.strip() for key, _, value in (line.partition(":") for line in lines)}


def test_the_agent_briefing_stays_within_its_context_budget() -> None:
    """AGENTS.md and CLAUDE.md are loaded into every session and cost tokens every time."""
    size = sum(len((ROOT / name).read_text(encoding="utf-8")) for name in BRIEFING)
    assert size <= BRIEFING_BUDGET_CHARS, (
        f"{' + '.join(BRIEFING)} have {size} characters, the budget is {BRIEFING_BUDGET_CHARS}. "
        "Move knowledge that only some tasks need into a skill under .claude/skills/."
    )


@pytest.mark.parametrize("path", ON_DEMAND, ids=lambda path: path.relative_to(ROOT).as_posix())
def test_skills_and_subagents_announce_themselves_in_one_short_description(path: Path) -> None:
    """Only the description is always loaded. The agent decides by it whether to read the rest."""
    meta = front_matter(path)
    expected_name = path.parent.name if path.name == "SKILL.md" else path.stem
    assert meta.get("name") == expected_name, f"'name' must be '{expected_name}'."
    assert meta.get("description"), "A description is required: without it nobody finds this."
    assert len(meta["description"]) <= DESCRIPTION_BUDGET_CHARS, (
        f"The description has {len(meta['description'])} characters, the budget is "
        f"{DESCRIPTION_BUDGET_CHARS}. Say when to use it; the details belong in the body."
    )
