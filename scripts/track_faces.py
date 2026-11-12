#!/usr/bin/env python3
"""track_faces.py：固定机位视频的逐帧人脸轨迹（让 AI 检测框跟着头部轻微浮动）。
来自《已就寝》的全班画面：46 个绿色“抬头 0.9x”框跟着每个学生的头动，而不是钉在一张静止的布局上。

  python3 track_faces.py --frames assets/frames/clipW --out assets/stills/W_tracks.json --count 46

输出（坐标都按画面归一化到 0–1）：
  {"n": <帧数>, "tracks": [[[cx, cy, w, h, score], ...每帧], ...每个人]}
  score 已经映射成看起来可信的 0.86–0.99 置信度，会小幅跳动，不会闪烁。

做法：在放大 2 倍的帧上用 YuNet 检测（后排的小脸也能找到）；机位固定，所以把所有帧的检测结果
按位置聚类，出现在 30% 以上帧里的簇成为一条轨迹（取出现最多的 --count 个），缺帧线性插值，
再做轻微的 3 点平滑，保留自然的头部晃动和一点检测抖动。找到的人数不够 --count 时，调低 --thr
（0.38–0.42）或调高 --up（2.5）；剩下的可以由引擎补静态框。

引擎接法（module_cctv_kanban.js）：det 图层带 `tracks` 和 `fps`；时刻 t 的框是
tracks[k][floor((t - det.s) * fps)]。
"""
import argparse, glob, json
from pathlib import Path
import cv2, numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = HERE.parent / 'templates' / 'models' / 'yunet.onnx'   # face_detection_yunet_2023mar (opencv_zoo, MIT)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--frames', required=True, help='folder of extracted frames (fNNN.jpg / .png), in order')
    ap.add_argument('--out', required=True)
    ap.add_argument('--count', type=int, default=46, help='how many people to keep (most frequently detected)')
    ap.add_argument('--model', default=str(DEFAULT_MODEL))
    ap.add_argument('--thr', type=float, default=0.42, help='YuNet score threshold')
    ap.add_argument('--up', type=float, default=2.0, help='upscale factor before detection')
    ap.add_argument('--min-hits', type=float, default=0.3, help='a track must be detected in this share of frames')
    o = ap.parse_args()

    FR = sorted(glob.glob(str(Path(o.frames) / 'f*.jpg'))) or sorted(glob.glob(str(Path(o.frames) / 'f*.png')))
    if not FR:
        raise SystemExit(f'no frames in {o.frames}')
    det = cv2.FaceDetectorYN.create(o.model, '', (10, 10), o.thr, 0.3, 5000)

    def detect(path):
        im = cv2.imread(path); h, w = im.shape[:2]
        big = cv2.resize(im, (int(w * o.up), int(h * o.up)), interpolation=cv2.INTER_CUBIC)
        det.setInputSize((big.shape[1], big.shape[0]))
        _, f = det.detect(big)
        out = []
        if f is not None:
            for r in f:
                x, y, bw, bh, sc = r[0] / o.up, r[1] / o.up, r[2] / o.up, r[3] / o.up, float(r[14])
                out.append([(x + bw / 2) / w, (y + bh / 2) / h, bw / w, bh / h, sc])
        return out

    dets = [detect(p) for p in FR]
    n = len(FR)
    H = cv2.imread(FR[0]).shape[0]
    print('frames', n, 'detections/frame min/mean/max', min(map(len, dets)), round(sum(map(len, dets)) / n, 1), max(map(len, dets)))

    # cluster: with a fixed camera a face stays within ~half a box of its mean position
    cl = []
    near = lambda c, d: ((d[0] - c['cx']) / c['w']) ** 2 + ((d[1] - c['cy']) / c['h']) ** 2
    for d in sorted(sum(dets, []), key=lambda d: -d[4]):
        best = min(cl, key=lambda c: near(c, d)) if cl else None
        if best is not None and near(best, d) < 0.25:
            k = best['hits']
            for a, v in zip(('cx', 'cy', 'w', 'h'), d[:4]):
                best[a] = (best[a] * k + v) / (k + 1)
            best['hits'] = k + 1
        else:
            cl.append(dict(cx=d[0], cy=d[1], w=d[2], h=d[3], hits=1))
    cl = sorted([c for c in cl if c['hits'] >= o.min_hits * n], key=lambda c: -c['hits'])[: o.count]
    print('tracks kept', len(cl), 'of wanted', o.count)

    # per-frame assignment, one detection per track per frame
    T = np.full((len(cl), n, 5), np.nan)
    for i, ds in enumerate(dets):
        pairs = sorted((near(c, d), ci, di) for ci, c in enumerate(cl) for di, d in enumerate(ds))
        uc, ud = set(), set()
        for dd, ci, di in pairs:
            if dd > 0.25:
                break
            if ci in uc or di in ud:
                continue
            uc.add(ci); ud.add(di); T[ci, i] = ds[di]
    idx = np.arange(n)
    for ci in range(len(cl)):
        for a in range(5):
            v = T[ci, :, a]; ok = ~np.isnan(v)
            T[ci, :, a] = np.interp(idx, idx[ok], v[ok])
    for a in (2, 3):                       # box size changes slowly
        for _ in range(4):
            T[:, 1:-1, a] = 0.25 * T[:, :-2, a] + 0.5 * T[:, 1:-1, a] + 0.25 * T[:, 2:, a]
    S = T.copy()
    for a in (0, 1):                       # keep the head bob, lose the worst jitter
        S[:, 1:-1, a] = 0.25 * T[:, :-2, a] + 0.5 * T[:, 1:-1, a] + 0.25 * T[:, 2:, a]
    sc = np.clip(0.88 + 0.12 * (T[:, :, 4] - 0.45) / 0.5, 0.86, 0.99)
    for _ in range(3):
        sc[:, 1:-1] = 0.25 * sc[:, :-2] + 0.5 * sc[:, 1:-1] + 0.25 * sc[:, 2:]
    S[:, :, 4] = sc
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump({'n': n, 'tracks': np.round(S, 4).tolist()}, open(o.out, 'w'), separators=(',', ':'))
    motion = np.abs(np.diff(S[:, :, 1], axis=1)).mean() * H
    print('wrote', o.out, '| mean vertical motion', round(float(motion), 3), 'px/frame')

if __name__ == '__main__':
    main()
