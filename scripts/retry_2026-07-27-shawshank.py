#!/usr/bin/env python3
"""
Retry script for creating WeChat draft.
Run this after IP is added to whitelist:
  python D:\blog\scripts\retry_2026-07-27-shawshank.py
"""
import json, urllib.request, os

# --- Configuration ---
APP_ID = "wx4f7ec5527892c5d6"
APP_SECRET = open(r"D:\blog\scripts\.env", "r").read().split("WEIXIN_APP_SECRET=")[1].strip()

TITLE = "人到中年，我终于看懂了《肖申克的救赎》"
COVER_PATH = r"D:\blog\content\posts\cover_2026-07-26.png"
HTML_PATH = r"D:\blog\content\posts\2026-07-27-shawshank-midlife.html"

def get_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "access_token" not in data:
        raise Exception(f"Token failed: {data}")
    return data["access_token"]

def upload_cover(token):
    boundary = "----FormBoundary"
    with open(COVER_PATH, "rb") as f:
        file_data = f.read()
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="media"; filename="cover.png"\r\nContent-Type: image/png\r\n\r\n').encode() + file_data + f'\r\n--{boundary}--\r\n'.encode()
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in result:
        raise Exception(f"Upload failed: {result}")
    return result["media_id"]

def create_draft(token, html_content, thumb_media_id):
    article = {
        "title": TITLE[:64],
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "content_source_url": "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }
    # CRITICAL: ensure_ascii=False for Chinese
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in result:
        raise Exception(f"Draft failed: {result}")
    return result["media_id"]

def verify_draft(token, media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
    payload = json.dumps({"offset": 0, "count": 5, "no_content": 1}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    for item in result.get("item", []):
        if item.get("media_id") == media_id:
            title = item.get("content", {}).get("news_item", [{}])[0].get("title", "")
            if "\\\\u" in repr(title) or "\\u" in repr(title):
                print(f"WARNING: Title may be garbled: {title}")
            print(f"Verified title: {title}")
            return True
    return False

if __name__ == "__main__":
    print("1. Getting access token...")
    token = get_token()
    print(f"   OK: {token[:20]}...")

    print("2. Uploading cover...")
    thumb_id = upload_cover(token)
    print(f"   OK: {thumb_id}")

    print("3. Reading HTML...")
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    print("4. Creating draft...")
    draft_id = create_draft(token, html, thumb_id)
    print(f"   OK: {draft_id}")

    print("5. Verifying...")
    ok = verify_draft(token, draft_id)
    print(f"   {'OK' if ok else 'WARNING: could not verify'}")

    print(f"\\nDone! media_id: {draft_id}")
