#!/usr/bin/env python3
"""
重试脚本 - 2026-07-31
文章: 凌晨三点的便利店，藏着多少年轻人的秘密
问题: IP 60.176.236.20 不在微信公众号IP白名单中
使用方法: python D:/blog/scripts/retry_2026-07-31.py
前提: 用户已将IP 60.176.236.20 添加到 mp.weixin.qq.com → 设置与开发 → 基本配置 → IP白名单
"""
import os, json, re, urllib.request, urllib.parse

BLOG_DIR = r"D:\blog"
POSTS_DIR = os.path.join(BLOG_DIR, "content", "posts")

# ---- Load env ----
env = {}
env_path = os.path.join(BLOG_DIR, "scripts", ".env")
with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

app_id = env.get("WEIXIN_APP_ID") or env.get("WECHAT_APP_ID")
app_secret = env.get("WEIXIN_APP_SECRET") or env.get("WECHAT_APP_SECRET")

# ---- 1. Get token ----
token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
with urllib.request.urlopen(token_url, timeout=10) as resp:
    token_data = json.loads(resp.read().decode("utf-8"))
if "access_token" not in token_data:
    print(f"❌ Token获取失败: {token_data}")
    exit(1)
access_token = token_data["access_token"]
print(f"✅ Token获取成功")

# ---- 2. Upload cover ----
cover_path = r"D:\blog\covers\cover_2026-07-31_convenience.png"
boundary = "----FormBoundary"
with open(cover_path, "rb") as f:
    data = f.read()
body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.png\"\r\nContent-Type: image/png\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
req = urllib.request.Request(upload_url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
with urllib.request.urlopen(req, timeout=30) as resp:
    upload_result = json.loads(resp.read().decode("utf-8"))
thumb_media_id = upload_result.get("media_id")
if not thumb_media_id:
    print(f"❌ 封面上传失败: {upload_result}")
    exit(1)
print(f"✅ 封面上传成功: {thumb_media_id[:20]}...")

# ---- 3. Read HTML content ----
html_path = os.path.join(POSTS_DIR, "2026-07-31-convenience-store-at-3am.html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# ---- 4. Create draft ----
draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
article = {
    "title": "凌晨三点的便利店，藏着多少年轻人的秘密"[:64],
    "content": html_content,
    "thumb_media_id": thumb_media_id,
    "content_source_url": "",
    "need_open_comment": 1,
    "only_fans_can_comment": 0
}
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(draft_url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as resp:
    draft_result = json.loads(resp.read().decode("utf-8"))
media_id = draft_result.get("media_id")
if not media_id:
    print(f"❌ 草稿创建失败: {draft_result}")
    exit(1)
print(f"✅ 草稿创建成功! media_id: {media_id}")

# ---- 5. Verify ----
verify_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={access_token}"
verify_payload = json.dumps({"offset": 0, "count": 1, "no_content": 1}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(verify_url, data=verify_payload, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=10) as resp:
    verify_result = json.loads(resp.read().decode("utf-8"))
items = verify_result.get("item", [])
if items:
    latest = items[0].get("content", {}).get("news_item", [{}])[0]
    vtitle = latest.get("title", "")
    has_chinese = any("\u4e00" <= c <= "\u9fff" for c in vtitle)
    print(f"✅ 验证通过! 标题: {vtitle} (中文正常: {has_chinese})")
else:
    print("⚠️ 无法验证草稿")
