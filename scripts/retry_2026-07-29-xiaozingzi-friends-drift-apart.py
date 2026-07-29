#!/usr/bin/env python3
"""重试脚本 - 2026-07-29 成年人的友情散场
IP白名单添加后运行此脚本即可完成草稿创建。
"""

import os, json, re, datetime, urllib.request, urllib.parse, time, io

TODAY = "2026-07-29"
SLUG = "xiaozingzi-friends-drift-apart"
POSTS_DIR = "D:/blog/content/posts"
COVER_PATH = os.path.join(POSTS_DIR, f"cover_{TODAY}-{SLUG}.png")
HTML_PATH = os.path.join(POSTS_DIR, f"{TODAY}-{SLUG}.html")

# 读取微信凭证
env_lines = []
with open("D:/blog/scripts/.env", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            env_lines.append(line)

APP_ID = APP_SECRET = None
for line in env_lines:
    if line.startswith("WEIXIN_APP_ID="):
        APP_ID = line.split("=", 1)[1].strip()
    elif line.startswith("WEIXIN_APP_SECRET="):
        APP_SECRET = line.split("=", 1)[1].strip()

print(f"APP_ID: {APP_ID}")

# 1. 获取 access_token
token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
req = urllib.request.Request(token_url)
with urllib.request.urlopen(req, timeout=30) as resp:
    token_data = json.loads(resp.read().decode("utf-8"))

if "access_token" not in token_data:
    print(f"❌ 获取 access_token 失败: {token_data}")
    exit(1)

access_token = token_data["access_token"]
print(f"✅ access_token 获取成功")

# 2. 上传封面图
upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
with open(COVER_PATH, "rb") as f:
    img_data = f.read()

boundary = f"----WebKitFormBoundary{int(time.time()*1000)}"
body = io.BytesIO()
body.write(f"--{boundary}\r\n".encode("utf-8"))
body.write(f'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'.encode("utf-8"))
body.write(b"Content-Type: image/png\r\n\r\n")
body.write(img_data)
body.write(f"\r\n--{boundary}--\r\n".encode("utf-8"))
payload = body.getvalue()

upload_req = urllib.request.Request(upload_url, data=payload, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
with urllib.request.urlopen(upload_req, timeout=30) as resp:
    upload_result = json.loads(resp.read().decode("utf-8"))

if "media_id" not in upload_result:
    print(f"❌ 上传失败: {upload_result}")
    exit(1)

thumb_media_id = upload_result["media_id"]
print(f"✅ thumb_media_id: {thumb_media_id}")

# 3. 读取HTML
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html_content = f.read()

# 4. 创建草稿（ensure_ascii=False）
draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
article = {
    "title": "成年人的友情散场，从来不是因为吵了一架",
    "digest": "不是讨厌，不是吵架，就是没话可说了。我们不是不想对方了，是真的没有多余的精力了。",
    "content": html_content,
    "content_source_url": "",
    "thumb_media_id": thumb_media_id,
    "need_open_comment": 1,
    "only_fans_can_comment": 0,
}
data = {"articles": [article]}
payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
draft_req = urllib.request.Request(draft_url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(draft_req, timeout=30) as resp:
    draft_result = json.loads(resp.read().decode("utf-8"))

if "media_id" in draft_result:
    print(f"\n🎉 草稿创建成功！")
    print(f"media_id: {draft_result['media_id']}")
else:
    print(f"\n❌ 草稿创建失败: {draft_result}")
