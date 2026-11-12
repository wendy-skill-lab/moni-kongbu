"""iPhone / 微信界面音：和《宝宝一直在笑》成片逐采样一致的按键声、触屏点击、收消息“叮”等。
发送消息只有按“发送”键那一下按键声，不加任何“嗖”之类的发送音（用户 11-12 明确要求不要）。

音效库在 assets/audio/ui/（脚手架会从技能 templates/audio/ui/ 复制过去）。库里的波形已经按宝宝成片的绝对电平做好：
混音时在“电平锚定之后、限幅之前”直接加进去，成片里就和宝宝那条一样响（编码只有安全限幅，不做响度归一）。

    key_click.wav   拼音键盘按键（每个字母一下、每次选词上屏一下、按“发送”一下）  成片峰值约 -11 dBFS
    touch_tap.wav   手指点按屏幕（进出页面、点横幅、点语音条、点按钮）              约 -20 dBFS
    msg_ding.wav    微信收到消息（正在这个聊天里，或弹出横幅时）                    约 -13.5 dBFS
    swipe.wav       上滑、切 App 的手指划动
    lock.wav        侧边键锁屏
    faceid_buzz.wav 面容解锁成功的两下轻震

在 soundtrack.py 里：
    import ui_sounds as UI                       # 脚手架已把本文件复制进 src/
    ...                                          # 其他声音混好、mix *= 锚定增益 之后
    mix += UI.bus(F, N, taps=taps, dings=UI.auto_dings(F), swipes=[...], locks=[...])
    ...                                          # 然后再做限幅、写 wav

命令行：
    python3 src/ui_sounds.py demo 试听.wav                     打一句话、发送、对方回复，听一遍
    python3 src/ui_sounds.py check 成片.mp4 [--data src/film_data.json] [--offset 3.5]   （_无提示 版或 soundtrack.wav 用 --offset 0）
        量成片里的按键声：是不是同一个波形（相关系数）、比宝宝那条响还是轻（dB）
"""
from pathlib import Path
import argparse, json, os, subprocess, sys
import numpy as np

SR = 48000
HERE = Path(__file__).resolve().parent
# 宝宝成片的时间偏移：发送键在气泡出现前 0.06 秒，手指点按比画面早 0.02 秒，划动早 0.05 秒
SEND_KEY_LEAD, TAP_LEAD, SWIPE_LEAD, LOCK_LEAD = 0.06, 0.02, 0.05, 0.02


def _lib_dir():
    cands = [os.environ.get('UI_SFX_DIR'), HERE.parent / 'assets' / 'audio' / 'ui', HERE.parent / 'templates' / 'audio' / 'ui']
    for c in cands:
        if c and (Path(c) / 'key_click.wav').exists():
            return Path(c)
    sys.exit('找不到界面音效库（key_click.wav）。把技能的 templates/audio/ui/ 复制到项目 assets/audio/ui/，或设 UI_SFX_DIR')


_cache = {}


def sound(name):
    """读库里的一个音效，返回 float64 立体声数组 (n, 2)（已是成片电平）。"""
    if name not in _cache:
        from scipy.io import wavfile
        sr, y = wavfile.read(_lib_dir() / f'{name}.wav')
        assert sr == SR, f'{name}.wav 采样率应为 {SR}'
        y = y.astype(np.float64)
        _cache[name] = y if y.ndim == 2 else np.stack([y, y], axis=1)   # 一律按立体声用（锁屏、划动是立体声原样）
    return _cache[name]


def typing_events(d):
    """和引擎 draftState 一致的打字排程。d 是 film_data.json 里 drafts 的一项：
    start、send、chunks=[[拼音, 汉字(, 这一段前的停顿秒数)] ...]，可选 rate（固定每键秒数倍率）、hold（打了不发）。
    返回 (按键时间列表, 发送键时间或 None, 气泡出现时间或 None)。"""
    letters, commits, n = [], [], 0.0
    for c in d['chunks']:
        if c[0]:
            for _ in c[0].replace(' ', ''):
                letters.append((n, len(commits)))
                n += 0.105
            n += 0.12
            commits.append(n)
            n += 0.2
        else:
            n += 0.2
            commits.append(n)
            n += 0.14
    pauses = [(c[2] if len(c) > 2 else 0) for c in d['chunks']]
    f = d.get('rate') or (min(1, ((d['send'] - 0.25) - d['start'] - sum(pauses)) / n) if n else 1)
    incl = np.cumsum(pauses) if pauses else []
    keys = [d['start'] + e * f + incl[i] for e, i in letters]
    keys += [d['start'] + e * f + incl[i] for i, e in enumerate(commits)]
    if d.get('hold'):
        return sorted(keys), None, None
    return sorted(keys), d['send'] - SEND_KEY_LEAD, d['send']


def in_chat(F, chat, x0):
    return any(s['type'] == 'chat' and s.get('chat') == chat and s['s'] <= x0 < s['e'] for s in F.get('segments', []))


def auto_dings(F, skip=()):
    """宝宝那条的规则：别人发来的消息，正停在这个聊天里，或者同时弹出了横幅，就“叮”一下。
    skip：要静音的时间段 [(a, b), ...]（比如通话中、黑屏后、故意的死寂）。"""
    out = []
    banners = [b['t'] for b in F.get('banners', [])]
    for chat, ms in F.get('msgs', {}).items():
        for m in ms:
            t = m.get('t', 0)
            if t <= 0 or m.get('who') == 'me' or m.get('kind') in ('time', 'system', 'recall'):
                continue
            if any(a <= t < b for a, b in skip):
                continue
            if in_chat(F, chat, t) or any(abs(bt - t) < 0.05 for bt in banners):
                out.append(t)
    return sorted(set(round(x, 4) for x in out))


def bus(F, N, taps=(), dings=None, swipes=(), locks=(), faceid=None, skip=()):
    """生成整条界面音（立体声，成片电平）。
    taps / swipes / locks：画面上的点按、划动、锁屏时刻；dings：收消息时刻（None 表示用 auto_dings）；
    faceid：[(开始, 结束)]，None 表示读 F['faceid']；skip：整段静音的时间段。
    发送消息只有按“发送”键的按键声，没有发送音。"""
    out = np.zeros((N, 2))

    def put(y, at):
        if any(a <= at < b for a, b in skip):
            return
        a = int(round(at * SR))
        if a < 0:
            y, a = y[-a:], 0
        b = min(N, a + len(y))
        if b > a:
            out[a:b] += y[:b - a]

    key = sound('key_click')
    for d in F.get('drafts', []):
        ks, sk, _ = typing_events(d)
        for k in ks:
            put(key, k)
        if sk is not None:
            put(key, sk)                      # 按“发送”键，和字母键是同一个声音（宝宝原版）
    tp = sound('touch_tap')
    for x in taps:
        put(tp, x - TAP_LEAD)
    dg = sound('msg_ding')
    for x in (auto_dings(F, skip) if dings is None else dings):
        put(dg, x)
    sw = sound('swipe')
    for x in swipes:
        put(sw, x - SWIPE_LEAD)
    lk = sound('lock')
    for x in locks:
        put(lk, x - LOCK_LEAD)
    bz = sound('faceid_buzz')
    for s0, _ in (F.get('faceid', []) if faceid is None else faceid):
        put(bz, s0 + 0.45)
    return out


# ---------------- 命令行 ----------------
def _write(path, y):
    import wave
    y = np.clip(y, -1, 1)
    if y.ndim == 1:
        y = np.stack([y, y], axis=1)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y * 32767).astype('<i2').tobytes())


def demo(out):
    d = dict(chat='a', start=0.4, send=3.2, chunks=[['wo dao le', '我到了'], ['ni ne', '你呢']])
    F = dict(drafts=[d], msgs={'a': [dict(t=3.2, who='me', text='我到了你呢'), dict(t=4.6, who='a', text='刚下车')]},
             segments=[dict(type='chat', chat='a', s=0, e=6)], banners=[])
    N = int(6 * SR)
    floor = np.random.default_rng(0).normal(0, 1, N) * 10 ** (-46 / 20)     # 宝宝那条打字时的底噪
    y = bus(F, N, taps=[0.2]) + floor[:, None]
    _write(out, y)
    print('试听已写出：', out, '（0.2 秒点输入框，0.4–3.1 秒打“我到了你呢”，3.14 秒按发送，4.6 秒对方回复“叮”）')


def check(video, data, offset):
    # 先按立体声解码再取左右平均：ffmpeg 的 -ac 1 会把两个相同声道按 0.707 相加，立体声会虚高 3 dB
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(video), '-vn', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'])
    y = np.frombuffer(raw, np.float32).astype(np.float64).reshape(-1, 2).mean(axis=1)
    F = json.loads(Path(data).read_text())
    ref = sound('key_click')[:, 0]

    def match(r, t0, w=0.008):
        a = int((t0 + offset) * SR)
        seg = y[max(0, a - int(w * SR)): a + int(w * SR) + len(r)]
        if len(seg) < len(r):
            return 0.0, 0.0
        c = np.correlate(seg, r, 'valid'); k = int(np.argmax(np.abs(c))); s = seg[k:k + len(r)]
        # 扣掉背景底噪：取声音前 30 ms 的能量当底噪，只算按键本身像不像（教室、电流声大的片子相关会被底噪拉低）
        b0 = max(0, a - int(w * SR) - int(0.03 * SR)); bg = y[b0: max(b0, a - int(w * SR))]
        nE = float(np.mean(bg ** 2)) * len(r) if len(bg) else 0.0
        den = np.sqrt(max(float(np.dot(s, s)) - nE, 0.05 * float(np.dot(s, s)))) * np.linalg.norm(r)
        pk = np.max(np.abs(seg[: len(r) + 2 * int(w * SR)]))          # 电平按峰值比，换了波形也量得准
        return (min(1.0, float(np.dot(s, r) / den)) if den else 0.0), float(pk / np.max(np.abs(r)))
    R, G = [], []
    for d in F.get('drafts', []):
        ks, sk, _ = typing_events(d)
        for k in ks + ([sk] if sk is not None else []):
            r, g = match(ref, k); R.append(r); G.append(g)
    ok = True
    if R:
        r, g = float(np.median(R)), float(np.median(G))
        db = 20 * np.log10(max(g, 1e-6))
        same = r >= 0.85
        loud = abs(db) <= 1.5
        ok &= same and loud
        print(f'按键声 {len(R)} 次：和宝宝原版波形相关 {r:.3f}（≥0.85 算同一个声音）{"✓" if same else "✗ 不是同一个按键声"}；'
              f'电平 {db:+.1f} dB（相对宝宝，±1.5 以内）{"✓" if loud else "✗ 偏响" if db > 0 else "✗ 偏轻"}')
    else:
        print('没有打字（drafts 为空）')
    print('发送：只有按“发送”键那一下按键声，不加发送音')
    print('结论：', '和宝宝那条一致' if ok else '有问题，按上面的 ✗ 改')
    return ok


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='iPhone / 微信界面音（宝宝原版按键声、点按、叮等）')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('demo'); p.add_argument('out')
    p = sub.add_parser('check'); p.add_argument('video'); p.add_argument('--data', default=str(HERE / 'film_data.json') if (HERE / 'film_data.json').exists() else 'src/film_data.json'); p.add_argument('--offset', type=float, default=3.5, help='成片开头观看提示的秒数；_无提示 版和 soundtrack.wav 用 0')
    a = ap.parse_args()
    if a.cmd == 'demo':
        demo(a.out)
    else:
        sys.exit(0 if check(a.video, a.data, a.offset) else 1)
