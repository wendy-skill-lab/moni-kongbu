"""Render the opening viewing-advisory card (1080x1920) used before the film."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os

ROOT = Path(__file__).resolve().parent.parent
def choose_font(env_name, candidates):
    explicit = os.environ.get(env_name)
    if explicit:
        if not Path(explicit).is_file():
            raise SystemExit(f'{env_name} does not point to a font file: {explicit}')
        return explicit
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    raise SystemExit('Missing CJK font. Set CJK_FONT_PATH to a usable .ttf/.otf/.ttc file.')

FONT = choose_font('CJK_FONT_PATH', [
    '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf',
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/STHeiti Light.ttc',
])
BOLD = choose_font('CJK_FONT_BOLD_PATH', [
    '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Medium.otf', FONT,
])
W, H = 1080, 1920
im = Image.new('RGB', (W, H), (0, 0, 0))
d = ImageDraw.Draw(im)


def centre(text, y, size, colour, font=FONT, spacing=0):
    f = ImageFont.truetype(font, size, index=0)
    if spacing:
        widths = [d.textlength(ch, font=f) for ch in text]
        total = sum(widths) + spacing * (len(text) - 1)
        x = (W - total) / 2
        for ch, w in zip(text, widths):
            d.text((x, y), ch, font=f, fill=colour)
            x += w + spacing
    else:
        d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=colour)


centre('观看提示', 700, 64, (236, 236, 236), BOLD, spacing=18)
d.line([(W / 2 - 60, 812), (W / 2 + 60, 812)], fill=(120, 120, 120), width=2)
lines = ['本视频含有恐怖、惊悚元素，', '可能引起不适。', '心脏病患者、未成年人及易受惊吓者', '请谨慎观看。']
for i, s in enumerate(lines):
    centre(s, 870 + i * 70, 40, (200, 200, 200))
centre('剧情纯属虚构 · 建议佩戴耳机', 1190, 32, (125, 125, 125))
out = ROOT / 'assets' / 'warning_card.png'
out.parent.mkdir(parents=True, exist_ok=True)
im.save(out)
print('Saved', out)
