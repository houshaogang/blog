#!/usr/bin/env python3
"""Retry WeChat API after IP whitelist update"""
import json, os, re, requests
from pathlib import Path

BLOG_DIR = Path(r"D:\blog")
POSTS_DIR = BLOG_DIR / "content" / "posts"

# Load env
env = {}
for line in open(BLOG_DIR / "scripts" / ".env", "r", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()

app_id = env["WEIXIN_APP_ID"]
app_secret = env["WEIXIN_APP_SECRET"]

# 1. Get access token
print("1. Getting access token...")
resp = requests.get(f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}")
data = resp.json()
if "access_token" not in data:
    print(f"❌ Failed: {data}")
    exit(1)
token = data["access_token"]
print(f"✅ Token: {token[:15]}...")

# 2. Upload cover
print("\n2. Uploading cover...")
cover = POSTS_DIR / "cover_2026-08-23-midnight-scrolling-chungking-express.png"
with open(cover, "rb") as f:
    files = {"media": ("cover.png", f, "image/png")}
    resp = requests.post(f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image", files=files)
upload = resp.json()
if "media_id" not in upload:
    print(f"❌ Upload failed: {upload}")
    exit(1)
thumb_id = upload["media_id"]
print(f"✅ thumb_media_id: {thumb_id}")

# 3. Read HTML content
print("\n3. Creating draft...")
html_path = POSTS_DIR / "2026-08-23-midnight-scrolling-chungking-express.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# 4. Create draft with proper encoding
article = {
    "title": "凌晨两点还在刷手机的人，心里都藏着一个王家卫",
    "digest": "你有多久没有在凌晨两点，安安静静地放下手机了？那种感觉，就像王家卫在《重庆森林》里拍的那样。",
    "content": html,
    "thumb_media_id": thumb_id,
    "content_source_url": ""
}
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
resp = requests.post(
    f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}",
    data=payload,
    headers={"Content-Type": "application/json; charset=utf-8"}
)
draft = resp.json()
if "media_id" not in draft:
    print(f"❌ Draft failed: {draft}")
    exit(1)

print(f"✅ Draft created! media_id: {draft['media_id']}")
print(f"\n📋 登录 mp.weixin.qq.com → 草稿箱 → 发表")
