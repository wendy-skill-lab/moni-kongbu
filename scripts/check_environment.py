#!/usr/bin/env python3
"""只读检查本地制作环境；不安装依赖、不联网、不调用生成工具。"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def run(command, cwd=None):
    try:
        p = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=12)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as error:
        return 1, str(error)


def inspect(project):
    items = []
    def add(name, ok, required, detail):
        items.append(dict(name=name, ok=bool(ok), required=required, detail=detail))
    add('Python 3', sys.version_info >= (3, 8), True, sys.version.split()[0])
    node, ffmpeg = shutil.which('node'), shutil.which('ffmpeg')
    add('Node.js', node, True, node or '缺失：界面渲染需要 Node.js')
    add('FFmpeg', ffmpeg, True, ffmpeg or '缺失：视频与音频编码需要 FFmpeg')
    if ffmpeg:
        rc, text = run([ffmpeg, '-hide_banner', '-filters'])
        add('FFmpeg rubberband', rc == 0 and 'rubberband' in text, False,
            '声音变速时按需使用；不是生成服务')
    for module in ('numpy', 'PIL', 'cv2', 'scipy'):
        add('Python ' + module, importlib.util.find_spec(module) is not None, False,
            '按需用于混音、图像处理、人脸检测或声音后期')
    for module in ('playwright', '@fontsource-variable/inter'):
        rc, info = (run([node, '-e', 'console.log(require.resolve(process.argv[1],{paths:[process.cwd()]}))', module], project)
                    if node else (1, '缺少 Node.js'))
        add('Node ' + module, rc == 0, True,
            info if rc == 0 else '未在项目依赖中找到；脚手架可按需安装')
    browser = os.environ.get('CHROMIUM_PATH')
    if browser:
        browser_ok = Path(browser).is_file() and os.access(browser, os.X_OK)
        detail = browser
    elif node:
        rc, info = run([node, '-e', 'const fs=require("fs");const p=require(require.resolve("playwright",{paths:[process.cwd()]}));const x=fs.existsSync("/usr/bin/chromium")?"/usr/bin/chromium":p.chromium.executablePath();console.log(x);process.exit(fs.existsSync(x)?0:1)'], project)
        browser_ok, detail = rc == 0, info if rc == 0 else '需安装 Playwright Chromium，或设置 CHROMIUM_PATH'
    else:
        browser_ok, detail = False, '需 Node.js 与 Playwright，或可执行 CHROMIUM_PATH'
    add('Chromium', browser_ok, True, detail)
    font = os.environ.get('CJK_FONT_PATH')
    candidates = [font] if font else [
        '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf',
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
    ]
    chosen = next((x for x in candidates if x and Path(x).is_file()), None)
    add('中文字体文件', chosen, True, chosen or '请设置 CJK_FONT_PATH；文件存在不代表所有字形都已验收')
    return items


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project', type=Path, default=Path.cwd(), help='工程或准备安装依赖的目录')
    ap.add_argument('--json', action='store_true', help='输出结构化结果')
    ap.add_argument('--strict', action='store_true', help='有必需项缺失时退出码为 1')
    args = ap.parse_args()
    project = args.project.expanduser().resolve()
    if not project.is_dir():
        ap.error('项目目录不存在：' + str(project))
    checks = inspect(project)
    report = dict(project=str(project), checks=checks,
                  local_render_ready=all(x['ok'] for x in checks if x['required']),
                  note='不检测 Manus 权限、生成额度、素材版权或完整片验收；不安装依赖。')
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print('只读环境检查：' + str(project))
        for item in checks:
            print(('已找到' if item['ok'] else '需补齐') + ' | ' + item['name'] + ' | ' + item['detail'])
        print(report['note'])
    return int(args.strict and not report['local_render_ready'])


if __name__ == '__main__':
    raise SystemExit(main())
