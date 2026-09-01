# -*- coding: utf-8 -*-
"""
微信公众号草稿发布 - 重试脚本
IP 白名单通过后运行此脚本即可发布今日文章
用法: D:/python310/python.exe D:/blog/scripts/retry_2026-09-01.py
"""
import os
import sys
import json
import re
import time
import requests
import markdown

# --- 配置 ---
APP_ID = "wx4f7ec5527892c5d6"
ENV_FILE = r"D:\blog\scripts\.env"
ARTICLE_PATH = r"D:\blog\content\posts\2026-09-01-midnight-reread-little-prince-healing.md"
COVER_PATH = r"D:\blog\content\posts\cover_2026-09-01-midnight-reread-little-prince.png"
TITLE = "凌晨重读《小王子》，终于明白大人为什么需要被治愈"
DIGEST = "小时候觉得小王子好可怜，长大后才发现，我们早就变成了那些大人。凌晨两点，重读这本写给大人的童话。"

def get_secret():
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "APP_SECRET" in line and "=" in line:
                return line.strip().split("=", 1)[1].strip()
    raise Exception("找不到 APP_SECRET")

def main():
    print(f"📱 微信公众号草稿发布 - 重试脚本")
    print(f"📅 2026-09-01")
    print()

    # Step 1: Get access_token
    secret = get_secret()
    print("🔑 获取 access_token...")
    token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={secret}"
    resp = requests.get(token_url, timeout=10)
    data = resp.json()

    if "access_token" not in data:
        print(f"❌ 获取 token 失败: {data}")
        sys.exit(1)

    access_token = data["access_token"]
    print(f"✅ Token 获取成功")

    # Step 2: Upload cover
    print(f"📤 上传封面图...")
    upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    with open(COVER_PATH, "rb") as f:
        resp = requests.post(upload_url, files={"media": ("cover.png", f, "image/png")}, timeout=30)
    upload_data = resp.json()

    if "media_id" not in upload_data:
        print(f"❌ 封面上传失败: {upload_data}")
        sys.exit(1)

    thumb_media_id = upload_data["media_id"]
    print(f"✅ 封面上传成功: {thumb_media_id}")

    # Step 3: Read and convert article
    print(f"📝 转换文章为 HTML...")
    with open(ARTICLE_PATH, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Remove frontmatter
    md_content = re.sub(r'^---\n.*?---\n', '', md_content, flags=re.DOTALL)
    html_body = markdown.markdown(md_content, extensions=['extra', 'nl2br'])

    # Add inline styles
    html_body = html_body.replace('<p>', '<p style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 16px;">')
    html_body = html_body.replace('<h1>', '<h1 style="font-size: 24px; color: #333; text-align: center; margin: 30px 0 20px;">')
    html_body = html_body.replace('<h2>', '<h2 style="font-size: 20px; color: #333; margin: 25px 0 15px; border-left: 4px solid #d4a574; padding-left: 12px;">')
    html_body = html_body.replace('<blockquote>', '<blockquote style="border-left: 3px solid #d4a574; padding: 12px 16px; margin: 20px 0; background: #faf8f5; color: #555; font-style: italic;">')
    html_body = html_body.replace('<em>', '<em style="color: #666;">')
    html_body = html_body.replace('<strong>', '<strong style="color: #333;">')
    html_body = html_body.replace('<hr>', '<hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">')
    html_body = html_body.replace('<hr />', '<hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">')

    html_content = '<section style="padding: 10px; max-width: 100%;">\n' + html_body + '\n</section>'

    # Step 4: Create draft
    print(f"📋 创建草稿...")
    draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    article = {
        "title": TITLE,
        "author": "",
        "digest": DIGEST,
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }

    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    resp = requests.post(draft_url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"}, timeout=30)
    result = resp.json()

    if "media_id" in result:
        print(f"✅ 草稿创建成功！")
        print(f"📌 media_id: {result['media_id']}")
        print(f"📌 请到公众号后台 → 草稿箱 → 发布")
    else:
        print(f"❌ 草稿创建失败: {result}")

if __name__ == "__main__":
    main()
