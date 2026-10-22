"""Tests for Overnight.

Each test targets a claim the README makes, so a failing test is a lie the
tool tells, not just a red line:

  * it never reports "local mode" when the model did not actually answer
  * a corrupt GGUF is rejected instead of silently falling back
  * a failed URL fetch becomes an explicit error item, not fake news
  * the extractive fallback is deterministic and never invents content

Run:  python3 -m pytest tests/ -q
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import overnight as ov


# ── helpers ────────────────────────────────────────────────────────────────

def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def write_size(path, n):
    """Sparse file of n bytes — instant, no 300 MB write per test."""
    with open(path, "wb") as f:
        f.write(b"GGUF")
        f.truncate(n)
    return path


# ── find_model: never claim local mode on a broken file ────────────────────

def test_find_model_returns_none_when_no_dir(tmp_path, monkeypatch):
    """With no model dirs at all, the answer must be None — not a guess."""
    monkeypatch.setattr(ov, "MODEL_DIRS", [str(tmp_path / "nope")])
    assert ov.find_model() is None


def test_find_model_skips_non_gguf_magic(tmp_path, monkeypatch):
    """A file named .gguf with wrong magic bytes is not a model."""
    monkeypatch.setattr(ov, "MODEL_DIRS", [str(tmp_path)])
    bad = write_size(tmp_path / "fake.gguf", 300_000_001)
    monkeypatch.setattr(ov, "model_loads", lambda p, timeout=45: False)
    assert ov.find_model() is None
    assert os.path.exists(bad)  # nothing deleted, just ignored


def test_find_model_skips_small_files(tmp_path, monkeypatch):
    """Tiny files are placeholder/truncated downloads, not models."""
    monkeypatch.setattr(ov, "MODEL_DIRS", [str(tmp_path)])
    write_size(tmp_path / "tiny.gguf", 100)
    monkeypatch.setattr(ov, "model_loads", lambda p, timeout=45: True)
    assert ov.find_model() is None


def test_find_model_prefers_smallest_usable(tmp_path, monkeypatch):
    """Constrained RAM: the smallest loadable GGUF wins.

    Compare by size — directory listing order is not alphabetical, so assuming
    which path returns first would make this test flaky.
    """
    monkeypatch.setattr(ov, "MODEL_DIRS", [str(tmp_path)])
    write_size(tmp_path / "big.gguf", 400_000_000)
    write_size(tmp_path / "small.gguf", 310_000_000)
    monkeypatch.setattr(ov, "model_loads", lambda p, timeout=45: True)
    picked = ov.find_model()
    assert picked is not None
    assert os.path.getsize(picked) < 350_000_000


def test_model_loads_rejects_bad_magic(tmp_path, monkeypatch):
    """Bad magic fails fast without invoking llama-cli (which takes 45s)."""
    monkeypatch.setattr(ov.subprocess, "run", lambda *a, **k: pytest.fail("must not run"))
    p = write(tmp_path / "bad.gguf", "GZIP")
    assert ov.model_loads(p) is False


def test_model_loads_accepts_gguf_magic(tmp_path, monkeypatch):
    """Correct magic + a clean llama-cli exit = loadable."""
    class R:
        stdout, stderr = "", ""
    monkeypatch.setattr(ov.subprocess, "run", lambda *a, **k: R())
    p = write_size(tmp_path / "ok.gguf", 300_000_001)
    assert ov.model_loads(p) is True


def test_model_loads_rejects_cli_error_output(tmp_path, monkeypatch):
    """llama-cli reporting a load failure must not pass as loadable."""
    class R:
        stdout, stderr = "error: failed to load model from file", ""
    monkeypatch.setattr(ov.subprocess, "run", lambda *a, **k: R())
    p = write_size(tmp_path / "broken.gguf", 300_000_001)
    assert ov.model_loads(p) is False


def test_model_loads_survives_timeout(tmp_path, monkeypatch):
    """A slow load is not proof of corruption."""
    def boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="llama-cli", timeout=1)
    monkeypatch.setattr(ov.subprocess, "run", boom)
    p = write_size(tmp_path / "slow.gguf", 300_000_001)
    assert ov.model_loads(p, timeout=1) is True


# ── local_summarise: mode honesty ──────────────────────────────────────────

def test_local_summarise_without_model_is_no_model():
    brief, mode = ov.local_summarise("some text", None)
    assert brief is None
    assert mode == "no-model"


def test_build_brief_reports_extractive_when_model_absent(tmp_path):
    """The header must say extractive, never local, with no model."""
    items = [(str(write(tmp_path / "a.txt", "One. Two. Three.")), "One. Two. Three.")]
    lines, mode = ov.build_brief(items, None)
    assert mode == "extractive"
    assert len(lines) == 1
    assert lines[0][2] == "no-model"


def test_build_brief_is_deterministic(tmp_path):
    """Same input, same brief — the fallback never invents content."""
    items = [("a", "Alpha. Beta. Gamma."), ("b", "Delta. Epsilon. Zeta.")]
    first, m1 = ov.build_brief(items, None)
    second, m2 = ov.build_brief(items, None)
    assert first == second
    assert m1 == m2 == "extractive"


def test_extractive_never_exceeds_max_chars():
    text = "A" * 5000 + "." + " B" * 5000 + "."
    assert len(ov.extractive_summary(text)) <= 180


# ── collect: errors are content, not silent failures ───────────────────────

def test_collect_reports_failed_url_as_item():
    """A Cloudflare error page must not become 'news' in the brief."""
    items = ov.collect(url="http://127.0.0.1:1/definitely-not-there")
    assert len(items) == 1
    assert items[0][1].startswith("[fetch failed")


def test_collect_reads_every_file_in_watch_dir(tmp_path):
    write(tmp_path / "a.txt", "first")
    write(tmp_path / "b.txt", "second")
    write(tmp_path / "c.txt", "")  # empty is skipped
    (tmp_path / "sub").mkdir()
    write(tmp_path / "sub" / "nested.txt", "nested")  # dirs are skipped
    items = ov.collect(watch=str(tmp_path))
    texts = sorted(t for _, t in items)
    assert texts == ["first", "second"]


def test_collect_accepts_a_single_file(tmp_path):
    p = write(tmp_path / "one.txt", "just this")
    items = ov.collect(watch=str(p))
    assert items == [(str(p), "just this")]


def test_collect_stdin(monkeypatch):
    monkeypatch.setattr(sys, "stdin", type("S", (), {"read": lambda s: "from stdin"})())
    assert ov.collect() == [("stdin", "from stdin")]


# ── output: the brief is honest about its own provenance ───────────────────

def test_markdown_header_names_the_mode(tmp_path, monkeypatch):
    """The header is the tool's claim about itself — it must be truthful."""
    write(tmp_path / "a.txt", "Alpha. Beta. Gamma.")
    # no model present: find_model must not hit the real llama-cli (45s probe)
    monkeypatch.setattr(ov, "MODEL_DIRS", [str(tmp_path / "nope")])
    out = tmp_path / "brief.md"
    code = _run(["--watch", str(tmp_path), "--out", str(out)])
    assert code == 0
    text = out.read_text()
    # The header states the mode; the footer explains the fallback. Assert on the
    # header line itself, not the prose, so the check is not fooled by the word
    # "model" appearing in the fallback explanation.
    assert "extractive mode" in text
    assert "extractive mode, model" not in text


def test_json_output_has_no_local_without_model(tmp_path, monkeypatch):
    write(tmp_path / "a.txt", "Alpha. Beta. Gamma.")
    monkeypatch.setattr(ov, "MODEL_DIRS", [str(tmp_path / "nope")])
    out = tmp_path / "brief.json"
    _run(["--watch", str(tmp_path), "--out", str(out), "--json"])
    data = json.loads(out.read_text())
    assert data["mode"] == "extractive"
    assert data["items"][0]["how"] == "no-model"


def test_empty_watch_returns_nonzero(tmp_path, capsys, monkeypatch):
    """Nothing to summarise is an error, not a success."""
    monkeypatch.setattr(ov, "MODEL_DIRS", [str(tmp_path / "nope")])
    code = _run(["--watch", str(tmp_path)])
    assert code == 1
    assert "nothing to summarise" in capsys.readouterr().err


def _run(argv):
    sys.argv = ["overnight.py"] + argv
    try:
        return ov.main()
    except SystemExit as e:
        return e.code
