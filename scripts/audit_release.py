"""Audit Git's actual candidate index without initializing/staging/committing the user's repository.

No network, external scanner or product dependency. Pattern checks are best effort,
not proof that a repository or its history contains no sensitive information.
"""

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 10_000_000  # Conservative decimal 10 MB, not 10 MiB.
PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{60,})\b"),
    "aws_access_key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "credential_url": re.compile(r"https?://[^\s/:]+:[^\s/@]+@"),
    "literal_credential": re.compile(
        r"(?i)(?:api[_-]?key|access[_-]?token|password|client[_-]?secret)"
        r"\s*[:=]\s*['\"]([A-Za-z0-9_+/=-]{24,})['\"]"
    ),
}
PRIVATE_PARTS = {
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".artifacts",
    "data",
    ".aws",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".codex",
    ".agents",
}


def git(arguments, *, cwd, data=None):
    executable = shutil.which("git")
    if executable is None:
        raise RuntimeError("Git is required to verify actual release inclusion")
    result = subprocess.run(  # noqa: S603 -- fixed Git executable, argv only, no shell or network command.
        [executable, *arguments], cwd=cwd, input=data, check=True, capture_output=True
    )
    return result.stdout


def private_path(name):
    path = Path(name)
    return (
        bool(set(path.parts) & PRIVATE_PARTS)
        or path.name == ".env"
        or (path.name.startswith(".env.") and path.name != ".env.example")
        or path.name.startswith(".coverage")
        or path.name.endswith((".sqlite3-wal", ".sqlite3-shm", ".db-wal", ".db-shm"))
        or path.suffix.lower() in {".pyc", ".sqlite", ".sqlite3", ".db", ".zip", ".pem", ".key", ".pfx"}
    )


def scan(name, content):
    findings = []
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return [{"path": name, "kind": "binary_requires_review", "line": None}]
    for number, line in enumerate(text.splitlines(), 1):
        for kind, pattern in PATTERNS.items():
            if pattern.search(line):
                findings.append({"path": name, "kind": kind, "line": number})
    return findings


def audit(root=ROOT):
    root = Path(root).resolve()
    artifacts = root / ".artifacts" / "release"
    if not artifacts.resolve().is_relative_to(root):
        raise ValueError("Release evidence must remain inside the project")
    artifacts.mkdir(parents=True, exist_ok=True)
    # Metadata-only inventory includes private local data, but never reads its content.
    inventory = [
        (p.relative_to(root).as_posix(), p.stat().st_size)
        for p in root.rglob("*")
        if p.is_file() and not p.is_symlink()
    ]
    try:
        top = git(["rev-parse", "--show-toplevel"], cwd=root).decode().strip()
        if Path(top).resolve() != root:
            raise ValueError("Audit the repository root, not a subdirectory of a parent repository")
        actual_tracked = git(["ls-files", "-z"], cwd=root).decode().split("\0")[:-1]
        ignored_tracked = (
            git(["ls-files", "-ci", "--exclude-standard", "-z"], cwd=root).decode().split("\0")[:-1]
        )
        history = git(["count-objects", "-v"], cwd=root).decode().strip()
        shallow = git(["rev-parse", "--is-shallow-repository"], cwd=root).decode().strip()
    except subprocess.CalledProcessError:
        if (root / ".git").exists():
            raise RuntimeError(
                "Existing Git metadata could not be inspected; release audit stopped"
            ) from None
        actual_tracked, ignored_tracked, history, shallow = None, [], None, None
    with tempfile.TemporaryDirectory(prefix="index-", dir=artifacts) as temporary:
        git_dir = Path(temporary).resolve()
        assert git_dir.is_relative_to(artifacts.resolve())
        git(["init", "--bare", str(git_dir)], cwd=root)
        options = [
            "--git-dir",
            str(git_dir),
            "--work-tree",
            str(root),
            "-c",
            "core.bare=false",
            "-c",
            "core.autocrlf=false",
        ]
        names = (
            git([*options, "ls-files", "--others", "--exclude-standard", "-z"], cwd=root)
            .decode()
            .split("\0")[:-1]
        )
        findings, entries = [], []
        for name in names:
            path = root / name
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                findings.append({"path": name, "kind": "symlink_requires_review", "line": None})
                continue
            content = path.read_bytes()
            entries.append(
                {"path": name, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
            )
            if private_path(name):
                findings.append({"path": name, "kind": "private_path_in_candidate", "line": None})
            findings.extend(scan(name, content))
        # Only populate the disposable index after checks; never stage in the real .git.
        git_blob_bytes = None
        if not findings:
            git([*options, "add", "--all"], cwd=root)
            indexed = git([*options, "ls-files", "-z"], cwd=root).decode().split("\0")[:-1]
            assert set(indexed) == set(names), "Disposable Git index differs from candidate inventory"
            staged = git([*options, "ls-files", "--stage", "-z"], cwd=root).decode().split("\0")[:-1]
            object_ids = [item.split("\t", 1)[0].split()[1] for item in staged]
            sizes = git(
                [*options, "cat-file", "--batch-check=%(objectsize)"],
                cwd=root,
                data=("\n".join(object_ids) + "\n").encode(),
            ).splitlines()
            git_blob_bytes = sum(int(size) for size in sizes)
        metadata_bytes = sum(p.stat().st_size for p in git_dir.rglob("*") if p.is_file())
    total = sum(item["bytes"] for item in entries)
    result = {
        "scope": "local release candidate; no commit, push, history rewrite or GitHub size certification",
        "working_tree_files": len(inventory),
        "working_tree_bytes": sum(size for _, size in inventory),
        "working_tree_largest": sorted(inventory, key=lambda item: item[1], reverse=True)[:12],
        "git_present": actual_tracked is not None,
        "actual_tracked_files": len(actual_tracked) if actual_tracked is not None else None,
        "actual_tracked_bytes": sum(
            (root / name).stat().st_size for name in actual_tracked if (root / name).is_file()
        )
        if actual_tracked is not None
        else None,
        "ignored_but_tracked": ignored_tracked,
        "git_object_statistics": history,
        "shallow_history": shallow,
        "candidate_files": len(entries),
        "candidate_bytes": total,
        "candidate_git_blob_bytes": git_blob_bytes,
        "disposable_git_metadata_bytes": metadata_bytes,
        "limit_bytes": LIMIT,
        "conservative_source_plus_index_below_limit": total + metadata_bytes < LIMIT,
        "findings": findings,
        "candidate": entries,
        "passed": not findings and not ignored_tracked and total + metadata_bytes < LIMIT,
        "limitations": [
            "Pattern matching is not a comprehensive secret, PII, dependency or history scan.",
            "Existing history contents are not scanned; inspect it separately before publication.",
            "GitHub remote size/accessibility remain unverified until the owner publishes and checks them.",
        ],
    }
    (artifacts / "release-manifest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    report = audit()
    print(json.dumps({key: value for key, value in report.items() if key != "candidate"}, indent=2))
    raise SystemExit(0 if report["passed"] else 1)
