# -*- coding: utf-8 -*-
import json, os, re, sys, time, requests

TITLE = "凌晨两点，我梦见了小时候的暑假"
DIGEST = "小时候嫌暑假太长，长大后才明白，那是人生里最奢侈的一段时光"
MD_PATH = r"D:\blog\content\posts\2026-08-29-childhood-summer-dreams.md"
POST_DIR = r"D:\blog\content\posts"
ENV_PATH = r"D:\blog\scripts\.env"

def load_env():
    env = {}
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    app_id = env.get("WEIXIN_APP_ID", "")
    app_secret = env.get("WEIXIN_APP_SECRET", "")
    return app_id, app_secret

def find_latest_cover():
    covers = sorted([f for f in os.listdir(POST_DIR) if f.startswith("cover_") and f.endswith(".png")], reverse=True)
    if covers:
        return os.path.join(POST_DIR, covers[0])
    return None

def md_to_html(md):
    lines_in = md.split("\n")
    html = []
    in_bq = False
    def inline(t):
        t = re.sub(r"\*\*(.+?)\*\*", r'<strong style="font-weight:bold;color:#222;">\1</strong>', t)
        t = re.sub(r"\*(.+?)\*", r'<em style="font-style:italic;color:#555;">\1</em>', t)
        return t
    for line in lines_in:
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
            html.append('<section style="border-top:1px solid #e0e0e0;margin:30px 0;"></section>')
            continue
        if s.startswith("## "):
            if in_bq:
                html.append("</blockquote>")
                in_bq = False
            html.append('<h2 style="font-size:20px;font-weight:bold;color:#333;margin:30px 0 16px;border-left:4px solid #8B4513;padding-left:12px;">' + inline(s[3:]) + '</h2>')
            continue
        if s.startswith("> "):
            if not in_bq:
                html.append('<blockquote style="border-left:4px solid #e74c3c;padding:10px 15px;margin:20px 0;background:#fdf2f2;color:#666;font-style:italic;">')
                in_bq = True
            html.append('<p style="margin:5px 0;font-size:15px;line-height:1.8;color:#666;">' + inline(s[2:]) + '</p>')
            continue
        if s.startswith("**") and s.endswith("**") and s.count("**") == 2:
            text = s.strip("*")
            html.append('<p style="font-size:16px;line-height:1.8;color:#333;margin:16px 0;font-weight:bold;text-align:center;">' + inline(text) + '</p>')
            continue
        if in_bq:
            html.append("</blockquote>")
            in_bq = False
        html.append('<p style="font-size:16px;line-height:1.8;color:#333;margin:12px 0;text-indent:2em;">' + inline(s) + '</p>')
    if in_bq:
        html.append("</blockquote>")
    return "\n".join(html)

def main():
    app_id, app_secret = load_env()
    print("App ID: " + app_id[:8] + "...")
    print("Secret len: " + str(len(app_secret)))

    # Get token
    url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=" + app_id + "&secret=" + app_secret
    r = requests.get(url, timeout=15).json()
    if "access_token" not in r:
        print("Token error: " + json.dumps(r, ensure_ascii=False))
        sys.exit(1)
    token = r["access_token"]
    print("Token OK")

    # Find and upload cover
    cover = find_latest_cover()
    if not cover or not os.path.exists(cover):
        print("ERROR: No cover found")
        sys.exit(1)
    print("Cover: " + cover)
    u_url = "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=" + token + "&type=image"
    with open(cover, "rb") as f:
        ur = requests.post(u_url, files={"media": ("cover.png", f, "image/png")}, timeout=30).json()
    if "media_id" not in ur:
        print("Upload error: " + json.dumps(ur, ensure_ascii=False))
        sys.exit(1)
    thumb_id = ur["media_id"]
    print("Cover uploaded: " + thumb_id)

    # Read and convert markdown
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md = f.read()
    md_body = re.sub(r"^---\n.*?\n---\n", "", md.strip(), flags=re.DOTALL)
    md_body = re.sub(r"^#\s+.+\n", "", md_body.strip())
    html_body = md_to_html(md_body)
    footer = '<section style="border-top:1px solid #e0e0e0;margin:40px 0 20px;"></section>\n<div style="text-align:center;margin:20px 0;">\n<p style="font-size:14px;color:#999;margin:0 0 8px;">深夜解忧铺</p>\n<p style="font-size:16px;color:#8B4513;font-weight:bold;margin:0;">你的心事，有人听</p>\n</div>'
    html_content = '<section style="max-width:100%;padding:20px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,PingFang SC,Hiragino Sans GB,Microsoft YaHei,sans-serif;">\n' + html_body + '\n' + footer + '\n</section>'

    # Create draft
    article = {
        "title": TITLE,
        "digest": DIGEST,
        "content": html_content,
        "thumb_media_id": thumb_id,
        "content_source_url": "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }
    d_url = "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=" + token
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    dr = requests.post(d_url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"}, timeout=30).json()
    if "media_id" in dr:
        mid = dr["media_id"]
        print("Draft created: " + mid)
    else:
        print("Draft error: " + json.dumps(dr, ensure_ascii=False))
        sys.exit(1)

    # Verify
    time.sleep(1)
    bg_url = "https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=" + token
    bg_data = json.dumps({"offset": 0, "count": 5, "no_content": True}, ensure_ascii=False).encode("utf-8")
    bg_r = requests.post(bg_url, data=bg_data, headers={"Content-Type": "application/json; charset=utf-8"}, timeout=15).json()
    for item in bg_r.get("item", []):
        if item.get("media_id") == mid:
            t = item["content"]["news_item"][0]["title"]
            print("Verified title: " + t)
            has_backslash = chr(92) + "u" in t
            if has_backslash:
                print("WARNING: Title contains unicode escapes!")
            else:
                print("Title encoding OK")
            break
    print("DONE")

if __name__ == "__main__":
    main()
