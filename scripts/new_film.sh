#!/usr/bin/env bash
# 新建一个短片项目（从技能模板复制引擎、示例模块、时间轴、混音、封面、图标和通用音效）。
# 用法：bash new_film.sh <项目目录> <片名> [cctv|car]
#   cctv = 以《已就寝》模块为底版：监控实时与回放、公众号模板消息、群聊 @、微信视频通话、通话小窗
#   car  = 以《我们到了》模块为底版：车企 App、代驾地图、语音通话
# 可选环境变量：REUSE_NODE_MODULES=<已有的 node_modules 目录>，有就直接链接过来，省掉安装时间。
# 离线建项目：SKIP_NPM_INSTALL=1，只复制资源，不运行 npm；依赖需另行核对。
set -euo pipefail
SK="$(cd "$(dirname "$0")/.." && pwd)"
P="${1:?缺少项目目录}"; TITLE="${2:?缺少片名}"; BASE="${3:-cctv}"
case "$BASE" in cctv|car) ;; *) echo "未知底版 ${BASE}（只能是 cctv 或 car）"; exit 1 ;; esac
if [ -d "$P" ] && [ -n "$(find "$P" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
  echo "拒绝覆盖非空项目目录：${P}。请使用新目录；修改旧片应在原工程中按需更新。"
  exit 1
fi
mkdir -p "$P"/{src,assets/{gen,video,audio,stills,thumb,frames,noise},cover,research,qa,qa_final}
T="$SK/templates"
cp "$T/engine/film_head.html" "$P/src/film_head.html"
case "$BASE" in
  cctv) cp "$T/engine/module_cctv_kanban.js" "$P/src/part.js" ;;
  car)  cp "$T/engine/module_car_call.js" "$P/src/part.js" ;;
  *) echo "未知底版 ${BASE}（只能是 cctv 或 car）"; exit 1 ;;
esac
cp "$T/build_data_example.py" "$P/src/build_data.py"
cp "$T/soundtrack_example.py" "$P/src/soundtrack.py"
cp "$T/make_auditions_example.py" "$P/src/make_auditions.py"   # soundtrack.py 会引用它（铃声、背书的版本）
cp "$SK/scripts/render.js" "$SK/scripts/assemble.py" "$SK/scripts/encode.sh" "$SK/scripts/warning_card.py" \
   "$SK/scripts/crop169.py" "$SK/scripts/soften_figure.py" "$SK/scripts/contact_sheet.py" "$SK/scripts/ui_sounds.py" \
   "$SK/scripts/floorplan.py" "$SK/scripts/asset_board.py" "$P/src/"
# 方位图与资产板示例：改成本片内容后，逐段确认再生成视频。
cp "$T/floorplan_example.json" "$P/research/floorplan.json"
cp "$T/asset_board_example.json" "$P/asset_board.json"
cp "$T/cover/cover.html" "$T/cover/shot.js" "$P/cover/"
cp "$T/audio/"*.mp3 "$P/assets/audio/"
mkdir -p "$P/assets/audio/ui" && cp "$T/audio/ui/"*.wav "$P/assets/audio/ui/"   # 随附库基准音效；权利说明见 resources，不视为统一 MIT 素材
[ -e "$P/icons" ] || cp -r "$T/icons" "$P/icons"
cp "$SK/references/资源说明.md" "$P/research/ASSET_NOTICE.md"
cp "$SK/LICENSE" "$P/LICENSE"
echo "$TITLE" > "$P/src/TITLE"

# Node 依赖：Playwright（逐帧截图）和 Inter 字体（film_head.html 里写死了 ../node_modules/@fontsource-variable/inter 路径）
if [ ! -e "$P/node_modules/playwright" ]; then
  if [ "${SKIP_NPM_INSTALL:-0}" = "1" ]; then
    echo "已跳过 npm 安装（SKIP_NPM_INSTALL=1）；本次只创建项目文件。"
  elif [ -n "${REUSE_NODE_MODULES:-}" ] && [ -d "$REUSE_NODE_MODULES/playwright" ]; then
    ln -s "$REUSE_NODE_MODULES" "$P/node_modules"
  else
    echo "正在安装 playwright 和 @fontsource-variable/inter（约 1 分钟）……"
    if ! (cd "$P" && npm init -y >/dev/null 2>&1 && npm install --no-audit --no-fund playwright @fontsource-variable/inter >/tmp/new_film_npm.log 2>&1); then
      echo "警告：npm 安装失败，日志在 /tmp/new_film_npm.log。可以手动执行：cd $P && npm install playwright @fontsource-variable/inter"
    fi
  fi
fi
[ -x /usr/bin/chromium ] || echo "警告：没有 /usr/bin/chromium。请设置 CHROMIUM_PATH，或执行：cd $P && npx playwright install chromium"
python3 -c "import cv2, scipy" 2>/dev/null || echo "提示：图像和人脸跟踪脚本需要 opencv 和 scipy，请在 Python 虚拟环境中安装 opencv-python-headless scipy"

cat > "$P/PLAN.md" <<EOF
# 《${TITLE}》制作计划（上下文压缩后先读这里）
- 恐怖要素：<按当前阶段确认>
- 最恐怖的画面：<已确认的原话>
- 定稿的视觉呈现脚本：<路径>
- 模块底版：${BASE}（src/part.js，结尾自带 setTime 与 </script></body></html>）
- 场景方位：research/floorplan.json → research/floorplan.png（机位、门窗、墙角、人物的位置）
- 三条硬规矩：同一晚；第一视角（“我”是看见的人）；“我”以打字为主，人声留给关键声音证据
- 当前阶段与已确认内容：<方向／脚本／关键静帧／成片>
- 虚构与 AI 标识：<成片、封面、文案分别如何标注>
- 素材权利与来源：<参照 research/ASSET_NOTICE.md，逐项记录>
- 素材清单、节拍时间表、用户反馈：随做随追加

## 资产表（每一段确认后才生成对应视频）
| 段 | 资产 | 文件 | 状态 | 用户意见 |
| --- | --- | --- | --- | --- |

## 节拍时间表、关键决定、用户反馈
<按当前阶段追加，不跳过确认关卡>
EOF
echo "项目已建好：${P}（片名：${TITLE}，底版：${BASE}）"
echo "下一步：进入项目目录，按当前阶段确认方位和资产："
echo "  python3 src/floorplan.py research/floorplan.json research/floorplan.png"
echo "改 src/part.js 和 src/build_data.py 后检查界面帧："
echo "  python3 src/build_data.py && python3 src/assemble.py && (cd src && node render.js qa 1,5,10)"
echo "  python3 src/asset_board.py asset_board.json"
echo "逐段确认资产后再生成对应视频；保留素材权利、虚构与 AI 标识记录。"
