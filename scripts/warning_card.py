"""片头提示卡（1080x1920，3.5 秒，encode.sh 自动接在片头）。

提供四种样式及多套措辞；默认按片名哈希选择，重复渲染保持一致。
不同片名可能选到相同样式，可用参数或环境变量覆盖。

用法：
  python3 warning_card.py                         # 读 src/TITLE 和 src/film_data.json，按片名自动挑
  python3 warning_card.py --title 虚构场景示例         # 指定片名
  python3 warning_card.py --style osd --variant 1  # 指定样式和措辞
  python3 warning_card.py --list                   # 列出样式和措辞
  python3 warning_card.py --preview qa/cards.jpg   # 把所有样式拼成一张预览，给用户挑
环境变量 WARN_STYLE / WARN_VARIANT 也可以指定（encode.sh 会传进来）。
"""
import argparse
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
W, H = 1080, 1920
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


@lru_cache(maxsize=128)
def _cjk_font(size, bold=False):
    regular = choose_font('CJK_FONT_PATH', [
        '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        'C:/Windows/Fonts/msyh.ttc',
    ])
    path = choose_font('CJK_FONT_BOLD_PATH', [
        '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Medium.otf',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
        regular,
    ]) if bold else regular
    try:
        return ImageFont.truetype(path, size, index=0)
    except OSError as error:
        raise SystemExit(f'Cannot load CJK font; check CJK_FONT_PATH/CJK_FONT_BOLD_PATH: {error}')


def font(weight='Regular', size=40, mono=False):
    # CJK coverage takes priority over fixed collection indexes for OSD text.
    return _cjk_font(size, bold=weight in ('Bold', 'Medium'))


# ---------------------------------------------------------------- 措辞
# 每套措辞都要说到四件事：虚构、有惊悚画面或声音、未成年人和易受惊吓者谨慎、建议戴耳机。
COPY = {
    'alert': [
        {'title': '内容提醒',
         'body': ['接下来是一段虚构的手机录屏，', '有惊悚画面和突然的声音。', '未成年人和容易受惊的朋友', '请谨慎观看。'],
         'button': '我知道了', 'foot': '建议戴上耳机'},
        {'title': '播放前提醒',
         'body': ['以下内容为虚构创作，', '包含恐怖画面和音效。', '未成年人、易受惊吓或心脏不适者', '请谨慎观看。'],
         'button': '继续播放', 'foot': '戴耳机效果更好'},
        {'title': '这是一段虚构录屏',
         'body': ['里面的人和事都不存在，', '但有些画面和声音会吓到你。', '未成年人及易受惊吓者请谨慎观看。'],
         'button': '好', 'foot': '建议戴耳机，在安静的地方看'},
    ],
    'osd': [
        {'head': '回放前须知',
         'lines': ['本片为虚构作品', '人物、地点、事件均不存在', '含惊悚画面与突发声音', '未成年人及易受惊吓者请谨慎观看', '建议佩戴耳机']},
        {'head': '录像说明',
         'lines': ['以下录像为虚构创作', '含惊悚画面与突发声音', '声音细节较多，建议戴耳机', '未成年人及易受惊吓者请谨慎观看']},
    ],
    'headphones': [
        {'head': '戴上耳机', 'sub': '这一期，声音也是线索。',
         'small': ['虚构短片 · 含惊悚画面与音效', '未成年人及易受惊吓者请谨慎观看']},
        {'head': '关掉外放', 'sub': '戴上耳机，听清每一个声音。',
         'small': ['本片纯属虚构，含恐怖元素', '未成年人及易受惊吓者请谨慎观看']},
    ],
    'file': [
        {'name': '屏幕录制', 'rows': [('来源', '手机屏幕录制 · 虚构'), ('内容', '惊悚画面 · 突发声音'), ('提醒', '未成年人及易受惊吓者慎看'), ('建议', '佩戴耳机')]},
        {'name': '屏幕录制', 'rows': [('类型', '虚构短片'), ('包含', '恐怖画面和音效'), ('提醒', '未成年人及易受惊吓者慎看'), ('建议', '佩戴耳机')]},
    ],
}
STYLES = list(COPY)
STYLE_NAMES = {'alert': '系统弹窗', 'osd': '监控回放须知', 'headphones': '戴上耳机', 'file': '录屏信息卡'}


# ---------------------------------------------------------------- 通用画法
def grain(im, amount=6, seed=7):
    rng = np.random.default_rng(seed)
    a = np.asarray(im).astype(np.int16)
    n = rng.normal(0, amount, (a.shape[0], a.shape[1], 1)).astype(np.int16)
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))


def vignette(im, strength=0.55):
    y, x = np.ogrid[:H, :W]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 1.6)) ** 2)
    m = np.clip(1 - strength * np.clip(r - 0.35, 0, None), 0, 1)[..., None]
    return Image.fromarray((np.asarray(im).astype(np.float32) * m).astype(np.uint8))


def text_w(d, s, f, spacing=0):
    return d.textlength(s, font=f) + spacing * max(len(s) - 1, 0)


def draw_spaced(d, xy, s, f, fill, spacing=0):
    x, y = xy
    if not spacing:
        d.text((x, y), s, font=f, fill=fill)
        return
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + spacing


def centre(d, y, s, f, fill, spacing=0, cx=W / 2):
    draw_spaced(d, (cx - text_w(d, s, f, spacing) / 2, y), s, f, fill, spacing)


def fit(d, s, weight, size, max_w, mono=False):
    while size > 20:
        f = font(weight, size, mono)
        if d.textlength(s, font=f) <= max_w:
            return f
        size -= 2
    return font(weight, size, mono)


def fmt_dur(sec):
    if not sec:
        return None
    sec = int(round(sec))
    return f'{sec // 60:02d}:{sec % 60:02d}'


# ---------------------------------------------------------------- 四种样式
def card_alert(c, title, dur):
    im = Image.new('RGB', (W, H), (6, 6, 8))
    glow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(glow).ellipse((140, 560, 940, 1340), fill=60)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    im = Image.composite(Image.new('RGB', (W, H), (40, 44, 56)), im, glow)
    d = ImageDraw.Draw(im)
    bw = 780
    fbt = font('Medium', 46)
    body_h = len(c['body']) * 58
    bh = 70 + 70 + 24 + body_h + 52 + 128
    x0, y0 = (W - bw) // 2, int(H * 0.47 - bh / 2)
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=44, fill=(36, 36, 39))
    y = y0 + 70
    tf = fit(d, c['title'], 'Bold', 50, bw - 100)
    centre(d, y, c['title'], tf, (245, 245, 247))
    y += 70 + 24
    for s in c['body']:
        centre(d, y, s, fit(d, s, 'Regular', 37, bw - 90), (200, 200, 206))
        y += 58
    y += 40
    d.line((x0, y, x0 + bw, y), fill=(66, 66, 70), width=2)
    centre(d, y + 34, c['button'], fbt, (10, 132, 255))
    centre(d, y0 + bh + 60, c['foot'], font('Regular', 32), (120, 120, 126))
    return vignette(grain(im, 5), 0.35)


def card_osd(c, title, dur):
    im = Image.new('RGB', (W, H), (8, 10, 9))
    a = np.asarray(im).astype(np.int16)
    a[::4] -= 4
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    x0, y0, x1 = 130, 560, 950
    fh = font('Bold', 44, mono=True)
    y1 = y0 + 150 + len(c['lines']) * 74 + 150
    L, wcol = 60, (225, 225, 225)
    for (cx, cy, dx, dy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line((cx, cy, cx + dx * L, cy), fill=wcol, width=4)
        d.line((cx, cy, cx, cy + dy * L), fill=wcol, width=4)
    d.ellipse((x0 + 60, y0 + 78, x0 + 84, y0 + 102), fill=(225, 40, 40))
    d.text((x0 + 104, y0 + 62), c['head'], font=fh, fill=(240, 240, 240))
    y = y0 + 160
    for s in c['lines']:
        d.text((x0 + 60, y), '- ' + s, font=fit(d, '- ' + s, 'Regular', 38, x1 - x0 - 110, mono=True), fill=(205, 210, 205))
        y += 74
    fs = font('Regular', 32, mono=True)
    d.text((x0 + 60, y1 - 92), f'PLAYBACK  00:00:00 / {fmt_dur(dur) or "--:--"}', font=fs, fill=(130, 136, 130))
    d.rectangle((x0 + 60, y1 - 40, x1 - 60, y1 - 34), fill=(50, 54, 50))
    return vignette(grain(im, 9), 0.6)


def card_headphones(c, title, dur):
    im = Image.new('RGB', (W, H), (12, 12, 14))
    d = ImageDraw.Draw(im)
    cx, cy, col = W // 2, 690, (215, 215, 220)
    d.arc((cx - 120, cy - 120, cx + 120, cy + 120), 180, 360, fill=col, width=10)
    for sx in (-1, 1):
        x = cx + sx * 120
        d.rounded_rectangle((x - 30, cy - 10, x + 30, cy + 110), radius=22, outline=col, width=10)
    centre(d, 880, c['head'], font('Bold', 92), (245, 245, 247), spacing=26)
    centre(d, 1020, c['sub'], font('Regular', 40), (190, 190, 196))
    d.line((W / 2 - 40, 1110, W / 2 + 40, 1110), fill=(70, 70, 76), width=2)
    for i, s in enumerate(c['small']):
        centre(d, 1150 + i * 52, s, font('Regular', 30), (118, 118, 124))
    return vignette(grain(im, 5), 0.4)


def card_file(c, title, dur):
    im = Image.new('RGB', (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    rows = [('名称', title)] + ([('时长', fmt_dur(dur))] if dur else []) + list(c['rows'])
    cw, rh = 860, 96
    ch = 150 + len(rows) * rh + 30
    x0, y0 = (W - cw) // 2, int(H * 0.47 - ch / 2)
    d.rounded_rectangle((x0, y0, x0 + cw, y0 + ch), radius=36, fill=(28, 28, 30))
    # 标题：一个录屏小图标 + “屏幕录制”
    ix, iy = x0 + 50, y0 + 52
    d.ellipse((ix, iy, ix + 48, iy + 48), outline=(235, 235, 240), width=5)
    d.ellipse((ix + 14, iy + 14, ix + 34, iy + 34), fill=(235, 60, 60))
    d.text((ix + 72, iy - 6), c['name'], font=font('Bold', 46), fill=(245, 245, 247))
    y = y0 + 150
    fl = font('Regular', 34)
    for k, v in rows:
        d.line((x0 + 50, y, x0 + cw - 50, y), fill=(56, 56, 60), width=2)
        d.text((x0 + 50, y + 26), k, font=fl, fill=(142, 142, 147))
        fv = fit(d, v, 'Regular', 34, cw - 230)
        d.text((x0 + cw - 50 - d.textlength(v, font=fv), y + 26), v, font=fv, fill=(235, 235, 240))
        y += rh
    return vignette(grain(im, 4), 0.3)


DRAW = {'alert': card_alert, 'osd': card_osd, 'headphones': card_headphones, 'file': card_file}


# ---------------------------------------------------------------- 选择和输出
def pick(title, style=None, variant=None):
    h = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16)
    style = style or STYLES[h % len(STYLES)]
    n = len(COPY[style])
    variant = (h // 7) % n if variant is None else int(variant) % n
    return style, variant


def render(title, dur, style=None, variant=None):
    style, variant = pick(title, style, variant)
    return DRAW[style](COPY[style][variant], title, dur), style, variant


def read_meta():
    title, dur = '未命名', None
    for base in (ROOT, Path.cwd()):
        t = base / 'src' / 'TITLE'
        if t.exists():
            title = t.read_text(encoding='utf-8').strip() or title
            fd = base / 'src' / 'film_data.json'
            if fd.exists():
                with fd.open(encoding='utf-8') as handle:
                    dur = json.load(handle).get('duration')
            break
    return title, dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--title')
    ap.add_argument('--duration', type=float)
    ap.add_argument('--style', choices=STYLES, default=os.environ.get('WARN_STYLE') or None)
    ap.add_argument('--variant', type=int, default=os.environ.get('WARN_VARIANT') or None)
    ap.add_argument('--out')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--preview')
    a = ap.parse_args()
    if a.style is not None and a.style not in STYLES:
        ap.error('WARN_STYLE must be one of: ' + ', '.join(STYLES))
    if a.duration is not None and (not np.isfinite(a.duration) or a.duration < 0):
        ap.error('--duration must be a nonnegative finite number')
    title, dur = read_meta()
    title = a.title or title
    dur = a.duration if a.duration is not None else dur
    if a.list:
        for s in STYLES:
            print(s, STYLE_NAMES[s], f'{len(COPY[s])} 套措辞')
        print('本片默认：', *pick(title))
        return
    if a.preview:
        tiles = []
        for s in STYLES:
            for v in (range(len(COPY[s])) if a.style == s else [pick(title, s)[1]]):
                im, _, _ = render(title, dur, s, v)
                tiles.append((im.resize((360, 640), Image.LANCZOS), f'{s} {STYLE_NAMES[s]} #{v}'))
        sheet = Image.new('RGB', (len(tiles) * 380 + 20, 720), (30, 30, 30))
        dd = ImageDraw.Draw(sheet)
        for i, (t, lab) in enumerate(tiles):
            sheet.paste(t, (20 + i * 380, 20))
            dd.text((20 + i * 380, 672), lab, font=font('Regular', 24), fill=(200, 200, 200))
        Path(a.preview).parent.mkdir(parents=True, exist_ok=True)
        sheet.save(a.preview, quality=90)
        print('Saved preview', a.preview)
        return
    im, style, variant = render(title, dur, a.style, a.variant)
    out = Path(a.out) if a.out else ROOT / 'assets' / 'warning_card.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    print(f'Saved {out}  style={style}（{STYLE_NAMES[style]}）variant={variant}')


if __name__ == '__main__':
    main()
