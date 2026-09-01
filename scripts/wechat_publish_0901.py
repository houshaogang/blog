# -*- coding: utf-8 -*-
"""WeChat Official Account: Get token, upload cover, create draft"""
import os
import sys
import json
import re
import time
import requests
import markdown

# --- Read .env ---
env_path = r"D:\blog\scripts\.env"
app_id = None
app_secret = None
with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if "APP_ID" in k:
                app_id = v
            elif "APP_SECRET" in k:
                app_secret = v

print(f"App ID: {app_id}")
print(f"App Secret: {app_secret[:6]}...{app_secret[-4:]}")

# --- Step 1: Get access_token ---
token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
resp = requests.get(token_url, timeout=10)
token_data = resp.json()
print(f"\nToken response: {json.dumps(token_data, ensure_ascii=False)}")

if "access_token" not in token_data:
    print("ERROR: Failed to get access_token!")
    sys.exit(1)

access_token = token_data["access_token"]
print(f"\naccess_token: {access_token[:20]}...")

# --- Step 2: Upload cover image ---
cover_path = r"D:\blog\content\posts\cover_2026-09-01-midnight-reread-little-prince.png"
upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"

with open(cover_path, "rb") as f:
    files = {"media": ("cover.png", f, "image/png")}
    resp = requests.post(upload_url, files=files, timeout=30)

upload_data = resp.json()
print(f"\nUpload response: {json.dumps(upload_data, ensure_ascii=False)}")

if "media_id" not in upload_data:
    print("ERROR: Failed to upload cover image!")
    sys.exit(1)

thumb_media_id = upload_data["media_id"]
print(f"thumb_media_id: {thumb_media_id}")

# --- Step 3: Read article and convert to HTML ---
article_path = r"D:\blog\content\posts\2026-09-01-midnight-reread-little-prince-healing.md"
with open(article_path, "r", encoding="utf-8") as f:
    md_content = f.read()

# Remove frontmatter
md_content = re.sub(r'^---\n.*?---\n', '', md_content, flags=re.DOTALL)

# Convert markdown to HTML
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

# Wrap in container
html_content = '<section style="padding: 10px; max-width: 100%;">\n' + html_body + '\n</section>'

# --- Step 4: Create draft ---
title = "凌晨重读《小王子》，终于明白大人为什么需要被治愈"
digest = "小时候觉得小王子好可怜，长大后才发现，我们早就变成了那些大人。凌晨两点，重读这本写给大人的童话。"

draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"

article = {
    "title": title,
    "author": "",
    "digest": digest,
    "content": html_content,
    "thumb_media_id": thumb_media_id,
    "need_open_comment": 1,
    "only_fans_can_comment": 0
}

# CRITICAL: Use ensure_ascii=False to preserve Chinese characters
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
headers = {"Content-Type": "application/json; charset=utf-8"}

resp = requests.post(draft_url, data=payload, headers=headers, timeout=30)
draft_data = resp.json()
print(f"\nDraft response: {json.dumps(draft_data, ensure_ascii=False)}")

if "media_id" not in draft_data:
    print("ERROR: Failed to create draft!")
    sys.exit(1)

draft_media_id = draft_data["media_id"]
print(f"\nDraft created! media_id: {draft_media_id}")

# --- Step 5: Verify draft content (check for encoding issues) ---
time.sleep(2)

batch_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={access_token}"
batch_payload = json.dumps({"offset": 0, "count": 1, "no_content": 0}, ensure_ascii=False).encode("utf-8")
resp = requests.post(batch_url, data=batch_payload, headers=headers, timeout=30)
batch_data = resp.json()

if batch_data.get("item"):
    latest = batch_data["item"][0]
    news = latest.get("content", {}).get("news_item", [])
    if news:
        latest_title = news[0].get("title", "")
        print(f"\nLatest draft title: {latest_title}")

        # Check for unicode escapes
        has_escape = False
        for i, c in enumerate(latest_title):
            if c == '\\' and i + 1 < len(latest_title) and latest_title[i + 1] == 'u':
                has_escape = True
                break
        if has_escape:
            print("WARNING: Possible encoding issue detected!")
        else:
            print("Title encoding looks correct (no unicode escapes)")
    else:
        print("Could not extract news_item from batch response")
else:
    print(f"Batch response: {json.dumps(batch_data, ensure_ascii=False)}")

print(f"\n{'='*50}")
print(f"Article title: {title}")
print(f"Word count: ~2300")
print(f"Draft media_id: {draft_media_id}")
print(f"Cover thumb_media_id: {thumb_media_id}")
print(f"{'='*50}")
