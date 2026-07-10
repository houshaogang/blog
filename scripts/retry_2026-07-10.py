#!/usr/bin/env python3
\"\"\"WeChat Draft Creator - 2026-07-10
Run this after adding the server IP to mp.weixin.qq.com IP whitelist
Current IP: 60.176.225.97
\"\"\"
import requests, json, os, sys, time

ENV = r"D:\blog\scripts\.env"
HTML_PATH = r"D:\blog\content\posts\2026-07-10-parents-aging-speed.html"
COVER_DIR = r"D:\blog\content\posts"
TITLE = "你有多久，没有认真看看爸妈的脸了？"
DIGEST = "从龙应台《目送》到朱自清《背影》，聊聊我们来不及说出口的那些话。深夜，想给爸妈打个电话。"

def load_env():
    aid = aset = None
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if line.startswith("WECHAT_APP_ID="): aid = line.split("=",1)[1].strip().strip('"')
            elif line.startswith("WECHAT_APP_SECRET="): aset = line.split("=",1)[1].strip().strip('"')
    return aid, aset

def get_token(aid, aset):
    r = requests.get(f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={aid}&secret={aset}", timeout=15).json()
    if "access_token" in r: return r["access_token"]
    print(f"Token error: {r}"); return None

def find_cover():
    covers = sorted([os.path.join(COVER_DIR,f) for f in os.listdir(COVER_DIR) if f.startswith("cover_") and f.endswith((".png",".jpg"))], key=os.path.getmtime, reverse=True)
    return covers[0] if covers else None

def main():
    aid, aset = load_env()
    token = get_token(aid, aset)
    if not token: sys.exit(1)
    print(f"Token OK")

    cover = find_cover()
    if not cover: print("No cover"); sys.exit(1)
    print(f"Cover: {os.path.basename(cover)}")

    # Upload cover
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    with open(cover, "rb") as f:
        r = requests.post(url, files={"media": (os.path.basename(cover), f, "image/png")}, timeout=30).json()
    if "media_id" not in r: print(f"Upload error: {r}"); sys.exit(1)
    thumb_id = r["media_id"]
    print(f"thumb_media_id: {thumb_id}")

    # Read HTML
    with open(HTML_PATH, encoding="utf-8") as f: html = f.read()

    # Create draft - IMPORTANT: use ensure_ascii=False for Chinese!
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    article = {
        "title": TITLE[:64],
        "content": html,
        "thumb_media_id": thumb_id,
        "digest": DIGEST[:120],
        "content_source_url": "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    import urllib.request
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    if result.get("media_id"):
        print(f"DRAFT CREATED! media_id: {result['media_id']}")
    else:
        print(f"Draft error: {result}")

if __name__ == "__main__":
    main()