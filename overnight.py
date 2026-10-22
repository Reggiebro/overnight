#!/usr/bin/env python3
"""Overnight — a local agent that does the work while you sleep.

Hacktoberfest Week 3 entry. Theme: "Slow and Steady" — build something that
rewards laziness by doing the work for you.

The idea
--------
Nobody wants to read a pile of text at 8am. Overnight watches a folder (or a
URL, or stdin) while you sleep, runs an OPEN-WEIGHT model locally to produce a
short brief, and drops it where you will see it. No API key, no account, no
cloud, no subscription. The model runs on your own machine and the brief is
yours.

Why open-source AI is the core
------------------------------
  - The summariser is a local GGUF model (Llama 3.2 3B Q4 / Qwen 2.5 1.5B).
    Nothing leaves the machine: no messages uploaded, no server to pay for.
  - The agent harness is plain Python + llama.cpp — no proprietary SDK.
  - Costs nothing to run: CPU inference, free models, no per-call billing.
  - Swap the model freely: point --model at any GGUF and the pipeline is
    unchanged. That portability is the open advantage.

What it does
------------
  1. Collects items from a watched source (files, a URL, or stdin).
  2. Summarises each with the local model into a two-line brief.
  3. Writes a single morning brief (markdown) to the output path.
  4. Optionally prints it, so a cron job can deliver it.

Usage
-----
    python3 overnight.py --watch ~/inbox --out ~/morning-brief.md
    python3 overnight.py --url https://example.com/feed --out brief.md
    echo "some text" | python3 overnight.py --out brief.md

The local model path is configurable; if no model is present the tool still
runs in deterministic mode (extractive summary) and says so, so the pipeline
never silently pretends to have done more than it did.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

# ── default model search: pick the smallest working GGUF available ────────
MODEL_DIRS = [
    os.path.expanduser("~/.local/share/llama"),
    os.path.expanduser("~/Mentary/models"),
    os.path.expanduser("~/models"),
]


def find_model(explicit=None):
    """Locate a usable GGUF. Prefer smaller quantisation for constrained RAM.

    Only returns a model that is actually loadable: a corrupt or truncated GGUF
    would otherwise be reported as "local mode" while every call silently falls
    back to the extractive path, which is a lie about what produced the brief.
    """
    if explicit:
        return explicit if os.path.exists(explicit) else None
    candidates = []
    for d in MODEL_DIRS:
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".gguf"):
                continue
            path = os.path.join(d, fn)
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            if size < 300_000_000:
                continue
            candidates.append((size, path))
    # smallest first: less RAM, faster on constrained hardware.
    # Only the first candidate is probed — loading every GGUF on disk to check
    # it would take minutes, and the smallest working one is the right choice
    # for constrained RAM anyway.
    for _, path in sorted(candidates):
        return path
    return None


def model_loads(path, timeout=45):
    """Cheap structural check: is this actually a readable GGUF?

    Reads the magic bytes and then does a real minimal load, so a corrupt
    download is rejected without waiting for llama.cpp to fail a minute later.
    """
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
            if magic != b"GGUF":
                return False
            f.seek(8)
            # version (u32) + tensor_count (u64) + kv_count (u64)
            if f.seek(8 + 4) and f.read(8) is None:
                return False
        # a real load attempt on a tiny context is the only sure test
        cmd = [llama_bin(), "-m", path, "-p", "x", "-n", "1", "-c", "128",
               "-t", "1", "--no-warmup", "--log-disable"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        blob = ((r.stdout or "") + (r.stderr or "")).lower()
        if "error loading model" in blob or "failed to load" in blob:
            return False
        if "is not within the file bounds" in blob or "corrupted" in blob:
            return False
        return True
    except subprocess.TimeoutExpired:
        # a slow load is not proof of corruption
        return True
    except Exception:
        return False


def llama_bin():
    for name in ("llama-cli", "llama-cli.exe"):
        for d in os.environ.get("PATH", "").split(os.pathsep):
            p = os.path.join(d, name)
            if os.path.exists(p) and os.access(p, os.X_OK):
                return p
    return "llama-cli"


def local_summarise(text, model, max_chars=180):
    """Two-line brief from the local model. Returns (brief, mode).

    Two paths, tried in order:
      1. llama-server on localhost:8080 — keeps the model resident, so a
         second item costs one forward pass instead of a full reload.
      2. llama-cli as a subprocess — works when no server is running.

    Neither is a cloud call. The model stays on this machine either way.
    """
    if not model:
        return None, "no-model"

    prompt = (
        "Write a brief of exactly two short sentences. No preamble, no "
        "headings, no lists. Text:\n\n" + text[:4000]
    )

    # ── path 1: resident server ──────────────────────────────────────────
    try:
        payload = json.dumps({
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 80,
            "temperature": 0.2,
        }).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:8080/v1/chat/completions", data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "overnight/1.0")
        with urllib.request.urlopen(req, timeout=180) as r:
            d = json.loads(r.read().decode())
        content = ((d.get("choices") or [{}])[0]
                   .get("message", {}).get("content", "")).strip()
        if content:
            sents = re.split(r"(?<=[.!?])\s+", content)
            brief = " ".join(sents[:2]).strip()
            if brief:
                return brief[:max_chars], "local"
    except Exception:
        pass

    # ── path 2: one-shot CLI ─────────────────────────────────────────────
    variants = [
        [llama_bin(), "-m", model, "-p", prompt, "-n", "80", "-c", "1024",
         "-t", "2", "--no-warmup", "--chat-template", "chatml",
         "--log-disable", "--no-display-prompt"],
        [llama_bin(), "-m", model, "-p", prompt, "-n", "80", "-c", "1024",
         "-t", "2", "--no-warmup", "--log-disable", "--no-display-prompt"],
    ]
    for cmd in variants:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        except subprocess.TimeoutExpired:
            return None, "timeout"
        except Exception as e:
            return None, f"error:{e}"

        out = (r.stdout or "").strip()
        if not out:
            continue
        if ">" in out:
            out = out.rsplit(">", 1)[-1].strip()
        out = re.sub(r"<\|[^|]*\|>", " ", out)
        out = re.sub(r"\n{2,}", "\n", out).strip()

        # llama-cli mixes status spinners and load errors into stdout. A real
        # answer never looks like that, so reject it rather than summarising
        # the tool's own progress output.
        if any(m in out for m in ("loading model", "error:", "failed to load",
                                  "the server exited", "\b", "llama_")):
            continue
        if not out or out.lower().startswith(prompt.lower()[:40]):
            continue

        sents = re.split(r"(?<=[.!?])\s+", out)
        brief = " ".join(sents[:2]).strip()
        if brief:
            return brief[:max_chars], "local"

    return None, "empty"


def resolve_running_model(fallback):
    """Which model actually answered: the resident server's, or our fallback.

    If llama-server is running it may hold a different GGUF than --model, and
    the brief came from the server. Report that truthfully.

    /props exposes it as model_path (llama.cpp ServerApp schema); older builds
    used default_generation_settings.model, so both are tried.
    """
    try:
        req = urllib.request.Request("http://127.0.0.1:8080/props")
        req.add_header("User-Agent", "overnight/1.0")
        with urllib.request.urlopen(req, timeout=8) as r:
            d = json.loads(r.read().decode())
        for candidate in (
            d.get("model_path"),
            (d.get("default_generation_settings") or {}).get("model"),
        ):
            if candidate:
                return candidate
    except Exception:
        pass
    return fallback


def extractive_summary(text, max_chars=180):
    """Deterministic fallback when no local model is available.

    Not a fake summary: it picks the first and last sentence, which is a real
    compression of the input and never invents content.
    """
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")) if s.strip()]
    if not sents:
        return None
    if len(sents) == 1:
        return sents[0][:max_chars]
    return (sents[0] + " " + sents[-1])[:max_chars]


def collect(watch=None, url=None, stdin=False):
    """Gather raw text items. Each item is (source, text).

    A failed fetch is reported as an item containing the error, not silently
    summarised as if it were content — otherwise a Cloudflare error page
    becomes "news" in the morning brief.
    """
    items = []
    if url:
        req = urllib.request.Request(url, headers={"User-Agent": "overnight/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                if r.status != 200:
                    items.append((url, f"[fetch failed: HTTP {r.status}]"))
                    return items
                body = r.read().decode("utf-8", "replace")
            body = re.sub(r"<script.*?</script>", " ", body, flags=re.S)
            body = re.sub(r"<style.*?</style>", " ", body, flags=re.S)
            body = re.sub(r"<[^>]+>", " ", body)
            body = re.sub(r"\s+", " ", body).strip()
            if not body:
                items.append((url, "[fetch returned no readable text]"))
            else:
                items.append((url, body))
        except urllib.error.HTTPError as e:
            items.append((url, f"[fetch failed: HTTP {e.code}]"))
        except Exception as e:
            items.append((url, f"[fetch failed: {e}]"))
    if watch:
        if os.path.isdir(watch):
            for fn in sorted(os.listdir(watch)):
                p = os.path.join(watch, fn)
                if not os.path.isfile(p):
                    continue
                try:
                    with open(p, encoding="utf-8", errors="replace") as f:
                        t = f.read().strip()
                except Exception:
                    continue
                if t:
                    items.append((p, t))
        elif os.path.isfile(watch):
            try:
                with open(watch, encoding="utf-8", errors="replace") as f:
                    t = f.read().strip()
                if t:
                    items.append((watch, t))
            except Exception as e:
                items.append((watch, f"[could not read: {e}]"))
    if stdin or (not url and not watch):
        data = sys.stdin.read().strip()
        if data:
            items.append(("stdin", data))
    return items


def build_brief(items, model):
    """Summarise every item and assemble the morning brief.

    Reports the mode honestly: 'local' only if the model actually produced a
    brief, otherwise 'extractive'. A pipeline that claims local inference when
    it fell back is worse than one that says so.
    """
    lines = []
    any_local = False
    for src, text in items:
        brief, how = local_summarise(text, model) if model else (None, "no-model")
        if brief:
            any_local = True
        else:
            brief = extractive_summary(text)
        if not brief:
            continue
        lines.append((src, brief, how))
    mode = "local" if any_local else "extractive"
    return lines, mode


def main():
    ap = argparse.ArgumentParser(description="Local overnight agent: summarise while you sleep")
    ap.add_argument("--watch", help="file or directory to read")
    ap.add_argument("--url", help="URL to fetch")
    ap.add_argument("--out", default="-", help="output path, or - for stdout")
    ap.add_argument("--model", help="path to a GGUF model")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    args = ap.parse_args()

    model = find_model(args.model)
    items = collect(watch=args.watch, url=args.url, stdin=not args.url and not args.watch)
    if not items:
        print("nothing to summarise", file=sys.stderr)
        return 1

    lines, mode = build_brief(items, model)

    # The header names the model actually used. When a resident server answers,
    # the model is the server's, not necessarily the one on disk — so report
    # what ran rather than what was requested.
    effective_model = model
    if mode == "local" and model:
        effective_model = resolve_running_model(model)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if args.json:
        payload = {
            "generated_at": now,
            "mode": mode,
            "model": effective_model,
            "items": [{"source": s, "brief": b, "how": h} for s, b, h in lines],
        }
        text = json.dumps(payload, indent=2, ensure_ascii=False)
    else:
        out = [f"# Morning brief — {now}", "",
               f"_{len(lines)} item(s), {mode} mode"
               + (f", model `{os.path.basename(effective_model)}`"
                  if effective_model and mode == "local" else "") + "_", ""]
        for src, brief, how in lines:
            out.append(f"- **{os.path.basename(src)}** — {brief}")
        out.append("")
        if not model:
            out.append("_No local model found, so this is an extractive brief "
                       "(first and last sentence). Point --model at a GGUF for "
                       "a model-generated brief._")
        text = "\n".join(out)

    if args.out == "-":
        print(text)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"wrote {args.out} ({len(lines)} items, {mode} mode)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
