#!/usr/bin/env python3
"""
Retry script: Create WeChat draft after IP is whitelisted.
Run this after adding 183.156.234.239 to WeChat whitelist.
Usage: python D:/blog/scripts/retry_2026-08-08.py
"""
import json
import urllib.request
import urllib.error
import os

# --- Config ---
APP_ID = "wx4f7ec5527892c5d6"
# Read secret from .env
with open("D:/blog/scripts/.env", "r", encoding="utf-8") as f:
    for line in f:
        if "WEIXIN_APP_SECRET" in line:
            APP_SECRET = line.split("=", 1)[1].strip()
            break

TITLE = "你那么努力地活着，为什么还是没人真正懂你"
DIGEST = "被误解是人生的常态。你不必被所有人理解，但总有人会穿过人海看见你。"
COVER_PATH = "D:/blog/content/posts/cover_2026-08-08-misunderstood.png"
HTML_PATH = "D:/blog/content/posts/2026-08-08-misunderstood-is-normal-being-understood-is-luxury.html"

def get_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    resp = urllib.request.urlopen(url, timeout=15)
    data = json.loads(resp.read().decode("utf-8"))
    if "access_token" not in data:
        raise Exception(f"Token error: {data}")
    print(f"✅ Got access_token")
    return data["access_token"]

def upload_cover(token, cover_path):
    """Upload cover image as permanent material"""
    import mimetypes
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    with open(cover_path, "rb") as f:
        file_data = f.read()
    
    filename = os.path.basename(cover_path)
    content_type = mimetypes.guess_type(cover_path)[0] or "image/png"
    
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")
    
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(url, data=body)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode("utf-8"))
    
    if "media_id" not in result:
        raise Exception(f"Upload error: {result}")
    
    print(f"✅ Cover uploaded: {result['media_id']}")
    return result["media_id"]

def create_draft(token, thumb_media_id, html_content):
    """Create draft with ensure_ascii=False for proper Chinese encoding"""
    article = {
        "title": TITLE,
        "digest": DIGEST,
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }
    
    data = {"articles": [article]}
    
    # CRITICAL: Use ensure_ascii=False to prevent Chinese unicode escaping
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    req = urllib.request.Request(url, data=payload)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode("utf-8"))
    
    if "media_id" not in result:
        raise Exception(f"Draft error: {result}")
    
    print(f"✅ Draft created: media_id={result['media_id']}")
    return result["media_id"]

def verify_draft(token, media_id):
    """Verify the draft title contains real Chinese characters"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
    data = json.dumps({"offset": 0, "count": 1, "no_content": 1}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    
    resp = urllib.request.urlopen(req, timeout=15)
    result = json.loads(resp.read().decode("utf-8"))
    
    if "item" in result and result["item"]:
        item = result["item"][0]
        content = item.get("content", {})
        articles = content.get("news_item", [])
        if articles:
            title = articles[0].get("title", "")
            print(f"\n📋 Verification - Draft title: {title}")
            if "\\u" in repr(title) or "\u" in title:
                print("⚠️ WARNING: Title appears to have unicode escapes!")
                return False
            else:
                print("✅ Title contains proper Chinese characters")
                return True
    return False

if __name__ == "__main__":
    print("=" * 50)
    print("WeChat Draft Creator - Retry Script")
    print("=" * 50)
    
    # 1. Get token
    token = get_token()
    
    # 2. Upload cover
    thumb_media_id = upload_cover(token, COVER_PATH)
    
    # 3. Read HTML
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()
    print(f"📄 HTML content loaded ({len(html_content)} chars)")
    
    # 4. Create draft
    draft_media_id = create_draft(token, thumb_media_id, html_content)
    
    # 5. Verify
    verify_draft(token, draft_media_id)
    
    print(f"\n🎉 Done! Draft media_id: {draft_media_id}")
    print("Go to WeChat backend → 草稿箱 → 发表")
