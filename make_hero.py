#!/usr/bin/env python3
"""Hero slika za članak — jedan stvarni par (ulaz -> brief), velik i čitljiv.

Izlaz: demo_hero.png (1280x640)
"""
import html
import json
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 640
BG = (15, 17, 21)
PANEL = (26, 29, 36)
ACCENT = (138, 180, 248)
TEXT = (230, 230, 230)
DIM = (154, 160, 166)
OK = (126, 231, 135)


def font(size, bold=False):
    names = ["DejaVuSansMono-Bold.ttf", "DejaVuSansMono.ttf"] if bold else ["DejaVuSansMono.ttf"]
    for name in names:
        for d in ("/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/dejavu/"):
            p = os.path.join(d, name)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def wrap(d, text, fnt, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def main():
    data = json.load(open("/home/redman8326/overnight/real_briefs.json"))
    item = data[0]  # najkraći, najčistiji par

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, W, 56], fill=PANEL)
    d.text((40, 16), "Overnight — local AI brief, while you sleep",
           font=font(20, True), fill=ACCENT)
    d.text((W - 300, 20), "Qwen 2.5 1.5B · local", font=font(14), fill=DIM)

    top, rh = 80, 480

    # ulaz
    d.rounded_rectangle([40, top, 580, top + rh], 12, fill=PANEL)
    d.text((60, top + 18), "INPUT", font=font(14), fill=DIM)
    y = top + 48
    for ln in wrap(d, html.unescape(item["text"]), font(18), 480)[:11]:
        d.text((60, y), ln, font=font(18), fill=TEXT)
        y += 30

    d.text((600, top + rh // 2 - 16), "->", font=font(34, True), fill=ACCENT)

    # brief
    d.rounded_rectangle([640, top, W - 40, top + rh], 12, fill=PANEL)
    d.text((660, top + 18), "BRIEF", font=font(14), fill=OK)
    y = top + 48
    for ln in wrap(d, html.unescape(item["brief"]), font(19, True), 560)[:11]:
        d.text((660, y), ln, font=font(19, True), fill=TEXT)
        y += 32

    d.text((40, H - 30), "mod: local · no API key, no cloud, no bill",
           font=font(15), fill=DIM)

    out = "/home/redman8326/overnight/demo_hero.png"
    img.save(out)
    print("snimljeno:", out, os.path.getsize(out), "bajta")


if __name__ == "__main__":
    main()
