#!/usr/bin/env python3
"""
重试脚本：创建微信公众号草稿
日期：2026-08-17
标题：深夜看完灵魂急转弯，我终于和30岁的自己和解了

使用方法：
1. 先将当前服务器IP加入微信公众号白名单
2. 运行：python D:/blog/scripts/retry_2026-08-17-soul-soothing.py
"""
import json
import os
import urllib.request

# 配置
TITLE = "深夜看完灵魂急转弯，我终于和30岁的自己和解了"
DIGEST = "三十岁的你，也许没有达到二十岁时对自己的期待，但你经历了那些想象不到的风雨，依然在往前走。这就够了。"
HTML_PATH = r"D:\blog\content\posts\2026-08-17-soul-soothing-30s-reconcile.html"
COVER_PATH = r"D:\blog\content\posts\cover_2026-08-17-soul-soothing.png"

# 加载凭证
env = {}
env_path = r"D:\blog\scripts\.env"
with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

APP_ID = env.get("WEIXIN_APP_ID")
APP_SECRET = env.get("WEIXIN_APP_SECRET")

# 1. 获取 access_token
print("[1/5] 获取 access_token...")
token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
req = urllib.request.Request(token_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    token_data = json.loads(resp.read().decode("utf-8"))

if "access_token" not in token_data:
    print(f"ERROR: {token_data}")
    exit(1)

access_token = token_data["access_token"]
print(f"  ✅ access_token: {access_token[:20]}...")

# 2. 上传封面图
print("[2/5] 上传封面图...")
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
with open(COVER_PATH, "rb") as f:
    cover_data = f.read()

cover_fn = os.path.basename(COVER_PATH)
cover_body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="media"; filename="{cover_fn}"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode("utf-8") + cover_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
upload_req = urllib.request.Request(upload_url, data=cover_body, headers={
    "Content-Type": f"multipart/form-data; boundary={boundary}",
    "User-Agent": "Mozilla/5.0"
})
with urllib.request.urlopen(upload_req, timeout=60) as resp:
    upload_data = json.loads(resp.read().decode("utf-8"))

if "media_id" not in upload_data:
    print(f"ERROR uploading cover: {upload_data}")
    exit(1)

thumb_media_id = upload_data["media_id"]
print(f"  ✅ thumb_media_id: {thumb_media_id}")

# 3. 读取 HTML 内容
print("[3/5] 读取 HTML 内容...")
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html_content = f.read()
print(f"  ✅ HTML 长度: {len(html_content)} 字符")

# 4. 创建草稿（正确中文编码）
print("[4/5] 创建草稿...")
article = {
    "title": TITLE,
    "digest": DIGEST,
    "content": html_content,
    "thumb_media_id": thumb_media_id,
    "need_open_comment": 1,
    "only_fans_can_comment": 0
}

draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
draft_req = urllib.request.Request(draft_url, data=payload, headers={
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": "Mozilla/5.0"
})
with urllib.request.urlopen(draft_req, timeout=30) as resp:
    draft_data = json.loads(resp.read().decode("utf-8"))

if "media_id" not in draft_data:
    print(f"ERROR creating draft: {draft_data}")
    exit(1)

media_id = draft_data["media_id"]
print(f"  ✅ 草稿 media_id: {media_id}")

# 5. 验证草稿（检查中文编码）
print("[5/5] 验证草稿...")
batch_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={access_token}"
verify_payload = json.dumps({"offset": 0, "count": 1, "no_content": 1}, ensure_ascii=False).encode("utf-8")
verify_req = urllib.request.Request(batch_url, data=verify_payload, headers={
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": "Mozilla/5.0"
})
with urllib.request.urlopen(verify_req, timeout=30) as vresp:
    vdata = json.loads(vresp.read().decode("utf-8"))

items = vdata.get("item", [])
if items:
    first_title = items[0].get("content", {}).get("news_item", [{}])[0].get("title", "")
    if "\u" in first_title or not any(ord(c) > 127 for c in first_title):
        print(f"  ⚠️ 标题可能包含乱码: {first_title}")
        print(f"  正确标题应为: {TITLE}")
    else:
        print(f"  ✅ 标题验证通过: {first_title}")
else:
    print(f"  ⚠️ 无法验证草稿")

print(f"\n{'='*60}")
print(f"✅ 草稿创建成功!")
print(f"   标题: {TITLE}")
print(f"   media_id: {media_id}")
print(f"   操作提示: 请在微信公众号后台查看草稿并发布")
print(f"{'='*60}")
