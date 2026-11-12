"""Build film_data.json for 《已就寝》. All times are film seconds (before the 3.5 s advisory card)."""
import json, math
from pathlib import Path
OUT = Path(__file__).with_name('film_data.json')
P = {'me': ['陈默妈妈', 'avatar_mom'], 'wang': ['王老师', 'avatar_wang'], 'school': ['南城一中家校通', 'school_badge'],
     'p1': ['张子轩妈妈', 'avatar_p1'], 'p2': ['李一诺爸爸', 'avatar_p2'], 'p3': ['刘思雨妈妈', 'avatar_p3'], 'p4': ['赵晨阳妈妈', 'avatar_p4'],
     'p5': ['王浩然妈妈', 'avatar_p5'], 'p6': ['陈雨桐爸爸', 'avatar_p6'], 'p7': ['孙一鸣妈妈', 'avatar_p7'], 'p8': ['周佳怡妈妈', 'avatar_p8'],
     'chenmo': ['陈默', 'avatar_chenmo'],
     'p9': ['林子墨妈妈', 'avatar_p9'], 'p10': ['黄梓涵妈妈', 'avatar_p10'], 'p11': ['吴俊杰爸爸', 'avatar_p11'], 'p12': ['郑欣怡妈妈', 'avatar_p12'],
     'p13': ['何宇航妈妈', 'avatar_p13'], 'p14': ['马诗琪妈妈', 'avatar_p14'], 'p15': ['胡嘉豪爸爸', 'avatar_p15'], 'p16': ['郭雨萱妈妈', 'avatar_p16'],
     'p17': ['罗文博妈妈', 'avatar_p17'], 'p18': ['高思彤妈妈', 'avatar_p18'], 'p19': ['梁子豪妈妈', 'avatar_p19'], 'p20': ['宋可欣爸爸', 'avatar_p20']}
seg, drafts, kbd, typing, faceid, taps, atpick = [], [], [], [], [], [], []
msgs = {'wang': [], 'grp': [], 'chenmo': []}
svc = []
live, over, counts, zooms = [], [], [], []
det = []
sleeps, locks_t = [], []
PACE = 0.72          # typing speed factor (1 = 0.105 s per pinyin letter)
CN_FRAMES = 384
CLIP_N = {'v9c0': 243, 'v9cA': 192, 'v9cB': 243, 'v10cW': 289}
NOISE_K = 1.0  # 引擎动态噪点层的倍率。实拍素材过了 scripts/cctv_look.py 之后改成 0.6，免得噪点叠两遍（实拍质感.md 第 7 节）
PLUS, BANNERS, SOUND, CAMS = [], [], [[0, 0]], [[0, 1]]
SHEET = FLOAT = None
def S(s, e, typ, **kw):
    seg.append(dict(s=round(s, 3), e=round(e, 3), type=typ, **kw))
def M(chat, t, who, text=None, **kw):
    m = dict(t=round(t, 3), who=who, **kw)
    if text is not None:
        m['text'] = text
    msgs[chat].append(m)
def TL(chat, t, label=None):
    msgs[chat].append(dict(t=round(t, 3), kind='time', **({'label': label} if label else {})))
def TAP(t, what):
    taps.append(dict(t=round(t, 3), what=what))
def nat(chunks):
    n, ev = 0.0, []
    for c in chunks:
        if c[0]:
            n += len(c[0].replace(' ', '')) * 0.105 + 0.12
            ev.append(n)
            n += 0.2
        else:
            n += 0.2
            ev.append(n)
            n += 0.14
    return n, ev
def commit_times(d):
    """Mirror of draftState() in kb_part.js: the time each chunk is committed."""
    n, ev = nat(d['chunks'])
    tot = sum((c[2] if len(c) > 2 else 0) for c in d['chunks'])
    f = min(1, ((d['send'] - 0.25) - d['start'] - tot) / n)
    out, acc = [], 0
    for c, e in zip(d['chunks'], ev):
        acc += (c[2] if len(c) > 2 else 0)
        out.append(d['start'] + e * f + acc)
    return out
def ME(chat, t, chunks):
    n, _ = nat(chunks)
    tot = sum((c[2] if len(c) > 2 else 0) for c in chunks)
    send = t + 0.25 + n * PACE + tot
    d = dict(chat=chat, start=round(t, 3), send=round(send, 3), chunks=chunks)
    drafts.append(d)
    M(chat, send, 'me', ''.join(c[1] for c in chunks))
    kbd.append(dict(chat=chat, s=round(t - 0.35, 3), e=round(send + 0.5, 3)))
    return send
def HIM(chat, t, text, think=1.2, **kw):
    if chat == 'wang':
        typing.append(dict(chat=chat, s=round(t, 3), e=round(t + think, 3)))
    M(chat, t + think, 'wang', text, **kw)
    return t + think
def SVC(t, title, intro, fields, label=None):
    svc.append(dict(t=round(t - 0.001, 3), kind='time', **({'label': label} if label else {})))
    svc.append(dict(t=round(t, 3), kind='tpl', who='school', title=title, intro=intro, fields=fields))
CHAT = lambda c: {'type': 'chat', 'chat': c}
LIST = {'type': 'list'}
SV = {'type': 'svc'}
KB = {'type': 'kb', 'mode': 'live'}
def hms(x):
    return '%02d:%02d:%02d' % (x // 3600 % 24, x // 60 % 60, x % 60)
def sec(h, m, s):
    return h * 3600 + m * 60 + s
clocks = []
def clock_sec(t):
    c = clocks[0]
    for x in clocks:
        if t >= x[0]:
            c = x
    return c[1] * 3600 + c[2] * 60 + c[3] + math.floor(t - c[0])
def open_kb(t, frm):
    """Mini program slides up from `frm`; returns (end of slide, time the live picture is up)."""
    S(t, t + 0.42, 'mpOpen', **{'from': frm, 'to': KB})
    over.append(dict(s=round(t, 3), e=round(t + 0.9, 3), kind='connect'))
    return t + 0.42, t + 0.9
def close_kb(t, to):
    TAP(t, 'capsule')
    S(t + 0.12, t + 0.52, 'mpClose', **{'from': KB, 'to': to})
    return t + 0.52
def to_list_from_chat(t, c):
    S(t, t + 0.35, 'pop', **{'from': CHAT(c), 'to': LIST})
    return t + 0.35
def list_tap(t, name, to, hold=0.55):
    S(t, t + hold, 'list', tapRow=[round(t + hold - 0.18, 3), name])
    S(t + hold, t + hold + 0.35, 'push', **{'from': LIST, 'to': to})
    return t + hold + 0.35
def list_pull(t):
    pull, ptap = t + 0.25, t + 1.0
    S(t, ptap + 0.15, 'list', pull=round(pull, 3), pullTap=round(ptap, 3))
    return ptap + 0.15, {'type': 'list', 'pull': round(pull, 3), 'pullTap': round(ptap, 3)}
def buffer(t, img, dur=1.2, ir=False):
    over.append(dict(s=round(t, 3), e=round(t + dur, 3), kind='buffer', img=img, ts=None, ir=ir))
    return t + dur

# ---------- history ----------
TL('chenmo', -150500, '星期日 18:40')
M('chenmo', -150499, 'chenmo', '妈 我到学校了', when='星期日')
M('chenmo', -150498, 'me', '好 降温了 晚上多穿点', when='星期日')
M('chenmo', -150497, 'chenmo', '嗯', when='星期日')
SVC(-90000, '返校提醒', '您好，您的孩子已返校。', [['学生', '陈默'], ['班级', '高一(7)班'], ['返校时间', '2026-11-08 18:42'], ['校门', '东门']], label='昨天 18:42')
SVC(-80000, '就寝提醒', '您好，您的孩子已就寝。', [['学生', '陈默'], ['宿舍床位', '3号楼 412室 2号床'], ['状态', '已就寝'], ['查寝时间', '2026-11-08 22:05']], label='昨天 22:05')
TL('wang', -500000, '11月3日 20:41')
M('wang', -499999, 'me', '王老师 陈默这次月考数学怎么又退步了', when='11月3日')
M('wang', -499998, 'wang', '这次题难 他最近上课状态不太好 老犯困 您在家多留意下', when='11月3日')
M('wang', -499997, 'me', '好的 谢谢王老师', when='11月3日')
TL('grp', -9100, '19:02')
M('grp', -9099, 'wang', '@所有人 本周晚自习看班照常开放（19:00—22:30），家长可在“南城一中家校通”里查看，请勿截图、录屏外传', when='19:02')
for i, (w, x) in enumerate([('p1', '收到'), ('p2', '收到 辛苦王老师'), ('p3', '收到'), ('p4', '收到')]):
    M('grp', -9098 + i, w, x, when='19:03')

# ---------- 1. 21:14 the classroom-state push ----------
clocks.append([-300, 21, 9, 4])          # t=0 -> 21:14:04
live.append({'s': 0, 'kind': 'clip', 'clip': 'v9c0', 'from': 0})
counts.append([0, '46 / 应到 46'])
SVC(0.3, '课堂状态提醒', '您好，系统检测到孩子在晚自习期间趴桌。', [['学生', '陈默'], ['班级', '高一(7)班'], ['时段', '晚自习第二节'], ['时长', '已超过 10 分钟']])
lock1 = dict(notifs=[dict(app='wechat', who='school', title='南城一中家校通', body='[课堂状态提醒] 陈默 晚自习趴桌', when='现在')], newAt=0.3, tapAt=1.45)
S(0, 1.55, 'lock', **lock1)
locks_t.append(0.0)
faceid.append([1.0, 1.55])
S(1.55, 1.95, 'notifOpen', to=SV)
S(1.95, 3.25, 'svc')
TAP(3.05, 'card')
t, up = open_kb(3.25, SV)
zooms.append(dict(s=4.9, e=8.9, z=2.4, fx=0.80, fy=0.46))
S(t, 9.3, 'kb', mode='live')
t = close_kb(9.3, SV)
S(9.3, 9.42, 'kb', mode='live')
S(t, t + 0.3, 'svc'); t += 0.3
S(t, t + 0.35, 'pop', **{'from': SV, 'to': LIST}); t += 0.35
t = list_tap(t, '王老师', CHAT('wang'))
chat_s = t
TL('wang', t + 0.1)
a = ME('wang', t + 0.3, [['w l s', '王老师'], ['', ' '], ['chen mo', '陈默'], ['you', '又'], ['pa zhe', '趴着'], ['shui jiao', '睡觉']])
a = ME('wang', a + 0.3, [['ma fan nin', '麻烦您'], ['ba ta', '把他'], ['zhuai qi lai', '拽起来'], ['', ' '], ['bu xing', '不行'], ['jiu rang ta', '就让他'], ['qu hou mian', '去后面'], ['zhan zhe', '站着']])
reply1 = HIM('wang', a + 0.6, '好的陈默妈妈 我去看看', think=1.3)
# ---------- 2. she taps his shoulder; he walks to the corner; she leaves by the back door -> lock ----------
t = reply1 + 0.9
S(chat_s, t, 'chat', chat='wang')
t = to_list_from_chat(t, 'wang')
t, frm = list_pull(t)
t, up = open_kb(t, frm)
cA_s = up - 0.8
live.append({'s': round(cA_s, 3), 'kind': 'clip', 'clip': 'v9cA', 'from': 0})
cB_s = cA_s + 192 / 24
live.append({'s': round(cB_s, 3), 'kind': 'clip', 'clip': 'v9cB', 'from': 0})
zooms.append(dict(s=round(cA_s + 4.6, 3), e=round(cB_s + 6.2, 3), z=2.2, fx=0.79, fy=0.45))
side1 = cB_s + 240 / 24             # the frame she is in the back doorway
S(t, side1, 'kb', mode='live')
S(side1, side1 + 0.16, 'sleep', **{'from': KB})
sleeps.append(side1)
black1 = side1 + 0.16
P3 = black1 + 1.3
S(black1, P3, 'black')
# ---------- 3. 22:12 not in bed ----------
clocks.append([round(P3, 3), 22, 12, 3])
live.append({'s': round(P3, 3), 'kind': 'still', 'src': 'v9N1', 'ir': True})
counts.append([round(P3, 3), '1'])
SVC(P3 + 0.35, '未就寝提醒', '您好，您的孩子今晚查寝未到。', [['学生', '陈默'], ['宿舍床位', '3号楼 412室 2号床'], ['状态', {'hl': True, 'v': '未就寝'}], ['查寝时间', '2026-11-09 22:10']])
lock3 = dict(notifs=[dict(app='wechat', who='school', title='南城一中家校通', body='[未就寝提醒] 陈默 22:10查寝未到', when='现在')], wake=round(P3, 3), newAt=round(P3 + 0.35, 3), tapAt=round(P3 + 2.0, 3))
S(P3, P3 + 2.1, 'lock', **lock3)
locks_t.append(P3)
faceid.append([round(P3 + 1.5, 3), round(P3 + 2.1, 3)])
t = P3 + 2.1
S(t, t + 0.4, 'notifOpen', to=SV); t += 0.4
S(t, t + 2.1, 'svc'); t += 2.1
S(t, t + 0.35, 'pop', **{'from': SV, 'to': LIST}); t += 0.35
t = list_tap(t, '高一(7)班家长群', CHAT('grp'))
grp_s = t
TL('grp', t + 0.1)
d0 = len(drafts)
a = ME('grp', t + 0.3, [['', '@'], ['', '王老师 ', 1.7], ['gong zhong hao', '公众号'], ['ti xing', '提醒'], ['chen mo', '陈默'], ['mei', '没'], ['jiu qin', '就寝'], ['', ' '], ['ta', '他'], ['hui su she le ma', '回宿舍了吗']])
ct = commit_times(drafts[d0])
atpick.append(dict(chat='grp', s=round(ct[0] + 0.08, 3), e=round(ct[1] - 0.06, 3), tapAt=round(ct[1] - 0.4, 3)))
reply3 = HIM('grp', a + 0.6, '@陈默妈妈 晚自习结束都已经回去了呀', think=1.9, atMe=True)
t = reply3 + 1.4
S(grp_s, t, 'chat', chat='grp')
# ---------- 4. 22:14 he is still in the corner ----------
t = to_list_from_chat(t, 'grp')
t, frm = list_pull(t)
t, up = open_kb(t, frm)
zooms.append(dict(s=round(up + 0.9, 3), e=round(up + 4.6, 3), z=2.6, fx=0.81, fy=0.45))
leave = up + 5.0
S(t, leave, 'kb', mode='live')
t = close_kb(leave, LIST)
S(leave, leave + 0.12, 'kb', mode='live')
t = list_tap(t, '王老师', CHAT('wang'))
chat_s = t
clocks.append([round(chat_s - 0.2, 3), 22, 14, 6])
TL('wang', t + 0.1)
a = ME('wang', t + 0.3, [['w l s', '王老师'], ['', ' '], ['ta hai zai', '他还在'], ['jiao shi', '教室'], ['', ' '], ['zui li mian', '最里面'], ['na ge', '那个'], ['qiang jiao', '墙角'], ['zhan zhe ne', '站着呢']])
r = HIM('wang', a + 0.8, '没有啊 宿管说他刚回去 已经躺下了', think=1.8)
# ---------- 5. a message from 陈默 -> video call -> minimise ----------
bn = r + 1.7
tapb = bn + 1.8
BANNERS.append(dict(t=round(bn, 3), app='wechat', who='chenmo', title='陈默', body='妈，我洗漱完上床了，别管了', tap=round(tapb, 3)))
TL('chenmo', bn - 0.01)
M('chenmo', bn, 'chenmo', '妈，我洗漱完上床了，别管了')
S(chat_s, tapb + 0.12, 'chat', chat='wang')
S(tapb + 0.12, tapb + 0.47, 'push', **{'from': CHAT('wang'), 'to': CHAT('chenmo')})
cm_s = tapb + 0.47
a = ME('chenmo', cm_s + 1.0, [['ni', '你'], ['bie', '别'], ['pian ma', '骗妈'], ['', '，'], ['shei', '谁'], ['qi fu ni le', '欺负你了'], ['', '？']])
tp = a + 1.0
TAP(tp, 'plusBtn')
pl_s = tp + 0.07
sh_s = pl_s + 1.0
sh_e = sh_s + 1.0
PLUS.append(dict(chat='chenmo', s=round(pl_s, 3), e=round(sh_e, 3), tapItem='video', tapAt=round(sh_s - 0.05, 3)))
SHEET = dict(chat='chenmo', s=round(sh_s, 3), e=round(sh_e, 3), tapAt=round(sh_e - 0.1, 3), pick='video')
S(cm_s, sh_e, 'chat', chat='chenmo')
vc_s = sh_e + 0.32
vc_e = vc_s + 3.1
S(sh_e, vc_s, 'vcallIn', chat='chenmo')
S(vc_s, vc_e, 'vcall')
TAP(vc_e - 0.12, 'vmin')
S(vc_e, vc_e + 0.4, 'vcallMin', chat='chenmo')
t = vc_e + 0.4 + 0.45
S(vc_e + 0.4, t, 'chat', chat='chenmo')
# ---------- 6. the phone in his pocket ----------
t = to_list_from_chat(t, 'chenmo')
t, frm = list_pull(t)
kb_open = t
t, up = open_kb(t, frm)
snd = up + 1.9
TAP(snd, 'sound')
SOUND.append([round(snd, 3), 1])
cn = snd + 7.6                       # the call is answered
live.append({'s': round(vc_s, 3), 'kind': 'still', 'src': 'v9N1', 'ir': True,
             'pulse': dict(src='v9N1p', s=round(vc_s, 3), period=2.0, on=[0.05, 0.46], lo=0.22, hi=1.0, steady=round(cn, 3), hold=0.85)})
leave = cn + 2.3
zooms.append(dict(s=round(up + 0.7, 3), e=round(leave + 0.3, 3), z=2.6, fx=0.81, fy=0.45))
S(t, leave, 'kb', mode='live')
t = close_kb(leave, LIST)
S(leave, leave + 0.12, 'kb', mode='live')
t = list_tap(t, '陈默', CHAT('chenmo'))
c2 = t
live.append({'s': round(c2 + 0.5, 3), 'kind': 'still', 'src': 'v9W', 'ir': True})
counts.append([round(c2 + 0.5, 3), '46 / 应到 46'])
a = ME('chenmo', t + 0.45, [['chen mo', '陈默'], ['', ' '], ['ni', '你'], ['zen me le', '怎么了']])
a = ME('chenmo', a + 0.4, [['ni', '你'], ['zen me', '怎么'], ['bu shuo hua', '不说话']])
t = a + 1.5
S(c2, t, 'chat', chat='chenmo')
# ---------- 7. the whole class is back in their seats; reciting through the call ----------
t = to_list_from_chat(t, 'chenmo')
t, frm = list_pull(t)
t, up2 = open_kb(t, frm)
live.append({'s': round(up2, 3), 'kind': 'clip', 'clip': 'v10cW', 'from': 0, 'ir': True})   # plays from the moment the picture is up
rec_s = up2 + 0.5
bell = up2 + 6.2
BELL_DUR = 4.2
zooms.append(dict(s=round(up2 + 2.8, 3), e=round(up2 + 11.3, 3), z=2.2, fx=0.90, fy=0.80))   # v10b: front-right block by the window, the biggest faces
leave = up2 + 11.0
S(t, leave, 'kb', mode='live')
t = close_kb(leave, LIST)
S(leave, leave + 0.12, 'kb', mode='live')
# ---------- 8. 家长群: 今晚全班已就寝 -> 20 x 收到 -> the 21st ----------
gm = t + 0.6
S(t, gm + 0.9, 'list')
TL('grp', gm - 0.01)
M('grp', gm, 'wang', '各位家长 今晚全班已就寝 大家早点休息')
t = list_tap(gm + 0.9, '高一(7)班家长群', CHAT('grp'), hold=0.6)
g_s = t
x = g_s + 0.6
replies = [('p1', '收到'), ('p2', '收到 辛苦王老师'), ('p5', '好的 收到'), ('p3', '收到'), ('p9', '收到'), ('p6', '收到 谢谢王老师'),
           ('p11', '收到'), ('p4', '收到'), ('p13', '好的 收到'), ('p7', '收到'), ('p15', '收到 辛苦王老师'), ('p8', '收到'),
           ('p10', '收到'), ('p17', '收到'), ('p12', '收到 谢谢王老师'), ('p19', '收到'), ('p14', '收到'), ('p20', '好的 收到'),
           ('p16', '收到'), ('p18', '收到')]
rep_t = []
for i, (w, txt) in enumerate(replies):
    M('grp', x, w, txt)
    rep_t.append(round(x, 3))
    x += max(0.13, 0.55 * (0.86 ** i))
bn2 = rep_t[-1] + 1.15              # the last 收到 settles ... then 陈默
tapb2 = bn2 + 1.9
BANNERS.append(dict(t=round(bn2, 3), app='wechat', who='chenmo', title='陈默', body='妈，我说话了，你听，我在背书。', tap=round(tapb2, 3)))
M('chenmo', bn2, 'chenmo', '妈，我说话了，你听，我在背书。')
S(g_s, tapb2 + 0.12, 'chat', chat='grp')
S(tapb2 + 0.12, tapb2 + 0.47, 'push', **{'from': CHAT('grp'), 'to': CHAT('chenmo')})
cm2 = tapb2 + 0.47
cut = cm2 + 2.0                      # the room runs away, faster and faster ... and stops dead with the picture
black = cut
S(cm2, black, 'chat', chat='chenmo')
card = black + 1.6
duration = round(card + 3.4, 2)
FLOAT = dict(s=round(vc_e + 0.25, 3), connect=round(cn, 3), e=round(black, 3), video=True)
FLOAT['drag'] = round(up2 - 0.65, 3); FLOAT['dragY'] = 380
# ---------- AI 抬头率 boxes ----------
ORANGE, GREEN = '#ff9f0a', '#34e27a'
det.append(dict(s=0, e=round(cB_s + 0.5, 3), col=ORANGE, since=clock_sec(0) - 624, jit=0.05,
                boxes=[[0.818, 0.474, 0.040, 0.050, '陈默 · 持续低头 {dur}']]))
det.append(dict(s=round(P3, 3), e=round(c2 + 0.5, 3), col=ORANGE, since=sec(21, 14, 48), jit=0.05,
                boxes=[[0.819, 0.357, 0.026, 0.042, '陈默 · 持续低头 {dur}']]))
_trk = Path(__file__).parent.parent / 'assets/stills/v9/W_tracks.json'   # from scripts/track_faces.py
W_TRK = json.load(open(_trk)) if _trk.exists() else {'n': 1, 'tracks': []}
det.append(dict(s=round(up2, 3), e=round(black + 1, 3), col=GREEN, stagger=0.03, trk='W', t0=round(up2, 3), rate=1,
                lab='抬头 {sc}', boxes=[]))
counts.append([round(up2 + 0.03 * len(W_TRK['tracks']) + 0.2, 3), '46 / 应到 46 · 抬头率 100%'])
counts.sort(key=lambda c: c[0])
R = {}
# ---------- checks / fix-ups ----------
seg.sort(key=lambda s: (s['s'], s['e']))
seg[:] = [s for s in seg if s['e'] - s['s'] > 0.001]
for a_, b_ in zip(seg, seg[1:]):
    if a_['e'] > b_['s']:
        a_['e'] = b_['s']
seg[:] = [s for s in seg if s['e'] - s['s'] > 0.001]
for a_, b_ in zip(seg, seg[1:]):
    assert abs(a_['e'] - b_['s']) < 0.02, ('gap/overlap', a_['type'], a_['s'], a_['e'], b_['type'], b_['s'])
for k in kbd:   # keyboard must be down before she leaves the chat
    nxt = [s for s in seg if s['type'] in ('pop', 'push') and s['s'] >= k['s']]
    if nxt:
        assert k['e'] <= nxt[0]['s'] + 0.01, ('keyboard still up when leaving', k, nxt[0]['s'])
live.sort(key=lambda e: e['s'])
r3 = lambda d: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in d.items()}
F = dict(
    duration=duration, blackAt=round(black, 3), cardAt=round(card, 3), clocks=clocks, dates=[[-1e9, '11月9日 星期一']], people=P,
    chats={'wang': dict(title='王老师', readUntil=-499990), 'grp': dict(title='高一(7)班家长群(96)', readUntil=-9000), 'school': dict(title='南城一中家校通', readUntil=-79990), 'chenmo': dict(title='陈默', readUntil=-150000)},
    msgs=msgs, svc=svc, drafts=drafts, keyboard=kbd, typing=typing, scroll=[], plus=PLUS, sheet=SHEET, segments=seg, banners=BANNERS, faceid=faceid, float=FLOAT, vcall=dict(who='chenmo'), sound=SOUND, cams=CAMS, greenDot=1e9,
    taps=taps, atPick=atpick, call=dict(connect=1e9, end=0),
    kb=dict(noise=NOISE_K, live=[r3(x) for x in live], over=[r3(x) for x in over], counts=counts, zooms=[r3(z) for z in zooms], det=det, clips=CLIP_N, replay=R, tracks={'W': W_TRK}),
    listStatic=[dict(name='锦绣花园3期业主群', icon='grid', preview='[12条] 物业：6栋电梯明天上午检修', time='20:46', muted=True, k=-1000),
                dict(name='订阅号消息', icon='sub', preview='南城教育发布：关于做好冬季校园安全工作的通知', time='19:30', k=-8000),
                dict(name='妈', av='avatar_ma', preview='降温了 让默默多带件外套', time='星期日', k=-150000),
                dict(name='文件传输助手', icon='ft', preview='[文件] 高一期中考试安排.pdf', time='星期五', k=-300000)],
    decoys={}, idleCandidates=['的', '我', '了', '是', '不', '在', '你'],
    sfx=dict(sleep=sleeps, locks=[0.0, side1, P3], lockNotifs=[0.3, P3 + 0.35], black=black,
             callIn=sh_e, callScreen=[vc_s, vc_e], minimise=vc_e, kbOpen=kb_open, up=up, soundOn=snd, ringStart=vc_s, connect=cn,
             recite=[rec_s, cut], bell=bell, bellDur=BELL_DUR, banner=bn, bannerTap=tapb, groupMsg=gm, replies=rep_t,
             banner2=bn2, banner2Tap=tapb2, chenmoChat=cm2, stutters=[], inApp=[bn, gm, bn2])
)
for d in drafts:
    for c in d['chunks']:
        py, txt = c[0], c[1]
        if py and txt not in F['decoys']:
            F['decoys'][txt] = [txt] + ([txt[:2]] if len(txt) > 2 else []) + [txt[0]] + [x for x in ['的', '了', '吗'] if x != txt][:2]
OUT.write_text(json.dumps(F, ensure_ascii=False, indent=1))
r = lambda x: round(x, 2)
print('duration', duration, '(+3.5 card =', r(duration + 3.5), ')')
print('reply1', r(reply1), 'cA', r(cA_s), 'cB', r(cB_s), 'side1', r(side1), 'P3', r(P3), 'reply3', r(reply3))
print('banner', r(bn), 'call', r(vc_s), 'kb', r(up), 'sound', r(snd), 'connect', r(cn), 'W', r(c2 + 0.5), 'kb2', r(up2), 'bell', r(bell), 'group', r(g_s), 'banner2', r(bn2), 'cut', r(cut), 'black', r(black))
print('clock at 0:', hms(clock_sec(0)), 'side1:', hms(clock_sec(side1)), 'P3:', hms(clock_sec(P3)), 'connect:', hms(clock_sec(cn)), 'black:', hms(clock_sec(black)))
