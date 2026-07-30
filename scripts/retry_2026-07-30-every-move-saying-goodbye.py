#!/usr/bin/env python3
"""
重试脚本：创建草稿
生成时间：2026-07-30
当前IP需要添加到白名单
用法：python D:/blog/scripts/retry_2026-07-30-every-move-saying-goodbye.py
"""
import json, os, urllib.request
from pathlib import Path

BLOG_DIR = Path(r"D:\blog")
POSTS_DIR = BLOG_DIR / "content" / "posts"
SCRIPTS_DIR = BLOG_DIR / "scripts"

# Load env
env = {}
for path in [SCRIPTS_DIR / ".env"]:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")

app_id = env.get("WECHAT_APP_ID") or env.get("WEIXIN_APP_ID")
app_secret = env.get("WECHAT_APP_SECRET") or env.get("WEIXIN_APP_SECRET")

# Get token
token_url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=" + app_id + "&secret=" + app_secret
with urllib.request.urlopen(token_url, timeout=10) as resp:
    token_data = json.loads(resp.read().decode("utf-8"))
if "access_token" not in token_data:
    print("❌ Token获取失败:", token_data)
    exit(1)
token = token_data["access_token"]
print("✅ Token获取成功")

# Upload cover
cover_files = sorted(POSTS_DIR.glob("cover_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
if not cover_files:
    cover_files = sorted(POSTS_DIR.glob("cover_*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
cover_path = cover_files[0]
print("🎨 使用封面:", cover_path)

boundary = "----FormBoundary"
with open(cover_path, "rb") as f:
    data = f.read()
body = ("--" + boundary + "\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n").encode() + data + ("\r\n--" + boundary + "--\r\n").encode()
upload_url = "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=" + token + "&type=image"
req = urllib.request.Request(upload_url, data=body, headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
with urllib.request.urlopen(req, timeout=30) as resp:
    upload_data = json.loads(resp.read().decode("utf-8"))
thumb_media_id = upload_data.get("media_id")
if not thumb_media_id:
    print("❌ 封面上传失败:", upload_data)
    exit(1)
print("✅ 封面上传成功:", thumb_media_id[:30])

# Load HTML content
html_path = POSTS_DIR / "2026-07-30-every-move-saying-goodbye.html"
html_content = open(html_path, encoding="utf-8").read()

# Create draft with proper encoding
title_text = "每一次搬家都是在和过去的自己告别"
draft_url = "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=" + token
article = {
    "title": title_text[:64],
    "content": html_content,
    "thumb_media_id": thumb_media_id,
    "content_source_url": "",
    "need_open_comment": 1,
    "only_fans_can_comment": 0
}
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(draft_url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as resp:
    draft_data = json.loads(resp.read().decode("utf-8"))
media_id = draft_data.get("media_id")
if media_id:
    print("✅ 草稿创建成功! media_id:", media_id)
    # Verify title encoding
    verify_url = "https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=" + token
    verify_payload = json.dumps({"offset": 0, "count": 1, "no_content": 1}, ensure_ascii=False).encode("utf-8")
    req2 = urllib.request.Request(verify_url, data=verify_payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req2, timeout=15) as resp2:
        verify_data = json.loads(resp2.read().decode("utf-8"))
    items = verify_data.get("item", [])
    if items and items[0].get("content", {}).get("news_item"):
        item_title = items[0]["content"]["news_item"][0].get("title", "")
        print("✅ 标题验证:", item_title)
else:
    print("❌ 草稿创建失败:", draft_data)
