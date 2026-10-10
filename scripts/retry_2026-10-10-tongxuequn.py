# -*- coding: utf-8 -*-
"""
重试发布脚本 - 2026-10-10 同学群里最安静的那个人，当年是最热闹的
原因：API 40164 - IP 183.159.115.101 不在微信白名单
修复：mp.weixin.qq.com -> 设置与开发 -> 基本配置 -> IP白名单 -> 添加 183.159.115.101
然后运行：python retry_2026-10-10-tongxuequn.py
"""
import json, os, re, urllib.request, mimetypes, uuid

POST_PATH = r"D:/blog/content/posts/2026-10-10-tong-xue-qun-zui-an-jing.md"
COVER_PATH = r"D:/blog/covers/cover_2026-10-10-tongxuequn-real.png"
ENV_PATH = r"D:/blog/scripts/.env"
TITLE = "同学群里最安静的那个人，当年是最热闹的"
DIGEST = "当年最怕冷场的那个人，现在成了群里最安静的。沉默不是不在乎，是插不上嘴了。"

# ---------- 1. 读凭证 ----------
env = {}
with open(ENV_PATH, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

# ---------- 2. 获取 token ----------
token_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential"
             f"&appid={env['WEIXIN_APP_ID']}&secret={env['WEIXIN_APP_SECRET']}")
with urllib.request.urlopen(token_url, timeout=15) as resp:
    result = json.loads(resp.read().decode("utf-8"))
if "access_token" not in result:
    raise SystemExit(f"获取token失败: {result} (如仍是40164，先加IP白名单)")
token = result["access_token"]
print("✅ token OK")

# ---------- 3. 上传封面 (multipart/form-data) ----------
def upload_image(token, filepath):
    boundary = uuid.uuid4().hex
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        filedata = f.read()
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'.encode()
    body += b"Content-Type: image/png\r\n\r\n"
    body += filedata + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        r = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in r:
        raise SystemExit(f"上传封面失败: {r}")
    return r["media_id"]

thumb_media_id = upload_image(token, COVER_PATH)
print("✅ 封面上传成功:", thumb_media_id)

# ---------- 4. Markdown -> HTML ----------
with open(POST_PATH, "r", encoding="utf-8") as f:
    raw = f.read()

# 去掉 frontmatter
if raw.startswith("---"):
    parts = raw.split("---", 2)
    body_md = parts[2] if len(parts) >= 3 else raw
else:
    body_md = raw

lines = body_md.split("\n")
html_parts = []
p_style = 'style="font-size: 16px; line-height: 1.8; color: #333; margin: 0 0 20px 0;"'
h2_style = 'style="font-size: 20px; font-weight: bold; color: #2b2b2b; margin: 32px 0 16px 0;"'

def inline(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    return text

buf = []
def flush():
    if buf:
        para = " ".join(buf).strip()
        if para:
            html_parts.append(f"<p {p_style}>{inline(para)}</p>")
        buf.clear()

for line in lines:
    stripped = line.strip()
    if not stripped or stripped == "---":
        flush()
        continue
    if stripped.startswith("## "):
        flush()
        html_parts.append(f"<h2 {h2_style}>{inline(stripped[3:].strip())}</h2>")
    elif stripped.startswith("# "):
        flush()
        html_parts.append(f"<h1 {h2_style}>{inline(stripped[2:].strip())}</h1>")
    else:
        buf.append(stripped)
flush()

footer = ('<hr style="border:none;border-top:1px solid #ddd;margin:32px 0 16px 0;">'
          '<p style="font-size:14px;color:#999;text-align:center;">深夜解忧铺</p>'
          '<p style="font-size:14px;color:#999;text-align:center;">你的心事，有人听</p>')
content_html = "\n".join(html_parts) + footer

# ---------- 5. 创建草稿 (ensure_ascii=False 关键!) ----------
draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
article = {
    "title": TITLE,
    "digest": DIGEST,
    "content": content_html,
    "thumb_media_id": thumb_media_id,
    "need_open_comment": 1,
    "only_fans_can_comment": 0,
}
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(draft_url, data=payload,
    headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as resp:
    r = json.loads(resp.read().decode("utf-8"))
if "media_id" not in r:
    raise SystemExit(f"创建草稿失败: {r}")
draft_id = r["media_id"]
print("✅ 草稿创建成功, media_id:", draft_id)

# ---------- 6. 验证中文编码 ----------
batch_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
payload = json.dumps({"media_id": draft_id, "offset": 0, "count": 1}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(batch_url, data=payload,
    headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as resp:
    check = json.loads(resp.read().decode("utf-8"))
got_title = check.get("news_item", [{}])[0].get("title", "")
if "\\u" in got_title or got_title != TITLE:
    raise SystemExit(f"❌ 标题乱码: {got_title!r} -> 请删除草稿 {draft_id} 后重跑")
print("✅ 编码验证通过, 草稿标题:", got_title)
print("\n完成！请到 mp.weixin.qq.com 草稿箱检查并发布。")
