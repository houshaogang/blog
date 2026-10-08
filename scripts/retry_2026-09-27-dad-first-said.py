#!/usr/bin/env python3
"""手动重试发布：我爸第一次说「我不懂」的时候，我愣了好久
当微信API白名单问题解决后运行此脚本
"""
import json, os, random, sys, urllib.request
from pathlib import Path

BLOG_DIR = Path(r"D:\blog")
COVERS_DIR = BLOG_DIR / "covers"

def load_env():
    env = {}
    for path in [BLOG_DIR / "scripts" / ".env",
                 Path(os.environ.get("USERPROFILE", "")) / "AppData/Local/hermes/.env"]:
        if path.exists():
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def get_token(env):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={env['WEIXIN_APP_ID']}&secret={env['WEIXIN_APP_SECRET']}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode()).get("access_token")

def upload_image(token, path):
    boundary = "----FormBoundary"
    with open(path, "rb") as f:
        data = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode()).get("media_id")

def create_draft(token, title, content, thumb_media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    article = {"title": title[:64], "content": content, "thumb_media_id": thumb_media_id,
               "content_source_url": "", "need_open_comment": 1, "only_fans_can_comment": 0}
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode()).get("media_id")

def main():
    env = load_env()
    token = get_token(env)
    print(f"✅ Token获取成功")

    title = "我爸第一次说「我不懂」的时候，我愣了好久"
    slug = "cover_2026-09-27_我爸第一次说我不懂的"
    cover = COVERS_DIR / f"{slug}.jpg"

    thumb_id = upload_image(token, str(cover))
    if not thumb_id:
        print("❌ 封面上传失败"); return
    print(f"📤 封面上传成功: {thumb_id[:30]}...")

    content_file = Path(r"D:\blog\content\posts\2026-09-27-dad-first-said-i-dont-know.md")
    content = content_file.read_text(encoding="utf-8")

    media_id = create_draft(token, title, content, thumb_id)
    if media_id:
        print(f"✅ 草稿创建成功! media_id: {media_id}")
    else:
        print("❌ 草稿创建失败")

if __name__ == "__main__":
    main()
