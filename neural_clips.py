"""Render recorded rate activations and commands; no synthetic neural activity."""
import runtime
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = runtime.ROOT
OUT = ROOT / 'outputs'
FONT = Path('/usr/share/fonts/truetype/dejavu')

def font(size, bold=False):
    name = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    try:
        return ImageFont.truetype(str(FONT / name) if FONT.exists() else name, size)
    except OSError:
        return ImageFont.load_default()

BG = '#101e29'
TEXT = '#e7ece3'
MUTED = '#9eb4b8'
GOLD = '#f2bf70'
CYAN = '#6adecf'

def make_frame(data, index, title, start, end):
    f = data['frames'][index]
    im = Image.new('RGB', (800, 500), BG)
    d = ImageDraw.Draw(im)
    d.text((28, 20), 'DROSOPHILA AIRLINES / NEURAL RECORDER', font=font(15, True), fill=CYAN)
    d.text((28, 49), title, font=font(29, True), fill=TEXT)
    d.text((28, 91), '384 sampled neurons · recorded model activity · 1.5× replay', font=font(14), fill=MUTED)
    values = np.asarray(f['neural']['sample'])
    # Sample order only: do not imply anatomical coordinates or connectivity.
    for k, value in enumerate(values):
        x, y = 40 + (k % 32) * 23, 130 + (k // 32) * 13
        strength = min(1, abs(float(value)) * 8)
        base = (106, 222, 207) if value >= 0 else (242, 191, 112)
        color = tuple(int(25 + (c-25) * (.12+.88*strength)) for c in base)
        radius = 2 + 3 * strength
        d.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color)
    d.text((28, 292), '+ activation', font=font(13), fill=CYAN)
    d.text((143, 292), '− activation', font=font(13), fill=GOLD)
    d.text((270, 292), 'Brightness = magnitude (saturates at |0.125|)', font=font(13), fill=MUTED)
    segment = [q for q in data['frames'] if start <= q['t'] <= end]
    for channel, label, y, color in [(0, 'AILERON', 348, CYAN), (1, 'ELEVATOR', 407, GOLD)]:
        d.text((28, y-17), label, font=font(13, True), fill=color)
        d.text((28, y+3), f"{f['controls'][channel]:+.3f}", font=font(17), fill=TEXT)
        peak = max(.03, max(abs(q['controls'][channel]) for q in segment))
        d.line((155, y, 765, y), fill='#334651', width=1)
        points = [(155+(q['t']-start)/(end-start)*610, y-q['controls'][channel]/peak*22) for q in segment]
        if len(points) > 1:
            d.line(points, fill=color, width=2)
        cursor = 155+(f['t']-start)/(end-start)*610
        d.line((cursor, y-25, cursor, y+25), fill=TEXT, width=1)
    d.text((28, 457), f"SIM {f['t']:05.1f}s / fixed connectome + trained output adapter", font=font(14), fill=TEXT)
    d.text((28, 479), 'Sample grid, not anatomy. Rate values, not spikes. Assisted aircraft control.', font=font(12), fill=MUTED)
    return im

def main():
    data = json.loads((OUT/'flight.json').read_text())
    times = np.asarray([f['t'] for f in data['frames']])
    segments = [('neural-approach', 'Captain, hold the approach.', 0, 9),
                ('neural-touchdown', 'Small brain. Final approach.', data['touchdown_time']-8, data['touchdown_time']+4)]
    for name, title, start, end in segments:
        # Exactly 100 ms/GIF frame: no fractional GIF timing drift.
        sample_times = np.arange(start, end, .15)
        images = [make_frame(data, int(np.argmin(abs(times-t))), title, start, end) for t in sample_times]
        images[len(images)//2].save(OUT/f'{name}.png')
        palette = images[len(images)//2].quantize(colors=128)
        indexed = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in images]
        indexed[0].save(OUT/f'{name}.gif', save_all=True, append_images=indexed[1:], duration=100, loop=0, optimize=False)
        print(f'Saved {name}.gif ({len(images)/10:.1f}s) and .png', flush=True)

if __name__ == '__main__':
    main()
