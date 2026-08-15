"""
Retry script for creating WeChat draft after IP whitelisting.
Current unlisted IP: 183.158.16.77
Run: python D:/blog/scripts/retry_draft_2026-08-15.py
"""
import json, os, re, sys
import urllib.request

# ===== Article Config =====
TITLE = "那些不再联系的朋友，从未真正忘记过你"
DIGEST = "深夜刷朋友圈突然刷到一张很久没见的脸想点个赞最后还是默默划走了不是不想是不知道该以什么身份去点这个赞"

# ===== Environment =====
env_path = "D:/blog/scripts/.env"
env_vars = {}
with open(env_path, "r") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip()

APP_ID = env_vars["WEIXIN_APP_ID"]
APP_SECRET = env_vars["WEIXIN_APP_SECRET"]

# ===== 1. Get Access Token =====
token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
req = urllib.request.Request(token_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    token_data = json.loads(resp.read().decode("utf-8"))
if "access_token" not in token_data:
    print(f"ERROR: {token_data}")
    sys.exit(1)
access_token = token_data["access_token"]
print(f"[1/4] access_token obtained: {access_token[:20]}...")

# ===== 2. Upload Cover Image =====
import glob
cover_files = sorted(glob.glob("D:/blog/content/posts/cover_*.png"), key=os.path.getmtime, reverse=True)
if not cover_files:
    print("ERROR: No cover images found in D:/blog/content/posts/")
    sys.exit(1)
cover_path = cover_files[0]
print(f"[2/4] Using cover: {os.path.basename(cover_path)}")

import mimetypes
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
with open(cover_path, "rb") as f:
    cover_data = f.read()

cover_body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="media"; filename="{os.path.basename(cover_path)}"\r\n'
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
    sys.exit(1)
thumb_media_id = upload_data["media_id"]
print(f"[2/4] Cover uploaded: {thumb_media_id}")

# ===== 3. Read HTML Content =====
html_path = "D:/blog/content/posts/2026-08-15-friends-who-drift-away.html"
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()
print(f"[3/4] HTML content loaded: {len(html_content)} chars")

# ===== 4. Create Draft =====
article = {
    "title": TITLE,
    "digest": DIGEST,
    "content": html_content,
    "thumb_media_id": thumb_media_id,
    "need_open_comment": 1,
    "only_fans_can_comment": 0
}

draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
# CRITICAL: ensure_ascii=False to preserve Chinese characters
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
    
    # Verify: fetch back and check title
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
        if "联系" in check_title or "朋友" in check_title:
            print("✓ Chinese characters verified - no encoding issues!")
        else:
            print("⚠ Title mismatch, please check manually")
    print(f"\n✅ DONE! Draft media_id: {media_id}")
    print(f"   Login to WeChat MP backend -> Drafts -> Publish")
else:
    print(f"ERROR creating draft: {draft_data}")
