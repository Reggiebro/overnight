#!/usr/bin/env python3
"""Renderuje demo video iz STVARNIH odgovora modela (real_briefs.json).

Svaki tekst u videu je stvarno ono što je model rekao — nema lažnog sadržaja.
Izlaz: demo.mp4 (1280x720, 15 fps).

    python3 render_demo_video.py
"""
import json
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

FRAMES = "/tmp/ov_frames"
OUT = "/home/redman8326/overnight/demo.mp4"
W, H = 1280, 720
FPS = 15
SEC_PER_FRAME = 4

BG = (15, 17, 21)
PANEL = (26, 29, 36)
ACCENT = (138, 180, 248)
TEXT = (230, 230, 230)
DIM = (154, 160, 166)
OK = (126, 231, 135)
WARN = (242, 204, 96)


def font(size, bold=False):
    for name in (["DejaVuSansMono-Bold.ttf", "DejaVuSansMono.ttf"] if bold
                 else ["DejaVuSansMono.ttf"]):
        for d in ("/usr/share/fonts/truetype/dejavu/",
                  "/usr/share/fonts/dejavu/"):
            p = os.path.join(d, name)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def wrap(draw, text, fnt, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_frame(idx, kind, item, total):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # header
    d.rectangle([0, 0, W, 64], fill=PANEL)
    d.text((40, 20), "Overnight — lokalni AI brief", font=font(22, True), fill=ACCENT)
    d.text((W - 380, 24), "Qwen 2.5 1.5B · lokalno", font=font(16), fill=DIM)

    # panel
    d.rounded_rectangle([40, 100, W - 40, H - 100], 12, fill=PANEL)

    is_in = kind == "input"
    d.text((70, 130), f"{'ULAZ' if is_in else 'BRIEF'} — {item['name']}",
           font=font(17), fill=DIM)

    fnt = font(25)
    lines = wrap(d, item["text" if is_in else "brief"], fnt, W - 200)
    y = 185
    for ln in lines[:9]:
        d.text((70, y), ln, font=fnt, fill=TEXT)
        y += 40

    # footer
    mode_txt = "mod: local · bez API ključa, bez clouda"
    d.text((70, H - 82), mode_txt, font=font(16), fill=OK if not is_in else DIM)
    d.text((70, H - 58), f"{item['secs']}s · frame {idx}/{total}",
           font=font(14), fill=DIM)

    return img


def main():
    data = json.load(open("/home/redman8326/overnight/real_briefs.json"))
    os.makedirs(FRAMES, exist_ok=True)
    for f in os.listdir(FRAMES):
        os.remove(os.path.join(FRAMES, f))

    frames = []
    for item in data:
        frames.append(("input", item))
        frames.append(("output", item))

    for i, (kind, item) in enumerate(frames, 1):
        img = make_frame(i, kind, item, len(frames))
        img.save(f"{FRAMES}/f{i:04d}.png")

    concat = f"{FRAMES}/list.txt"
    with open(concat, "w") as f:
        for i in range(1, len(frames) + 1):
            f.write(f"file '{FRAMES}/f{i:04d}.png'\n")
            f.write(f"duration {SEC_PER_FRAME}\n")
        # ffmpeg concat needs the last frame repeated
        f.write(f"file '{FRAMES}/f{len(frames):04d}.png'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat,
           "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-r", str(FPS), OUT]
    subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(OUT):
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
             "-of", "default=nw=1", OUT], capture_output=True, text=True)
        print("=== GOTOVO ===")
        print(p.stdout)
        print(OUT)
    else:
        print("VIDEO NIJE NAPRAVLJEN")
        print(subprocess.run(cmd, capture_output=True, text=True).stderr[-2000:])


if __name__ == "__main__":
    main()
