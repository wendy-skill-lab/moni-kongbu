#!/usr/bin/env python3
"""把 AI 画得太清楚的黑影弱化成一块看不清的发暗（“鬼看不见”规则）。
图像编辑模型在出“干净底图”时会挪动人物，所以永远不要拿干净底图相减。做法是：找出和原底图不同的、
又暗又不饱和的像素，用忽略这块人形的归一化卷积估计周围的背景，只保留 KEEP 比例的暗度，再模糊、去色，
让它看起来像一团烟，而不是一个清楚的剪影。
用法：
  soften_figure.py --edited R2_truth.png --base S3.png --out R2_soft.png [--keep 0.3]
  soften_figure.py --edited S1_shadow.png --base S1.png --matte-out matte.png   # 只输出透明度遮罩，
      用来乘到视频的每一帧上（见 references/制作.md）
常用 KEEP：0.3；还是太明显就用 0.2。依赖 opencv-python-headless 和 scipy
（建议在 Python 虚拟环境中安装）。
"""
import argparse
import numpy as np
import cv2
from PIL import Image
from scipy import ndimage


def load(p, size):
    return np.asarray(Image.open(p).convert('RGB').resize(size, Image.LANCZOS), np.float32)


def shadow_mask(g, o, lum_max=75, sat_max=40, diff_min=35):
    lum = g.mean(2); sat = g.max(2) - g.min(2); d = np.abs(g - o).max(2)
    m = (lum < lum_max) & (sat < sat_max) & (d > diff_min)
    m = ndimage.binary_opening(m, iterations=2)
    m = ndimage.binary_closing(m, iterations=5)
    lab, n = ndimage.label(m)
    if n == 0:
        return np.zeros_like(lum)
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    keep = [i + 1 for i, s in enumerate(sizes) if s > 0.25 * sizes.max()]
    m = ndimage.binary_fill_holes(np.isin(lab, keep))
    return ndimage.binary_dilation(m, iterations=3).astype(np.float32)


def smoke(shape, seed=7):
    rng = np.random.default_rng(seed)
    s = cv2.GaussianBlur(rng.random(shape).astype(np.float32), (0, 0), 10)
    return (s - s.mean()) / (s.std() + 1e-6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--edited', required=True, help='frame with the painted shadow')
    ap.add_argument('--base', required=True, help='original frame without it (pixel-aligned)')
    ap.add_argument('--out', help='softened frame output')
    ap.add_argument('--matte-out', help='write only a soft alpha matte of the shadow')
    ap.add_argument('--keep', type=float, default=0.3, help='fraction of darkness kept (0..1)')
    ap.add_argument('--size', default='1920x1080')
    a = ap.parse_args()
    size = tuple(int(v) for v in a.size.split('x'))
    g, o = load(a.edited, size), load(a.base, size)
    m = shadow_mask(g, o)
    if m.sum() == 0:
        raise SystemExit('no shadow detected: check alignment or loosen thresholds')
    shape = (size[1], size[0])
    if a.matte_out:
        al = np.clip(cv2.GaussianBlur(m, (0, 0), 8) * (0.85 + 0.2 * smoke(shape)), 0, 1)
        Image.fromarray((al * 255).astype(np.uint8)).save(a.matte_out)
        print('matte bbox', Image.fromarray((al * 255).astype(np.uint8)).getbbox())
        return
    out_w = 1 - ndimage.binary_dilation(m > 0.5, iterations=8).astype(np.float32)
    num = cv2.GaussianBlur(g * out_w[..., None], (0, 0), 28)
    den = cv2.GaussianBlur(out_w, (0, 0), 28)[..., None] + 1e-4
    bg = num / den
    gb = cv2.GaussianBlur(g, (0, 0), 5.0)
    w = np.clip(cv2.GaussianBlur(m, (0, 0), 6) * (0.9 + 0.12 * smoke(shape)), 0, 1)[..., None]
    fig = bg * (1 - a.keep) + gb * a.keep
    fig = fig * 0.25 + fig.mean(2, keepdims=True) * 0.75
    out = g * (1 - w) + fig * w
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(a.out)
    print('saved', a.out)


if __name__ == '__main__':
    main()
