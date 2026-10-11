# -*- coding: utf-8 -*-
"""重试发布脚本：2026-10-11「每天在车里坐十分钟，是我最后的自由」
原因：2026-10-11 07:01 预检失败，IP 183.159.115.101 不在微信白名单。
修复：登录 mp.weixin.qq.com → 设置与开发 → 基本配置 → IP白名单，添加 183.159.115.101
然后运行: python D:/blog/scripts/retry_2026-10-11-che-li.py
"""
import json, os, re, urllib.request, io
import requests
from PIL import Image

ARTICLE_MD = r"D:/blog/content/posts/2026-10-11-che-li-de-shi-fen-zhong.md"
COVER_PNG  = r"D:/blog/covers/cover_2026-10-11-che-li.png"
TITLE = "每天在车里坐十分钟，是我最后的自由"
DIGEST = "熄火之后，我不着急下车。人到中年，连发呆都要先找个没人的地方。"

# 1. 读凭证
env = {}
with open("D:/blog/scripts/.env", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

# 2. 获取 token
token_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential"
             f"&appid={env['WEIXIN_APP_ID']}&secret={env['WEIXIN_APP_SECRET']}")
with urllib.request.urlopen(token_url, timeout=10) as resp:
    result = json.loads(resp.read().decode("utf-8"))
if "access_token" not in result:
    raise SystemExit(f"获取 token 失败: {result}")
token = result["access_token"]
print("✅ token OK")

# 3. 上传封面
with open(COVER_PNG, "rb") as f:
    up = requests.post(
        f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image",
        files={"media": ("cover.png", f, "image/png")}).json()
if "media_id" not in up:
    raise SystemExit(f"封面上传失败: {up}")
thumb_media_id = up["media_id"]
print(f"✅ 封面已上传: {thumb_media_id}")

# 4. Markdown -> HTML（保留 ## 标题、加粗、斜体）
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def inline(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    return s

with open(ARTICLE_MD, "r", encoding="utf-8") as f:
    md = f.read()
# 去 frontmatter
md = re.sub(r"^---\n.*?\n---\n", "", md, flags=re.S)

P = '<p style="font-size:16px;line-height:1.8;color:#333;margin:0 0 20px 0;">{}</p>'
H2 = ('<h2 style="font-size:18px;font-weight:bold;color:#333;'
      'margin:32px 0 16px 0;text-align:left;">{}</h2>')

parts, buf = [], []
def flush():
    if buf:
        text = " ".join(x.strip() for x in buf if x.strip())
        if text:
            parts.append(P.format(inline(esc(text))))
        buf.clear()

for line in md.splitlines():
    line = line.strip()
    if line.startswith("## "):
        flush()
        parts.append(H2.format(inline(esc(line[3:].strip()))))
    elif line == "---":
        flush()
        parts.append('<hr style="border:none;border-top:1px solid #e5e5e5;margin:24px 0;"/>')
    elif line == "":
        flush()
    else:
        buf.append(line)
flush()

footer = ('<p style="font-size:13px;color:#999;text-align:center;margin-top:40px;'
          'border-top:1px solid #e5e5e5;padding-top:16px;">深夜解忧铺<br/>你的心事有人听</p>')
content = "".join(parts) + footer

# 5. 创建草稿（关键：ensure_ascii=False）
article = {
    "title": TITLE,
    "digest": DIGEST,
    "content": content,
    "thumb_media_id": thumb_media_id,
    "need_open_comment": 1,
    "only_fans_can_comment": 0,
}
draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(draft_url, data=payload,
                             headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as resp:
    draft = json.loads(resp.read().decode("utf-8"))
if "media_id" not in draft:
    raise SystemExit(f"创建草稿失败: {draft}")
media_id = draft["media_id"]
print(f"✅ 草稿创建成功: {media_id}")

# 6. 验证中文无乱码
check_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
cp = json.dumps({"media_id": media_id, "no_content": 1}, ensure_ascii=False).encode("utf-8")
creq = urllib.request.Request(check_url, data=cp,
                              headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(creq, timeout=30) as resp:
    got = json.loads(resp.read().decode("utf-8"))
t = got.get("news_item", [{}])[0].get("title", "")
if "\\u" in t or "车" not in t:
    # 删除并报错
    dp = json.dumps({"media_id": media_id}, ensure_ascii=False).encode("utf-8")
    dreq = urllib.request.Request(
        f"https://api.weixin.qq.com/cgi-bin/draft/delete?access_token={token}",
        data=dp, headers={"Content-Type": "application/json; charset=utf-8"})
    urllib.request.urlopen(dreq, timeout=30)
    raise SystemExit(f"标题乱码: {t!r}，草稿已删除，请修复后重试")
print(f"✅ 标题验证通过: {t}")
print("完成。请到公众号后台 草稿箱 检查后排版发布。")
