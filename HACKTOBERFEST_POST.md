---
title: "I Built an Agent That Reads So I Don't Have To"
tags: ["hacktoberfest", "opensource", "ai", "python"]
published: false
description: "Overnight runs a local open-weight model on my own machine, reads everything I point it at, and hands me a two-line brief in the morning. No API key, no cloud, no bill. Here is why that is the point."
---

# I Built an Agent That Reads So I Don't Have To

This is my entry for the Hacktoberfest "Slow and Steady" challenge. The theme asks
you to build something that rewards laziness. I took it literally: I built a tool
that does the slow, boring part of my morning so I can be lazy instead.

It's called **Overnight**, and it works while I sleep.

## The actual problem

I read a lot of things I don't want to read. Support tickets, changelogs, incident
reports, long pull-request discussions. Each one is three paragraphs of setup for
two sentences of content. Reading them is not hard. It's just *wasteful* — my
attention gets spent on filler so I can find the two lines that matter.

The annoying part isn't the volume. It's the timing. Nobody wants to open forty
tabs at 8am. By the time you've read them you've already been awake for an hour,
and the day has started in a worse mood than it needed to.

So the fix isn't a better reader. It's doing the reading while you're asleep.

## What it does

You point Overnight at something — a folder, a single file, a URL, or stdin. It
reads every item, runs an open-weight model **on your own machine**, and writes a
two-sentence brief per item to a markdown file. You wake up, open one file, and
you're caught up.

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

That's the whole tool. There is no cleverness in it. It's a watcher, a model, and
a file. Which is exactly why it fits "Slow and Steady" — it runs every night
without being asked, and it produces the same correct result every time.

## Why open source isn't a marketing line here

I want to be specific, because "uses AI" is not the same as "uses open-source AI."
The model is a GGUF file sitting on disk — currently Qwen 2.5 1.5B Q4_K_M. The
harness is about 250 lines of Python with no SDK from any vendor.

That choice is the project. A closed API would have made most of the above
impossible, and here's the concrete reason:

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
  want to know why a summary came out a certain way, I can read the code and
  check.

The last one mattered most to me. A closed model would be a black box that can
change under me without notice. An open one is a file I can inspect.

## The part I'm actually proud of

The tool is honest about what it did, and that took more care than the summary
logic.

The output header says `local mode` only when the model actually produced the
brief. If no model is found, it says `extractive mode` and takes the first and
last sentence — a real compression, not an invention. And if there's genuinely
nothing to summarise, it exits non-zero rather than quietly writing an empty file.

There's a subtler version of the same problem. `find_model()` searches a few
directories and picks the smallest usable GGUF. If it just returned the first
file it found, a truncated download would be reported as "local mode" while every
call silently fell back to the extractive path — the header would be lying. So
it probes each candidate with a real load before returning it, and rejects
anything that doesn't actually load. The header can be trusted because the
check is real.

A failed URL fetch is handled the same way: it becomes an item that literally says
`[fetch failed: HTTP 502]`, so a Cloudflare error page never gets summarised into
fake news in your morning brief.

That's the standard I held it to: the tool never claims more than it did.

## The demo

It's running on a free Oracle Cloud instance (8 vCPU / 24 GB) with the model on
disk:

**https://92.5.41.244:8000/overnight/**

Paste any text, click the button, get a two-sentence brief from the local model.
Nothing is sent to a provider. It's also proof the thing works on hardware that
isn't my laptop — I had to move it because my old machine has a firmware thermal
trip and was shutting itself down under CPU load. The agent now lives somewhere
it can't cook itself.

## The honest limits

I'd rather say this than have you find out:

- **The model is small.** Qwen 2.5 1.5B is deliberately tiny — it runs on CPU
  without a GPU and loads in seconds. It is not clever, it is not witty, and it
  will occasionally produce a summary that misses the point. For a real setup you'd
  swap in something larger.
- **Output is in English.** The model is mostly English-trained. If you feed it
  Bosnian it'll give you English back.
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
claims `local mode` without a model. CI runs the same suite on Python 3.10–3.12.

There's a `--json` flag if you want to pipe it into something else, and a cron
line in the README if you want it to actually run while you sleep.

## The point

I wanted a tool that rewards laziness. Not laziness as in "I don't want to work" —
laziness as in "this task should not cost me attention." Reading forty things to
find two sentences is exactly that kind of task.

Open-source AI is what makes it possible to hand that task to a machine without
handing the contents of my life to a server at the same time. That's the
argument the project makes, and it's the one I'd stand behind.

Slow and steady: run it every night, trust it in the morning.
