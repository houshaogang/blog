# -*- coding: utf-8 -*-
"""
重试脚本：添加IP 183.158.17.39 到微信公众号白名单后运行此脚本。
文章：30岁才看懂《小王子》：成年人的孤独，是一场与自己和解的旅程
用法：python D:/blog/scripts/retry_2026-08-22.py
"""

import json, os, re, sys, urllib.request

APP_ID_FILE = r"D:\blog\scripts\.env"
COVER_PATH = r"D:\blog\content\posts\cover_2026-08-22-midnight-reread-classic.png"
ARTICLE_PATH = r"D:\blog\content\posts\2026-08-22-midnight-reread-classic.md"
TITLE = "30岁才看懂《小王子》：成年人的孤独，是一场与自己和解的旅程"
DIGEST = "小时候读小王子只觉得温柔，长大后再翻开才发现写的全是不敢承认的人生。三十岁以后才明白，他不是在看星星，他是在想一个人。"


def load_env():
    env = {}
    for path in [APP_ID_FILE, os.path.expanduser(r"~\AppData\Local\hermes\.env")]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#") or not line or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def md_to_html(md_text):
    style = 'style="font-size: 16px; line-height: 1.8; color: #333; font-family: -apple-system, BlinkMacSystemFont, sans-serif;"'
    lines = md_text.strip().split("\n")
    html = []
    skip = True
    for line in lines:
        s = line.strip()
        if skip and not s:
            continue
        if skip and s.startswith("# "):
            skip = False
            continue
        skip = False
        if s == "---":
            html.append('<hr style="border:none;border-top:1px solid #e0e0e0;margin:24px 0;">')
            continue
        if s.startswith("> **") and s.endswith("**"):
            text = s[2:].strip().strip("*").strip("*")
            html.append('<p {}><strong style="font-size:18px;color:#555;">{}</strong></p>'.format(style, text))
            continue
        if s.startswith("> "):
            text = s[2:].strip()
            html.append('<blockquote style="border-left:4px solid #ddd;padding-left:16px;margin:16px 0;color:#666;">{}</blockquote>'.format(text))
            continue
        if s.startswith("## "):
            text = s[3:].strip()
            html.append('<h2 style="font-size:20px;color:#333;margin:32px 0 16px;border-bottom:1px solid #eee;padding-bottom:8px;">{}</h2>'.format(text))
            continue
        if s.startswith("# ") and not skip:
            text = s[2:].strip()
            html.append('<h1 style="font-size:24px;color:#222;margin:0 0 16px;text-align:center;">{}</h1>'.format(text))
            continue
        if not s:
            html.append('<p style="margin:12px 0;">&nbsp;</p>')
            continue
        # Handle bold text
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        html.append('<p {}>{}</p>'.format(style, s))

    # Add footer
    html.append('<hr style="border:none;border-top:1px solid #e0e0e0;margin:40px 0 24px;">')
    html.append('<p style="text-align:center;color:#999;font-size:14px;margin:8px 0;">深夜解忧铺</p>')
    html.append('<p style="text-align:center;color:#999;font-size:14px;margin:8px 0;">你的心事，有人听。</p>')

    return "\n".join(html)


def upload_image(token, path):
    boundary = "----FormBoundary"
    with open(path, "rb") as f:
        data = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.png\"\r\nContent-Type: image/png\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def create_draft(token, article_data):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    payload = json.dumps({"articles": [article_data]}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def verify_draft(token, media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
    payload = json.dumps({"offset": 0, "count": 5, "no_content": 1}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    for item in result.get("item", []):
        if item.get("media_id") == media_id:
            title = item.get("content", {}).get("news_item", [{}])[0].get("title", "")
            if "\u" in repr(title) and "\\u" not in repr(title):
                print(f"  ✓ Title verified (real Chinese): {title}")
                return True
            else:
                print(f"  ✗ Title appears garbled: {repr(title)}")
                return False
    print(f"  ✗ Draft not found with media_id: {media_id}")
    return False


def main():
    print("=" * 60)
    print("微信公众号草稿发布 - 2026-08-22")
    print("=" * 60)

    env = load_env()
    token = None
    for url in [
        f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={env['WEIXIN_APP_ID']}&secret={env['WEIXIN_APP_SECRET']}",
    ]:
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                token = data.get("access_token")
                if token:
                    break
        except:
            pass

    if not token:
        print("ERROR: Failed to get access_token. IP may not be in whitelist.")
        print("请在微信公众号后台 -> 开发 -> 基本配置 -> IP白名单 中添加: 183.158.17.39")
        return

    print(f"1. Got access_token ({len(token)} chars)")

    # Upload cover
    if not os.path.exists(COVER_PATH):
        print(f"ERROR: Cover not found: {COVER_PATH}")
        return
    upload_result = upload_image(token, COVER_PATH)
    thumb_media_id = upload_result.get("media_id")
    if not thumb_media_id:
        print(f"ERROR: Upload failed: {upload_result}")
        return
    print(f"2. Cover uploaded: {thumb_media_id}")

    # Read and convert markdown
    with open(ARTICLE_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()
    html_content = md_to_html(md_text)
    print(f"3. Markdown converted to HTML ({len(html_content)} chars)")

    # Create draft
    article = {
        "title": TITLE,
        "author": "",
        "digest": DIGEST,
        "content": html_content,
        "content_source_url": "",
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }
    draft_result = create_draft(token, article)
    media_id = draft_result.get("media_id")
    if not media_id:
        print(f"ERROR: Draft creation failed: {draft_result}")
        return
    print(f"4. Draft created: media_id={media_id}")

    # Verify
    print("5. Verifying draft title encoding...")
    verify_draft(token, media_id)

    print("\n" + "=" * 60)
    print("SUCCESS! Draft published.")
    print(f"  Title: {TITLE}")
    print(f"  media_id: {media_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
