# Overnight — a local agent that does the reading while you sleep.

Hacktoberfest Week 3 entry. Theme: **"Slow and Steady"** — build something that
rewards laziness by doing the work for you.

You point it at a folder, a URL, or a pile of text. It summarises everything
with an **open-weight model running on your own machine**, and leaves a short
brief where you will see it in the morning.

No API key. No account. No cloud. No subscription.

## Live demo

**https://92.5.41.244:8000/overnight/** — paste text, get a two-sentence brief
from a local model. Runs on a free Oracle Cloud instance (8 vCPU / 24 GB) with
a Qwen 2.5 1.5B GGUF model. Nothing is sent to a provider.

## The idea

Nobody wants to open forty tabs at 8am. Overnight reads them overnight and
hands you a two-line brief per item. The work happens while you sleep — that
is the whole point.

The theme is "Slow and Steady": the project is built around doing the slow,
boring reading so you do not have to. It is a small tool that rewards laziness
by being reliable. That is the entire thesis.

## Why open-source AI is the core

The summariser is a local GGUF model (Llama 3.2 3B Q4_K_M, or Qwen 2.5 1.5B).
That is not a detail; it is what makes the project work:

- **Nothing leaves the machine.** Your messages, your files, your reading — all
  of it stays local. There is no server to trust and no provider to leak to.
- **It costs nothing to run.** CPU inference on a free model. No per-call
  billing, no usage cap, no credit card.
- **It works offline.** A train, a plane, a cabin with no signal: the agent
  still runs, because the model is on disk.
- **You can swap the model.** Point `--model` at any GGUF and the pipeline is
  unchanged. Want a better model later? Drop it in. Want to fine-tune for your
  own vocabulary? You can, because the weights are yours.
- **You can inspect what it does.** The whole harness is ~250 lines of Python
  with no proprietary SDK. There is no black box to take on faith.

A closed API could not do most of that. It would need your text uploaded, would
bill you per call, would stop working without connectivity, and would change
under you without notice.

## Install

```bash
git clone https://github.com/Reggiebro/overnight
cd overnight
```

Requirements: `python3` and a GGUF model you already have. llama.cpp
(`llama-cli` / `llama-server`) is used if present.

```bash
# find a model automatically (smallest usable GGUF in the usual dirs)
python3 overnight.py --watch ~/inbox --out ~/morning-brief.md

# or be explicit
python3 overnight.py --watch ~/inbox \
    --model ~/.local/share/llama/qwen-uncensored.gguf \
    --out ~/morning-brief.md
```

## Usage

```bash
# a folder of text files
python3 overnight.py --watch ~/inbox --out ~/morning-brief.md

# a single file
python3 overnight.py --watch article.txt --out brief.md

# a URL (markup stripped before the model sees it)
python3 overnight.py --url https://example.com/feed --out brief.md

# stdin
cat notes.txt | python3 overnight.py --out brief.md

# machine-readable output
python3 overnight.py --watch ~/inbox --out brief.json --json
```

### Running it overnight

```cron
0 6 * * *  cd ~/overnight && python3 overnight.py --watch ~/inbox --out ~/morning-brief.md
```

## Faster: keep the model resident

`llama-cli` reloads the model for every item. If you have several items, start
the server once and Overnight will use it automatically:

```bash
llama-server -m ~/.local/share/llama/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  -c 2048 -t 8 --host 0.0.0.0 --port 8080
```

With no server running, Overnight falls back to the CLI and still works.

## What it does and does not claim

The brief is honest about how it was made. The header says `local mode` only
when the model actually produced the brief, and `extractive mode` when it fell
back to taking the first and last sentence. If no model is found, it says so in
the output rather than quietly pretending.

The extractive fallback is a real compression of your text — it never invents
content. A model brief is a genuine generation.

`find_model()` probes each candidate GGUF with a real load before returning it,
so a truncated download is rejected rather than silently falling back to the
extractive path while the header still claims `local mode`.

## Tests

```bash
pip install pytest
python3 -m pytest tests/ -q
```

The suite covers the claims the README makes: a corrupt GGUF is never reported
as usable, a failed URL fetch becomes an explicit error item instead of fake
news, the extractive fallback is deterministic and bounded, and the output
header never claims `local mode` without a model.

CI runs the same suite on Python 3.10–3.12 on every push and pull request.

## Example output

```
# Morning brief — 2026-10-22 20:26 UTC

_2 item(s), local mode, model `qwen2.5-1.5b-instruct-q4_k_m.gguf`_

- **a.txt** — The first sentence is here. The second sentence is beyond it.
- **b.txt** — The server is up. The team is working.
```

## Why this fits "Slow and Steady"

The project has no cleverness in it. It is a watcher, a model, and a file. What
makes it work is that it runs every night without being asked and produces the
same correct result. Slow and steady.

## License

MIT
