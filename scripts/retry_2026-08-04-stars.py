#!/usr/bin/env python3
"""
Retry script for: 你有多久，没抬头看过星星了
Generated: 2026-08-04
Server IP to whitelist: 183.159.200.104
"""
import requests
import json
import re
import os
import sys

ENV_PATH = r"D:\\blog\\scripts\\.env"
MD_PATH = r"D:\\blog\\content\\posts\\2026-08-04-how-long-since-you-looked-at-stars.md"
COVER_PATH = r"D:\\blog\\content\\posts\\cover_2026-08-04-stars.png"
TITLE = "\u4f60\u6709\u591a\u4e45\uff0c\u6ca1\u5934\u770b\u8fc7\u661f\u661f\u4e86"
DIGEST = "\u5c0f\u65f6\u5019\u5916\u5a46\u8bf4\u6bcf\u9897\u661f\u661f\u90fd\u662f\u5b88\u62a4\u661f\uff0c\u957f\u5927\u540e\u6211\u4eec\u6d3b\u5728\u706f\u5149\u91cc\uff0c\u518d\u4e5f\u770b\u4e0d\u89c1\u5b83\u4eec"

def load_env(path):
    creds = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                creds[key.strip()] = val.strip().strip("\"'")
    return creds.get("WECHAT_APP_ID") or creds.get("WEIXIN_APP_ID"), \\
           creds.get("WECHAT_APP_SECRET") or creds.get("WEIXIN_APP_SECRET")

def get_access_token(app_id, app_secret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    resp = requests.get(url, timeout=15)
    data = resp.json()
    if "access_token" in data:
        return data["access_token"]
    print(f"Token error: {data}", file=sys.stderr)
    return None

def upload_cover(token, filepath):
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    with open(filepath, "rb") as f:
        resp = requests.post(url, files={"media": (os.path.basename(filepath), f, "image/png")}, timeout=30)
    data = resp.json()
    if "media_id" in data:
        return data["media_id"]
    print(f"Upload error: {data}", file=sys.stderr)
    return None

def markdown_to_html(md_content):
    body = re.sub(r"^---\\n.*?---\\n", "", md_content, flags=re.DOTALL).strip()
    body = re.sub(r"^### (.+)$", r'<h3 style="font-size:18px;font-weight:bold;color:#333;margin:24px 0 12px;">\\1</h3>', body, flags=re.MULTILINE)
    body = re.sub(r"^## (.+)$", r'<h2 style="font-size:20px;font-weight:bold;color:#333;margin:30px 0 16px;border-left:4px solid #8B4513;padding-left:12px;">\\1</h2>', body, flags=re.MULTILINE)
    body = re.sub(r"^# (.+)$", r'<h1 style="font-size:24px;font-weight:bold;color:#333;margin:0 0 20px;text-align:center;">\\1</h1>', body, flags=re.MULTILINE)
    body = re.sub(r"\\*\\*\\*(.+?)\\*\\*\\*", r"<strong><em>\\1</em></strong>", body)
    body = re.sub(r"\\*\\*(.+?)\\*\\*", r'<strong style="color:#222;font-weight:bold;">\\1</strong>', body)
    body = re.sub(r"\\*(.+?)\\*", r"<em>\\1</em>", body)
    body = re.sub(r"^---+$", r'<hr style="border:none;border-top:1px solid #ddd;margin:30px 0;">', body, flags=re.MULTILINE)
    paragraphs = body.split("\\n\\n")
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if p.startswith("<h") or p.startswith("<hr"):
            html_parts.append(p)
        else:
            p_html = p.replace("\\n", "<br>")
            html_parts.append(f'<p style="font-size:16px;line-height:1.8;color:#333;margin:0 0 16px;">{p_html}</p>')
    body_html = "\\n".join(html_parts)
    footer = "\\n<hr style=\\"border:none;border-top:1px solid #e0e0e0;margin:40px 0 20px;\\">\\n<div style=\\"text-align:center;margin:20px 0;\\">\\n<p style=\\"font-size:14px;color:#999;margin:0 0 8px;\\">深夜解忧铺</p>\\n<p style=\\"font-size:16px;color:#8B4513;font-weight:bold;margin:0;\\">你的心事，有人听</p>\\n</div>"
    return f'<section style="max-width:100%;padding:20px;font-family:-apple-system,BlinkMacSystemFont,\\'Segoe UI\\',\\'PingFang SC\\',\\'Hiragino Sans GB\\',\\'Microsoft YaHei\\',sans-serif;">\\n{body_html}\\n{footer}\\n</section>'

def create_draft(token, thumb_media_id, html_content, title, digest):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    article = {
        "title": title,
        "digest": digest,
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "content_source_url": "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    resp = requests.post(url, data=payload, headers=headers, timeout=30)
    result = resp.json()
    if "media_id" in result:
        return result["media_id"]
    print(f"Draft error: {result}", file=sys.stderr)
    return None

def main():
    print("=" * 50)
    print(f"WeChat Draft - {TITLE}")
    print("=" * 50)
    
    app_id, app_secret = load_env(ENV_PATH)
    if not app_id:
        print("Credentials not found", file=sys.stderr)
        sys.exit(1)
    
    token = get_access_token(app_id, app_secret)
    if not token:
        sys.exit(1)
    print("Access token OK")
    
    thumb_id = upload_cover(token, COVER_PATH)
    if not thumb_id:
        sys.exit(1)
    print(f"Cover uploaded: {thumb_id}")
    
    with open(MD_PATH, "r", encoding="utf-8") as f:
        html = markdown_to_html(f.read())
    
    media_id = create_draft(token, thumb_id, html, TITLE, DIGEST)
    if not media_id:
        sys.exit(1)
    print(f"Draft created: {media_id}")
    
    # Verify
    verify_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
    v_data = json.dumps({"offset": 0, "count": 5, "no_content": True}, ensure_ascii=False).encode("utf-8")
    v_headers = {"Content-Type": "application/json; charset=utf-8"}
    v_resp = requests.post(verify_url, data=v_data, headers=v_headers, timeout=15)
    v_result = v_resp.json()
    for item in v_result.get("item", []):
        if item.get("media_id") == media_id:
            articles = item.get("content", {}).get("news_item", [])
            if articles:
                print(f"Verified title: {articles[0].get('title', '')}")
    print(f"\nDONE - media_id: {media_id}")

if __name__ == "__main__":
    main()
