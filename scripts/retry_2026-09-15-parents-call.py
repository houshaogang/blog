# -*- coding: utf-8 -*-
"""
重试发布脚本 - 35岁以后我开始害怕接到爸妈的电话
错误: 40164 IP不在白名单 (125.119.125.179)
解决: 在 mp.weixin.qq.com → 设置与开发 → 基本配置 → IP白名单 添加 125.119.125.179
"""
import os, json, re, urllib.request, urllib.parse

# === 配置 ===
DRAFT_PATH = r"D:\blog\content\posts\2026-09-15-fear-parents-call.md"
COVER_PATH = r"D:\blog\content\posts\cover_2026-09-15-parents-call.png"

env = {}
with open(r"D:\blog\scripts\.env", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

APP_ID = env["WEIXIN_APP_ID"]
APP_SECRET = env["WEIXIN_APP_SECRET"]

# === 1. 获取 token ===
print("1. 获取 access_token...")
token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
with urllib.request.urlopen(urllib.request.Request(token_url), timeout=15) as r:
    token_data = json.loads(r.read().decode("utf-8"))
token = token_data.get("access_token")
if not token:
    raise Exception(f"Token 获取失败: {token_data}")
print(f"   ✅ token={token[:20]}...")

# === 2. 上传封面 ===
print("2. 上传封面图...")
upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
with open(COVER_PATH, "rb") as f:
    cover_data = f.read()
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode("utf-8") + cover_data + f"\r\n--{boundary}--\r\n".encode("utf-8")
req = urllib.request.Request(upload_url, data=body, headers={
    "Content-Type": f"multipart/form-data; boundary={boundary}"
})
with urllib.request.urlopen(req, timeout=30) as r:
    upload_result = json.loads(r.read().decode("utf-8"))
thumb_media_id = upload_result.get("media_id")
if not thumb_media_id:
    raise Exception(f"上传封面失败: {upload_result}")
print(f"   ✅ thumb_media_id={thumb_media_id}")

# === 3. Markdown → HTML ===
print("3. Markdown → HTML...")
with open(DRAFT_PATH, "r", encoding="utf-8") as f:
    md = f.read()

# 提取 frontmatter
fm_match = re.search(r"^---\n(.+?)\n---", md, re.DOTALL)
if fm_match:
    fm = fm_match.group(1)
    title_m = re.search(r'title:\s*"(.+?)"', fm)
    title = title_m.group(1) if title_m else "未命名"
    tags_m = re.search(r"tags:\s*\[(.+?)\]", fm)
    tags = tags_m.group(1) if tags_m else "情感"
    body_md = md[fm_match.end():].strip()
else:
    title = "未命名"
    tags = "情感"
    body_md = md

# 转 HTML
lines = body_md.split("\n")
html_parts = []
in_blockquote = False
for line in lines:
    line = line.strip()
    if not line:
        continue
    if line.startswith("---"):
        continue
    if line.startswith("## "):
        if in_blockquote:
            html_parts.append("</blockquote>")
            in_blockquote = False
        section = line[3:].strip()
        html_parts.append(f'<h2 style="font-size: 20px; font-weight: bold; color: #333; margin: 30px 0 15px 0; border-left: 4px solid #c0392b; padding-left: 12px;">{section}</h2>')
    elif line.startswith("**文 / 深夜解忧铺**"):
        html_parts.append(f'<p style="text-align: center; font-size: 14px; color: #888; margin: 20px 0;">{line}</p>')
    elif line.startswith("*") and line.endswith("*") and not line.startswith("**"):
        inner = line.strip("*")
        html_parts.append(f'<p style="text-align: center; font-size: 16px; line-height: 1.8; color: #555; font-style: italic; margin: 30px 0 10px 0;">{inner}</p>')
    elif line.startswith("> "):
        inner = line[2:]
        if not in_blockquote:
            html_parts.append('<blockquote style="border-left: 3px solid #c0392b; padding: 10px 15px; margin: 15px 0; background: #fdf2f2; color: #555;">')
            in_blockquote = True
        html_parts.append(f'<p style="font-size: 16px; line-height: 1.8; color: #555;">{inner}</p>')
    else:
        # 处理加粗
        processed = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        html_parts.append(f'<p style="font-size: 16px; line-height: 1.8; color: #333; margin: 10px 0;">{processed}</p>')
if in_blockquote:
    html_parts.append("</blockquote>")

article_html = "\n".join(html_parts)

# 摘要 (取第一段非空内容)
digest_text = re.sub(r"<[^>]+>", "", html_parts[1] if len(html_parts) > 1 else title)
digest_text = re.sub(r"[\*\#\>\-]", "", digest_text).strip()[:120]

# === 4. 创建草稿 ===
print("4. 创建草稿...")
draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
article = {
    "title": title,
    "digest": digest_text,
    "content": article_html,
    "thumb_media_id": thumb_media_id,
    "content_source_url": "",
}
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(draft_url, data=payload, headers={
    "Content-Type": "application/json; charset=utf-8"
})
with urllib.request.urlopen(req, timeout=30) as r:
    draft_result = json.loads(r.read().decode("utf-8"))

media_id = draft_result.get("media_id")
if not media_id:
    raise Exception(f"创建草稿失败: {draft_result}")
print(f"   ✅ 草稿 media_id: {media_id}")

# === 5. 验证 ===
print("5. 验证草稿...")
verify_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
verify_payload = json.dumps({"offset": 0, "count": 1, "no_content": 1}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(verify_url, data=verify_payload, headers={
    "Content-Type": "application/json; charset=utf-8"
})
with urllib.request.urlopen(req, timeout=15) as r:
    verify_result = json.loads(r.read().decode("utf-8"))
items = verify_result.get("item", [])
if items:
    latest = items[0].get("content", {}).get("news_item", [{}])[0]
    print(f"   最新草稿标题: {latest.get('title', 'N/A')}")

print("\n" + "="*50)
print("✅ 全部完成！")
print(f"   标题: {title}")
print(f"   草稿 ID: {media_id}")
print(f"   请到 mp.weixin.qq.com 后台预览并发布")
print("="*50)
