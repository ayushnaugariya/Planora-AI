"""Release checks use a disposable Git index and never hide tracked private files."""

import subprocess

import pytest

from scripts.audit_release import audit, git, private_path, scan


def seed(root):
    (root / ".gitignore").write_text(".env\ndata/\n.artifacts/\n__pycache__/\n", encoding="utf-8")
    (root / "app.py").write_text("print('offline example')\n", encoding="utf-8")
    (root / ".env").write_text("PRIVATE_LOCAL_VALUE=not-for-publication\n", encoding="utf-8")
    (root / "data").mkdir()
    (root / "data/events.sqlite3").write_bytes(b"private database fixture")


def test_actual_git_candidate_excludes_local_data_without_initializing_user_git(tmp_path):
    seed(tmp_path)
    result = audit(tmp_path)
    assert result["passed"] and not result["git_present"]
    assert {entry["path"] for entry in result["candidate"]} == {".gitignore", "app.py"}
    assert not (tmp_path / ".git").exists()
    assert (tmp_path / ".env").exists() and (tmp_path / "data/events.sqlite3").exists()
    assert result["candidate_bytes"] < result["working_tree_bytes"]
    assert result["candidate_git_blob_bytes"] > 0
    assert result["conservative_source_plus_index_below_limit"]


def test_tracked_ignored_files_block_release_without_touching_actual_index(tmp_path):
    seed(tmp_path)
    git(["init", str(tmp_path)], cwd=tmp_path)
    git(["add", "--force", ".env"], cwd=tmp_path)
    before = git(["ls-files", "--stage"], cwd=tmp_path)
    report = audit(tmp_path)
    assert report["git_present"] and not report["passed"]
    assert report["ignored_but_tracked"] == [".env"]
    assert all(not item["path"].startswith(".git/") for item in report["candidate"])
    assert before == git(["ls-files", "--stage"], cwd=tmp_path)
    assert git(["remote"], cwd=tmp_path) == b""
    with pytest.raises(subprocess.CalledProcessError):
        git(["rev-parse", "HEAD"], cwd=tmp_path)  # The audit did not create a commit.


def test_secret_findings_are_redacted_and_block_the_candidate(tmp_path):
    seed(tmp_path)
    fake_key = "AIza" + "a" * 35  # Synthetic pattern fixture, never a provider call.
    (tmp_path / "unsafe.txt").write_text("credential: " + fake_key, encoding="utf-8")
    report = audit(tmp_path)
    assert not report["passed"]
    assert any(item["kind"] == "google_api_key" and item["line"] == 1 for item in report["findings"])
    assert fake_key not in str(report)


@pytest.mark.parametrize(
    "name",
    [
        ".env",
        "config/.env.production",
        "data/events.sqlite3",
        "private.key",
        "__pycache__/main.pyc",
        ".coverage",
        "events.sqlite3-shm",
    ],
)
def test_private_release_paths_are_recognized(name):
    assert private_path(name)


def test_safe_template_and_binary_review_are_distinct():
    assert not private_path(".env.example")
    assert not scan(".env.example", b"GEMINI_API_KEY=\n")
    assert scan("unreviewed.bin", b"\xff\x00")[0]["kind"] == "binary_requires_review"


def test_broken_real_git_metadata_fails_closed(tmp_path):
    seed(tmp_path)
    (tmp_path / ".git").write_text("gitdir: missing-private-repository\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="could not be inspected"):
        audit(tmp_path)
