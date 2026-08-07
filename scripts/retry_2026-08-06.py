#!/usr/bin/env python3
"""
重试脚本：IP白名单添加后执行此脚本创建草稿。
当前阻断IP: 183.159.200.104
"""
import json, os, sys, urllib.request

# ===== 从 .env 读取凭据 =====
def load_credentials(env_path="D:/blog/scripts/.env"):
    env_vars = {}
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip().strip('"').strip("'")
    return env_vars.get('WEIXIN_APP_ID', ''), env_vars.get('WEIXIN_APP_SECRET', '')

# ===== 获取 access_token =====
def get_token(app_id, app_secret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "access_token" in data:
        return data["access_token"]
    raise Exception(f"Token failed: {data}")

# ===== 上传封面图 =====
def upload_cover(token, cover_path):
    boundary = "----RetryBoundary"
    with open(cover_path, "rb") as f:
        file_data = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" in result:
        return result["media_id"]
    raise Exception(f"Upload failed: {result}")

# ===== 创建草稿 =====
def create_draft(token, title, digest, html_content, thumb_media_id):
    article = {
        "title": title[:64],
        "digest": digest[:120],
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "content_source_url": "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0
        # ⚠️ 不要传 author — 会报 45110
    }
    # ⚠️ 关键：用 ensure_ascii=False 防止中文乱码
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json; charset=utf-8"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" in result:
        return result["media_id"]
    raise Exception(f"Draft failed: {result}")

# ===== 验证草稿 =====
def verify_draft(token, media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
    payload = json.dumps({"offset": 0, "count": 5, "no_content": 1}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json; charset=utf-8"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    for item in result.get("item", []):
        if item.get("media_id") == media_id:
            title_check = item.get("content", {}).get("news_item", [{}])[0].get("title", "")
            if "\\u" in repr(title_check):
                raise Exception(f"Chinese garbled in title: {title_check}")
            return True, title_check
    return False, ""

# ===== 硬编码文章信息 =====
TITLE = "人到中年，连哭都变成了一种奢侈"
DIGEST = "小时候哭是一种本能，长大后哭变成了一种奢侈。《入殓师》告诉我们：能哭出来，是一种能力。"
COVER_PATH = "D:/blog/content/posts/cover_2026-08-06-人到中年连哭都变成了一种奢侈.png"
HTML_PATH = "D:/blog/content/posts/2026-08-06-人到中年连哭都变成了一种奢侈.html"

if __name__ == "__main__":
    print("1. 读取凭据...")
    app_id, app_secret = load_credentials()
    if not app_id or not app_secret:
        print("ERROR: 未找到凭据，请检查 D:/blog/scripts/.env")
        sys.exit(1)
    print(f"   ✓ app_id: {app_id[:8]}...")

    print("2. 获取 access_token...")
    token = get_token(app_id, app_secret)
    print(f"   ✓ {token[:15]}...")

    print("3. 上传封面图...")
    thumb_id = upload_cover(token, COVER_PATH)
    print(f"   ✓ {thumb_id[:30]}...")

    print("4. 读取HTML...")
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()
    print(f"   ✓ {len(html)} 字符")

    print("5. 创建草稿...")
    draft_id = create_draft(token, TITLE, DIGEST, html, thumb_id)
    print(f"   ✓ media_id: {draft_id}")

    print("6. 验证草稿...")
    ok, checked_title = verify_draft(token, draft_id)
    print(f"   ✓ 标题: {checked_title}")
    print(f"   ✓ 验证: {'通过' if ok else '未找到'}")

    print(f"\n🎉 完成！media_id: {draft_id}")
