#!/usr/bin/env python3
"""
Retry draft: 30岁以后，我们是怎么弄丢自己的
IP to whitelist: 115.206.28.8
Run after adding IP to WeChat whitelist.
Usage: python retry_2026-08-01_30岁以后.py
"""
import json, os, urllib.request

def get_token():
    env = {}
    for path in ["D:/blog/scripts/.env", os.path.expanduser("~/AppData/Local/hermes/.env")]:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip().strip('"').strip("'")
    app_id = env.get("WEIXIN_APP_ID") or env.get("WECHAT_APP_ID")
    app_secret = env.get("WEIXIN_APP_SECRET") or env.get("WECHAT_APP_SECRET")
    url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}".format(app_id, app_secret)
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "access_token" in data:
        return data["access_token"]
    raise Exception("Token failed: {}".format(data))

def upload_cover(token, path):
    boundary = "----FormBoundary"
    with open(path, "rb") as f:
        file_data = f.read()
    body = ("--{}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".format(boundary)).encode() + file_data + ("\r\n--{}--\r\n".format(boundary)).encode()
    url = "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={}&type=image".format(token)
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "multipart/form-data; boundary={}".format(boundary)})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" in result:
        return result["media_id"]
    raise Exception("Upload failed: {}".format(result))

def create_draft(token, title, html_content, thumb_media_id):
    article = {
        "title": title[:64],
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "content_source_url": "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    url = "https://api.weixin.qq.com/cgi-bin/draft/add?access_token={}".format(token)
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" in result:
        return result["media_id"]
    raise Exception("Draft failed: {}".format(result))

def verify_draft(token, media_id):
    url = "https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={}".format(token)
    payload = json.dumps({"offset": 0, "count": 5, "no_content": 1}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    for item in result.get("item", []):
        if item.get("media_id") == media_id:
            t = item.get("content", {}).get("news_item", [{}])[0].get("title", "")
            if "\\u" in repr(t) and "30" not in t:
                return False
            return True
    return False

if __name__ == "__main__":
    TITLE = "30岁以后，我们是怎么弄丢自己的"
    COVER = r"D:\blog\covers\cover_2026-08-01_30岁以后我们是怎么弄丢自己的.jpg"
    HTML = r"D:\blog\content\posts\2026-08-01-30岁以后我们是怎么弄丢自己的.html"

    print("1. Getting access token...")
    token = get_token()
    print("   OK: {}...".format(token[:20]))

    print("2. Uploading cover...")
    thumb_id = upload_cover(token, COVER)
    print("   OK: {}...".format(thumb_id[:30]))

    print("3. Creating draft...")
    with open(HTML, "r", encoding="utf-8") as f:
        html = f.read()
    draft_id = create_draft(token, TITLE, html, thumb_id)
    print("   OK: {}".format(draft_id))

    print("4. Verifying...")
    ok = verify_draft(token, draft_id)
    if ok:
        print("   Verified OK")
    else:
        print("   WARNING: could not verify title encoding")

    print("\nDone! media_id: {}".format(draft_id))
