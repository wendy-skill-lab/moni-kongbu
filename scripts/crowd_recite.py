#!/usr/bin/env python3
"""crowd_recite.py：用几条 TTS 声部叠出“一屋子人在背书”。
来自《已就寝》（熄灯的教室里，全班对着电话齐声背书）。所有风格都听不出字，所有人等电平
（没有哪个声音突出），整体沿一条平滑曲线越背越快，在最后硬停；画面要在同一帧切黑。

输入：8–20 条不同音色的单声道声部，每条念同一段伪文本（打乱的古文，见 references/提示词.md
的 P10），一个音色一个文件，例如 stems/gibA_leda.wav。

  # 1) 只有 --style unison（齐读）需要先对齐：把每个声部按句对齐到参考声部（DTW）
  python3 crowd_recite.py align --stems stems/ --ref stems/gibA_leda.wav --out stems_aligned/
  # 2) 生成齐背（干声，48 kHz 单声道 wav），可选加上微信通话音质
  python3 crowd_recite.py make --stems stems/ --dur 24 --style chaos --out recite.wav
  python3 crowd_recite.py make --stems stems_aligned/ --dur 24 --style unison --phone --out recite_call.wav

可选风格：
  chaos    60 个学生，各自从自己文本的随机位置开始念，语速、音高、远近都不同
  crowded  120 个学生，更远、更闷、房间感更重
  unison   所有人从同一处、同一语速开始（需要先 align）：一起停顿，像全班齐读，但一个字都听不出来
  reverse  每个声音都倒放：有背书的节奏，但每个音节都不对
  rising   一路加速到 3.2 倍，音调也跟着被拽高（像磁带快进）

依赖：带 rubberband 滤镜的 ffmpeg、numpy、scipy。
放到后台跑时要写成 `python3 -u crowd_recite.py ... < /dev/null`（能看到终端的后台 ffmpeg 会被
系统挂起，一直不动也不报错）。
"""
import argparse, os, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.signal import stft, butter, sosfiltfilt
from scipy.fft import dct

SR = 48000
STYLES = {
    'chaos':   dict(),
    'crowded': dict(layers=6, far=(0.55, 0.95), pitches=(0.88, 0.92, 0.96, 1.0, 1.04, 1.08, 1.12), wet=0.6),
    'unison':  dict(aligned=True, layers=5, spread=0.09),
    'reverse': dict(reverse=True),
    'rising':  dict(v1=3.2, pitch_end=1.75),
}

# ------------------------------------------------------------------ audio helpers
def load(p, sr=SR):
    cmd = ['ffmpeg', '-v', 'error', '-nostdin', '-i', str(p), '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).astype(np.float64)

def ff(x, af):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', 'pipe:0', '-af', af,
                        '-ar', str(SR), '-ac', '1', '-f', 'f32le', '-'], input=x.astype(np.float32).tobytes(), capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).astype(np.float64)

def save_wav(x, p):
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', 'pipe:0', str(p)],
                   input=np.asarray(x, np.float32).tobytes(), check=True)

def band(x, lo, hi, order=4):
    return sosfiltfilt(butter(order, [lo, hi], 'bandpass', fs=SR, output='sos'), x)

def lowpass(x, fc, order=4):
    return sosfiltfilt(butter(order, fc, 'lowpass', fs=SR, output='sos'), x)

def room_ir(early, tail, n_ref=14, seed=0):
    r = np.random.default_rng(seed)
    ir = np.zeros(int((early + tail) * SR)); ir[0] = 1.0
    for _ in range(n_ref):
        d = r.uniform(0.012, early)
        ir[int(d * SR)] += r.uniform(0.15, 0.4) * (1 - d / early * 0.6)
    k = np.arange(len(ir) - int(early * SR))
    ir[int(early * SR):] += r.normal(0, 1, len(k)) * 0.05 * np.exp(-k / (tail * SR / 4))
    return ir

def roomed(x, ir, wet):
    n = len(x) + len(ir) - 1; L = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:n]
    y[:len(x)] *= wet; y[:len(x)] += x * (1 - wet); y[len(x):] *= wet
    return y

def agc(x, target=0.12, att=0.02, rel=0.35, maxg=6.0, blk=240):
    e = np.abs(x)
    eb = np.array([e[i:i + blk].max() for i in range(0, len(e), blk)])
    ab, rb = np.exp(-blk / (att * SR)), np.exp(-blk / (rel * SR))
    ev = np.zeros_like(eb); v = 1e-3
    for i, q in enumerate(eb):
        v = q + (v - q) * (ab if q > v else rb); ev[i] = v
    env = np.repeat(ev, blk)[:len(x)]
    return x * np.minimum(maxg, target / np.maximum(env, 1e-4))

def phone(x, lo=280, hi=3600, noise=0.004, seed=10):
    """WeChat call: narrow band, AGC squash, light saturation, line noise"""
    y = agc(band(x, lo, hi))
    y = np.tanh(y * 2.2) / np.tanh(2.2)
    return y + band(np.random.default_rng(seed).normal(0, 1, len(y)), lo, hi) * noise

def speech_bounds(x, thr_db=-38, min_sil=0.16):
    """onset, offset and pause midpoints (s) from a 10 ms RMS envelope"""
    h = int(0.01 * SR)
    e = 20 * np.log10(np.array([np.sqrt(np.mean(x[i:i + h] ** 2)) + 1e-9 for i in range(0, len(x) - h, h)]))
    on = e > (e.max() + thr_db)
    idx = np.where(on)[0]
    mids, run = [], 0
    for k in range(idx[0], idx[-1]):
        if not on[k]:
            run += 1
        else:
            if run * 0.01 >= min_sil:
                mids.append((k - run / 2) * 0.01)
            run = 0
    return idx[0] * 0.01, (idx[-1] + 1) * 0.01, mids, e

# ------------------------------------------------------------------ phrase-level alignment (DTW on MFCC)
HOP = 0.02
def _mel_fb(n_fft, sr, n_mels=26, fmin=80, fmax=7600):
    mel = lambda f: 2595 * np.log10(1 + f / 700); imel = lambda m: 700 * (10 ** (m / 2595) - 1)
    bins = np.floor((n_fft + 1) * imel(np.linspace(mel(fmin), mel(fmax), n_mels + 2)) / sr).astype(int)
    fb = np.zeros((n_mels, n_fft // 2 + 1))
    for m in range(1, n_mels + 1):
        a, b, c = bins[m - 1], bins[m], bins[m + 1]
        fb[m - 1, a:b] = (np.arange(a, b) - a) / max(1, b - a); fb[m - 1, b:c] = (c - np.arange(b, c)) / max(1, c - b)
    return fb

def _feats(x16):
    _, _, Z = stft(x16, 16000, nperseg=512, noverlap=512 - int(HOP * 16000))
    P = np.abs(Z) ** 2
    c = dct(np.log(_mel_fb(512, 16000) @ P + 1e-9).T, type=2, norm='ortho', axis=1)[:, 1:14]
    c = (c - c.mean(0)) / (c.std(0) + 1e-6)
    return c / (np.linalg.norm(c, axis=1, keepdims=True) + 1e-9)

def _dtw(A, B):
    C = 1 - A @ B.T; n, m = C.shape
    D = np.full((n + 2, m + 2), np.inf); D[2, 2] = C[0, 0]
    ptr = np.zeros((n + 2, m + 2), np.int8)
    for i in range(3, n + 2):
        c = C[i - 2]
        cand = np.stack([D[i - 1, 1:m + 1] + c, D[i - 1, 0:m] + c * 1.5, D[i - 2, 1:m + 1] + c * 1.5])
        k = np.argmin(cand, 0); D[i, 2:] = cand[k, np.arange(m)]; ptr[i, 2:] = k
    i, j, P = n + 1, m + 1, []
    while i >= 2 and j >= 2:
        P.append((i - 2, j - 2))
        if i == 2 and j == 2:
            break
        k = ptr[i, j]
        i, j = (i - 1, j - 1) if k == 0 else (i - 1, j - 2) if k == 1 else (i - 2, j - 1)
    P = np.array(P[::-1]); return P[:, 0], P[:, 1]

def align(stems_dir, ref_path, out_dir):
    """stretch every stem phrase by phrase onto the reference voice's timeline (pauses land together)"""
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    ref = load(ref_path); rs0, rs1, rmids, _ = speech_bounds(ref)
    bnd = [rs0] + rmids + [rs1]
    A = _feats(load(ref_path, sr=16000))
    out = {Path(ref_path).stem: ref[int(rs0 * SR): int(rs1 * SR)]}
    for v in sorted(Path(stems_dir).glob('*.wav')):
        if v.resolve() == Path(ref_path).resolve():
            continue
        x = load(v); s0, s1, _, ex = speech_bounds(x)
        pi, pj = _dtw(A, _feats(load(v, sr=16000)))
        def snap(t, win=0.12):
            a, b = int(max(0, (t - win) / 0.01)), int(min(len(ex) - 1, (t + win) / 0.01))
            return (a + int(np.argmin(ex[a:b + 1]))) * 0.01
        src = np.maximum.accumulate(np.array([s0] + [snap(float(np.interp(b / HOP, pi, pj)) * HOP) for b in rmids] + [s1]))
        pieces = []
        for k in range(len(bnd) - 1):
            L_ref = bnd[k + 1] - bnd[k]
            seg = x[int(src[k] * SR): int(src[k + 1] * SR)]
            if len(seg) < 0.02 * SR:
                seg = np.zeros(int(0.02 * SR))
            tempo = np.clip(len(seg) / SR / L_ref, 0.6, 1.6)
            pad = np.zeros(int(0.06 * SR))
            y = ff(np.concatenate([pad, seg, pad]), f'rubberband=tempo={tempo:.5f}:transients=smooth:formant=preserved')
            c = int(0.06 * SR / tempo); y = y[c: c + int(L_ref * SR)]
            y = np.concatenate([y, np.zeros(max(0, int(L_ref * SR) - len(y)))])
            f = int(0.008 * SR); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
            pieces.append(y)
        out[v.stem] = np.concatenate(pieces)
        print(f'aligned {v.name}: {len(x) / SR:.2f}s -> {len(out[v.stem]) / SR:.2f}s', flush=True)
    n = min(len(y) for y in out.values())
    for k, y in out.items():
        save_wav(y[:n], out_dir / f'{k}.wav')
    print(f'{len(out)} aligned stems, {n / SR:.2f}s each -> {out_dir}')

# ------------------------------------------------------------------ the room
def murmur(stems_dir, D, layers=3, v0=1.0, v1=2.4, gamma=1.35, seed=11, far=(0.35, 0.9),
           pitches=(0.93, 0.96, 0.98, 1.0, 1.02, 1.04, 1.07), reverse=False, aligned=False, spread=0.09,
           pitch_end=1.0, wet=0.45, crescendo=(-3.0, 2.0)):
    r = np.random.default_rng(seed)
    srcs = sorted(Path(stems_dir).glob('*.wav'))
    if not srcs:
        sys.exit(f'no .wav stems in {stems_dir}')
    src_len = D * (v0 + v1) / 2 * 1.25 + 3          # enough input for the accelerating output
    n = int(src_len * SR); mix = np.zeros(n); cnt = 0
    for p in srcs:
        x = load(p)
        if not aligned:
            s0, s1, _, _ = speech_bounds(x); x = x[int(s0 * SR): int(s1 * SR)]
        if reverse:
            x = x[::-1].copy()
        x = x / (np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2)) + 1e-9) * 0.1
        loop = np.tile(np.concatenate([x, np.zeros(int(0.25 * SR))]), int(src_len * 1.3 * SR / len(x)) + 3)
        for _ in range(layers):
            sp = 1.0 if aligned else r.uniform(0.92, 1.12)
            pitch = float(r.choice(pitches))
            if aligned:   # same place, same pace, a few tens of ms apart
                seg = np.concatenate([np.zeros(int(r.uniform(0, spread) * SR)), loop])[: n + SR]
            else:         # everyone somewhere else in their own text
                a = int(r.uniform(0, len(x))); seg = loop[a: a + int(n * sp) + SR]
            z = ff(seg, f'rubberband=tempo={sp:.4f}:pitch={pitch:.3f}:transients=smooth:formant=preserved')[:n]
            d = r.uniform(*far)
            z = lowpass(z, 7200 - 3800 * d) * (1.0 - 0.3 * d) * r.uniform(0.92, 1.0)
            mix[:len(z)] += z; cnt += 1
        print(f'  {p.name} x{layers}', flush=True)
    mix /= cnt ** 0.5
    # one smooth accelerating time map for the whole room (rubberband driven by asendcmd, in input time)
    cmds, s, t, sp = [], 0.0, 0.0, v0
    while t < D + 0.5 and s < src_len - 0.2:
        u = min(1.0, t / D) ** gamma; sp = v0 + (v1 - v0) * u
        c = f'{s:.2f} rubberband tempo {sp:.4f}'
        if pitch_end != 1.0:
            c += f', rubberband pitch {1.0 + (pitch_end - 1.0) * u:.4f}'
        cmds.append(c); s += 0.1; t += 0.1 / sp
    cf = Path(f'/tmp/crowd_recite_cmds_{os.getpid()}.txt'); cf.write_text(';\n'.join(cmds) + ';\n')
    y = ff(mix, f'asendcmd=f={cf},rubberband=tempo={v0}:transients=smooth')[: int(D * SR)]
    y = np.concatenate([y, np.zeros(max(0, int(D * SR) - len(y)))])
    f = int(0.012 * SR); y[-f:] *= np.linspace(1, 0, f)                       # dead stop at full speed
    g = 10 ** ((crescendo[0] + (crescendo[1] - crescendo[0]) * (np.arange(len(y)) / len(y)) ** 1.5) / 20)
    print(f'{cnt} students, end speed {sp:.2f}x, {len(y) / SR:.2f}s')
    return y * g, wet

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('align', help='phrase-align stems to a reference voice (for --style unison)')
    a.add_argument('--stems', required=True); a.add_argument('--ref', required=True); a.add_argument('--out', required=True)
    m = sub.add_parser('make', help='render the chorus')
    m.add_argument('--stems', required=True, help='folder of voice stems (aligned ones for unison)')
    m.add_argument('--dur', type=float, required=True, help='seconds; the sound stops dead here')
    m.add_argument('--style', default='unison', choices=sorted(STYLES))
    m.add_argument('--end-speed', type=float, help='override the final tempo (default per style)')
    m.add_argument('--seed', type=int, default=11)
    m.add_argument('--phone', action='store_true', help='classroom room + WeChat call chain (what the mum hears)')
    m.add_argument('--out', required=True)
    o = ap.parse_args()
    if o.cmd == 'align':
        align(o.stems, o.ref, o.out); return
    st = dict(STYLES[o.style]); st['seed'] = o.seed
    if o.end_speed:
        st['v1'] = o.end_speed
    y, wet = murmur(o.stems, o.dur, **st)
    if o.phone:
        y = phone(roomed(y, room_ir(0.07, 0.75, seed=5), wet))[: len(y)]
    y = y / (np.max(np.abs(y)) + 1e-9) * 0.89
    save_wav(y, o.out); print('wrote', o.out)

if __name__ == '__main__':
    main()
