#!/usr/bin/env python3
"""重试脚本：2026-08-13 创建微信草稿"""
import json, os, urllib.request, time
from pathlib import Path

# 加载凭据
env = {}
for line in open(r"D:\blog\scripts\.env", "r", encoding="utf-8"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

# 获取 Token
token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={env['WEIXIN_APP_ID']}&secret={env['WEIXIN_APP_SECRET']}"
with urllib.request.urlopen(token_url, timeout=10) as resp:
    token_data = json.loads(resp.read().decode("utf-8"))
if "access_token" not in token_data:
    print(f"Token获取失败: {token_data}")
    exit(1)
access_token = token_data["access_token"]
print(f"Token获取成功")

# 读取 HTML
html_path = r"D:\blog\content\posts\2026-08-13-we-are-all-1900-standing-at-rail.html"
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# 上传封面
cover_path = r"D:\blog\content\posts\cover_2026-08-13-we-are-all-1900-standing-at-rail.png"
boundary = "----FormBoundary" + str(int(time.time()))
with open(cover_path, "rb") as f:
    cover_data = f.read()
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode() + cover_data + f"\r\n--{boundary}--\r\n".encode()

upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
req = urllib.request.Request(upload_url, data=body, headers={
    "Content-Type": f"multipart/form-data; boundary={boundary}"
})
with urllib.request.urlopen(req, timeout=30) as resp:
    upload_result = json.loads(resp.read().decode("utf-8"))
thumb_media_id = upload_result.get("media_id")
if not thumb_media_id:
    print(f"封面上传失败: {upload_result}")
    exit(1)
print(f"封面上传成功: {thumb_media_id}")

# 创建草稿（ensure_ascii=False！）
title = "我们都是1900，站在船舷边却不敢走上去"
digest = "我们这代人，都像1900一样站在船舷边，看着外面的世界，却始终不敢走上去。不是不想，是走不动了。"

draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
article = {
    "title": title[:64],
    "content": html_content,
    "thumb_media_id": thumb_media_id,
    "digest": digest[:120],
    "content_source_url": "",
    "need_open_comment": 1,
    "only_fans_can_comment": 0
}
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(draft_url, data=payload, headers={
    "Content-Type": "application/json; charset=utf-8"
})
with urllib.request.urlopen(req, timeout=30) as resp:
    draft_result = json.loads(resp.read().decode("utf-8"))

media_id = draft_result.get("media_id")
if media_id:
    print(f"草稿创建成功! media_id: {media_id}")
    # 验证中文编码
    verify_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={access_token}"
    verify_data = json.dumps({"offset": 0, "count": 1, "no_content": 1}, ensure_ascii=False).encode("utf-8")
    req2 = urllib.request.Request(verify_url, data=verify_data, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req2, timeout=10) as resp2:
        vr = json.loads(resp2.read().decode("utf-8"))
    items = vr.get("item", [])
    if items:
        vtitle = items[0].get("content", {}).get("title", "")
        print(f"验证标题: {vtitle}")
        print("中文编码正确" if "\\u" not in repr(vtitle) else "可能存在编码问题")
else:
    print(f"草稿创建失败: {draft_result}")
