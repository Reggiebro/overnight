# Tekstovi za dijeljenje — Overnight članak

Članak: https://dev.to/reggiebro/i-built-an-agent-that-reads-so-i-dont-have-to-346a

---

## Reddit (r/selfhosted ili r/LocalLLaMA)

Naslov:
My laptop's BIOS keeps shutting it down (4x in one day). So I built a reading
agent, moved it to a free Oracle tier, and now it does the reading while I sleep.

Tijelo:
The laptop is a 2011 MEDION. It shuts down *cleanly* — journald flushes,
filesystems sync — which is the trap, because a clean shutdown looks deliberate.
So I went looking for a software cause. Logged everything. Checked my own scripts.

The logs said:
```
thermal thermal_zone0: acpitz: critical temperature reached
reboot: HARDWARE PROTECTION shutdown (Temperature too high)
```

Four times in one day. Firmware thermal protection. CPU sits at 41-45C against a
90C critical trip — the CPU is never the problem. SMART was logging the Toshiba
at 102-120C.

So I moved the thing I was building — an agent that reads everything I point it at
overnight and leaves a two-line brief per item in the morning — onto a free Oracle
instance. No API key, open-weight model on disk, nothing leaves the machine.

It's my Hacktoberfest Week 3 entry. Theme is "Slow and Steady" — build something
that rewards laziness. This one does the reading while I'm asleep.

Live demo: https://92.5.41.244:8000/overnight/

The honest part I like: the header only says "local mode" when the model actually
answered. No model? It says "extractive mode" and takes the first and last
sentence — it doesn't pretend. A failed URL fetch becomes an item that literally
says [fetch failed: HTTP 502] instead of a Cloudflare page becoming fake news.

Honest limits: the model is Qwen 2.5 1.5B, deliberately tiny so it runs on CPU
without a GPU. It's not clever. It will occasionally miss the point. For a real
setup you'd swap in something bigger.

---

## Mastodon / X (duži thread, 5 postova)

1/ My 2011 laptop shuts down 4 times a day. Not a crash — a clean shutdown.
Which is the trap. A clean shutdown looks deliberate.

2/ The logs: "acpitz: critical temperature reached" → "HARDWARE PROTECTION
shutdown". Firmware thermal protection. CPU at 41-45C against a 90C trip. The
CPU is never the problem — the drives are (SMART: Toshiba at 102-120C).

3/ So I moved the reading agent I was building onto a free Oracle instance. It
reads everything I point it at overnight and leaves a two-line brief per item.
Open-weight model on disk. No API key. Nothing leaves the machine.

4/ It's my Hacktoberfest entry (theme: Slow and Steady — reward laziness). The
part I'm proud of isn't the summary. It's that the header only says "local mode"
when the model actually answered. Otherwise it says so. A failed fetch becomes
"[fetch failed: HTTP 502]" — never fake news.

5/ Demo: https://92.5.41.244:8000/overnight/
Write-up: https://dev.to/reggiebro/i-built-an-agent-that-reads-so-i-dont-have-to-346a

Honest limit: the model is Qwen 2.5 1.5B. Tiny. Not clever. Swap in something
bigger for a real setup.

---

## Discord (MLH / dev.to server) — kratko

[Hacktoberfest Week 3 entry] My laptop's BIOS keeps shutting it down, so I built
a reading agent and moved it to a free Oracle tier. It reads while I sleep and
hands me a two-line brief per item in the morning. Open-weight model on disk, no
API key, nothing leaves the machine.

Theme was "Slow and Steady" — reward laziness. This one does the reading while
I'm asleep.

Live demo: https://92.5.41.244:8000/overnight/
Write-up: https://dev.to/reggiebro/i-built-an-agent-that-reads-so-i-dont-have-to-346a

The honest part: the header only says "local mode" when the model actually
answered. No model → it says "extractive mode" and takes first+last sentence. It
doesn't pretend.

---

## Hacker News (ako ide tamo — duži, tehnički)

Title: My 2011 laptop's BIOS trips a thermal shutdown 4x a day; I moved my reading
agent to a free Oracle tier

Body:
The machine is a MEDION E7216, no battery, Kali 2026.3, kernel 7.1.5. It powers
off cleanly — which sent me looking for a software cause for a while.

The signature pair in the journal:

    kernel: thermal thermal_zone0: acpitz: critical temperature reached
    kernel: reboot: HARDWARE PROTECTION shutdown (Temperature too high)

That's firmware asserting TZ to the OS. The acpitz zone comes from a 2011 AMI
BIOS and reads an uncalibrated board sensor. CPU cores were at 41-45C against a
90C critical trip; the drives were the real problem (Toshiba at 102-120C per
SMART).

So I built the thing I was already building onto a free Oracle E3.Flex instead.
It's an overnight reading agent: point it at a folder, a URL, or stdin; it runs
an open-weight GGUF model on the box and writes a two-sentence brief per item.
~250 lines of Python, no vendor SDK.

One detail worth recording: current llama-cli builds don't generate text — they
drop into an interactive chat session (banner, "available commands:", "Exiting...").
My first version fell back to extractive mode and *looked* fine while never using
the model. Fix was llama-server on 8080, which the tool already supported as a
resident path.

Demo: https://92.5.41.244:8000/overnight/
Code: https://github.com/Reggiebro/overnight

---

## Ko šalješ i zašto

| platform | subreddit/server | zašto |
|---|---|---|
| Reddit | r/selfhosted, r/LocalLLaMA | priča o lokalnom modelu, to je njihova tema |
| Reddit | r/linux | log linije i firmware bug, tehnička priča |
| Mastodon | #opensourc #hacktoberfest | hashtagovi povezuju sa zajednicom |
| X |Hacktoberfest hashtag | jednostavno, ali X ide dalje |
| Discord | MLH Discord (pravila ga spominju) | offi cijalno mjesto za učesnike |
| Discord | dev.to server | tamo gde se takmičari okupljaju |

Bitno: ne spamuj istu poruku svugdje. Svaka zajednica ima svoj ton — Reddit
želi tehničke detalje, Discord želi kratko, Mastodon želi thread.

---

## Red koji radi (provjereno iz top članaka)

Top članci imaju 44-55 reakcija. Oni su je dobili jer:

1. **Nisu čekali da ih feed otkrije** — slali su link u zajednice gdje već postoje
2. **Imali su sliku** — kriokuler, banner, email digest. Tvoj sada ima (demo_hero.png)
3. **Imali su konkretan hook** — ne "napravio sam AI alat", nego "kriokuler mi
   pada pritiska" / "slothd sortira fajlove" / "stuck in same topics"
4. **Kom entarisali su na drugim prijavama** — autor to vidi i često uzvraća

---

## Šta NE raditi

- Ne kupuj reakcije, ne pravi lažne naloge. Dev.to otkriva to; pravila kažu da
  vodi diskvalifikaciji i suspendovanju sa sajta.
- Ne briši i objavljuj ponovo. Pravila kažu da samo prva prijava računa.
- Ne spamuj istu poruku u 10 servera. Bolje 3 mjesta dobro, nego 10 loše.

---

## Linkovi koji trebaju biti u svakoj poruci

- Članak: https://dev.to/reggiebro/i-built-an-agent-that-reads-so-i-dont-have-to-346a
- Demo: https://92.5.41.244:8000/overnight/
- Kod: https://github.com/Reggiebro/overnight
- Video: https://github.com/Reggiebro/overnight/releases/download/v1.0.0/demo.mp4
