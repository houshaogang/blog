#!/usr/bin/env python3
"""
微信公众号草稿发布 - 重试脚本
运行前请确保：在 mp.weixin.qq.com 后台添加 IP 220.184.23.122 到白名单
设置路径：设置与开发 → 基本配置 → IP白名单
"""
import os
import json
import urllib.request
import glob
import re

BLOG_DIR = r"D:\blog"
POSTS_DIR = os.path.join(BLOG_DIR, "content", "posts")
ENV_PATH = os.path.join(BLOG_DIR, "scripts", ".env")

TITLE = "凌晨三点刷到老同学的朋友圈，我才明白有些关系真的会过期"
DIGEST = "从《触不可及》到《海上钢琴师》，聊聊那些我们走着走着就散了的朋友。凌晨三点，你会给谁发消息？"
HTML_PATH = os.path.join(POSTS_DIR, "2026-07-13-old-friends-expire.html")

def load_env():
    cfg = {}
    with open(ENV_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg

def get_token(cfg):
    url = (f"https://api.weixin.qq.com/cgi-bin/token?"
           f"grant_type=client_credential&appid={cfg['WECHAT_APP_ID']}&secret={cfg['WECHAT_APP_SECRET']}")
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    if 'access_token' not in data:
        print(f"❌ Token error: {data}")
        return None
    print(f"✅ Token OK")
    return data['access_token']

def find_cover():
    covers = sorted(
        glob.glob(os.path.join(POSTS_DIR, "cover_*.png")),
        key=os.path.getmtime, reverse=True
    )
    return covers[0] if covers else None

def upload_cover(token, path):
    boundary = "----FormBoundary"
    with open(path, "rb") as f:
        data = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode('utf-8') + data + f"\r\n--{boundary}--\r\n".encode('utf-8')
    
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(url, data=body)
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    
    if 'media_id' not in result:
        print(f"❌ Upload error: {result}")
        return None
    print(f"✅ Cover uploaded, media_id: {result['media_id'][:30]}...")
    return result['media_id']

def create_draft(token, title, content, thumb_media_id):
    article = {
        "title": title[:64],
        "content": content,
        "thumb_media_id": thumb_media_id,
        "digest": DIGEST[:120],
        "content_source_url": "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    # CRITICAL: ensure_ascii=False for Chinese characters!
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    
    if 'media_id' not in result:
        print(f"❌ Draft error: {result}")
        return None
    print(f"✅ Draft created! media_id: {result['media_id']}")
    return result['media_id']

def verify_draft(token, media_id):
    """Verify the draft was created with correct Chinese characters"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
    payload = json.dumps({"offset": 0, "count": 1}, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    
    items = result.get('item', [])
    if items:
        title = items[0].get('content', {}).get('news_item', [{}])[0].get('title', '')
        if '\\u' in title or len(title) < 5:
            print(f"⚠️  Possible encoding issue: title='{title}'")
            return False
        else:
            print(f"✅ Verified: title='{title}'")
            return True
    return True

def main():
    print("=" * 60)
    print("深夜解忧铺 - 微信公众号草稿发布")
    print("=" * 60)
    
    cfg = load_env()
    token = get_token(cfg)
    if not token:
        return
    
    cover = find_cover()
    if not cover:
        print("❌ No cover image found")
        return
    print(f"📸 Cover: {os.path.basename(cover)}")
    
    thumb_id = upload_cover(token, cover)
    if not thumb_id:
        return
    
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()
    
    media_id = create_draft(token, TITLE, html, thumb_id)
    if media_id:
        print(f"\n🎉 发布成功！")
        print(f"   标题: {TITLE}")
        print(f"   media_id: {media_id}")
        print(f"\n📋 后续操作:")
        print(f"   1. 登录 mp.weixin.qq.com")
        print(f"   2. 进入 草稿箱")
        print(f"   3. 找到文章，预览并发布")
        # Verify
        verify_draft(token, media_id)

if __name__ == "__main__":
    main()
