"""(example from 《已就寝》 v10c — the reusable parts live in scripts/crowd_recite.py and scripts/swap_audio.sh)
v10 audition builder for 《已就寝》: recitation chorus + pocket ringtone candidates.

Everything is rendered through the same acoustic chain the film uses, so what the
user hears here is what ends up in the film:
  ring  : phone in his trouser pocket -> classroom (far corner) -> cheap 看班 camera mic
  recite: a room full of students -> the phone in his pocket -> WeChat call (narrow band + AGC)
Outputs -> assets/audio/v10_try/试听/ ; aligned stems -> assets/audio/v10_try/chorus_aligned/
"""
import subprocess, json, sys
from pathlib import Path
import os
import numpy as np
from scipy.signal import stft, butter, sosfiltfilt, sosfilt
from scipy.fft import dct

ROOT = Path(__file__).resolve().parent.parent
TRY = ROOT / 'assets/audio/v10_try'
OUTD = TRY / '试听'
ALN = TRY / 'chorus_aligned'
OUTD.mkdir(parents=True, exist_ok=True); ALN.mkdir(parents=True, exist_ok=True)
SR = 48000
rng = np.random.default_rng(10)

def load(p, af=None, sr=SR):
    cmd = ['ffmpeg', '-v', 'error', '-i', str(p), '-ac', '1', '-ar', str(sr)]
    if af:
        cmd += ['-af', af]
    cmd += ['-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).astype(np.float64)

def ff(x, af):
    """run a mono float signal through an ffmpeg audio filter"""
    r = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-af', af,
                        '-ar', str(SR), '-ac', '1', '-f', 'f32le', '-'], input=x.astype(np.float32).tobytes(), capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).astype(np.float64)

def save(x, name):
    x = np.asarray(x)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    p = OUTD / name
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-b:a', '192k', str(p)],
                   input=x.astype(np.float32).tobytes(), check=True)
    return p

def band(x, lo, hi, order=4):
    sos = butter(order, [lo, hi], 'bandpass', fs=SR, output='sos')
    return sosfiltfilt(sos, x)

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

def conv(x, ir):
    n = len(x) + len(ir) - 1
    L = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:n]

def roomed(x, ir, wet):
    y = conv(x, ir)
    y[:len(x)] *= wet
    y[:len(x)] += x * (1 - wet)
    y[len(x):] *= wet
    return y

def agc(x, target=0.12, att=0.02, rel=0.35, maxg=6.0):
    e = np.abs(x)
    a1, r1 = np.exp(-1 / (att * SR)), np.exp(-1 / (rel * SR))
    env = np.zeros_like(e); v = 0.0
    # block-wise envelope follower (fast enough at 48 kHz in numpy blocks)
    blk = 240
    eb = np.array([e[i:i + blk].max() for i in range(0, len(e), blk)])
    ev = np.zeros_like(eb); v = 1e-3
    ab, rb = a1 ** blk, r1 ** blk
    for i, q in enumerate(eb):
        v = q + (v - q) * (ab if q > v else rb)
        ev[i] = v
    env = np.repeat(ev, blk)[:len(x)]
    g = np.minimum(maxg, target / np.maximum(env, 1e-4))
    return x * g

def phone(x, lo=280, hi=3600, noise=0.004):
    """WeChat call: narrow band, AGC squash, light saturation, line noise"""
    y = band(x, lo, hi)
    y = agc(y)
    y = np.tanh(y * 2.2) / np.tanh(2.2)
    y = y + band(rng.normal(0, 1, len(y)), lo, hi) * noise
    return y

def norm_rms(x, db=-19.0):
    r = np.sqrt(np.mean(x[np.abs(x) > 1e-4] ** 2)) if np.any(np.abs(x) > 1e-4) else 1
    y = x * 10 ** (db / 20) / r
    pk = np.max(np.abs(y))
    return y * (0.95 / pk if pk > 0.95 else 1)

# ------------------------------------------------------------------ chorus alignment (DTW)
VOICES = sorted((TRY / 'chorus').glob('c*.wav'))
REF = TRY / 'chorus' / 'c7_autonoe.wav'

def mel_fb(n_fft, sr, n_mels=26, fmin=80, fmax=7600):
    mel = lambda f: 2595 * np.log10(1 + f / 700)
    imel = lambda m: 700 * (10 ** (m / 2595) - 1)
    pts = imel(np.linspace(mel(fmin), mel(fmax), n_mels + 2))
    bins = np.floor((n_fft + 1) * pts / sr).astype(int)
    fb = np.zeros((n_mels, n_fft // 2 + 1))
    for m in range(1, n_mels + 1):
        a, b, c = bins[m - 1], bins[m], bins[m + 1]
        fb[m - 1, a:b] = (np.arange(a, b) - a) / max(1, b - a)
        fb[m - 1, b:c] = (c - np.arange(b, c)) / max(1, c - b)
    return fb

HOP = 0.02
def feats(x16):
    f, t, Z = stft(x16, 16000, nperseg=512, noverlap=512 - int(HOP * 16000))
    P = np.abs(Z) ** 2
    lm = np.log(mel_fb(512, 16000) @ P + 1e-9).T
    c = dct(lm, type=2, norm='ortho', axis=1)[:, 1:14]
    c = (c - c.mean(0)) / (c.std(0) + 1e-6)
    e = np.log(P.sum(0) + 1e-9)
    return c / (np.linalg.norm(c, axis=1, keepdims=True) + 1e-9), e

def dtw(A, B):
    """symmetric DTW with slope constraint (steps 1:1, 1:2, 2:1) -> path as (i, j) arrays"""
    C = 1 - A @ B.T
    n, m = C.shape
    D = np.full((n + 2, m + 2), np.inf); D[2, 2] = C[0, 0]
    ptr = np.zeros((n + 2, m + 2), np.int8)
    for i in range(2, n + 2):
        if i == 2:
            continue
        c = C[i - 2]
        cand = np.stack([D[i - 1, 1:m + 1] + c, D[i - 1, 0:m] + c * 1.5, D[i - 2, 1:m + 1] + c * 1.5])
        k = np.argmin(cand, 0)
        D[i, 2:] = cand[k, np.arange(m)]
        ptr[i, 2:] = k
    i, j = n + 1, m + 1
    P = []
    while i >= 2 and j >= 2:
        P.append((i - 2, j - 2))
        k = ptr[i, j]
        if i == 2 and j == 2:
            break
        if k == 0: i, j = i - 1, j - 1
        elif k == 1: i, j = i - 1, j - 2
        else: i, j = i - 2, j - 1
    P = np.array(P[::-1])
    return P[:, 0], P[:, 1]

def speech_bounds(x, thr_db=-38, min_sil=0.16):
    """pause midpoints (seconds) + onset/offset, from a 10 ms RMS envelope"""
    h = int(0.01 * SR)
    e = 20 * np.log10(np.array([np.sqrt(np.mean(x[i:i + h] ** 2)) + 1e-9 for i in range(0, len(x) - h, h)]))
    on = e > thr_db + e.max() + 0  # relative threshold below
    on = e > (e.max() + thr_db)
    idx = np.where(on)[0]
    s0, s1 = idx[0] * 0.01, (idx[-1] + 1) * 0.01
    mids, run = [], 0
    for k in range(idx[0], idx[-1]):
        if not on[k]:
            run += 1
        else:
            if run * 0.01 >= min_sil:
                mids.append((k - run / 2) * 0.01)
            run = 0
    return s0, s1, mids, e

def snap(t, e, win=0.12):
    a, b = int(max(0, (t - win) / 0.01)), int(min(len(e) - 1, (t + win) / 0.01))
    return (a + int(np.argmin(e[a:b + 1]))) * 0.01

def align_all():
    ref = load(REF)
    ref16 = load(REF, sr=16000)
    rs0, rs1, rmids, _ = speech_bounds(ref)
    bnd = [rs0] + rmids + [rs1]
    A, _ = feats(ref16)
    meta = {'ref': REF.name, 'bounds': bnd}
    out = {}
    for v in VOICES:
        x = load(v)
        if v == REF:
            y = x[int(rs0 * SR): int(rs1 * SR)]
            out[v.stem] = y
            continue
        x16 = load(v, sr=16000)
        B, _ = feats(x16)
        pi, pj = dtw(A, B)
        _, _, _, ex = speech_bounds(x)
        s0, s1, _, _ = speech_bounds(x)
        # map each reference boundary to the source timeline, then snap into the nearest quiet spot
        src = [s0] + [snap(float(np.interp(b / HOP, pi, pj)) * HOP, ex) for b in rmids] + [s1]
        src = np.maximum.accumulate(np.array(src))
        pieces = []
        for k in range(len(bnd) - 1):
            L_ref = bnd[k + 1] - bnd[k]
            a, b = src[k], src[k + 1]
            seg = x[int(a * SR): int(b * SR)]
            if len(seg) < 0.02 * SR:
                seg = np.zeros(int(0.02 * SR))
            tempo = np.clip(len(seg) / SR / L_ref, 0.6, 1.6)
            pad = np.zeros(int(0.06 * SR))
            y = ff(np.concatenate([pad, seg, pad]), f'rubberband=tempo={tempo:.5f}:transients=smooth:formant=preserved')
            c = int(0.06 * SR / tempo)
            y = y[c: c + int(L_ref * SR)]
            if len(y) < int(L_ref * SR):
                y = np.concatenate([y, np.zeros(int(L_ref * SR) - len(y))])
            f = int(0.008 * SR)
            y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
            pieces.append(y)
        out[v.stem] = np.concatenate(pieces)
        # alignment check: envelope correlation before/after
        def envc(p, q):
            h = int(0.02 * SR); n = min(len(p), len(q)) // h
            ep = np.array([np.sqrt(np.mean(p[i * h:(i + 1) * h] ** 2)) for i in range(n)])
            eq = np.array([np.sqrt(np.mean(q[i * h:(i + 1) * h] ** 2)) for i in range(n)])
            return float(np.corrcoef(ep, eq)[0, 1])
        r_before = envc(ref[int(rs0 * SR):], x[int(s0 * SR):])
        r_after = envc(out[REF.stem] if REF.stem in out else ref[int(rs0 * SR): int(rs1 * SR)], out[v.stem])
        print(f'{v.stem:12s} src {len(x)/SR:5.2f}s -> {len(out[v.stem])/SR:5.2f}s  env corr {r_before:.2f} -> {r_after:.2f}')
    n = min(len(y) for y in out.values())
    for k, y in out.items():
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', str(ALN / f'{k}.wav')],
                       input=y[:n].astype(np.float32).tobytes(), check=True)
    meta['dur'] = n / SR
    json.dump(meta, open(ALN / 'meta.json', 'w'), ensure_ascii=False, indent=1)
    return meta

def stems():
    return {p.stem: load(p) for p in sorted(ALN.glob('*.wav'))}

def use_set(name, ref):
    """switch the chorus source: 'c' = real 劝学 (v10), 'gibA' / 'gibB' = scrambled pseudo-text (v10b)"""
    global VOICES, REF, ALN
    if name == 'c':
        VOICES = sorted((TRY / 'chorus').glob('c*.wav')); REF = TRY / 'chorus' / 'c7_autonoe.wav'
        ALN = TRY / 'chorus_aligned'
    else:
        VOICES = sorted((TRY / 'gib').glob(f'{name}_*.wav')); REF = TRY / 'gib' / f'{name}_{ref}.wav'
        ALN = TRY / f'{name}_aligned'
    ALN.mkdir(exist_ok=True)

GIB_SET = {'G': ('gibA', 'leda'), 'H': ('gibB', 'autonoe')}

def students_even(st, layers=3, spread=0.10, seed=3):
    """a whole class with nobody in front: every voice levelled, all a few desks away from the phone"""
    r = np.random.default_rng(seed)
    n = max(len(y) for y in st.values()) + int(0.6 * SR)
    mix = np.zeros(n)
    for vi, (k, y) in enumerate(st.items()):
        y = y / (np.sqrt(np.mean(y[np.abs(y) > 0.01] ** 2)) + 1e-9) * 0.1
        for L in range(layers):
            pitch = float(r.choice([0.95, 0.975, 1.0, 1.025, 1.05]))
            z = y if pitch == 1.0 else ff(y, f'rubberband=pitch={pitch}:formant=preserved')
            far = r.uniform(0.4, 0.85)
            z = lowpass(z, 7000 - 3500 * far) * (1.0 - 0.3 * far) * r.uniform(0.92, 1.0)
            d = int((r.uniform(0, spread) + 0.02 * L) * SR)
            m = min(len(z), n - d)
            mix[d:d + m] += z[:m]
    return mix / (len(st) * layers) ** 0.5

def gib_chorus(version, D, v0=1.0, v1=2.5, gamma=1.25, gap=0.22, fps=24):
    """pseudo-text chorus, faster phrase after phrase all the way to the end, cut dead at D.
    returns (dry, wet, mouth) where mouth is a 0..1 opening curve at `fps` from the reference voice,
    put through exactly the same tempo map (so the lips on 看班 move with what is heard)."""
    name, ref = GIB_SET[version]
    use_set(name, ref)
    meta = json.load(open(ALN / 'meta.json'))
    st = stems()
    refv = st[f'{name}_{ref}']
    dry = students_even(st, layers=3, spread=0.10, seed=3)
    bnd = [b - meta['bounds'][0] for b in meta['bounds']]
    P = bnd[-1]
    segs = [(bnd[k], bnd[k + 1]) for k in range(len(bnd) - 1)]
    out, mo, t = [], [], 0.0
    h = int(SR / fps / 4)
    while t < D:
        for k, (a, b) in enumerate(segs):
            if t >= D:
                break
            last = k == len(segs) - 1
            seg = dry[int(a * SR): int((b + (0.12 if last else 0)) * SR)]
            rs = refv[int(a * SR): int(b * SR)]
            if last:
                seg = np.concatenate([seg, np.zeros(int(gap * SR))]); rs = np.concatenate([rs, np.zeros(int(gap * SR))])
            mid = t + (len(seg) / SR) / 2 / (v0 + (v1 - v0) * min(1, t / D) ** gamma)
            sp = v0 + (v1 - v0) * min(1.0, mid / D) ** gamma
            y = ff(seg, f'rubberband=tempo={sp:.4f}:transients=smooth')
            f = int(0.006 * SR)
            if len(y) > 2 * f:
                y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
            # mouth curve of the reference voice, squeezed by the same factor
            e = np.array([np.sqrt(np.mean(rs[i:i + h] ** 2)) for i in range(0, max(1, len(rs) - h), h)])
            n_out = max(1, int(round(len(y) / SR * fps * 4)))
            mo.append(np.interp(np.linspace(0, len(e) - 1, n_out), np.arange(len(e)), e))
            out.append(y)
            t += len(y) / SR
    y = np.concatenate(out)[: int(D * SR)]
    f = int(0.012 * SR); y[-f:] *= np.linspace(1, 0, f)              # dead stop, mid-word, at full speed
    g = 10 ** ((-2.5 + 4.5 * (np.arange(len(y)) / len(y)) ** 1.6) / 20)  # slowly louder as it runs away
    y = y * g
    m = np.concatenate(mo)
    m = m / (np.percentile(m, 95) + 1e-9)
    m = np.clip(m, 0, 1) ** 0.7
    m = m[: int(D * fps * 4)].reshape(-1, 4).max(1)                    # one value per video frame
    return y, 0.42, m

# ------------------------------------------------------------------ recitation versions
IR_CLASS = room_ir(0.07, 0.75, seed=5)
SOLO = load(TRY / 'chenmo_solo.wav')[: int(6.05 * SR)] if (TRY / 'chenmo_solo.wav').exists() else np.zeros(1)

def students(st, layers=3, spread=0.16, seed=1):
    """each TTS voice becomes several students: small pitch / timing / level / distance differences"""
    r = np.random.default_rng(seed)
    n = max(len(y) for y in st.values()) + int(0.6 * SR)
    mix = np.zeros(n)
    for vi, (k, y) in enumerate(st.items()):
        for L in range(layers):
            pitch = 1.0 if L == 0 else float(r.choice([0.94, 0.965, 1.035, 1.06]))
            z = y if pitch == 1.0 else ff(y, f'rubberband=pitch={pitch}:formant=preserved')
            far = r.uniform(0, 1)
            z = lowpass(z, 7000 - 3500 * far) * (1.0 - 0.55 * far) * r.uniform(0.75, 1.0)
            d = int((r.uniform(0, spread) + 0.03 * L) * SR)
            m = min(len(z), n - d)
            mix[d:d + m] += z[:m]
    return mix / (len(st) * layers) ** 0.5

def call_chain(dry, wet=0.42):
    return phone(roomed(dry, IR_CLASS, wet))

def tempo_ramp(x, bounds, v0=1.0, v1=1.7, gamma=1.3):
    """speed up phrase by phrase (cut on the shared pauses, so every voice speeds up together)"""
    out, K = [], len(bounds) - 1
    b = [bb - bounds[0] for bb in bounds]
    for k in range(K):
        seg = x[int(b[k] * SR): int(b[k + 1] * SR)] if k < K - 1 else x[int(b[k] * SR):]
        sp = v0 + (v1 - v0) * (k / max(1, K - 1)) ** gamma
        y = ff(seg, f'rubberband=tempo={sp:.4f}:transients=smooth')
        f = int(0.006 * SR)
        if len(y) > 2 * f:
            y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
        out.append(y)
    return np.concatenate(out)

def ending(chorus_phone, stop_at=None, gap=0.9, tail=1.4):
    """chorus through the call -> stops -> line hiss -> one voice carries on alone -> hiss"""
    if stop_at is not None:
        chorus_phone = chorus_phone[: int(stop_at * SR)]
        f = int(0.02 * SR)
        chorus_phone[-f:] *= np.linspace(1, 0, f)
    solo = phone(roomed(SOLO, IR_CLASS, 0.12), noise=0.0)
    solo = solo / np.sqrt(np.mean(solo[np.abs(solo) > 1e-3] ** 2)) * np.sqrt(np.mean(chorus_phone[np.abs(chorus_phone) > 1e-3] ** 2)) * 0.8
    gapx = np.zeros(int(gap * SR))
    tl = np.zeros(int(tail * SR))
    y = np.concatenate([chorus_phone, gapx, solo, tl])
    y += band(rng.normal(0, 1, len(y)), 280, 3600) * 0.004         # the line stays open the whole time
    return y

def fit(x, D):
    """time-stretch a dry chorus so it lasts exactly D seconds (ends on the paragraph)"""
    tempo = len(x) / SR / D
    y = ff(x, f'rubberband=tempo={tempo:.5f}:transients=smooth') if abs(tempo - 1) > 0.002 else x
    n = int(D * SR)
    return np.concatenate([y, np.zeros(max(0, n - len(y)))])[:n]

def dry_chorus(version, D, native_offset=0.5):
    """mono dry chorus for the film, exactly D seconds; returns (signal, room wetness)"""
    if version in MSTYLE:
        return murmur_chorus(D, **MSTYLE[version]), MSTYLE[version].get('wet', 0.45)
    if version in GIB_SET:
        y, wet, _ = gib_chorus(version, D)
        return y, wet
    meta = json.load(open(ALN / 'meta.json'))
    st = stems()
    if version == 'B':
        return fit(students(st, layers=3, spread=0.12, seed=2), D), 0.42
    if version == 'C':
        return fit(tempo_ramp(students(st, layers=3, spread=0.10, seed=3), meta['bounds'], 1.0, 1.75), D), 0.42
    if version == 'E':
        near = {k: st[k] for k in ('c7_autonoe', 'c2_umbriel', 'c5_leda', 'c3_zuben')}
        return fit(students(near, layers=1, spread=0.04, seed=4), D), 0.25
    if version == 'D':
        r = np.random.default_rng(7)
        n = int(D * SR)
        y = np.zeros(n)
        for x in [load(v) for v in VOICES]:
            for L in range(2):
                sp = r.uniform(1.0, 1.3)
                z = ff(x, f'rubberband=tempo={sp:.3f}:pitch={r.choice([0.95, 1.0, 1.04]):.3f}:transients=smooth')
                z = np.tile(z, int(D * SR / len(z)) + 3)
                a = int(r.uniform(0, len(z) / 3))
                z = z[a:a + n]
                far = r.uniform(0, 1)
                y[:len(z)] += lowpass(z, 7000 - 3500 * far) * (1 - 0.5 * far)
        return y / 4, 0.42
    if version == 'A':
        # the clip's own sound, lip-synced while the 看班 picture is on screen, then looped with crossfades
        nat = load(ROOT / 'assets/video/v10_W_recite.mp4')
        body = nat[int(native_offset * SR): int(11.6 * SR)]
        xf = int(0.35 * SR)
        out = body.copy()
        while len(out) < D * SR:
            seg = nat[int(1.0 * SR): int(11.6 * SR)].copy()
            out[-xf:] = out[-xf:] * np.linspace(1, 0, xf) + seg[:xf] * np.linspace(0, 1, xf)
            out = np.concatenate([out, seg[xf:]])
        return out[: int(D * SR)], 0.2
    raise ValueError(version)


MSTYLE = {   # v10c auditions — all unintelligible, all speeding up and stopping dead at the cut
    'M':  dict(),                                                               # 1 现版：60 人乌泱泱
    'M2': dict(layers=6, far=(0.55, 0.95), pitches=(0.88, 0.92, 0.96, 1.0, 1.04, 1.08, 1.12), wet=0.6),  # 2 更挤更糊
    'M3': dict(aligned='gibA', layers=5, spread=0.09),                          # 3 齐读：同一个节奏、一起停顿
    'M4': dict(reverse=True),                                                   # 4 倒着念
    'M5': dict(v1=3.2, pitch_end=1.75),                                         # 5 越来越快也越来越尖
}

def murmur_chorus(D, layers=3, v0=1.0, v1=2.4, gamma=1.35, seed=11, far=(0.35, 0.9),
                  pitches=(0.93, 0.96, 0.98, 1.0, 1.02, 1.04, 1.07), reverse=False, aligned=None, spread=0.09,
                  pitch_end=1.0, wet=0.45):
    """乌泱泱的一屋子人：20 pseudo-text voices x `layers` students, each starting somewhere random in its own
    looped text with its own pace / pitch / distance, all levelled (no one in front). The whole room then
    speeds up together on one smooth tempo curve and stops dead at D, at full speed.
    aligned='gibA': use the phrase-aligned stems instead, everyone from the same place at the same pace (a
    class reading in step, pauses together). reverse: every voice backwards. pitch_end: the pitch is dragged up
    along the same curve (tape fast-forward)."""
    r = np.random.default_rng(seed)
    srcs = sorted((TRY / f'{aligned}_aligned').glob('*.wav')) if aligned else sorted((TRY / 'gib').glob('gib*_*.wav'))
    src_len = D * (v0 + v1) / 2 * 1.25 + 3          # enough input for the accelerating output
    n = int(src_len * SR)
    mix = np.zeros(n)
    cnt = 0
    for p in srcs:
        x = load(p)
        if not aligned:
            s0, s1, _, _ = speech_bounds(x)
            x = x[int(s0 * SR): int(s1 * SR)]
        if reverse:
            x = x[::-1].copy()
        x = x / (np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2)) + 1e-9) * 0.1
        loop = np.tile(np.concatenate([x, np.zeros(int(0.25 * SR))]), int(src_len * 1.3 * SR / len(x)) + 3)
        for L in range(layers):
            sp = 1.0 if aligned else r.uniform(0.92, 1.12)
            pitch = float(r.choice(pitches))
            if aligned:
                seg = np.concatenate([np.zeros(int(r.uniform(0, spread) * SR)), loop])[: n + SR]
            else:
                a = int(r.uniform(0, len(x)))
                seg = loop[a: a + int(n * sp) + SR]
            z = ff(seg, f'rubberband=tempo={sp:.4f}:pitch={pitch:.3f}:transients=smooth:formant=preserved')[:n]
            fr_ = r.uniform(*far)
            z = lowpass(z, 7200 - 3800 * fr_) * (1.0 - 0.3 * fr_) * r.uniform(0.92, 1.0)
            mix[:len(z)] += z
            cnt += 1
    mix /= cnt ** 0.5
    # one smooth accelerating time map for the whole room (rubberband tempo driven by asendcmd, in input time)
    cmds, s, t = [], 0.0, 0.0
    while t < D + 0.5 and s < src_len - 0.2:
        u = min(1.0, t / D) ** gamma
        sp = v0 + (v1 - v0) * u
        c = f'{s:.2f} rubberband tempo {sp:.4f}'
        if pitch_end != 1.0:
            c += f', rubberband pitch {1.0 + (pitch_end - 1.0) * u:.4f}'
        cmds.append(c)
        s += 0.1; t += 0.1 / sp
    cf = Path(f'/tmp/murmur_cmds_{os.getpid()}.txt'); cf.write_text(';\n'.join(cmds) + ';\n')
    y = ff(mix, f"asendcmd=f={cf},rubberband=tempo={v0}:transients=smooth")
    y = y[: int(D * SR)]
    if len(y) < int(D * SR):
        y = np.concatenate([y, np.zeros(int(D * SR) - len(y))])
    f = int(0.012 * SR); y[-f:] *= np.linspace(1, 0, f)              # dead stop at full speed
    g = 10 ** ((-3.0 + 5.0 * (np.arange(len(y)) / len(y)) ** 1.5) / 20)  # the room gets louder as it runs away
    print('murmur: students', cnt, 'input used', round(s, 1), 's of', round(src_len, 1), '-> out', round(len(y) / SR, 2), 's, end speed', round(sp, 2))
    return y * g
def solo_line():
    return phone(roomed(SOLO, IR_CLASS, 0.12), noise=0.0)

def recite_versions(meta):
    st = stems()
    bnd = meta['bounds']
    vers = {}
    # B: 整齐齐背 (24 students, steady pace, ends together on the paragraph)
    dryB = students(st, layers=3, spread=0.12, seed=2)
    dryB = ff(dryB, 'rubberband=tempo=1.08:transients=smooth')
    vers['背书B_整齐齐背'] = ending(call_chain(dryB))
    # C: 越背越快 (same class, phrase by phrase faster: 1.0x -> 1.75x)
    dryC = students(st, layers=3, spread=0.10, seed=3)
    dryC = tempo_ramp(dryC, bnd, 1.0, 1.75)
    vers['背书C_越背越快'] = ending(call_chain(dryC))
    # E: 身边几个人 (the 4 best-aligned voices, close to the phone, words audible)
    near = {k: st[k] for k in ('c7_autonoe', 'c2_umbriel', 'c5_leda', 'c3_zuben')}
    dryE = students(near, layers=1, spread=0.04, seed=4)
    dryE = ff(dryE, 'rubberband=tempo=1.08:transients=smooth')
    vers['背书E_身边几个人'] = ending(call_chain(dryE, wet=0.25))
    # D: 各背各的 (unaligned voices from random places in the text, a murmuring room) -> cut dead
    raw = [load(v) for v in VOICES]
    n = int(22 * SR)
    dryD = np.zeros(n)
    r = np.random.default_rng(7)
    for vi, x in enumerate(raw):
        for L in range(2):
            sp = r.uniform(1.0, 1.3)
            z = ff(x, f'rubberband=tempo={sp:.3f}:pitch={r.choice([0.95, 1.0, 1.04]):.3f}:transients=smooth')
            z = np.tile(z, 3)
            a = int(r.uniform(0, len(z) / 3))
            z = z[a:a + n]
            far = r.uniform(0, 1)
            dryD[:len(z)] += lowpass(z, 7000 - 3500 * far) * (1 - 0.5 * far)
    dryD /= 4
    vers['背书D_各背各的'] = ending(call_chain(dryD), stop_at=20.0)
    # A: 视频原声 (the class in the clip, lip-synced; words are unintelligible "almost classical")
    nat = load(ROOT / 'assets/video/v10_W_recite.mp4')
    nat = nat[int(0.6 * SR):]
    vers['背书A_视频原声'] = ending(phone(roomed(nat, IR_CLASS, 0.2)), stop_at=11.2)
    out = []
    for k, y in vers.items():
        y = norm_rms(y, -19)
        out.append(save(y, f'{k}.mp3'))
        print(k, round(len(y) / SR, 2), 's')
    return out

# ------------------------------------------------------------------ ringtone versions (as heard on 看班)
IR_FAR = room_ir(0.09, 0.9, seed=3)
def cctv(x, wet=0.45, lo=200, hi=5200, drive=1.6):
    y = roomed(x, IR_FAR, wet)
    y = band(y, lo, hi)
    return np.tanh(y * drive) / np.tanh(drive)

RING_LEN = 7.6   # the call rings this long in the film before he "answers"
def ring_versions():
    srcs = {
        '铃声1_经典电子铃': (TRY / 'ring1_pocket_cctv.mp3', 0.0, 1900),
        '铃声2_马林巴旋律': (TRY / 'ring3_marimba_muffled.mp3', 0.0, 1700),
        '铃声3_铃声音乐': (TRY / 'ring4_music_raw.mp3', 3.0, 1500),
        '铃声4_只有振动': (TRY / 'ring2_vibrate.mp3', 0.0, 900),
    }
    out = []
    for name, (p, off, fc) in srcs.items():
        x = load(p)[int(off * SR):]
        x = x[: int(RING_LEN * SR)]
        if len(x) < RING_LEN * SR:
            x = np.concatenate([x, np.zeros(int(RING_LEN * SR) - len(x))])
        f = int(0.03 * SR); x[-int(0.004 * SR):] *= 0      # answered: stops dead
        x[:f] *= np.linspace(0, 1, f)
        pocket = lowpass(x, fc, order=3)                     # inside a trouser pocket
        pre, post = np.zeros(int(1.0 * SR)), np.zeros(int(1.4 * SR))
        dry = np.concatenate([pre, pocket, post])
        y = cctv(dry * 0.5)
        hiss = band(rng.normal(0, 1, len(y)), 300, 6500) * 0.012 + np.sin(2 * np.pi * 100 * np.arange(len(y)) / SR) * 0.004
        y = y / np.sqrt(np.mean(y[int(1.0 * SR): int((1.0 + RING_LEN) * SR)] ** 2)) * 0.05 + hiss
        y = norm_rms(y, -24)
        out.append(save(y, f'{name}.mp3'))
        print(name, round(len(y) / SR, 2), 's')
    return out

if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if what == 'gibalign':
        for v, (name, ref) in GIB_SET.items():
            use_set(name, ref); print('==', name, 'ref', ref); align_all()
        sys.exit(0)
    if what == 'gib':
        D = float(sys.argv[2]) if len(sys.argv) > 2 else 24.0
        for v, (name, ref) in GIB_SET.items():
            y, wet, m = gib_chorus(v, D)
            y = np.concatenate([y, np.zeros(int(1.2 * SR))])
            y = phone(roomed(y, IR_CLASS, wet))
            print(save(norm_rms(y, -19), f'背书{v}_{"乱码齐背" if v == "G" else "乱码藏词"}.mp3'), round(len(y) / SR, 2), 's',
                  'mouth frames', len(m), 'mean open', round(float(m.mean()), 2))
        sys.exit(0)
    if what in ('all', 'align'):
        meta = align_all()
    else:
        meta = json.load(open(ALN / 'meta.json'))
    if what in ('all', 'recite'):
        recite_versions(meta)
    if what in ('all', 'ring'):
        ring_versions()
