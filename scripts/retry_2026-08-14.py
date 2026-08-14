#!/usr/bin/env python3
"""
Retry script: create WeChat draft for 2026-08-14 article
Run after adding IP to WeChat whitelist: python D:/blog/scripts/retry_2026-08-14.py
"""

import json, urllib.request, os

# --- Config ---
TITLE = "你有多久没有认真为自己做一顿饭了"
DIGEST = "一个人住这么久，连好好喂饱自己都做不到。从冰箱里翻出半棵白菜和两个鸡蛋，认认真真炒了一盘醋溜白菜，那间住了三年的房子第一次有了家的感觉。"
HTML_PATH = r"D:\blog\content\posts\2026-08-14-cooking-for-one-little-forest.html"
COVER_PATH = r"D:\blog\content\posts\cover_2026-08-14-cooking-for-one-little-forest.png"

# --- Load credentials ---
env = {}
env_path = r"D:\blog\scripts\.env"
with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

APP_ID = env["WEIXIN_APP_ID"]
APP_SECRET = env["WEIXIN_APP_SECRET"]

# --- Step 1: Get access_token ---
token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
with urllib.request.urlopen(token_url, timeout=15) as resp:
    token_data = json.loads(resp.read().decode("utf-8"))

if "access_token" not in token_data:
    print(f"ERROR getting token: {token_data}")
    exit(1)

access_token = token_data["access_token"]
print(f"[1/4] Access token obtained")

# --- Step 2: Upload cover image ---
boundary = "----FormBoundary"
with open(COVER_PATH, "rb") as f:
    cover_data = f.read()

body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode() + cover_data + f"\r\n--{boundary}--\r\n".encode()

upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
req = urllib.request.Request(upload_url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
with urllib.request.urlopen(req, timeout=30) as resp:
    upload_result = json.loads(resp.read().decode("utf-8"))

thumb_media_id = upload_result.get("media_id")
if not thumb_media_id:
    print(f"ERROR uploading cover: {upload_result}")
    exit(1)
print(f"[2/4] Cover uploaded, media_id: {thumb_media_id}")

# --- Step 3: Read HTML content ---
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html_content = f.read()
print(f"[3/4] HTML content loaded ({len(html_content)} chars)")

# --- Step 4: Create draft ---
draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
article = {
    "title": TITLE[:64],
    "content": html_content,
    "thumb_media_id": thumb_media_id,
    "digest": DIGEST[:120],
    "content_source_url": "",
    "need_open_comment": 1,
    "only_fans_can_comment": 0
}
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(draft_url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as resp:
    draft_result = json.loads(resp.read().decode("utf-8"))

media_id = draft_result.get("media_id")
if media_id:
    print(f"[4/4] Draft created! media_id: {media_id}")
else:
    print(f"[4/4] ERROR creating draft: {draft_result}")
    exit(1)

# --- Step 5: Verify draft ---
verify_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={access_token}"
verify_payload = json.dumps({"offset": 0, "count": 1, "no_content": 1}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(verify_url, data=verify_payload, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=15) as resp:
    verify_data = json.loads(resp.read().decode("utf-8"))

items = verify_data.get("item", [])
if items:
    latest = items[0].get("content", {})
    vtitle = latest.get("title", "")
    print(f"\n=== Verification ===")
    print(f"Title: {vtitle}")
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in vtitle)
    print(f"Contains real Chinese: {has_chinese}")
    if has_chinese:
        print("✅ Chinese encoding correct!")
    else:
        print("❌ Possible encoding issue - check title")
else:
    print("Could not verify draft")

print(f"\n=== Done ===")
print(f"Title: {TITLE}")
print(f"media_id: {media_id}")
