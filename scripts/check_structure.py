"""Read-only import-cycle and pre-refactor HTTP contract verification.

Run from the project root: python -m scripts.check_structure
Function-local imports used by computed fields are intentionally deferred and
are not import-time edges. This command never starts lifespan or opens SQLite.
"""

import ast
import json
from pathlib import Path

from app.main import app

ROOT = Path(__file__).resolve().parents[1]


def import_graph() -> dict[str, set[str]]:
    files = {}
    for path in (ROOT / "app").rglob("*.py"):
        parts = list(path.relative_to(ROOT).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        files[".".join(parts)] = path
    graph: dict[str, set[str]] = {name: set() for name in files}
    for name, path in files.items():
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.ImportFrom):
                assert not node.level, f"Resolve relative import before checking: {name}"
                candidates = [node.module or ""]
                candidates.extend(f"{node.module}.{alias.name}" for alias in node.names)
            elif isinstance(node, ast.Import):
                candidates = [alias.name for alias in node.names]
            else:
                continue
            graph[name].update(target for target in candidates if target in files and target != name)
    return graph


def check_structure() -> int:
    graph = import_graph()
    visited: set[str] = set()
    active: list[str] = []

    def visit(name: str) -> None:
        assert name not in active, f"Import-time cycle: {' -> '.join([*active, name])}"
        if name in visited:
            return
        active.append(name)
        for dependency in sorted(graph[name]):
            visit(dependency)
        active.pop()
        visited.add(name)

    for name in sorted(graph):
        visit(name)
    expected = json.loads((ROOT / "tests/fixtures/api_contract.json").read_text(encoding="utf-8"))
    actual = app.openapi()
    # Product extensions may add endpoints and DTOs. Every original operation
    # and component still has to match exactly, including validation and errors.
    original = dict(actual)
    original["paths"] = {path: actual["paths"].get(path) for path in expected["paths"]}
    original["components"] = {
        group: {name: actual["components"].get(group, {}).get(name) for name in values}
        for group, values in expected["components"].items()
    }
    assert original == expected, "Existing HTTP OpenAPI contract differs from the pre-refactor baseline"
    return len(graph)


if __name__ == "__main__":
    print(f"PASS {check_structure()} application modules: acyclic graph, original HTTP contracts retained")
