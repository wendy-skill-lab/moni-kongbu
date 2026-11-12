"""Soundtrack for 《已就寝》 v10 (RING / RECITE env select the auditioned versions): diegetic only — her bedroom, the phone UI, one WeChat voice message, her outgoing call,
and (after she taps the 看班 speaker) the classroom through the camera mic: his pocket ringing, the 下课铃, the knocking.
No music, no stingers."""
from pathlib import Path
import json, subprocess, wave
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
F = json.loads((ROOT / 'src' / 'film_data.json').read_text())
A = ROOT / 'assets' / 'audio'
X = F['sfx']
SR = 48000
N = int(F['duration'] * SR)
rng = np.random.default_rng(1109)
import os, importlib.util as _iu
_sp = _iu.spec_from_file_location('make_auditions', ROOT / 'src' / 'make_auditions.py')
MA = _iu.module_from_spec(_sp); _sp.loader.exec_module(MA)
RING = os.environ.get('RING', '2')
RECITE = os.environ.get('RECITE', 'B')
print('RING', RING, 'RECITE', RECITE)
mix = np.zeros((N, 2))
t = np.arange(N) / SR
def load(name, af=None):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(name)] + (['-af', af] if af else []) + ['-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'])
    y = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    return y / max(np.max(np.abs(y)), 1e-9)
def put(y, at, gain=1.0):
    a = int(at * SR)
    if a < 0:
        y, a = y[-a:], 0
    b = min(N, a + len(y))
    if b > a:
        mix[a:b] += y[:b - a] * gain
def mono(x):
    return np.stack([x, x], axis=1)
def band(x, lo, hi):
    out = np.zeros_like(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    for c in range(x.shape[1]):
        S = np.fft.rfft(x[:, c])
        S[(f < lo) | (f > hi)] = 0
        out[:, c] = np.fft.irfft(S, len(x))
    return out
def fade(x, fin=0.01, fout=0.05):
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a)[:, None]
    if b:
        x[-b:] *= np.linspace(1, 0, b)[:, None]
    return x
def loop_to(x, n):
    reps = int(np.ceil(n / len(x))) + 1
    return np.concatenate([x] * reps)[:n]
def segs(kind=None, **kw):
    return [s for s in F['segments'] if (kind is None or s['type'] == kind) and all(s.get(k) == v for k, v in kw.items())]
def env_at(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return np.interp(t, xs, ys)
# ---------- her bedroom at night ----------
room = band(loop_to(load(A / 'home_night.mp3'), N), 40, 7000)
room_env = env_at([(0, 0.13), (X['black'] - 0.01, 0.13), (X['black'], 0.0), (F['duration'], 0.0)])
mix += room * room_env[:, None]
# ---------- phone UI ----------
# 界面音一律用 ui_sounds.py：按键声是《宝宝一直在笑》原版波形，发送只有按键声、不加发送音，电平按宝宝成片做好。
# 这里只收集时刻，等电平锚定之后再整条加进去（见文件末尾），不要在这里自己合成按键声或改它们的音量。
import sys
sys.path.insert(0, str(ROOT / 'src'))
import ui_sounds as UI
taps = [s['s'] for s in F['segments'] if s['type'] in ('push', 'pop')]
taps += [s['tapAt'] for s in segs('lock') if s.get('tapAt') and s['tapAt'] < X['black'] - 0.2]
taps += [x['t'] for x in F['taps']]
taps += [s['tapRow'][0] for s in segs('list') if s.get('tapRow')]
taps += [s['pullTap'] for s in segs('list') if s.get('pullTap')]
taps += [p['tapAt'] for p in F['atPick']]
taps += [w['tapAt'] for w in F['plus'] if w.get('tapAt')]
taps += [F['sheet']['tapAt']] if F.get('sheet') else []
taps += [m['play'][0] for c in F['msgs'].values() for m in c if m.get('kind') == 'voice']
swipes = [s['pull'] for s in segs('list') if s.get('pull')]
# 收消息“叮”：正停在这个聊天里收到的、App 内横幅、锁屏推送；通话接通到黑屏之间不叮（齐背盖住了一切）
quiet = lambda x: X['connect'] <= x < X['black']
dings = [m['t'] for chat in ('wang', 'grp') for m in F['msgs'][chat]
         if m['t'] > 0 and m.get('who') != 'me' and m.get('kind') != 'time' and UI.in_chat(F, chat, m['t']) and not quiet(m['t'])]
dings += [x + 0.05 for x in X['inApp'] if not quiet(x)] + [x + 0.05 for x in X['lockNotifs']]
locks = list(X['sleep'])          # 侧边键锁屏
# ---------- v9: her video call, his pocket, the class reciting through the call ----------
# All original synthesis except the six recitation voices (generated TTS, assets/audio/recite).
def tone(f, dur, decay=None):
    x = np.arange(int(dur * SR)) / SR
    y = np.sin(2 * np.pi * f * x)
    if decay:
        y *= np.exp(-x / decay)
    return y
def room_ir(early, tail, n_ref=14, seed=0):
    r = np.random.default_rng(seed)
    ir = np.zeros(int((early + tail) * SR))
    ir[0] = 1.0
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
def cctv(x, wet_ir, wet=0.35, lo=200, hi=5200, drive=1.6):
    """mono numpy -> stereo through a classroom and a cheap camera mic"""
    y = conv(x, wet_ir) * wet + np.concatenate([x, np.zeros(len(wet_ir) - 1)]) * (1 - wet)
    y = band(mono(y), lo, hi)
    return np.tanh(y * drive) / np.tanh(drive)
IR_FAR = room_ir(0.09, 0.9, seed=3)      # 机位1: front-corner camera; he is at the far back corner
on0, cn, black = X['soundOn'], X['connect'], X['black']
rec0, rec1 = X['recite']
P = [e['pulse'] for e in F['kb']['live'] if e.get('pulse')][0]

# 1) camera audio (only while the 看班 page is on screen): hiss + mains hum; his pocket ringing until the call connects
cls = np.zeros((N, 2))
def cput(y, at, gain=1.0):
    a = int(at * SR)
    b = min(N, a + len(y))
    if b > a:
        cls[a:b] += y[:b - a] * gain
hiss = band(mono(rng.normal(0, 1, N)), 300, 6500) * 0.012 + mono(np.sin(2 * np.pi * 100 * t)) * 0.004
cls += hiss
RING_SRC = {'1': ('ring1_pocket_cctv.mp3', 0.0, 1900), '2': ('ring3_marimba_muffled.mp3', 0.0, 1700),
            '3': ('ring4_music_raw.mp3', 3.0, 1500), '4': ('ring2_vibrate.mp3', 0.0, 900)}
fn, off_s, fc = RING_SRC[RING]
r0 = P['s']
L_ = int((cn - r0 + 1) * SR)
ring_path = MA.TRY / fn
if ring_path.exists():
    src = MA.load(ring_path)[int(off_s * SR):]
else:                                                             # 新项目还没挑铃声：先用合成的占位铃声，正式片换成挑定的版本
    print('缺铃声素材', ring_path, '：先用合成占位铃声，正式片要换成用户挑定的铃声')
    _x = np.arange(int(2.0 * SR)) / SR
    src = (np.sin(2 * np.pi * 880 * _x) + 0.5 * np.sin(2 * np.pi * 1320 * _x)) * (_x < 1.0) * 0.3
if len(src) > 12.5 * SR:
    src = src[: int(12.0 * SR)]
fi, fo = int(0.01 * SR), int(0.03 * SR)
src[:fi] *= np.linspace(0, 1, fi); src[-fo:] *= np.linspace(1, 0, fo)
rt = np.tile(src, L_ // len(src) + 2)[:L_]
rt[int((cn - r0) * SR):] = 0                                      # answered: it stops dead
rt = MA.lowpass(rt, fc, order=3)                                  # inside a trouser pocket
ring = cctv(rt, IR_FAR, wet=0.45)
ring_rms = np.sqrt(np.mean(ring[: int((cn - r0) * SR)] ** 2))
off = int((on0 - r0) * SR)
cput(ring[off:], on0, 0.035 / ring_rms)

# 2) the call itself (narrow-band, from the floating window): fabric rustle after it connects, then the recitation and the bell
def buf():
    return np.zeros((N, 2))
def bput(B, y, at, gain=1.0):
    a = int(at * SR)
    if a < 0:
        y, a = y[-a:], 0
    b = min(N, a + len(y))
    if b > a:
        B[a:b] += y[:b - a] * gain
line, voices, bellc = buf(), buf(), buf()
rs = rng.normal(0, 1, int(1.6 * SR)) * np.exp(-np.linspace(0, 3, int(1.6 * SR)))
bput(line, band(mono(rs), 300, 3400), cn + 0.05, 0.05)           # the phone shifting in the pocket as it picks up
line += band(mono(rng.normal(0, 1, N)), 300, 3400) * 0.006       # line noise for the whole call
D = rec1 - rec0
HAVE_CHORUS = True
try:
    dry, wet = MA.dry_chorus(RECITE, D)
    yv = MA.roomed(dry, MA.IR_CLASS, wet)[: int(D * SR)]
except FileNotFoundError as e:                                    # 新项目还没做背书声部：这一段先留空
    print('缺背书声部素材', e.filename, '：齐背先留空，正式片用 scripts/crowd_recite.py 生成')
    yv = np.zeros(int(D * SR))
    HAVE_CHORUS = False
yv = band(mono(yv), 300, 3400)
yv *= 0.047 / max(np.sqrt(np.mean(yv ** 2)), 1e-9)      # -4.6 dB vs first try: keeps the rest of the film at the v9 level
bput(voices, yv, rec0, 1.0)
recite_env = np.clip((t - rec0) / 0.25, 0, 1) * ((t >= rec0) & (t < rec1))
# 上课铃: old electric school bell, heard through the call AND (if she is on 看班) the camera mic
b0, bd = X['bell'], X['bellDur']
bl = np.zeros(int((bd + 1.5) * SR))
modes = [(1840, 0.05, 1.0), (2610, 0.035, 0.7), (3975, 0.022, 0.45), (5230, 0.015, 0.25)]
hit = sum(g_ * tone(f, 0.12, dec) for f, dec, g_ in modes)
kk = 0.0
while kk < bd:
    a = int(kk * SR)
    gg = 0.85 + 0.15 * rng.random()
    m = min(len(hit), len(bl) - a)
    bl[a:a + m] += hit[:m] * gg
    kk += 1 / 24.0 + rng.normal(0, 0.0015)
bl *= np.minimum(np.arange(len(bl)) / (0.015 * SR), 1)
bell_far = cctv(bl * 0.3, IR_FAR, wet=0.5, lo=300, hi=6000, drive=2.2)
cput(bell_far, b0, 0.025)
bc = band(bell_far, 300, 3400)
bput(bellc, np.tanh(bc * 2.5) / np.tanh(2.5), b0, 0.0195)
room_part = voices * recite_env[:, None] + bellc
room_part[t >= rec1] = 0                                          # the whole class stops at once
call_mix = line * ((t >= cn) & (t < black))[:, None] + room_part
call_mix = np.tanh(call_mix * 1.6) / np.tanh(1.6)                 # VoIP AGC squash
call_mix[t < cn] = 0
# v10b: no single voice at the end — the whole room runs away faster and faster and stops dead with the picture (rec1 == black)
mix += call_mix

# camera audio only while 看班 is on screen
kb_on = np.zeros(N)
for s in segs('kb'):
    kb_on[int(s['s'] * SR): int(s['e'] * SR)] = 1
kb_on[: int(on0 * SR)] = 0
k_ = int(0.03 * SR)
kb_on = np.convolve(kb_on, np.ones(k_) / k_, mode='same')
mix += cls * kb_on[:, None]

# her side: outgoing-call waiting tone (450 Hz, 1 s on / 4 s off) from the call screen until he picks up
x0 = X['callIn'] + 0.25
while x0 < cn - 0.05:
    d = min(1.0, cn - x0)
    y = tone(450, d) * np.minimum(np.arange(int(d * SR)) / (0.01 * SR), 1)
    y = fade(mono(y), 0.01, 0.02)
    put(band(y, 300, 3400), x0, 0.05 if x0 < X['minimise'] else 0.035)
    x0 += 5.0
# ---------- silence at the end ----------
mix[int(black * SR):] = 0
# Level anchor: the recitation (the loudest, most important sound) at about -15 dBFS RMS over its last 8 seconds.
a, b = int((rec1 - 8) * SR), int(rec1 * SR)
vr = np.sqrt(np.mean(mix[a:b] ** 2))
if HAVE_CHORUS:
    mix *= 10 ** (-15 / 20) / vr
else:                                                            # 没有锚点声音时不锚定，免得把底噪放大
    print('缺齐背，跳过电平锚定（正式片补齐素材后会按齐背锚定）')
# 界面音（按键、点按、叮、划动、锁屏、面容震动）按宝宝成片的绝对电平加进来；发送不加发送音
mix += UI.bus(F, N, taps=taps, dings=dings, swipes=swipes, locks=locks, skip=[(black, F['duration'])])
pre_peak = np.max(np.abs(mix))
# peak limiter (5 ms hold, 60 ms release) so nothing clips
lvl = np.max(np.abs(mix), axis=1)
hold = int(0.005 * SR)
env = np.maximum.reduce([np.roll(lvl, -k) for k in range(0, hold, 8)])
gr = np.minimum(1.0, 0.89 / np.maximum(env, 1e-9))
rel = np.exp(-1 / (0.06 * SR))
import scipy.signal as _ss
gr_s = 1 - _ss.lfilter([1 - rel], [1, -rel], 1 - gr)
gr = np.minimum(gr, np.clip(gr_s, 0, 1))
mix *= gr[:, None]
peak = np.max(np.abs(mix))
print('pre-limit peak', round(float(pre_peak), 3), 'max gain reduction dB', round(float(20 * np.log10(gr.min())), 1))
with wave.open(str(ROOT / os.environ.get('OUT', 'soundtrack.wav')), 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
print('Soundtrack complete. Peak', round(float(peak), 3), 'duration', F['duration'], 'taps', len(taps))
