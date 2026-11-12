#!/usr/bin/env python3
"""实拍质感后期：把模型生成的“干净”画面，处理成真设备拍出来、再经过 App 码流的样子。

静帧和视频用同一个预设处理，母版、变体和视频片段之间就不会跳。

用法：
  python3 cctv_look.py 输入.png 输出.jpg --preset cctv_color
  python3 cctv_look.py 输入.png 输出.jpg --preset cctv_color --night            # 关灯后硬撑彩色：增益拉高、噪点重、颜色发灰
  python3 cctv_look.py 输入.mp4 输出.mp4 --preset cctv_ir --fps 15            # 视频：逐帧处理 + 掉到 15 fps + 低码率重编码
  python3 cctv_look.py 输入.png 输出.jpg --preset cctv_ir --osd "2026-11-12 星期四 23:18:06" --channel "橱窗内侧"
  python3 cctv_look.py 输入.png --report                                      # 只做画质体检，不输出图片
  python3 cctv_look.py 输入.png 输出.jpg --preset cctv_ir --no-distort          # 原图已经有广角畸变时，不再叠加

噪点按“目标值”补差额：先量原图在码流分辨率下已有多少噪点，只补不够的部分（至少补 35%，视频才会有逐帧跳动的噪点）。

预设（--list 查看全部参数）：
  cctv_color   店铺 / 商场 / 教室 / 楼道的彩色枪机、半球（海康、大华这一类）
  cctv_ir      同一台机器熄灯后自动切到的黑白红外
  homecam      家用云台摄像头白天（更广角、标清码流、颜色偏淡）
  homecam_ir   家用云台摄像头夜视（中心亮四周暗，近处发白）
  babycam_ir   婴儿看护器夜视（比家用更糊、更暗，轻微偏绿）
  doorbell     门铃 / 猫眼（强鱼眼）
  dashcam      行车记录仪（广角、偏锐、高反差）
  trailcam     野外红外相机夜拍（红外闪光，近处过曝、远处全黑）
  phone_night  手机夜景模式（暗部涂抹、灯有光晕、锐化重）

说明：
  --osd 只在需要“烧进画面”的时候用（比如整屏回放、封面、单独发给用户看的样图）。
  片子里的监控画面，时间水印和检测框照旧由界面层画，这里不要重复加。
"""
import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PRESETS = {
    # barrel: 桶形畸变系数（越大越鱼眼）；zoom: 畸变后放大多少把黑边裁掉
    # stream: App 码流分辨率（画面先降到这个分辨率，再放大回输出尺寸）
    # ev: 曝光增益；knee: 高于它的亮部直接推到过曝；bloom: 过曝区域的光晕
    # black: 黑位抬升（红外的“雾”）；gamma: 中间调；sat: 饱和度；tint: BGR 色偏
    # vignette: 暗角；hotspot: 红外灯中心亮斑；blur: 镜头发软
    # sharpen: ISP 锐化（边缘白边）；noise_l / noise_c: 亮度 / 彩色噪点（0–255 尺度，暗部自动加重）
    # jpeg: 静帧压缩质量；kbps: 视频码率；gop: 关键帧间隔（每隔这么多帧画质“呼吸”一次）
    'cctv_color': dict(barrel=0.07, zoom=1.04, stream=(1280, 720), ev=1.08, knee=0.86, bloom=0.22,
                       black=0.015, gamma=1.0, sat=0.82, tint=(1.0, 1.02, 0.99), vignette=0.22, hotspot=0.0,
                       blur=0.5, sharpen=0.55, noise_l=3.0, noise_c=1.4, mono=False, jpeg=42, kbps=900, gop=50),
    'cctv_ir': dict(barrel=0.07, zoom=1.04, stream=(1280, 720), ev=1.05, knee=0.84, bloom=0.30,
                    black=0.09, gamma=0.95, sat=0.0, tint=(1.0, 1.0, 1.0), vignette=0.42, hotspot=0.20,
                    blur=1.0, sharpen=0.45, noise_l=2.8, noise_c=0.0, mono=True, jpeg=40, kbps=700, gop=50),
    'homecam': dict(barrel=0.14, zoom=1.08, stream=(960, 540), ev=1.06, knee=0.86, bloom=0.25,
                    black=0.02, gamma=1.0, sat=0.78, tint=(1.0, 1.01, 1.0), vignette=0.30, hotspot=0.0,
                    blur=0.7, sharpen=0.6, noise_l=3.2, noise_c=1.8, mono=False, jpeg=40, kbps=600, gop=40),
    'homecam_ir': dict(barrel=0.14, zoom=1.08, stream=(960, 540), ev=1.0, knee=0.82, bloom=0.32,
                       black=0.08, gamma=0.95, sat=0.0, tint=(1.0, 1.0, 1.0), vignette=0.50, hotspot=0.28,
                       blur=1.0, sharpen=0.5, noise_l=3.2, noise_c=0.0, mono=True, jpeg=38, kbps=500, gop=40),
    'babycam_ir': dict(barrel=0.16, zoom=1.09, stream=(854, 480), ev=0.96, knee=0.80, bloom=0.35,
                       black=0.09, gamma=0.92, sat=0.0, tint=(0.97, 1.03, 0.97), vignette=0.55, hotspot=0.30,
                       blur=1.2, sharpen=0.4, noise_l=3.4, noise_c=0.0, mono=True, jpeg=36, kbps=450, gop=30),
    'doorbell': dict(barrel=0.38, zoom=1.16, stream=(960, 720), ev=1.08, knee=0.84, bloom=0.30,
                     black=0.02, gamma=1.0, sat=0.75, tint=(1.0, 1.0, 1.0), vignette=0.45, hotspot=0.0,
                     blur=0.8, sharpen=0.55, noise_l=3.4, noise_c=2.0, mono=False, jpeg=38, kbps=500, gop=30),
    'dashcam': dict(barrel=0.10, zoom=1.05, stream=(1920, 1080), ev=1.04, knee=0.88, bloom=0.28,
                    black=0.0, gamma=1.05, sat=0.92, tint=(1.0, 1.0, 1.0), vignette=0.20, hotspot=0.0,
                    blur=0.3, sharpen=0.8, noise_l=2.6, noise_c=1.6, mono=False, jpeg=45, kbps=1600, gop=30),
    'trailcam': dict(barrel=0.05, zoom=1.03, stream=(1280, 720), ev=1.12, knee=0.78, bloom=0.40,
                     black=0.03, gamma=1.1, sat=0.0, tint=(1.0, 1.0, 1.0), vignette=0.65, hotspot=0.35,
                     blur=0.9, sharpen=0.45, noise_l=3.6, noise_c=0.0, mono=True, jpeg=40, kbps=900, gop=30),
    'phone_night': dict(barrel=0.0, zoom=1.0, stream=(2016, 1512), ev=1.10, knee=0.84, bloom=0.45,
                        black=0.03, gamma=0.9, sat=0.95, tint=(1.0, 1.0, 1.02), vignette=0.12, hotspot=0.0,
                        blur=0.0, sharpen=0.9, noise_l=2.0, noise_c=2.6, mono=False, jpeg=60, kbps=4000, gop=30,
                        smear=True),
}

FONT_CANDIDATES = [
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
]


def font(size):
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def barrel_maps(w, h, k, zoom):
    """桶形畸变的重映射表：输出像素从输入的哪里取。"""
    ys, xs = np.indices((h, w), dtype=np.float32)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    nx, ny = (xs - cx) / cx, (ys - cy) / cx  # 以宽度归一，横竖畸变一致
    nx, ny = nx / zoom, ny / zoom
    r2 = nx * nx + ny * ny
    f = 1 + k * r2
    return (nx * f * cx + cx).astype(np.float32), (ny * f * cx + cy).astype(np.float32)


def radial(w, h):
    ys, xs = np.indices((h, w), dtype=np.float32)
    nx, ny = (xs - w / 2) / (w / 2), (ys - h / 2) / (h / 2)
    return nx * nx * 0.8 + ny * ny * 0.6  # 横向画面，四角最大约 1.4


def noise_level(x):
    """平坦区高频残差的标准差（0–255 尺度），用来量“原图已经有多少噪点”。"""
    g = cv2.cvtColor((np.clip(x, 0, 1) * 255).astype(np.float32), cv2.COLOR_BGR2GRAY) if x.ndim == 3 else x
    blur = cv2.GaussianBlur(g, (0, 0), 2)
    mag = np.hypot(cv2.Sobel(blur, cv2.CV_32F, 1, 0), cv2.Sobel(blur, cv2.CV_32F, 0, 1))
    flat = mag < np.percentile(mag, 30)
    return float((g - blur)[flat].std())


class Look:
    def __init__(self, p, w, h, night=False, seed=7):
        self.p = dict(p)
        if night and not self.p['mono']:  # 关灯后硬撑彩色：增益拉高
            self.p.update(ev=self.p['ev'] * 1.25, noise_l=self.p['noise_l'] * 1.5, noise_c=self.p['noise_c'] * 1.7,
                          sat=self.p['sat'] * 0.62, black=self.p['black'] + 0.025, blur=self.p['blur'] + 0.4,
                          sharpen=self.p['sharpen'] * 0.7, knee=self.p['knee'] - 0.04)
        self.w, self.h = w, h
        self.maps = barrel_maps(w, h, self.p['barrel'], self.p['zoom']) if self.p['barrel'] > 0 else None
        r = radial(w, h)
        light = (1 - self.p['vignette'] * np.clip(r, 0, 1.4) / 1.4)
        if self.p['hotspot'] > 0:
            light = light * (1 + self.p['hotspot'] * np.exp(-r / 0.28)) / (1 + self.p['hotspot'] * 0.55)
        self.light = light[..., None].astype(np.float32)
        sw, sh = self.p['stream']
        if sw >= w:  # 码流分辨率不高于输出
            sw, sh = w, h
        self.sw, self.sh = sw, int(round(sw * h / w))
        self.rng = np.random.default_rng(seed)
        self.add = None

    def frame(self, bgr):
        p = self.p
        x = bgr.astype(np.float32) / 255.0
        if self.maps is not None:
            x = cv2.remap(x, self.maps[0], self.maps[1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if p['mono']:
            g = cv2.cvtColor(x, cv2.COLOR_BGR2GRAY)
            x = np.repeat(g[..., None], 3, axis=2)
        x = x * np.array(p['tint'], np.float32)
        x = x * p['ev'] * self.light
        x = np.power(np.clip(x, 0, None), p['gamma'])
        # 过曝：亮部超过 knee 后被迅速推到纯白（真摄像头的灯管、窗户、反光地面都是一片白）
        k = p['knee']
        hi = np.clip((x - k) / (1 - k), 0, None)
        x = np.where(x > k, k + (1 - k) * np.minimum(1.0, hi * 1.6), x)
        if p['bloom'] > 0:
            m = np.clip((x.max(axis=2, keepdims=True) - 0.9) / 0.1, 0, 1)
            b = cv2.GaussianBlur(m * x, (0, 0), self.w / 90)
            if b.ndim == 2:
                b = b[..., None]
            x = x + p['bloom'] * b
        x = p['black'] + (1 - p['black']) * x
        if not p['mono']:
            g = x.mean(axis=2, keepdims=True)
            x = g + p['sat'] * (x - g)
        x = np.clip(x, 0, 1)
        # 降到码流分辨率：镜头发软 → ISP 锐化（边缘白边）→ 传感器噪点
        s = cv2.resize(x, (self.sw, self.sh), interpolation=cv2.INTER_AREA)
        if p.get('smear'):  # 手机夜景：降噪把细节抹平
            s = cv2.bilateralFilter(s, 7, 0.08, 5)
        if p['blur'] > 0:
            s = cv2.GaussianBlur(s, (0, 0), p['blur'])
        if p['sharpen'] > 0:
            s = s + p['sharpen'] * (s - cv2.GaussianBlur(s, (0, 0), 1.6))
        if self.add is None:  # 第一帧量一次原图已有的噪点，之后整段视频用同一个补量，避免闪
            n_in = noise_level(s)
            t = p['noise_l']
            self.add = max(np.sqrt(max(t * t - n_in * n_in, 0.0)), 0.35 * t) / max(t, 1e-6)
            self.n_in = n_in
        lum = s.mean(axis=2, keepdims=True)
        dark = 1.0 + 1.0 * np.clip(1 - lum * 1.8, 0, 1)  # 暗部噪点更重
        # 真摄像头会先做降噪，剩下的噪点是一团一团的（粗）加一点细颗粒，不是均匀的细砂纸
        fine = cv2.GaussianBlur(self.rng.normal(0, 1, (self.sh, self.sw)).astype(np.float32), (0, 0), 0.5)
        coarse = cv2.GaussianBlur(self.rng.normal(0, 1, (self.sh, self.sw)).astype(np.float32), (0, 0), 1.4)
        nl = (0.45 * fine / max(fine.std(), 1e-6) + 0.75 * coarse / max(coarse.std(), 1e-6))[..., None]
        nl = nl * (p['noise_l'] * self.add / 255.0)
        s = s + nl * dark
        if p['noise_c'] > 0:
            nc = self.rng.normal(0, p['noise_c'] * self.add / 255.0, (self.sh, self.sw, 3)).astype(np.float32)
            nc = cv2.GaussianBlur(nc, (0, 0), 1.8) * 2.6
            nc = nc - nc.mean(axis=2, keepdims=True)
            s = s + nc * dark
        s = np.clip(s, 0, 1)
        s = (s * 255 + 0.5).astype(np.uint8)
        if p['jpeg']:  # 在码流分辨率下压缩：暗部和渐变出现块状、边缘有蚊式噪声
            s = jpeg(s, p['jpeg'])
        return cv2.resize(s, (self.w, self.h), interpolation=cv2.INTER_LINEAR)


def draw_osd(bgr, osd=None, channel=None):
    """真监控的烧录水印：左上“日期 星期 时间”，右下机位名；粗体白字带黑边。"""
    if not osd and not channel:
        return bgr
    im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(im)
    w, h = im.size
    sz = max(14, int(h * 0.036))
    f = font(sz)
    sw = max(1, sz // 12)
    if osd:
        d.text((int(w * 0.022), int(h * 0.028)), osd, font=f, fill=(255, 255, 255), stroke_width=sw, stroke_fill=(0, 0, 0))
    if channel:
        tw = d.textlength(channel, font=f)
        d.text((w - tw - int(w * 0.024), h - sz - int(h * 0.04)), channel, font=f, fill=(255, 255, 255),
               stroke_width=sw, stroke_fill=(0, 0, 0))
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


WEEK = '一二三四五六日'


def tick(osd, sec):
    """把 '2026-11-12 星期四 23:18:06' 往后推 sec 秒（跨天时日期和星期也跟着变）。"""
    import datetime as dt
    try:
        date, week, t = osd.split(' ')
        base = dt.datetime.strptime(date + ' ' + t, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return osd
    n = base + dt.timedelta(seconds=int(sec))
    return f"{n:%Y-%m-%d} 星期{WEEK[n.weekday()]} {n:%H:%M:%S}"


def jpeg(bgr, q):
    ok, buf = cv2.imencode('.jpg', bgr, [cv2.IMWRITE_JPEG_QUALITY, int(q)])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def report(bgr, name=''):
    """画质体检：在 1280 宽下量指标，给出“太干净 / 高光没过曝 / 太鲜艳”之类的提示。"""
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    h, w = g.shape
    s = 1280 / w
    g2 = cv2.resize(g, (1280, int(h * s)), interpolation=cv2.INTER_AREA)
    c2 = cv2.resize(bgr, (1280, int(h * s)), interpolation=cv2.INTER_AREA)
    blur = cv2.GaussianBlur(g2, (0, 0), 2)
    hp = g2 - blur
    mag = np.hypot(cv2.Sobel(blur, cv2.CV_32F, 1, 0), cv2.Sobel(blur, cv2.CV_32F, 0, 1))
    flat = mag < np.percentile(mag, 30)
    noise = float(hp[flat].std())
    dark = g2 < np.percentile(g2, 25)
    noise_dark = float(hp[dark & flat].std()) if (dark & flat).any() else noise
    sat = float(cv2.cvtColor(c2, cv2.COLOR_BGR2HSV)[..., 1].mean())
    p1, p50, p99 = [float(v) for v in np.percentile(g2, [1, 50, 99])]
    clip = float((g2 >= 250).mean() * 100)
    d = np.abs(np.diff(g2, axis=1))
    block = float(d[:, 7::8].mean() / max(d.mean(), 1e-6))
    r = dict(file=name, size=f'{w}x{h}', noise=round(noise, 2), noise_dark=round(noise_dark, 2), sat=round(sat, 1),
             p1=int(p1), p50=int(p50), p99=int(p99), clip_pct=round(clip, 2), block=round(block, 3))
    tips = []
    lim = 1.6 if sat < 3 else 2.2  # 黑白红外经过降噪，本来就偏平滑发雾，阈值低一些
    if noise < lim:
        tips.append(f'太干净：平坦区噪点 < {lim}，像渲染图（真监控彩色一般 2.5–6，红外 1.8–4）')
    if clip < 0.15 and p99 < 235:
        tips.append('高光没有过曝：画面里有灯、窗、反光地面的话，它们应该是一片白')
    if sat > 55:
        tips.append('颜色太鲜：监控和看护器的颜色偏淡，夜里更灰')
    if p1 > 40:
        tips.append('黑位太高：暗部发灰过头（红外可以略高，彩色不该）')
    if block < 1.03:
        tips.append('没有压缩痕迹：真码流在暗部和渐变上有块状压缩')
    r['tips'] = tips or ['指标正常（仍需和真实截图并排目测）']
    return r


def run_image(a, p):
    src = cv2.imread(a.input, cv2.IMREAD_COLOR)
    if src is None:
        src = cv2.cvtColor(np.array(Image.open(a.input).convert('RGB')), cv2.COLOR_RGB2BGR)
    if a.report:
        print(json.dumps(report(src, os.path.basename(a.input)), ensure_ascii=False, indent=1))
        if not a.output:
            return
    h, w = src.shape[:2]
    if a.width:
        h, w = int(round(h * a.width / w)), a.width
        src = cv2.resize(src, (w, h), interpolation=cv2.INTER_AREA)
    look = Look(p, w, h, night=a.night, seed=a.seed)
    out = look.frame(src)
    out = draw_osd(out, a.osd, a.channel)
    out = jpeg(out, 80)  # 水印也跟着过一遍轻压缩
    if a.output.lower().endswith(('.jpg', '.jpeg')):
        cv2.imwrite(a.output, out, [cv2.IMWRITE_JPEG_QUALITY, 92])
    else:
        cv2.imwrite(a.output, out)
    if a.report:
        print(json.dumps(report(out, os.path.basename(a.output)), ensure_ascii=False, indent=1))
    print('已输出', a.output)


def run_video(a, p):
    cap = cv2.VideoCapture(a.input)
    sfps = cap.get(cv2.CAP_PROP_FPS) or 24
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w0, h0 = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w, h = (a.width, int(round(h0 * a.width / w0)) // 2 * 2) if a.width else (w0 // 2 * 2, h0 // 2 * 2)
    fps = a.fps or sfps
    look = Look(p, w, h, night=a.night, seed=a.seed)
    rng = np.random.default_rng(a.seed + 1)
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w}x{h}', '-r', str(fps),
           '-i', '-']
    if a.keep_audio:
        cmd += ['-i', a.input, '-map', '0:v', '-map', '1:a?', '-c:a', 'aac', '-b:a', '96k', '-shortest']
    kb = a.kbps or p['kbps']
    cmd += ['-c:v', 'libx264', '-preset', 'medium', '-b:v', f'{kb}k', '-maxrate', f'{int(kb * 1.3)}k',
            '-bufsize', f'{kb}k', '-g', str(a.gop or p['gop']), '-bf', '0', '-pix_fmt', 'yuv420p', a.output]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frames = []
    ok, f = cap.read()
    while ok:
        frames.append(f)
        ok, f = cap.read()
    dur = len(frames) / sfps
    m = int(round(dur * fps))
    last = None
    for i in range(m):
        t = i / fps
        if last is not None and a.stutter > 0 and rng.random() < a.stutter:
            ff.stdin.write(last.tobytes())  # 偶尔卡一帧：重复上一帧
            continue
        src = frames[min(len(frames) - 1, int(t * sfps))]
        if (src.shape[1], src.shape[0]) != (w, h):
            src = cv2.resize(src, (w, h), interpolation=cv2.INTER_AREA)
        out = look.frame(src)
        if a.osd or a.channel:
            out = draw_osd(out, tick(a.osd, t) if a.osd else None, a.channel)
        ff.stdin.write(out.tobytes())
        last = out
    ff.stdin.close()
    ff.wait()
    print(f'已输出 {a.output}：{m} 帧，{fps} fps，{kb} kbps，源 {n} 帧 / {sfps:.2f} fps')


def main():
    ap = argparse.ArgumentParser(description='实拍质感后期（监控 / 看护器 / 门铃 / 行车记录仪 / 红外相机 / 手机夜景）')
    ap.add_argument('input')
    ap.add_argument('output', nargs='?')
    ap.add_argument('--preset', default='cctv_color', choices=sorted(PRESETS))
    ap.add_argument('--night', action='store_true', help='彩色预设在暗光下硬撑：增益、噪点、发灰')
    ap.add_argument('--no-distort', action='store_true', help='原图已经有广角/鱼眼畸变时加上，不再叠加畸变')
    ap.add_argument('--set', action='append', default=[], help='覆盖预设参数，如 --set noise_l=5 --set barrel=0.1')
    ap.add_argument('--width', type=int, help='输出宽度（默认与输入相同）')
    ap.add_argument('--osd', help="烧录时间水印，如 '2026-11-12 星期四 23:18:06'（视频会逐秒走）")
    ap.add_argument('--channel', help='烧录机位名（右下角），如 橱窗内侧')
    ap.add_argument('--fps', type=float, help='视频输出帧率（监控常见 15 或 20）')
    ap.add_argument('--kbps', type=int, help='视频码率，默认按预设')
    ap.add_argument('--gop', type=int, help='关键帧间隔')
    ap.add_argument('--stutter', type=float, default=0.0, help='视频偶尔卡一帧的概率，如 0.02')
    ap.add_argument('--keep-audio', action='store_true')
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--report', action='store_true', help='打印画质体检')
    ap.add_argument('--list', action='store_true', help='列出预设参数')
    a = ap.parse_args()
    if a.list:
        print(json.dumps(PRESETS, ensure_ascii=False, indent=1))
        return
    p = dict(PRESETS[a.preset])
    for kv in a.set:
        k, v = kv.split('=', 1)
        p[k] = json.loads(v) if v[:1] in '[{' else (v.lower() == 'true' if v.lower() in ('true', 'false') else float(v))
    if a.no_distort:
        p['barrel'], p['zoom'] = 0.0, 1.0
    if not a.output and not a.report:
        ap.error('需要输出路径，或者加 --report 只做体检')
    if a.input.lower().endswith(('.mp4', '.mov', '.webm', '.mkv')):
        if not a.output:
            ap.error('视频需要输出路径')
        run_video(a, p)
    else:
        run_image(a, p)


if __name__ == '__main__':
    main()
