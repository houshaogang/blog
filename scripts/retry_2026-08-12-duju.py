#!/usr/bin/env python3
"""
重试脚本：添加IP白名单后执行此脚本创建草稿。
当前被阻断IP: 115.196.111.119
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

def get_token(app_id, app_secret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "access_token" in data:
        return data["access_token"]
    raise Exception(f"Token failed: {data}")

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

def create_draft(token, title, digest, html_content, thumb_media_id):
    article = {
        "title": title[:64],
        "digest": digest[:120],
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "content_source_url": "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }
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
            news = item.get("content", {}).get("news_item", [{}])[0]
            t = news.get("title", "")
            if "\\u" in repr(t):
                raise Exception(f"Chinese garbled in title: {t}")
            return True, t
    return False, ""

if __name__ == "__main__":
    TITLE = "独居之后，我终于和自己成为了朋友"
    DIGEST = "一个人住的第一年，我以为孤独会把我吞掉。三年后才发现，那些一个人的夜晚，是我离自己最近的时刻。"
    COVER_PATH = "D:/blog/content/posts/cover_2026-08-12-duju.png"
    HTML_PATH = "D:/blog/content/posts/2026-08-12-duju-dijiannian-hezijijiaopengyou.html"

    print("1. 获取 access_token...")
    app_id, app_secret = load_credentials()
    token = get_token(app_id, app_secret)
    print(f"   ✓ {token[:15]}...")

    print("2. 上传封面图...")
    thumb_id = upload_cover(token, COVER_PATH)
    print(f"   ✓ {thumb_id[:30]}...")

    print("3. 创建草稿...")
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()
    draft_id = create_draft(token, TITLE, DIGEST, html, thumb_id)
    print(f"   ✓ media_id: {draft_id}")

    print("4. 验证草稿...")
    ok, verified_title = verify_draft(token, draft_id)
    if ok:
        print(f"   ✓ 验证通过，标题: {verified_title}")
    else:
        print("   ⚠️ 未在最近5条草稿中找到（可能需要手动检查）")

    print(f"\n✅ 完成！media_id: {draft_id}")
