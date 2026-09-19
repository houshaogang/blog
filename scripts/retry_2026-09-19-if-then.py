#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号发布重试脚本
日期: 2026-09-19
文章: 如果当时勇敢一点，现在会不会不一样

使用方法:
1. 先在 mp.weixin.qq.com → 设置与开发 → 基本配置 → IP白名单 添加: 36.27.6.10
2. 运行: python D:/blog/scripts/retry_2026-09-19-if-then.py
"""

import json, os, re, sys, urllib.request

# === 配置 ===
TITLE = "如果当时勇敢一点，现在会不会不一样"
DIGEST = "如果当时勇敢一点，现在会不会不一样？人到中年才懂：遗憾不是没有得到，而是没有去要。"
MD_PATH = r"D:\blog\content\posts\2026-09-19-if-then.md"
COVER_PATH = r"D:\blog\content\posts\2026-09-19-cover-if-then.png"
ENV_PATH = r"D:\blog\scripts\.env"

# === 加载环境变量 ===
env = {}
with open(ENV_PATH, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

APP_ID = env["WEIXIN_APP_ID"]
APP_SECRET = env["WEIXIN_APP_SECRET"]
print(f"✅ APP_ID: {APP_ID[:6]}...")

# === Step 1: 获取 access_token ===
token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
with urllib.request.urlopen(token_url, timeout=10) as resp:
    token_data = json.loads(resp.read().decode("utf-8"))

if "access_token" not in token_data:
    print(f"❌ 获取token失败: {token_data}")
    sys.exit(1)

access_token = token_data["access_token"]
print(f"✅ access_token: {access_token[:20]}...")

# === Step 2: 上传封面图 ===
boundary = "----FormBoundary"
with open(COVER_PATH, "rb") as f:
    file_data = f.read()

body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
upload_req = urllib.request.Request(upload_url, data=body, headers={
    "Content-Type": f"multipart/form-data; boundary={boundary}"
})
with urllib.request.urlopen(upload_req, timeout=30) as resp:
    upload_result = json.loads(resp.read().decode("utf-8"))

print(f"📤 上传结果: {upload_result}")
thumb_media_id = upload_result.get("media_id", "")
if not thumb_media_id:
    print("❌ 上传封面失败")
    sys.exit(1)
print(f"✅ thumb_media_id: {thumb_media_id}")

# === Step 3: Markdown 转 HTML ===
with open(MD_PATH, "r", encoding="utf-8") as f:
    md_content = f.read()

# 去掉 frontmatter
md_body = re.sub(r"^---\n.*?---\n", "", md_content, flags=re.DOTALL).strip()

def md_to_html(md_text):
    lines = md_text.split("\n")
    html_parts = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s == "---":
            html_parts.append('<section style="border-top:1px solid #e0e0e0;margin:30px 0;"></section>')
        elif s.startswith("## "):
            num = s[3:].strip()
            html_parts.append(f'<h2 style="font-size:20px;color:#333;margin:30px 0 15px;font-weight:bold;border-left:4px solid #c0392b;padding-left:12px;">{num}</h2>')
        elif s.startswith("**") and s.endswith("**") and not s.startswith("**文"):
            text = s[2:-2]
            html_parts.append(f'<p style="font-size:16px;line-height:1.8;color:#333;text-align:center;font-weight:bold;margin:20px 0;">{text}</p>')
        elif s.startswith("*") and s.endswith("*") and not s.startswith("**"):
            text = s[1:-1]
            html_parts.append(f'<p style="font-size:16px;line-height:1.8;color:#888;text-align:center;font-style:italic;margin:30px 0;">{text}</p>')
        else:
            processed = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
            html_parts.append(f'<p style="font-size:16px;line-height:1.8;color:#333;margin:12px 0;">{processed}</p>')
    return "\n".join(html_parts)

body_html = md_to_html(md_body)

html_content = f"""<div style="max-width:677px;margin:0 auto;padding:20px;">
<p style="font-size:16px;line-height:1.8;color:#333;margin:12px 0;"><strong>文 / 深夜解忧铺</strong></p>
<hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
{body_html}
<hr style="border:none;border-top:1px solid #eee;margin:40px 0;">
<p style="font-size:14px;color:#999;text-align:center;">深夜解忧铺</p>
<p style="font-size:13px;color:#bbb;text-align:center;">你的心事，有人听。</p>
</div>"""

# === Step 4: 创建草稿 ===
article_data = {
    "title": TITLE,
    "author": "",
    "digest": DIGEST,
    "content": html_content,
    "thumb_media_id": thumb_media_id,
    "need_open_comment": 1,
    "only_fans_can_comment": 0
}

draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
payload = json.dumps({"articles": [article_data]}, ensure_ascii=False).encode("utf-8")
draft_req = urllib.request.Request(draft_url, data=payload, headers={
    "Content-Type": "application/json; charset=utf-8"
})

with urllib.request.urlopen(draft_req, timeout=30) as resp:
    draft_result = json.loads(resp.read().decode("utf-8"))

print(f"\n📝 草稿结果: {draft_result}")

if "media_id" in draft_result:
    media_id = draft_result["media_id"]
    print(f"\n✅ 草稿创建成功!")
    print(f"   media_id: {media_id}")
    print(f"   标题: {TITLE}")
    print(f"   请前往 mp.weixin.qq.com → 草稿箱 查看并发布")
else:
    print(f"\n❌ 草稿创建失败")
    sys.exit(1)

# === Step 5: 验证 ===
verify_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={access_token}"
verify_payload = json.dumps({"offset": 0, "count": 1, "no_content": 1}, ensure_ascii=False).encode("utf-8")
verify_req = urllib.request.Request(verify_url, data=verify_payload, headers={
    "Content-Type": "application/json; charset=utf-8"
})
with urllib.request.urlopen(verify_req, timeout=10) as resp:
    verify_result = json.loads(resp.read().decode("utf-8"))

if verify_result.get("item"):
    latest = verify_result["item"][0]
    news = latest.get("content", {}).get("news_item", [{}])[0]
    v_title = news.get("title", "")
    print(f"\n🔍 验证: 标题 = {v_title}")
    if "如果" in v_title:
        print("   ✅ 中文编码正确!")

print(f"\n==================================================")
print(f"发布完成！请在微信公众号后台草稿箱中查看。")
print(f"==================================================")
