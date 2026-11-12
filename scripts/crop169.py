import sys
from PIL import Image
# 用法：crop169.py 输入.png 输出.png  → 居中裁成正好 16:9，并缩放到 1920×1080
a=Image.open(sys.argv[1]).convert('RGB'); w,h=a.size
tw=round(h*16/9)
if tw<=w: a=a.crop(((w-tw)//2,0,(w-tw)//2+tw,h))
else:
    th=round(w*9/16); a=a.crop((0,(h-th)//2,w,(h-th)//2+th))
a=a.resize((1920,1080),Image.LANCZOS); a.save(sys.argv[2],quality=95)
print(sys.argv[2],a.size)
