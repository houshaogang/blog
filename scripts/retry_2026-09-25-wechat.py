#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retry script: wechat-publish-2026-09-25
Generated: 2026-09-25
Reason: IP 125.121.126.197 not in WeChat whitelist
Fix: Add 125.121.126.197 to mp.weixin.qq.com IP whitelist
"""

import json, os, re, urllib.request, urllib.parse, uuid

ENV_PATH = "D:/blog/scripts/.env"
ARTICLE_PATH = r"D:/blog/content/posts/2026-09-25-我们都在朋友圈表演快乐却把真实留给了陌生人.html"
COVER_PATH = r"D:/blog/covers/cover_2026-09-25_我们都在朋友圈表演快.jpg"
TITLE = "我们都在朋友圈表演快乐，却把真实留给了陌生人"
DIGEST = "我们精心经营朋友圈的完美人设，却把最真实的自己留给了陌生人。别把最好的自己留给陌生人，把最真的自己留给最亲的人。"

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
    f"Content-Type: image/jpeg\r\n\r\n"
).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

req = urllib.request.Request(upload_url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read().decode("utf-8"))

thumb_media_id = result.get("media_id")
if not thumb_media_id:
    print(f"Upload error: {result}")
    exit(1)
print(f"OK: {thumb_media_id}")

# 4. Create draft
print("Creating draft...")
# Read article content
with open(ARTICLE_PATH, "r", encoding="utf-8") as f:
    article_content = f.read()

draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
draft_data = {
    "articles": [{
        "title": TITLE,
        "author": "深夜解忧铺",
        "digest": DIGEST,
        "content": article_content,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }]
}
data = json.dumps(draft_data, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(draft_url, data=data, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read().decode("utf-8"))

if "media_id" in result:
    print(f"✅ Draft created! media_id: {result['media_id']}")
else:
    print(f"Draft error: {result}")
