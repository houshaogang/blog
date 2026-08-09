#!/usr/bin/env python3
"""
重试脚本：创建微信公众号草稿
IP白名单添加后运行此脚本即可完成草稿创建。
用法：python D:/blog/scripts/retry_2026-08-09.py
"""

import json, os, urllib.request

# 配置
APP_ID = "wx4f7ec5527892c5d6"
APP_SECRET = "e50936d3602d2301ce18d83f0e8961be9"

# 文章信息
TITLE = "故乡回不去，不是路太远，是有些人已经不在了"
DIGEST = "小时候觉得故乡好小，长大后才发现，故乡不是变小了，是里面住的人，一个一个地，悄悄搬走了。"

# 文件路径
HTML_PATH = r"D:/blog/content/posts/2026-08-09-hometown-cant-go-back.html"
COVER_PATH = r"D:/blog/content/posts/cover_2026-08-08-misunderstood.png"


def get_token():
    url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=" + APP_ID + "&secret=" + APP_SECRET
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "access_token" not in data:
        raise Exception("Token error: " + str(data))
    return data["access_token"]


def upload_cover(token):
    boundary = "----FormBoundary"
    with open(COVER_PATH, "rb") as f:
        img_data = f.read()
    body = ("--" + boundary + "\r\n"
            'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'
            "Content-Type: image/png\r\n\r\n").encode() + img_data + ("\r\n--" + boundary + "--\r\n").encode()
    url = "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=" + token + "&type=image"
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "multipart/form-data; boundary=" + boundary
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in data:
        raise Exception("Upload error: " + str(data))
    return data["media_id"]


def create_draft(token, thumb_media_id):
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
    url = "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=" + token
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json; charset=utf-8"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in data:
        raise Exception("Draft error: " + str(data))
    return data["media_id"]


def verify_draft(token):
    url = "https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=" + token
    payload = json.dumps({"offset": 0, "count": 1, "no_content": 1}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json; charset=utf-8"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    items = data.get("item", [])
    if items:
        latest = items[0].get("content", {}).get("news_item", [{}])[0]
        title = latest.get("title", "")
        has_chinese = any("\u4e00" <= c <= "\u9fff" for c in title)
        print("Verified title:", title)
        print("Contains real Chinese:", has_chinese)
        return has_chinese
    return False


if __name__ == "__main__":
    print("1. Getting access token...")
    token = get_token()
    print("   Token:", token[:20] + "...")
    
    print("2. Uploading cover image...")
    thumb_id = upload_cover(token)
    print("   media_id:", thumb_id)
    
    print("3. Creating draft...")
    draft_id = create_draft(token, thumb_id)
    print("   Draft media_id:", draft_id)
    
    print("4. Verifying draft...")
    verify_draft(token)
    
    print("\nDone!")
    print("Title:", TITLE)
    print("Media ID:", draft_id)
