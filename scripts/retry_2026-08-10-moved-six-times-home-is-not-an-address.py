#!/usr/bin/env python3
"""重试创建草稿 - IP白名单已添加后运行此脚本"""
import json, urllib.request
from pathlib import Path

BLOG_DIR = Path(r"D:\blog")
POSTS_DIR = BLOG_DIR / "content" / "posts"
SCRIPTS_DIR = BLOG_DIR / "scripts"

TITLE = "搬了六次家才明白，家从来不是一个地址"
DIGEST = "搬了六次家以后我才明白，家从来不是一个地址，而是一种被人惦记的感觉。"
HTML_PATH = str(POSTS_DIR / "2026-08-10-moved-six-times-home-is-not-an-address.html")
COVER_PATH = str(POSTS_DIR / "cover_2026-08-10-moved-six-times-home-is-not-an-address.png")

# Load env
env = {}
with open(str(SCRIPTS_DIR / ".env"), "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

APP_ID = env["WEIXIN_APP_ID"]
APP_SECRET = env["WEIXIN_APP_SECRET"]

# 1. Get token
token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
with urllib.request.urlopen(token_url, timeout=10) as resp:
    token_data = json.loads(resp.read().decode("utf-8"))
    access_token = token_data.get("access_token")
    if not access_token:
        print(f"❌ Token失败: {token_data}")
        exit(1)
    print(f"✅ Token: {access_token[:20]}...")

# 2. Upload cover
boundary = "----RetryBoundary"
with open(COVER_PATH, "rb") as f:
    img_data = f.read()
body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.png\"\r\nContent-Type: image/png\r\n\r\n").encode() + img_data + f"\r\n--{boundary}--\r\n".encode()
upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
req = urllib.request.Request(upload_url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
with urllib.request.urlopen(req, timeout=30) as resp:
    upload_data = json.loads(resp.read().decode("utf-8"))
    thumb_media_id = upload_data.get("media_id")
    if not thumb_media_id:
        print(f"❌ 封面上传失败: {upload_data}")
        exit(1)
    print(f"✅ 封面上传成功: {thumb_media_id[:30]}...")

# 3. Read HTML and create draft
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html_content = f.read()

article = {
    "title": TITLE[:64],
    "content": html_content,
    "thumb_media_id": thumb_media_id,
    "digest": DIGEST[:120],
    "content_source_url": "",
    "need_open_comment": 1,
    "only_fans_can_comment": 0
}
draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(draft_url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as resp:
    draft_data = json.loads(resp.read().decode("utf-8"))
    media_id = draft_data.get("media_id")
    if not media_id:
        print(f"❌ 草稿创建失败: {draft_data}")
        exit(1)
    print(f"✅ 草稿创建成功! media_id: {media_id}")

# 4. Verify
verify_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={access_token}"
verify_payload = json.dumps({"offset": 0, "count": 1, "no_content": 1}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(verify_url, data=verify_payload, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=15) as resp:
    verify_data = json.loads(resp.read().decode("utf-8"))
    items = verify_data.get("item", [])
    if items:
        content_item = items[0].get("content", {}).get("news_item", [{}])[0]
        print(f"🔍 验证标题: {content_item.get('title', '')}")

print(f"\n📋 草稿 media_id: {media_id}")
print(f"📝 标题: {TITLE}")
print("🎉 完成！请到公众号后台草稿箱发布。")
