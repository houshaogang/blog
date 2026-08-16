#!/usr/bin/env python3
"""
Retry script: create WeChat draft for 2026-08-16 article
Run after adding IP to WeChat whitelist: python D:/blog/scripts/retry_2026-08-16.py
"""
import json, os, urllib.request

TITLE = "总有一天你会发现，他们已经老了"
DIGEST = "你有没有认真看过父母的样子？他们不是突然变老的，是一点一点变老的。"
HTML_PATH = r"D:\blog\content\posts\2026-08-16-one-day-you-will-notice-they-are-old.html"
COVER_PATH = r"D:\blog\content\posts\cover_2026-08-16-one-day-you-will-notice-they-are-old.png"

# Load credentials
env = {}
env_path = r"D:\blog\scripts\.env"
with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

APP_ID = env.get("WEIXIN_APP_ID") or env.get("WECHAT_APP_ID")
APP_SECRET = env.get("WEIXIN_APP_SECRET") or env.get("WECHAT_APP_SECRET")

# 1. Get Access Token
token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
req = urllib.request.Request(token_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    token_data = json.loads(resp.read().decode("utf-8"))
if "access_token" not in token_data:
    print(f"ERROR: {token_data}")
    exit(1)
access_token = token_data["access_token"]
print(f"[1/4] access_token obtained: {access_token[:20]}...")

# 2. Upload Cover Image
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
with open(COVER_PATH, "rb") as f:
    cover_data = f.read()

cover_fn = os.path.basename(COVER_PATH)
cover_body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="media"; filename="{cover_fn}"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode("utf-8") + cover_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
upload_req = urllib.request.Request(upload_url, data=cover_body, headers={
    "Content-Type": f"multipart/form-data; boundary={boundary}",
    "User-Agent": "Mozilla/5.0"
})
with urllib.request.urlopen(upload_req, timeout=60) as resp:
    upload_data = json.loads(resp.read().decode("utf-8"))

if "media_id" not in upload_data:
    print(f"ERROR uploading cover: {upload_data}")
    exit(1)
thumb_media_id = upload_data["media_id"]
print(f"[2/4] Cover uploaded: {thumb_media_id}")

# 3. Read HTML Content
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html_content = f.read()
print(f"[3/4] HTML content loaded: {len(html_content)} chars")

# 4. Create Draft
article = {
    "title": TITLE,
    "digest": DIGEST,
    "content": html_content,
    "thumb_media_id": thumb_media_id,
    "need_open_comment": 1,
    "only_fans_can_comment": 0
}

draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
draft_req = urllib.request.Request(draft_url, data=payload, headers={
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": "Mozilla/5.0"
})
with urllib.request.urlopen(draft_req, timeout=30) as resp:
    draft_data = json.loads(resp.read().decode("utf-8"))

if "media_id" in draft_data:
    media_id = draft_data["media_id"]
    print(f"[4/4] Draft created! media_id: {media_id}")
    
    # Verify
    batch_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={access_token}"
    verify_payload = json.dumps({"offset": 0, "count": 1, "no_content": 1}, ensure_ascii=False).encode("utf-8")
    verify_req = urllib.request.Request(batch_url, data=verify_payload, headers={
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Mozilla/5.0"
    })
    with urllib.request.urlopen(verify_req, timeout=30) as vresp:
        vdata = json.loads(vresp.read().decode("utf-8"))
    
    if vdata.get("item"):
        item = vdata["item"][0]
        check_title = item.get("content", {}).get("news_item", [{}])[0].get("title", "")
        print(f"\n=== VERIFICATION ===")
        print(f"Title in draft: {check_title}")
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in check_title)
        if has_chinese:
            print("Chinese characters verified - no encoding issues!")
        else:
            print("Warning: Title may have encoding issues")
    print(f"\nDONE! Draft media_id: {media_id}")
    print("Login to WeChat MP backend -> Drafts -> Publish")
else:
    print(f"ERROR creating draft: {draft_data}")
