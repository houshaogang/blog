# -*- coding: utf-8 -*-
"""Retry script for WeChat draft creation."""
import json, os, re, sys, time, requests

TITLE = "九月开学前夜，我终于活成了妈妈的样子"
DIGEST = "小时候嫌她啰嗦，长大后才发现，那些唠叨是这世上最温暖的情书"
MD_PATH = r"D:\blog\content\posts\2026-08-24-baoshupi-mama.md"
COVER_PATH = r"D:\blog\content\posts\cover_2026-08-24-baoshupi-mama.png"
ENV_PATHS = [r"D:\blog\scripts\.env", os.path.expanduser(r"~\AppData\Local\hermes\.env")]


def load_env():
    env = {}
    for p in ENV_PATHS:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip().strip('"').strip("'")
    return env.get("WEIXIN_APP_ID") or env.get("WECHAT_APP_ID"), \
           env.get("WEIXIN_APP_SECRET") or env.get("WECHAT_APP_SECRET")


def md_to_html(md):
    lines_in = md.split("\n")
    html = []
    in_bq = False
    def inline(t):
        t = re.sub(r"\*\*(.+?)\*\*", r'<strong style="font-weight:bold;color:#222;">\1</strong>', t)
        return t
    for line in lines_in:
        s = line.strip()
        if not s:
            if in_bq: html.append("</blockquote>"); in_bq = False
            html.append("<br/>")
            continue
        if s == "---":
            if in_bq: html.append("</blockquote>"); in_bq = False
            html.append('<section style="border-top:1px solid #e0e0e0;margin:30px 0;"></section>')
            continue
        if s.startswith("## "):
            if in_bq: html.append("</blockquote>"); in_bq = False
            html.append(f'<h2 style="font-size:20px;font-weight:bold;color:#333;margin:30px 0 16px;border-left:4px solid #8B4513;padding-left:12px;">{inline(s[3:])}</h2>')
            continue
        if s.startswith("> "):
            if not in_bq: html.append('<blockquote style="border-left:4px solid #e74c3c;padding:10px 15px;margin:20px 0;background:#fdf2f2;color:#666;font-style:italic;">'); in_bq = True
            html.append(f'<p style="margin:5px 0;font-size:15px;line-height:1.8;color:#666;">{inline(s[2:])}</p>')
            continue
        if s.startswith("**") and s.endswith("**") and s.count("**") == 2:
            text = s.strip("*")
            html.append(f'<p style="font-size:16px;line-height:1.8;color:#333;margin:16px 0;font-weight:bold;text-align:center;">{inline(text)}</p>')
            continue
        if in_bq: html.append("</blockquote>"); in_bq = False
        html.append(f'<p style="font-size:16px;line-height:1.8;color:#333;margin:12px 0;text-indent:2em;">{inline(s)}</p>')
    if in_bq: html.append("</blockquote>")
    return "\n".join(html)


def main():
    app_id, app_secret = load_env()
    if not app_id:
        print("ERROR: No credentials found"); sys.exit(1)

    # Get token
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    r = requests.get(url, timeout=15).json()
    if "access_token" not in r:
        print(f"Token error: {r}"); sys.exit(1)
    token = r["access_token"]
    print("Token OK")

    # Upload cover
    u_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    with open(COVER_PATH, "rb") as f:
        ur = requests.post(u_url, files={"media": ("cover.png", f, "image/png")}, timeout=30).json()
    if "media_id" not in ur:
        print(f"Upload error: {ur}"); sys.exit(1)
    thumb_id = ur["media_id"]
    print(f"Cover uploaded: {thumb_id}")

    # Read and convert markdown
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md = f.read()
    md_body = re.sub(r"^#\s+.+\n", "", md.strip())
    html_body = md_to_html(md_body)
    footer = '\n<section style="border-top:1px solid #e0e0e0;margin:40px 0 20px;"></section>\n<div style="text-align:center;margin:20px 0;">\n<p style="font-size:14px;color:#999;margin:0 0 8px;">深夜解忧铺</p>\n<p style="font-size:16px;color:#8B4513;font-weight:bold;margin:0;">你的心事，有人听</p>\n</div>'
    html_content = f'<section style="max-width:100%;padding:20px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,PingFang SC,Hiragino Sans GB,Microsoft YaHei,sans-serif;">\n{html_body}\n{footer}\n</section>'

    # Create draft (NO author field!)
    article = {
        "title": TITLE,
        "digest": DIGEST,
        "content": html_content,
        "thumb_media_id": thumb_id,
        "content_source_url": "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }
    d_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    dr = requests.post(d_url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"}, timeout=30).json()
    if "media_id" in dr:
        print(f"Draft created: {dr['media_id']}")
    else:
        print(f"Draft error: {dr}")
        sys.exit(1)

    # Verify
    bg_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
    bg_data = json.dumps({"offset": 0, "count": 5, "no_content": True}, ensure_ascii=False).encode("utf-8")
    bg_r = requests.post(bg_url, data=bg_data, headers={"Content-Type": "application/json; charset=utf-8"}, timeout=15).json()
    for item in bg_r.get("item", []):
        if item.get("media_id") == dr["media_id"]:
            t = item["content"]["news_item"][0]["title"]
            print(f"Verified: {t}")
            break
    print("DONE")


if __name__ == "__main__":
    main()