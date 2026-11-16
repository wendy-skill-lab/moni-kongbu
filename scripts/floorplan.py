#!/usr/bin/env python3
"""俯视方位图：把主空间的机位、门窗、墙角、家具和人物位置画成一张平面图，第五步定资产时给用户确认。

用法：
  python3 floorplan.py <方位.json> <输出.png> [--scale 90]

JSON 格式（单位：米；原点在房间左上角，x 向右，y 向下；角度 0 = 朝右，90 = 朝下）：
{
  "title": "虚构活动室 · 俯视方位图",
  "room": {"w": 9, "h": 7},
  "items": [
    {"type": "rect", "x": 0.5, "y": 0.3, "w": 2.4, "h": 0.6, "label": "讲台"},
    {"type": "grid", "x": 1.2, "y": 1.6, "rows": 6, "cols": 8, "dx": 0.9, "dy": 0.85, "w": 0.6, "h": 0.4, "label": "课桌"},
    {"type": "door", "wall": "left", "at": 0.6, "len": 1.0, "label": "前门"},
    {"type": "window", "wall": "right", "from": 1.0, "to": 6.2},
    {"type": "corner", "x": 9, "y": 7, "label": "后墙角"}
  ],
  "cameras": [{"x": 0.2, "y": 0.4, "dir": 40, "fov": 100, "range": 9, "label": "示例机位 · 2.4m · 偏低偏侧"}],
  "people": [{"x": 8.1, "y": 6.3, "label": "示例人物甲", "facing": 90, "color": "#e5484d"}],
  "notes": ["机位在前门上方侧墙，斜对后墙角", "示例人物甲坐最后一排靠窗"]
}
门和窗的 wall 取 top / bottom / left / right，at、from、to 是沿墙的距离（米）。
rect 和 people 可加 "label_pos"：rect 取 center / above / below，people 取 above / below，用来错开重叠的字。
"""
import argparse, json, math, os
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont

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
def font(size, bold=False):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    ap.add_argument('out')
    ap.add_argument('--scale', type=float, default=90, help='每米多少像素')
    a = ap.parse_args()
    if not math.isfinite(a.scale) or a.scale <= 0:
        ap.error('--scale must be a positive finite number')
    with open(a.spec, encoding='utf-8') as handle:
        S = json.load(handle)
    k = a.scale
    rw, rh = S['room']['w'], S['room']['h']
    if not all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in (rw, rh)):
        ap.error('room.w and room.h must be positive finite numbers')
    notes = S.get('notes', [])
    M = 70                       # 外边距
    top = 90                     # 标题区
    note_h = 40 + 34 * len(notes)
    W = int(rw * k + 2 * M)
    H = int(top + rh * k + 2 * M + note_h)
    im = Image.new('RGB', (W, H), '#f7f5f0')
    d = ImageDraw.Draw(im, 'RGBA')
    ox, oy = M, top + M

    def P(x, y):
        return (ox + x * k, oy + y * k)

    d.text((M, 26), S.get('title', '俯视方位图'), fill='#111', font=font(34, True))
    # 1 米网格
    for i in range(int(rw) + 1):
        d.line([P(i, 0), P(i, rh)], fill='#e4e0d6', width=1)
    for j in range(int(rh) + 1):
        d.line([P(0, j), P(rw, j)], fill='#e4e0d6', width=1)
    d.rectangle([P(0, 0), P(rw, rh)], outline='#222', width=6)

    f_lab = font(20)

    def text(x, y, t, color='#333', f=None, bg=None):
        f = f or f_lab
        tw = d.textlength(t, font=f)
        x = min(max(x, 4), W - tw - 4)
        y = min(max(y, top), H - 30)
        if bg:
            d.rounded_rectangle([x - 6, y - 2, x + tw + 6, y + f.size + 8], 6, fill=bg)
        d.text((x, y), t, fill=color, font=f)

    def wall_seg(wall, s0, s1):
        if wall == 'top':
            return P(s0, 0), P(s1, 0)
        if wall == 'bottom':
            return P(s0, rh), P(s1, rh)
        if wall == 'left':
            return P(0, s0), P(0, s1)
        return P(rw, s0), P(rw, s1)

    def label_near(xy, t, dx=8, dy=-26, color='#333'):
        text(xy[0] + dx, xy[1] + dy, t, color)

    def wall_label(wall, p0, p1, t, color):
        # 上下墙的字放在墙外；左右墙的字放在墙内侧，避免超出画布
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        tw = d.textlength(t, font=f_lab)
        if wall == 'top':
            text(mid[0] - tw / 2, mid[1] - 32, t, color)
        elif wall == 'bottom':
            text(mid[0] - tw / 2, mid[1] + 8, t, color)
        elif wall == 'left':
            text(mid[0] + 12, mid[1] - 12, t, color)
        else:
            text(mid[0] - tw - 12, mid[1] - 12, t, color)

    for it in S.get('items', []):
        t = it['type']
        if t == 'rect':
            d.rectangle([P(it['x'], it['y']), P(it['x'] + it['w'], it['y'] + it['h'])],
                        fill=it.get('color', '#d9d3c4'), outline='#8a826f', width=2)
            if it.get('label'):
                pos = it.get('label_pos', 'center')
                cx = P(it['x'] + it['w'] / 2, 0)[0]
                cy = {'center': P(0, it['y'] + it['h'] / 2)[1] - 13,
                      'above': P(0, it['y'])[1] - 30,
                      'below': P(0, it['y'] + it['h'])[1] + 4}[pos]
                tw = d.textlength(it['label'], font=f_lab)
                text(cx - tw / 2, cy, it['label'])
        elif t == 'grid':
            for r in range(it['rows']):
                for c in range(it['cols']):
                    x = it['x'] + c * it['dx']; y = it['y'] + r * it['dy']
                    d.rectangle([P(x, y), P(x + it['w'], y + it['h'])], fill='#e6e0d2', outline='#a39b86', width=1)
            if it.get('label'):
                label_near(P(it['x'], it['y']), f"{it['label']}（{it['rows']}×{it['cols']}）", dx=0, dy=-28)
        elif t == 'door':
            s0 = it['at']; s1 = s0 + it.get('len', 0.9)
            p0, p1 = wall_seg(it['wall'], s0, s1)
            d.line([p0, p1], fill='#f7f5f0', width=8)
            d.line([p0, p1], fill='#c2410c', width=3)
            if it.get('label'):
                wall_label(it['wall'], p0, p1, it['label'], '#c2410c')
        elif t == 'window':
            p0, p1 = wall_seg(it['wall'], it['from'], it['to'])
            d.line([p0, p1], fill='#7cc4ea', width=10)
            wall_label(it['wall'], p0, p1, it.get('label', '窗'), '#2b7bb0')
        elif t == 'corner':
            cx, cy = P(it['x'], it['y'])
            d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], outline='#7c3aed', width=4)
            lx = cx + 18 if it['x'] < rw / 2 else cx - 18 - d.textlength(it.get('label', '墙角'), font=f_lab)
            ly = cy + 10 if it['y'] < rh / 2 else cy - 40
            text(lx, ly, it.get('label', '墙角'), '#7c3aed')

    for cam in S.get('cameras', []):
        cx, cy = P(cam['x'], cam['y'])
        rng = cam.get('range', max(rw, rh)) * k
        a0 = cam['dir'] - cam.get('fov', 90) / 2
        a1 = cam['dir'] + cam.get('fov', 90) / 2
        layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).pieslice([cx - rng, cy - rng, cx + rng, cy + rng], a0, a1,
                                       fill=(234, 179, 8, 70), outline=(202, 138, 4, 220), width=2)
        mask = Image.new('L', im.size, 0)
        ImageDraw.Draw(mask).rectangle([P(0, 0), P(rw, rh)], fill=255)
        layer.putalpha(ImageChops.multiply(layer.split()[3], mask))
        im.paste(layer, (0, 0), layer)
        ang = math.radians(cam['dir'])
        tri = [(cx + 22 * math.cos(ang), cy + 22 * math.sin(ang)),
               (cx + 14 * math.cos(ang + 2.4), cy + 14 * math.sin(ang + 2.4)),
               (cx + 14 * math.cos(ang - 2.4), cy + 14 * math.sin(ang - 2.4))]
        d.polygon(tri, fill='#a16207')
        lab = cam.get('label', '机位'); fb = font(20, True)
        lx = cx + 30 * math.cos(ang) - (d.textlength(lab, font=fb) if math.cos(ang) < 0 else 0)
        ly = cy + 30 * math.sin(ang) + (6 if math.sin(ang) >= 0 else -30)
        text(lx, ly, lab, '#854d0e', fb, bg=(255, 251, 235, 235))

    for p in S.get('people', []):
        cx, cy = P(p['x'], p['y'])
        col = p.get('color', '#2563eb')
        d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=col)
        if 'facing' in p:
            ang = math.radians(p['facing'])
            d.line([(cx, cy), (cx + 30 * math.cos(ang), cy + 30 * math.sin(ang))], fill=col, width=4)
        lab = p.get('label', ''); tw = d.textlength(lab, font=f_lab)
        if p.get('label_pos') == 'below':
            text(cx - tw / 2, cy + 16, lab, col)
        else:
            text(cx - tw / 2, cy - 44, lab, col)

    y = oy + rh * k + M - 10
    if notes:
        d.text((M, y), '方位说明', fill='#111', font=font(24, True)); y += 38
        for n in notes:
            d.text((M, y), '· ' + n, fill='#333', font=font(22)); y += 34
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    im.save(a.out)
    print(a.out)


if __name__ == '__main__':
    main()
