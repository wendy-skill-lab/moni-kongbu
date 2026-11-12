#!/usr/bin/env python3
"""检查帧拼图。
  contact_sheet.py qa <项目目录>                    # 拼 <项目>/qa/t_*.png（来自 `node render.js qa ...`）
  contact_sheet.py video <成片.mp4> <t1,t2,...>     # 按发布版时间（含 3.5 秒观看提示）从成片抽帧
  选项：--cols 6 --per 12 --out <目录> --crop x0,y0,x1,y1（先按 1080×1920 像素裁每一帧）
输出 sheet_0.jpg、sheet_1.jpg……，每格印上时间。用看图工具逐张看：字是否完整、发送前键盘是否还在、
输入框有没有换行、抖音右侧按钮栏和底部文案区下面有没有重要信息、时钟电量人数有没有往前走。
"""
import argparse, glob, os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'


def tiles_from_qa(proj):
    fs = glob.glob(os.path.join(proj, 'qa', 't_*.png'))
    return sorted(((float(os.path.basename(f)[2:-4]), f) for f in fs))


def tiles_from_video(mp4, times):
    tmp = tempfile.mkdtemp()
    out = []
    for t in times:
        f = os.path.join(tmp, f'f_{t:.2f}.png')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', mp4, '-frames:v', '1', f], check=True)
        out.append((t, f))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['qa', 'video'])
    ap.add_argument('src')
    ap.add_argument('times', nargs='?')
    ap.add_argument('--cols', type=int, default=6)
    ap.add_argument('--per', type=int, default=12)
    ap.add_argument('--tile', type=int, default=300)
    ap.add_argument('--crop')
    ap.add_argument('--out')
    a = ap.parse_args()
    items = tiles_from_qa(a.src) if a.mode == 'qa' else tiles_from_video(a.src, [float(x) for x in a.times.split(',')])
    out = a.out or (os.path.join(a.src, 'qa') if a.mode == 'qa' else os.path.join(os.path.dirname(os.path.abspath(a.src)), 'qa_final'))
    os.makedirs(out, exist_ok=True)
    try:
        font = ImageFont.truetype(FONT, 22)
    except OSError:
        font = ImageFont.load_default()
    crop = tuple(int(v) for v in a.crop.split(',')) if a.crop else None
    for k in range(0, len(items), a.per):
        chunk = items[k:k + a.per]
        ims = []
        for t, f in chunk:
            im = Image.open(f).convert('RGB')
            if crop:
                im = im.crop(crop)
            w = a.tile; h = round(im.height * w / im.width)
            im = im.resize((w, h), Image.LANCZOS)
            d = ImageDraw.Draw(im); d.rectangle((0, 0, 90, 28), fill='black'); d.text((5, 2), f'{t:.2f}', fill='yellow', font=font)
            ims.append(im)
        rows = (len(ims) + a.cols - 1) // a.cols
        th = max(i.height for i in ims)
        sheet = Image.new('RGB', (a.cols * a.tile, rows * (th + 8)), 'white')
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % a.cols) * a.tile, (i // a.cols) * (th + 8)))
        p = os.path.join(out, f'sheet_{k // a.per}.jpg'); sheet.save(p, quality=85); print(p)


if __name__ == '__main__':
    main()
