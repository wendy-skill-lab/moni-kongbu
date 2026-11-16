#!/usr/bin/env python3
"""逐段资产板：把视觉呈现脚本每一段要用的资产图（界面帧、实拍静帧、方位图、头像、聊天里发的照片）
按段排成一张张板子，第五步给用户逐段确认。还没做出来的资产画成灰色占位格，一眼能看出缺什么。

用法：
  python3 asset_board.py <资产清单.json> [--out <目录>] [--per 3] [--h 420]

清单格式（路径相对于清单文件所在目录；status 取 待确认 / 已确认 / 要改）：
{
  "title": "虚构场景示例 · 资产板 v1",
  "parts": [
    {"id": "第一段", "time": "0:03–0:14", "title": "界面帧 + 场景静帧", "status": "待确认",
     "items": [
       {"path": "qa/t_3.40.png", "label": "锁屏推送"},
       {"path": "assets/stills/S1.jpg", "label": "虚构场景母版"},
       {"path": "research/floorplan.png", "label": "方位图"}
     ],
     "note": "机位偏低偏侧；示例人物甲在窗边"}
  ]
}
输出 <目录>/board_0.jpg、board_1.jpg……（默认 qa/asset_board/），每张放 --per 段。
"""
import argparse, json, os
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

STATUS = {'已确认': '#16a34a', '待确认': '#d97706', '要改': '#dc2626'}


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


def wrap(d, text, f, width):
    lines, cur = [], ''
    for ch in text:
        if ch == '\n' or d.textlength(cur + ch, font=f) > width:
            lines.append(cur); cur = '' if ch == '\n' else ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def tile(path, label, h, base, max_w):
    p = path if os.path.isabs(path) else os.path.join(base, path)
    f = font(20)
    if os.path.exists(p):
        with Image.open(p) as source:
            im = source.convert('RGB')
        ratio = min(h / im.height, max_w / im.width)
        w = max(1, round(im.width * ratio))
        display_h = max(1, round(im.height * ratio))
        resized = im.resize((w, display_h), Image.LANCZOS)
        im = Image.new('RGB', (w, h), '#f3f4f6')
        im.paste(resized, (0, (h - display_h) // 2))
        ok = True
    else:
        w = min(max_w, max(1, round(h * 0.75)))
        im = Image.new('RGB', (w, h), '#d4d4d4')
        dd = ImageDraw.Draw(im)
        dd.rectangle([0, 0, w - 1, h - 1], outline='#9ca3af', width=3)
        msg = '待生成'
        dd.text(((w - dd.textlength(msg, font=font(30, True))) / 2, h / 2 - 22), msg, fill='#6b7280', font=font(30, True))
        ok = False
    cap_lines = wrap(ImageDraw.Draw(im), label or os.path.basename(path), f, w - 8)
    cap_h = 8 + 26 * len(cap_lines)
    out = Image.new('RGB', (w, h + cap_h), 'white')
    out.paste(im, (0, 0))
    dd = ImageDraw.Draw(out)
    for i, ln in enumerate(cap_lines):
        dd.text((4, h + 4 + 26 * i), ln, fill='#111' if ok else '#b91c1c', font=f)
    return out


def block(part, h, base, max_w):
    gap = 16
    tiles = [tile(it['path'], it.get('label', ''), h, base, max_w) for it in part.get('items', [])]
    rows, cur, cur_w = [], [], 0
    for t in tiles:
        if cur and cur_w + gap + t.width > max_w:
            rows.append(cur); cur, cur_w = [], 0
        cur.append(t); cur_w += (gap if cur_w else 0) + t.width
    if cur:
        rows.append(cur)
    tmp = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    note_lines = wrap(tmp, '备注：' + part['note'], font(22), max_w) if part.get('note') else []
    head_h = 64
    body_h = sum(max(t.height for t in r) + gap for r in rows)
    H = head_h + body_h + 30 * len(note_lines) + 24
    W = max_w + 40
    b = Image.new('RGB', (W, H), '#fafafa')
    d = ImageDraw.Draw(b)
    st = part.get('status', '待确认')
    d.rectangle([0, 0, W, head_h - 8], fill='#1f2937')
    d.text((20, 12), f"{part.get('id', '')}　{part.get('time', '')}　{part.get('title', '')}", fill='white', font=font(28, True))
    sw = d.textlength(st, font=font(24, True)) + 28
    d.rounded_rectangle([W - sw - 20, 12, W - 20, 46], 8, fill=STATUS.get(st, '#6b7280'))
    d.text((W - sw - 6, 13), st, fill='white', font=font(24, True))
    y = head_h
    for r in rows:
        x = 20
        for t in r:
            b.paste(t, (x, y)); x += t.width + gap
        y += max(t.height for t in r) + gap
    for ln in note_lines:
        d.text((20, y), ln, fill='#374151', font=font(22)); y += 30
    return b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('manifest')
    ap.add_argument('--out')
    ap.add_argument('--per', type=int, default=3, help='每张板子放几段')
    ap.add_argument('--h', type=int, default=420, help='每张资产图的显示高度')
    ap.add_argument('--width', type=int, default=2200)
    a = ap.parse_args()
    if a.per < 1 or a.h < 80 or a.width < 320:
        ap.error('--per must be positive; --h >= 80 and --width >= 320')
    with open(a.manifest, encoding='utf-8') as handle:
        M = json.load(handle)
    base = os.path.dirname(os.path.abspath(a.manifest))
    out = a.out or os.path.join(base, 'qa', 'asset_board')
    os.makedirs(out, exist_ok=True)
    parts = M['parts']
    missing = [(p.get('id', ''), it.get('label', it['path'])) for p in parts for it in p.get('items', [])
               if not os.path.exists(it['path'] if os.path.isabs(it['path']) else os.path.join(base, it['path']))]
    for k in range(0, len(parts), a.per):
        blocks = [block(p, a.h, base, a.width) for p in parts[k:k + a.per]]
        title_h = 80
        W = max(b.width for b in blocks)
        H = title_h + sum(b.height + 20 for b in blocks)
        sheet = Image.new('RGB', (W, H), 'white')
        d = ImageDraw.Draw(sheet)
        d.text((20, 18), f"{M.get('title', '资产板')}（{k // a.per + 1}/{(len(parts) + a.per - 1) // a.per}）", fill='#111', font=font(36, True))
        y = title_h
        for b in blocks:
            sheet.paste(b, (0, y)); y += b.height + 20
        p = os.path.join(out, f'board_{k // a.per}.jpg')
        sheet.save(p, quality=88); print(p)
    done = sum(1 for p in parts if p.get('status') == '已确认')
    print(f'已确认 {done}/{len(parts)} 段')
    if missing:
        print('还没做出来的资产：')
        for pid, lab in missing:
            print(f'  {pid}：{lab}')


if __name__ == '__main__':
    main()
