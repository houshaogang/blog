#!/usr/bin/env python3
"""
重试创建草稿脚本 - 2026-08-03
运行方式: python D:/blog/scripts/retry_2026-08-03.py
前提: 将 IP 183.159.200.104 添加到微信公众号白名单
"""
import json, urllib.request

# === 配置 ===
APP_ID = "wx4f7ec5527892c5d6"

# 从 .env 读取 secret
APP_SECRET = ""
with open("D:/blog/scripts/.env", "r", encoding="utf-8") as f:
    for line in f:
        if "WEIXIN_APP_SECRET" in line:
            APP_SECRET = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

TITLE = "一个人住的第三年，我终于不再为孤独感到羞耻"
DIGEST = "独居三年，从害怕一个人吃饭到享受一个人的夜晚，我终于学会了和自己相处。"
THUMB_PATH = "D:/blog/content/posts/cover_2026-08-02-pursuit-of-happyness.png"
HTML_PATH = "D:/blog/content/posts/2026-08-03-living-alone-third-year-chungking-express.html"

# === 获取 token ===
def get_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "access_token" not in data:
        print(f"❌ 获取token失败: {data}")
        return None
    return data["access_token"]

# === 上传封面 ===
def upload_cover(token):
    boundary = "----FormBoundary"
    with open(THUMB_PATH, "rb") as f:
        img_data = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.png\"\r\nContent-Type: image/png\r\n\r\n").encode() + img_data + f"\r\n--{boundary}--\r\n".encode()
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in data:
        print(f"❌ 上传封面失败: {data}")
        return None
    print(f"✅ 封面上传成功: {data['media_id'][:30]}...")
    return data["media_id"]

# === 创建草稿 ===
def create_draft(token, thumb_media_id):
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    article = {
        "title": TITLE[:64],
        "digest": DIGEST[:120],
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "content_source_url": "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }
    
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    # 关键: ensure_ascii=False 保持中文
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    
    if "media_id" in data:
        print(f"✅ 草稿创建成功! media_id: {data['media_id']}")
        return data["media_id"]
    else:
        print(f"❌ 草稿创建失败: {data}")
        return None

# === 验证 ===
def verify_draft(token):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
    payload = json.dumps({"offset": 0, "count": 1, "no_content": 1}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    
    items = data.get("item", [])
    if items:
        title = items[0].get("content", {}).get("news_item", [{}])[0].get("title", "")
        print(f"✅ 验证标题: {title}")
        if any(ord(c) > 0x4e00 for c in title):
            print("✅ 中文编码正常!")
        else:
            print("⚠️ 标题可能有编码问题")
    return data

# === 主流程 ===
if __name__ == "__main__":
    print("🔄 开始重试创建草稿...")
    token = get_token()
    if not token:
        exit(1)
    
    thumb_id = upload_cover(token)
    if not thumb_id:
        exit(1)
    
    media_id = create_draft(token, thumb_id)
    if media_id:
        verify_draft(token)
    
    print("\n📋 操作提示:")
    print(f"  文章标题: {TITLE}")
    print(f"  文章MD: D:/blog/content/posts/2026-08-03-living-alone-third-year-chungking-express.md")
    print(f"  文章HTML: D:/blog/content/posts/2026-08-03-living-alone-third-year-chungking-express.html")
    print("  请登录微信公众号后台 → 草稿箱 → 发表")
    print("  最佳发布时间: 21:00-23:00")
