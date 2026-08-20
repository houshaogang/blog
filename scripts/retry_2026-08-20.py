# -*- coding: utf-8 -*-
"""
重试脚本：添加IP 183.158.17.39 到微信公众号白名单后运行此脚本。
文章：凌晨三点的便利店，治愈了多少疲惫的灵魂
用法：python D:/blog/scripts/retry_2026-08-20.py
"""

import json, os, re, sys, time, urllib.request

APP_ID_FILE = r"D:\blog\scripts\.env"
COVER_PATH = r"D:\blog\content\posts\cover_2026-08-20-convenience-store-midnight.png"
ARTICLE_PATH = r"D:\blog\content\posts\2026-08-20-convenience-store-midnight.md"
TITLE = "凌晨三点的便利店，治愈了多少疲惫的灵魂"
DIGEST = "加班到深夜，整条街都暗了，只有便利店的灯还亮着。推门进去，热气扑面，关东煮冒着泡，店员说了句\u201c欢迎光临\u201d。一整天的疲惫，在这一刻被接住了。"


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
            html.append('<blockquote style="border-left:4px solid #ddd;padding-left:16px;margin:16px 0;color:#666;font-style:italic;">{}</blockquote>'.format(text))
            continue
        if s.startswith("## "):
            text = s[3:]
            html.append('<h2 style="font-size:20px;color:#333;margin:32px 0 16px;border-left:4px solid #c0392b;padding-left:12px;">{}</h2>'.format(text))
            continue
        if not s:
            html.append("")
            continue
        t = s
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"《(.+?)》", r"<em>《\1》</em>", t)
        html.append("<p {}>{}</p>".format(style, t))
    return "\n".join(html)


def main():
    print("=" * 50)
    print("深夜解忧铺 - 草稿创建脚本")
    print("=" * 50)

    print("\n[1/5] 加载凭证...")
    env = load_env()
    APP_ID = env.get("WEIXIN_APP_ID", "")
    APP_SECRET = env.get("WEIXIN_APP_SECRET", "")
    print("  APP_ID: {}...".format(APP_ID[:8]))

    print("\n[2/5] 获取 access_token...")
    token_url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}".format(APP_ID, APP_SECRET)
    req = urllib.request.Request(token_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        token_data = json.loads(resp.read().decode("utf-8"))
    if "access_token" not in token_data:
        print("  ❌ Token失败: {}".format(token_data))
        sys.exit(1)
    access_token = token_data["access_token"]
    print("  ✅ access_token: {}...".format(access_token[:20]))

    print("\n[3/5] 上传封面图...")
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = os.path.basename(COVER_PATH)
    with open(COVER_PATH, "rb") as f:
        file_data = f.read()
    body = ("--{}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"{}\"\r\nContent-Type: image/png\r\n\r\n").format(boundary, filename).encode("utf-8") + file_data + "\r\n--{}--\r\n".format(boundary).encode("utf-8")
    upload_url = "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={}&type=image".format(access_token)
    req = urllib.request.Request(upload_url, data=body, headers={"Content-Type": "multipart/form-data; boundary={}".format(boundary)})
    with urllib.request.urlopen(req, timeout=30) as resp:
        upload_result = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in upload_result:
        print("  ❌ 上传失败: {}".format(upload_result))
        sys.exit(1)
    thumb_media_id = upload_result["media_id"]
    print("  ✅ thumb_media_id: {}".format(thumb_media_id))

    print("\n[4/5] 转换 Markdown → HTML...")
    with open(ARTICLE_PATH, "r", encoding="utf-8") as f:
        md_content = f.read()
    html_content = md_to_html(md_content)
    footer = '<div style="text-align:center;margin-top:40px;padding-top:20px;border-top:1px solid #e0e0e0;"><p style="font-size:14px;color:#999;margin:8px 0;">深夜解忧铺</p><p style="font-size:16px;color:#666;margin:8px 0;font-weight:bold;">你的心事，有人听。晚安，陌生人。</p></div>'
    html_content += footer
    print("  HTML长度: {} 字符".format(len(html_content)))

    print("\n[5/5] 创建草稿...")
    article = {
        "title": TITLE[:64],
        "digest": DIGEST[:120],
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }
    draft_url = "https://api.weixin.qq.com/cgi-bin/draft/add?access_token={}".format(access_token)
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(draft_url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        draft_result = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in draft_result:
        print("  ❌ 草稿创建失败: {}".format(draft_result))
        sys.exit(1)
    media_id = draft_result["media_id"]
    print("  ✅ 草稿创建成功！media_id: {}".format(media_id))

    print("\n📋 验证草稿...")
    verify_url = "https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={}".format(access_token)
    verify_data = json.dumps({"offset": 0, "count": 1, "no_content": 1}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(verify_url, data=verify_data, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        verify_result = json.loads(resp.read().decode("utf-8"))
    if verify_result.get("item"):
        latest = verify_result["item"][0]["content"]["news_item"][0]
        vtitle = latest.get("title", "")
        print("  ✅ 标题验证通过: {}".format(vtitle))

    print("\n" + "=" * 50)
    print("✅ 完成！文章: {}".format(TITLE))
    print("  media_id: {}".format(media_id))
    print("  请登录 mp.weixin.qq.com 查看草稿并发布")
    print("=" * 50)


if __name__ == "__main__":
    main()
