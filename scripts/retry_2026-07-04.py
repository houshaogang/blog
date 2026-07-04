#!/usr/bin/env python3
"""重试发布草稿"""
import json, os, requests, urllib.request, time

env_path = r"D:\blog\scripts\.env"
app_id = app_secret = None
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            if k.strip() == 'WECHAT_APP_ID': app_id = v.strip().strip('"').strip("'")
            elif k.strip() == 'WECHAT_APP_SECRET': app_secret = v.strip().strip('"').strip("'")

token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
resp = requests.get(token_url, timeout=10)
data = resp.json()
if 'access_token' not in data:
    print(f"Token error: {data}")
    exit(1)
token = data['access_token']

# Upload cover
cover = r"D:\blog\content\posts\cover_2026-07-04-0704-we-dream-of-grandmothers-hearth.png"
with open(cover, 'rb') as f:
    ur = requests.post(
        f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image",
        files={'media': ('cover.png', f, 'image/png')}
    ).json()
if 'media_id' not in ur:
    print(f"Upload error: {ur}")
    exit(1)
thumb = ur['media_id']

# Read HTML
with open(r"D:\blog\content\posts\2026-07-04-0704-we-dream-of-grandmothers-hearth.html", 'r', encoding='utf-8') as f:
    content = f.read()

# Create draft
article = {
    "title": "凌晨三点，我又梦见了外婆的灶台",
    "digest": "小时候最期待的事，是放暑假去外婆家。灶台的火光映着外婆的脸，那是回不去的原点。",
    "content": content,
    "thumb_media_id": thumb,
    "need_open_comment": 1,
    "only_fans_can_comment": 0
}
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(
    f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}",
    data=payload,
    headers={"Content-Type": "application/json; charset=utf-8"}
)
with urllib.request.urlopen(req, timeout=30) as r:
    result = json.loads(r.read().decode("utf-8"))
print(f"Result: {json.dumps(result, ensure_ascii=False)}")
