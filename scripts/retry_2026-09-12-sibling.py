# -*- coding: utf-8 -*-
"""
微信公众号草稿发布 - 重试脚本
IP 白名单通过后运行此脚本即可发布今日文章
用法: python D:/blog/scripts/retry_2026-09-12-sibling.py
"""
import os, sys, json, re, urllib.request

APP_ID = "wx4f7ec5527892c5d6"
ENV_FILE = r"D:\blog\scripts\.env"
ARTICLE_PATH = r"D:\blog\content\posts\2026-09-12-sibling-distance.md"
COVER_PATH = r"D:\blog\content\posts\2026-09-12-cover-sibling.png"
TITLE = "小时候抢遥控器的那个人，现在连微信都不回了"
DIGEST = "小时候抢遥控器、偷零食、惹你生气的那个人，现在连见一面都难。不是谁做错了什么，就是长大了。"

def get_secret():
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "APP_SECRET" in line and "=" in line:
                return line.strip().split("=", 1)[1].strip()
    raise Exception("找不到 APP_SECRET")

def md_to_html(md_text):
    lines = md_text.split("\n")
    html = []
    in_bq = False
    def inline(t):
        t = re.sub(r"\*\*(.+?)\*\*", r'<strong style="font-weight:bold;color:#222;">\1</strong>', t)
        return t
    for line in lines:
        s = line.strip()
        if not s:
            if in_bq:
                html.append("</blockquote>")
                in_bq = False
            html.append("<br/>")
            continue
        if s == "---":
            if in_bq:
                html.append("</blockquote>")
                in_bq = False
            html.append('<hr style="border:none;border-top:1px solid #ddd;margin:24px 0">')
            continue
        if s.startswith(">"):
            if not in_bq:
                html.append('<blockquote style="border-left:3px solid #c0392b;padding:8px 16px;margin:16px 0;background:#fafafa">')
                in_bq = True
            content = inline(s.lstrip("> ").strip())
            html.append(f'<p style="margin:4px 0;font-size:16px;line-height:1.8;color:#333">{content}</p>')
            continue
        if in_bq:
            html.append("</blockquote>")
            in_bq = False
        processed = inline(s)
        html.append(f'<p style="margin:0 0 16px 0;font-size:16px;line-height:1.8;color:#333">{processed}</p>')
    if in_bq:
        html.append("</blockquote>")
    return "\n".join(html)

def main():
    print(f"📱 微信公众号草稿发布 - 重试脚本")
    print(f"📅 2026-09-12")
    print()

    # Step 1: Get access_token
    secret = get_secret()
    print("🔑 获取 access_token...")
    token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={secret}"
    with urllib.request.urlopen(token_url, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    
    if "access_token" not in data:
        print(f"❌ 获取 token 失败: {data}")
        sys.exit(1)
    
    access_token = data["access_token"]
    print(f"✅ Token 获取成功")

    # Step 2: Upload cover
    print(f"📤 上传封面图...")
    upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(COVER_PATH, "rb") as f:
        cover_data = f.read()
    filename = os.path.basename(COVER_PATH)
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"media\"; filename=\"{filename}\"\r\n"
        f"Content-Type: image/png\r\n\r\n"
    ).encode("utf-8") + cover_data + f"\r\n--{boundary}--\r\n".encode("utf-8")
    
    req = urllib.request.Request(upload_url, data=body)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        upload_data = json.loads(resp.read().decode("utf-8"))
    
    if "media_id" not in upload_data:
        print(f"❌ 封面上传失败: {upload_data}")
        sys.exit(1)
    
    thumb_media_id = upload_data["media_id"]
    print(f"✅ 封面上传成功: {thumb_media_id}")

    # Step 3: Read and convert article
    print(f"📝 转换文章为 HTML...")
    with open(ARTICLE_PATH, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # Remove title line
    lines = md_content.split("\n")
    body_lines = []
    skip = True
    for line in lines:
        if skip and line.startswith("# "):
            skip = False
            continue
        body_lines.append(line)
    md_body = "\n".join(body_lines)
    
    body_html = md_to_html(md_body)
    article_html = f"""<section style="max-width:100%;padding:0;margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
{body_html}
<hr style="border:none;border-top:1px solid #e0e0e0;margin:32px 0 16px 0">
<p style="text-align:center;font-size:14px;color:#999;margin:8px 0">深夜解忧铺</p>
<p style="text-align:center;font-size:13px;color:#bbb;margin:4px 0">你的心事有人听</p>
</section>"""

    # Step 4: Create draft
    print(f"📤 创建草稿...")
    article_data = {
        "title": TITLE,
        "author": "",
        "digest": DIGEST,
        "content": article_html,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }
    
    draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    payload = json.dumps({"articles": [article_data]}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(draft_url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        draft_result = json.loads(resp.read().decode("utf-8"))
    
    media_id = draft_result.get("media_id")
    if media_id:
        print(f"\n✅ 草稿创建成功！")
        print(f"   media_id: {media_id}")
    else:
        print(f"\n❌ 草稿创建失败: {json.dumps(draft_result, ensure_ascii=False)}")

if __name__ == "__main__":
    main()
