---
title: "I Built an Agent That Reads So I Don't Have To"
published: true
tags: devchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

## What I Built

Overnight is a small agent that reads the things I don't want to read, overnight,
and hands me a two-line brief per item in the morning.

You point it at a folder, a single file, a URL, or stdin. It reads every item,
runs an open-weight model **on my own machine**, and writes a two-sentence brief
per item to a markdown file. I wake up, open one file, I'm caught up.

The effort it saves is attention, not time. I read a lot of things that are three
paragraphs of setup for two sentences of content — support tickets, changelogs,
incident reports. Reading them is not hard, it's wasteful. And the timing makes it
worse: nobody wants to open forty tabs at 8am. So the fix isn't a better reader,
it's doing the reading while I'm asleep.

That's the laziness it rewards. Not "I don't want to work" — "this task should not
cost me attention."

```
# Morning brief — 2026-10-22 20:26 UTC

_2 item(s), local mode, model `qwen2.5-1.5b-instruct-q4_k_m.gguf`_

- **a.txt** — The first sentence is here. The second sentence is beyond it.
- **b.txt** — The server is up. The team is working.
```

Three commands cover everything:

```bash
python3 overnight.py --watch ~/inbox --out ~/morning-brief.md
python3 overnight.py --url https://example.com/feed --out brief.md
cat notes.txt | python3 overnight.py --out brief.md
```

That's the whole tool. There is no cleverness in it — it's a watcher, a model, and
a file. Which is exactly why it fits "Slow and Steady": it runs every night
without being asked, and it produces the same correct result every time.

## Demo

**Live: https://92.5.41.244:8000/overnight/** — paste any text, click the button,
get a two-sentence brief from a local model. Nothing is sent to a provider.

Video: https://github.com/Reggiebro/overnight/releases/download/v1.0.0/demo.mp4

It runs on a free Oracle Cloud instance (8 vCPU / 24 GB) with the model on disk.
It also proves the thing works on hardware that isn't my laptop — I had to move it
because my old machine has a firmware thermal trip and was shutting itself down
under CPU load. The agent now lives somewhere it can't cook itself.

## Code

<script class="devrelay-embed"
  src="https://devrelay.com/embed/Reggiebro/overnight"
  data-theme="dark"></script>

## How I Built It

The summariser is a GGUF model sitting on disk — currently Qwen 2.5 1.5B Q4_K_M.
The harness is about 250 lines of Python with no SDK from any vendor. It talks to
`llama-cli` as a subprocess, or to `llama-server` on localhost:8080 when a server
is already running (which keeps the model resident, so a second item costs one
forward pass instead of a full reload).

That open-source core is not decorative — it's what makes the project work. Here's
the concrete reason a closed API would have made most of the above impossible:

- **Nothing leaves the machine.** These are my tickets, my notes, my reading. With
  an API I'd be uploading them to someone else's server to have a summary handed
  back. The whole point of the tool is that the reading is mine.
- **It costs nothing to run.** CPU inference on a free model. No per-call billing,
  no usage cap, no credit card, no "you've hit your quota for this month."
- **It works offline.** A train, a plane, a cabin with no signal — the agent still
  runs, because the weights are on disk.
- **You can swap the model.** Point `--model` at any GGUF and the pipeline is
  unchanged. Better model comes out? Drop it in. Want to fine-tune on your own
  vocabulary? You can, because you own the weights.
- **You can read the whole thing.** There's no black box to take on faith. If I
  want to know why a summary came out a certain way, I can read the code.

The last one mattered most to me. A closed model would be a black box that can
change under me without notice. An open one is a file I can inspect.

## Why Does Open Innovation Matter?

Because the reading stays mine. That's the whole argument.

I read things that are awkward to hand to a third party: incident notes with
internal hostnames, draft docs that aren't published, tickets with customer names.
With a closed API I'd be choosing between not using the tool and shipping that
text somewhere I don't control. With an open model on disk, there's no third party
to leak to, no account to suspend, and no provider that can change its terms
under me. The tool works on a plane. It costs nothing when I run it every night.
And if the model gets worse, I swap it — I'm not waiting for someone else's
roadmap.

Open innovation made the project possible. Closed would have made it a trade-off.

## The part I'm actually proud of

The tool is honest about what it did, and that took more care than the summary
logic.

The output header says `local mode` only when the model actually produced the
brief. If no model is found, it says `extractive mode` and takes the first and
last sentence — a real compression, not an invention. And if there's genuinely
nothing to summarise, it exits non-zero rather than quietly writing an empty file.

There's a subtler version of the same problem. `find_model()` searches a few
directories and picks the smallest usable GGUF. If it just returned the first file
it found, a truncated download would be reported as "local mode" while every call
silently fell back to the extractive path — the header would be lying. So it probes
each candidate with a real load before returning it, and rejects anything that
doesn't actually load. The header can be trusted because the check is real.

A failed URL fetch is handled the same way: it becomes an item that literally says
`[fetch failed: HTTP 502]`, so a Cloudflare error page never gets summarised into
fake news in your morning brief.

That's the standard I held it to: the tool never claims more than it did.

## The honest limits

I'd rather say this than have you find out:

- **The model is small.** Qwen 2.5 1.5B is deliberately tiny — it runs on CPU
  without a GPU and loads in seconds. It is not clever, it is not witty, and it
  will occasionally produce a summary that misses the point. For a real setup you'd
  swap in something larger.
- **Output is in English.** The model is mostly English-trained. Feed it Bosnian
  and it'll give you English back.
- **It summarises, it doesn't think.** It compresses. It won't tell you the
  incident report is wrong, or that the changelog contradicts last week's.
- **CPU inference is slow at scale.** Fine for a morning brief. Not for a corpus.

I'm listing these because the interesting part of the project isn't that it
summarises text — that's easy. The interesting part is that it does so with
nothing leaving the machine, no account, and no bill, and still tells you
truthfully what happened.

## Try it

```bash
git clone https://github.com/Reggiebro/overnight
cd overnight
python3 -m pytest tests/ -q
python3 overnight.py --watch ~/inbox --out ~/morning-brief.md
```

The tests are worth a look — they cover the claims I made above rather than just
that functions return things. A corrupt GGUF is rejected, a failed fetch becomes
an explicit error, the extractive fallback is deterministic, and the header never
claims `local mode` without a model. CI runs the same suite on Python 3.10–3.12
and is green.

There's a `--json` flag if you want to pipe it into something else, and a cron
line in the README if you want it to actually run while you sleep.

## Prize Categories

I'm entering for **Best Use of GitHub Copilot** — the workflow automation here is
GitHub Actions: the test suite runs automatically on every push across three
Python versions, plus a no-model smoke test that verifies the tool still produces
a correct extractive brief with no model present. That's the category where this
project's automation actually shows.

## The Lazy Payoff

I've been running it nightly. The payoff is small and specific: I stopped opening
the inbox folder in the morning. I open one file instead of forty tabs, and the
day starts without the "read forty things before coffee" tax.

The tool has no cleverness in it. It's a watcher, a model, and a file. It works
because it runs every night without being asked and produces the same correct
result. Slow and steady: run it every night, trust it in the morning.
