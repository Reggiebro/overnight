---
title: "My Laptop Keeps Shutting Down. So I Moved the Reading Agent to the Cloud and Let It Run While I Sleep"
published: true
tags: devchallenge, hf26challenge, opensource
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

<!-- Suggested DEV tags: devchallenge, hf26challenge, opensource, ai -->

## The Backstory

I own a 2011 MEDION E7216 laptop. It is old, it has no battery, and it has a habit of turning itself off.

It doesn't crash. It shuts down *cleanly* — journald flushes, filesystems sync, the whole sequence. Which is the trap: a clean shutdown looks deliberate, so you go looking for a software cause. You check for a stuck power button. You check your own scripts. You check whether some agent of yours ran a `poweroff`.

I checked all of that. Here's what the logs actually said, four times in one day:

```
Oct 22 15:36:15 kernel: thermal thermal_zone0: acpitz: critical temperature reached
Oct 22 15:36:15 kernel: reboot: HARDWARE PROTECTION shutdown (Temperature too high)
```

Firmware thermal protection. The 2011 BIOS reads an uncalibrated board sensor and trips. The CPU sits at 41-45 °C against a 90 °C critical trip — the CPU is not overheating. The *drives* are: SMART was logging the Toshiba at 102-120 °C.

That matters for the story, because it meant I had to move the thing I was building.

This week's theme is **Slow and Steady**, and the prompt tells you to channel your
inner sloth. So here's mine: my sloth move wasn't building a tool that works harder.
It was building one that works *while I'm not looking*, and then moving it somewhere
it can't die. The laziest possible version of the project — and it turned out to be
the one that actually runs.

## What I Built

Overnight is a small agent that reads the things I don't want to read, and it does it **while I sleep**.

You point it at a folder, a file, a URL, or stdin. It reads every item, runs an open-weight model **on its own machine**, and writes a two-sentence brief per item to a markdown file. I wake up, open one file, I'm caught up.

It now runs on a free Oracle Cloud instance instead of my laptop — 8 vCPU / 24 GB, model on disk, nothing that can cook itself. That move is not a detail. It's why the demo works.

The effort it saves is attention, not time. I read a lot of things that are three paragraphs of setup for two sentences of content — support tickets, changelogs, incident reports. Reading them isn't hard, it's wasteful. And the timing makes it worse: nobody wants to open forty tabs at 8am. So the fix isn't a better reader, it's doing the reading while I'm asleep.

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

That's the whole tool. No cleverness in it — a watcher, a model, and a file. Which is exactly why it fits "Slow and Steady": it runs every night without being asked, and it produces the same correct result every time.

## Demo

**Live: https://92.5.41.244:8000/overnight/** — paste any text, click the button, get a two-sentence brief from a local model. Nothing is sent to a provider.

<video src="https://github.com/Reggiebro/overnight/releases/download/v1.0.0/demo.mp4" controls width="100%"></video>

The video shows the tool running, not a mockup. Every brief in it came from the real model on the Oracle box.

It's the same machine the agent runs on. That's deliberate: I can't demo it on my laptop without the risk of it dying mid-demo.

## Code

{% embed https://github.com/Reggiebro/overnight %}

## How I Built It

The summariser is a GGUF model on disk — Qwen 2.5 1.5B Q4_K_M. The harness is about 250 lines of Python with no SDK from any vendor. It talks to `llama-cli` as a subprocess, or to `llama-server` on localhost:8080 when a server is already running, which keeps the model resident so a second item costs one forward pass instead of a full reload.

That open-source core is what makes the project work, and it's why the cloud move is cheap: I can run llama.cpp on CPU on a free tier and pay nothing.

### The part that took the most care

The tool is honest about what it did.

The header says `local mode` only when the model actually produced the brief. No model found? It says `extractive mode` and takes the first and last sentence — a real compression, not an invention. Nothing to summarise? It exits non-zero rather than quietly writing an empty file.

There's a subtler version of the same bug. `find_model()` searches a few directories and picks the smallest usable GGUF. If it just returned the first file it found, a truncated download would be reported as "local mode" while every call silently fell back to the extractive path — the header would be lying. So it probes each candidate with a real load before returning it. The header can be trusted because the check is real.

A failed URL fetch gets the same treatment: it becomes an item that literally says `[fetch failed: HTTP 502]`, so a Cloudflare error page never gets summarised into fake news in your morning brief.

### The technical detour worth recording

`llama-cli` in current builds does not generate text — it drops into an interactive chat session (banner, `available commands:`, `Exiting...`). My first version fell back to extractive mode and *looked* fine, while quietly never using the model. The fix was `llama-server` on 8080, which Overnight already supported as a resident path.

I also had to filter llama.cpp's own status lines out of the output, because `Exiting...` was being read as a summary. That's the kind of bug that makes a tool report success while doing nothing.

## Why Does Open Innovation Matter?

Because the reading stays mine. That's the whole argument.

I read things that are awkward to hand to a third party: incident notes with internal hostnames, draft docs that aren't published, tickets with customer names. With a closed API I'd be choosing between not using the tool and shipping that text somewhere I don't control. With an open model on disk, there's no third party to leak to, no account to suspend, and no provider that can change its terms under me.

Open also made the deployment possible. I'm running this on a free Oracle tier with no GPU. CPU inference on a free model — no per-call billing, no usage cap, no "you've hit your quota." A closed API on a free tier doesn't work like that; you'd be paying per call for every morning.

And it works offline. A train, a plane, a cabin with no signal — the agent still runs, because the weights are on disk.

## The Lazy Payoff

I've been running it nightly. The payoff is small and specific: I stopped opening the inbox folder in the morning. I open one file instead of forty tabs, and the day starts without the "read forty things before coffee" tax.

I also stopped fighting a laptop that was dying. The agent moved to hardware that can take the load, and the laptop does the light work it can actually do. That's the lazy payoff I didn't expect: not just fewer tabs, but one less thing breaking under me.

## Why This Is the Sloth Move

International Sloth Day is tomorrow, and the theme asks you to channel your inner
sloth. Here's how I read that: a sloth doesn't do more work. It does the work at
the time when the work costs it nothing.

That's exactly what Overnight does. It reads while I'm asleep — the cost is zero
because I'm not paying attention. It runs on a free tier on hardware that can't
overheat. It never needs me to babysit it. It produces the same correct result
every night without being asked.

The laziest possible project, and it's the one that works.

## Prize Categories

I'm entering for **Best Use of GitHub Copilot** — the automation here is GitHub Actions: the test suite runs automatically on every push across three Python versions (3.10, 3.11, 3.12), plus a no-model smoke test that verifies the tool still produces a correct extractive brief with no model present. CI is green.
