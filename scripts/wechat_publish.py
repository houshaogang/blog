#!/usr/bin/env python3
"""
微信公众号文章发布脚本（带封面自动生成）
用法: python wechat_publish.py --title "标题" --file article.md
"""

import argparse
import json
import os
import random
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

BLOG_DIR = Path(r"D:\blog")
POSTS_DIR = BLOG_DIR / "content" / "posts"
COVERS_DIR = BLOG_DIR / "covers"

def load_env():
    env = {}
    for path in [BLOG_DIR / "scripts" / ".env", 
                 Path(os.environ.get("USERPROFILE", "")) / "AppData/Local/hermes/.env"]:
        if path.exists():
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def get_token(env):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={env['WEIXIN_APP_ID']}&secret={env['WEIXIN_APP_SECRET']}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8")).get("access_token")

def create_cover(title, output_path):
    """生成渐变背景+文字封面 (900x383)"""
    from PIL import Image, ImageDraw, ImageFont
    size = (900, 383)
    img = Image.new('RGB', size)
    draw = ImageDraw.Draw(img)
    
    palettes = [
        ((30, 41, 59), (71, 85, 105)),
        ((44, 62, 80), (52, 152, 219)),
        ((39, 174, 96), (22, 160, 133)),
        ((142, 68, 173), (192, 57, 43)),
        ((41, 128, 185), (22, 160, 133)),
    ]
    c = random.choice(palettes)
    for y in range(size[1]):
        r = y / size[1]
        draw.line([(0, y), (size[0], y)], fill=tuple(
            int(c[0][i] * (1 - r) + c[1][i] * r) for i in range(3)))
    
    try:
        font = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", 36)
    except:
        font = ImageFont.load_default()
    
    max_w = size[0] - 80
    lines, line = [], ""
    for ch in title:
        if draw.textbbox((0, 0), line + ch, font=font)[2] > max_w:
            lines.append(line)
            line = ch
        else:
            line += ch
    if line:
        lines.append(line)
    lines = lines[:3]
    
    y0 = (size[1] - len(lines) * 50) // 2
    for i, ln in enumerate(lines):
        bb = draw.textbbox((0, 0), ln, font=font)
        draw.text(((size[0] - bb[2] + bb[0]) // 2, y0 + i * 50), ln, fill='white', font=font)
    
    img.save(output_path, quality=95)

def upload_image(token, path):
    boundary = "----FormBoundary"
    with open(path, "rb") as f:
        data = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8")).get("media_id")

def create_draft(token, title, content, thumb_media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    article = {"title": title[:64], "content": content, "thumb_media_id": thumb_media_id,
               "content_source_url": "", "need_open_comment": 1, "only_fans_can_comment": 0}
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8")).get("media_id")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--file", help="从文件读取内容")
    parser.add_argument("--content", help="直接传入内容")
    parser.add_argument("--no-wechat", action="store_true")
    args = parser.parse_args()
    
    content = args.content or (open(args.file, "r", encoding="utf-8").read() if args.file else "")
    if not content:
        print("❌ 必须指定 --content 或 --file")
        sys.exit(1)
    
    # 保存本地
    today = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r'[^\w\u4e00-\u9fff-]', '', args.title[:30]).replace(" ", "-")
    filepath = POSTS_DIR / f"{today}-{slug}.md"
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"💾 已保存: {filepath}")
    
    if not args.no_wechat:
        env = load_env()
        if env.get("WEIXIN_APP_ID") and env.get("WEIXIN_APP_SECRET"):
            token = get_token(env)
            COVERS_DIR.mkdir(parents=True, exist_ok=True)
            cover_path = COVERS_DIR / f"cover_{today}_{slug[:10]}.jpg"
            create_cover(args.title, str(cover_path))
            print(f"🎨 封面生成: {cover_path}")
            
            thumb_id = upload_image(token, str(cover_path))
            if thumb_id:
                print(f"📤 封面上传成功")
                media_id = create_draft(token, args.title, content, thumb_id)
                if media_id:
                    print(f"✅ 微信草稿创建成功! media_id: {media_id[:30]}...")
                else:
                    print("❌ 草稿创建失败")
            else:
                print("❌ 封面上传失败")
        else:
            print("⚠️ 微信配置缺失，跳过推送")
    
    print(f"📝 博客: https://houshaogang.github.io/blog/")

if __name__ == "__main__":
    main()
