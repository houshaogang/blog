#!/usr/bin/env python3
"""Retry script: create WeChat draft after IP is whitelisted."""
import json, os, urllib.request, struct

APP_ID = "wx4f7ec5527892c5d6"
APP_SECRET = "e509360e9e5a326d287ea70757771be9"
TITLE = "三十岁以后，我终于和自己和解了"
COVER_PATH = r"D:/blog/content/posts/cover_2026-07-26.png"
HTML_PATH = r"D:/blog/content/posts/2026-07-26-三十岁以后我终于和自己和解了.html"

def get_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "access_token" in data:
        print(f"✅ Token obtained")
        return data["access_token"]
    print(f"❌ Token failed: {data}")
    return None

def upload_cover(token):
    boundary = "----FormBoundary"
    with open(COVER_PATH, "rb") as f:
        file_data = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.png\"\r\nContent-Type: image/png\r\n\r\n").encode() + file_data + f"\r\n--{boundary}--\r\n".encode()
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" in result:
        print(f"✅ Cover uploaded: {result['media_id'][:30]}...")
        return result["media_id"]
    print(f"❌ Upload failed: {result}")
    return None

def create_draft(token, thumb_media_id):
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()
    article = {
        "title": TITLE[:64],
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "content_source_url": "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" in result:
        print(f"✅ Draft created! media_id: {result['media_id']}")
        return result["media_id"]
    print(f"❌ Draft failed: {result}")
    return None

if __name__ == "__main__":
    token = get_token()
    if token:
        thumb_id = upload_cover(token)
        if thumb_id:
            draft_id = create_draft(token, thumb_id)
            if draft_id:
                print(f"\n🎉 All done! media_id: {draft_id}")
