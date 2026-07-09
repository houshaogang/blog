#!/usr/bin/env python3
"""WeChat Draft Creator - 2026-07-09
Run this after adding the server IP to mp.weixin.qq.com IP whitelist"""
import requests, json, os, sys, time

ENV = r"D:\blog\scripts\.env"
HTML_PATH = r"D:\blog\content\posts\2026-07-09-parents-aging-rediscovering-love.html"
COVER_DIR = r"D:\blog\content\posts"
TITLE = "那一年，我终于看懂了《目送》里的父亲母亲"
DIGEST = "不是那种过年回家时匆匆一瞥，不是视频通话里隔着屏幕的模糊画面，而是真真切切、安安静静地，看看他们眼角多了几条皱纹，鬓角又白了几根头发，走路是不是比去年慢了一点。"

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
    covers = sorted([os.path.join(COVER_DIR,f) for f in os.listdir(COVER_DIR) if f.startswith("cover_") and f.endswith((".png",".jpg"))], reverse=True)
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

    # Create draft - CRITICAL: ensure_ascii=False
    article = {"title": TITLE, "digest": DIGEST, "content": html,
               "thumb_media_id": thumb_id, "content_source_url": "",
               "need_open_comment": 1, "only_fans_can_comment": 0}
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    r = requests.post(draft_url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"}, timeout=30).json()
    if "media_id" not in r: print(f"Draft error: {r}"); sys.exit(1)
    mid = r["media_id"]
    print(f"DRAFT CREATED: {mid}")

    # Verify
    vr = requests.post(f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}",
                       data=json.dumps({"offset":0,"count":5,"no_content":True}, ensure_ascii=False).encode("utf-8"),
                       headers={"Content-Type":"application/json; charset=utf-8"}, timeout=15).json()
    for item in vr.get("item", []):
        if item.get("media_id") == mid:
            art = item.get("content",{}).get("news_item",[{}])[0]
            print(f"Title verified: {art.get('title','')}")
    print("DONE!")

if __name__ == "__main__": main()
