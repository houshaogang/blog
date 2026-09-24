#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retry script: you-shuo-chu-kou
Generated: 2026-09-24
Reason: IP 125.121.126.197 not in WeChat whitelist
Fix: Add 125.121.126.197 to mp.weixin.qq.com IP whitelist
"""

import json, os, re, urllib.request, urllib.parse, uuid

ENV_PATH = "D:/blog/scripts/.env"
ARTICLE_PATH = r"D:/blog/content/posts/2026-09-24-你没说出口的那句话后来怎样了.md"
COVER_PATH = r"D:/blog/content/posts/cover_2026-09-24-unspoken-words-real.png"
TITLE = "你没说出口的那句话后来怎样了"
DIGEST = "那些没说出口的话，后来都变成了深夜里的一个叹息。不是忘了，是来不及了。"

# 1. Read env
env = {}
with open(ENV_PATH, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

APP_ID = env["WEIXIN_APP_ID"]
APP_SECRET = env["WEIXIN_APP_SECRET"]

# 2. Get access_token
print("Getting access_token...")
token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
with urllib.request.urlopen(token_url, timeout=10) as resp:
    result = json.loads(resp.read().decode("utf-8"))
if "access_token" not in result:
    print(f"Token error: {result}")
    exit(1)
access_token = result["access_token"]
print("OK")

# 3. Upload cover
print("Uploading cover...")
upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
boundary = uuid.uuid4().hex
filename = os.path.basename(COVER_PATH)
with open(COVER_PATH, "rb") as f:
    file_data = f.read()
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")
req = urllib.request.Request(upload_url, data=body, headers={
    "Content-Type": f"multipart/form-data; boundary={boundary}"
})
with urllib.request.urlopen(req, timeout=30) as resp:
    upload_result = json.loads(resp.read().decode("utf-8"))
if "media_id" not in upload_result:
    print(f"Upload error: {upload_result}")
    exit(1)
thumb_media_id = upload_result["media_id"]
print(f"Cover uploaded: {thumb_media_id}")

# 4. Markdown to HTML
print("Converting markdown to HTML...")
with open(ARTICLE_PATH, "r", encoding="utf-8") as f:
    md_content = f.read()
md_content = re.sub(r"^---.*?---\s*", "", md_content, flags=re.DOTALL)

def md_to_wechat_html(md):
    lines = md.split("\n")
    parts = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            h = line[3:]
            parts.append(f'<h2 style="font-size:20px;font-weight:bold;color:#333;margin:30px 0 15px;border-left:4px solid #c0392b;padding-left:12px;">{h}</h2>')
            continue
        if line == "---":
            parts.append('<hr style="border:none;border-top:1px solid #ddd;margin:25px 0;">')
            continue
        line = re.sub(r"\*\*(.+?)\*\*", r'<strong style="color:#333;">\1</strong>', line)
        line = re.sub(r"\*(.+?)\*", r'<em style="color:#666;">\1</em>', line)
        parts.append(f'<p style="font-size:16px;line-height:1.8;color:#333;margin:12px 0;">{line}</p>')
    return "\n".join(parts)

body_html = md_to_wechat_html(md_content)
footer = '<div style="text-align:center;margin-top:40px;padding-top:20px;border-top:1px solid #eee;"><p style="font-size:14px;color:#999;">ShenYe JieYou Pu</p><p style="font-size:13px;color:#bbb;">Your thoughts, someone listens</p></div>'
full_html = body_html + footer

# 5. Create draft
print("Creating draft...")
draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
article = {
    "title": TITLE,
    "content": full_html,
    "thumb_media_id": thumb_media_id,
    "digest": DIGEST,
    "content_source_url": "",
    "need_open_comment": 1,
    "only_fans_can_comment": 0
}
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(draft_url, data=payload, headers={
    "Content-Type": "application/json; charset=utf-8"
})
with urllib.request.urlopen(req, timeout=30) as resp:
    draft_result = json.loads(resp.read().decode("utf-8"))
if "media_id" not in draft_result:
    print(f"Draft error: {draft_result}")
    exit(1)
media_id = draft_result["media_id"]
print(f"Done! media_id: {media_id}")
print("Go to mp.weixin.qq.com to preview and publish.")