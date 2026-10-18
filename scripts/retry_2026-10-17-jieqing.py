#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
手动重试脚本：2026-10-17 深夜解忧铺微信公众号草稿
场景：cron 预检发现 IP 不在白名单 (40164)，发布被跳过。
用法：IP 白名单添加完成后，手动运行本脚本即可补建草稿。

流程：获取 token -> 上传封面素材 -> Markdown 转 HTML -> 创建草稿
注意：draft 请求使用 ensure_ascii=False，author 字段不传（避免 45110）。
"""
import ast
import glob
import json
import os
import re
import sys
from datetime import datetime

import requests

# ========================= CONFIG =========================
APP_ID = "wx4f7ec5527892c5d6"
ENV_FILE = "D:/blog/scripts/.env"
ARTICLE_MD = "D:/blog/content/posts/2026-10-17-姐姐出嫁后回娘家变成了走亲戚.md"
COVER_PNG = "D:/blog/content/posts/cover_2026-10-17-jieqing.png"
TITLE = "姐姐出嫁后，回娘家变成了走亲戚"
DIGEST = "小时候替你打架的姐姐，长大后回娘家变成了走亲戚。没吵翻，也没矛盾，就是慢慢地，不知道怎么开口了。"
STATE_FILE = "D:/toutiao_auto/daily_state.json"
# ==========================================================


def get_secret():
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("WEIXIN_APP_SECRET="):
                return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("WEIXIN_APP_SECRET not found in .env")


def get_app_id():
    app_id = APP_ID
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("WEIXIN_APP_ID="):
                    app_id = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    return app_id


def get_access_token():
    token_url = (
        "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential"
        + "&appid=" + get_app_id() + "&secret=" + get_secret()
    )
    resp = requests.get(token_url, timeout=15)
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError("get token failed: %s" % data)
    return data["access_token"]


def upload_cover(token, image_path):
    upload_url = (
        "https://api.weixin.qq.com/cgi-bin/material/add_material"
        + "?access_token=" + token + "&type=image"
    )
    with open(image_path, "rb") as f:
        files = {"media": (os.path.basename(image_path), f, "image/png")}
        resp = requests.post(upload_url, files=files, timeout=60)
    data = resp.json()
    if "media_id" not in data:
        raise RuntimeError("upload cover failed: %s" % data)
    print("cover uploaded, media_id: %s" % data["media_id"])
    return data["media_id"]


def parse_md_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    title = TITLE
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split("\n"):
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"').strip("'")
            content = parts[2].strip()
    return title, content.strip()


def md_to_html(md_content):
    lines = md_content.split("\n")
    html_lines = []
    for raw in lines:
        line = raw.rstrip()
        if not line:
            html_lines.append("<p><br/></p>")
            continue
        if line.startswith("### "):
            html_lines.append(
                '<h2 style="font-size:19px;font-weight:bold;color:#333;'
                'margin:28px 0 14px;letter-spacing:1px;">' + line[4:] + "</h2>"
            )
            continue
        if line.startswith("## "):
            html_lines.append(
                '<h2 style="font-size:20px;font-weight:bold;color:#333;'
                'margin:30px 0 16px;letter-spacing:2px;text-align:center;">' + line[3:] + "</h2>"
            )
            continue
        if line.startswith("# "):
            html_lines.append(
                '<h1 style="font-size:22px;font-weight:bold;color:#333;'
                'margin:30px 0 15px;">' + line[2:] + "</h1>"
            )
            continue
        if line.startswith("---"):
            html_lines.append('<hr style="border:none;border-top:1px solid #eee;margin:25px 0;"/>')
            continue
        if line.startswith("> "):
            html_lines.append(
                '<blockquote style="border-left:3px solid #b8a99a;padding:10px 15px;'
                'margin:15px 0;background:#faf8f5;color:#666;">' + line[2:] + "</blockquote>"
            )
            continue
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        line = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", line)
        style = "font-size:16px;line-height:1.9;color:#3f3f3f;margin:14px 0;letter-spacing:0.5px;"
        if "<em>" in line and "<strong>" not in line:
            style += "text-align:center;color:#8a8178;"
        html_lines.append('<p style="' + style + '">' + line + "</p>")
    html_lines.append(
        '<p style="text-align:center;color:#b0a89e;font-size:13px;margin:36px 0 8px;">'
        "- - - - - - - - - - - - - - -</p>"
    )
    html_lines.append(
        '<p style="text-align:center;color:#9a9188;font-size:15px;margin:6px 0;'
        'letter-spacing:3px;">深夜解忧铺</p>'
    )
    html_lines.append(
        '<p style="text-align:center;color:#c0b8ae;font-size:13px;margin:6px 0 30px;">'
        "你的心事，有人听</p>"
    )
    return "\n".join(html_lines)


def create_draft(token, title, html_content, thumb_media_id):
    draft_url = "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=" + token
    article = {
        "title": title,
        "digest": DIGEST,
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "content_source_url": "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    resp = requests.post(
        draft_url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30,
    )
    result = resp.json()
    if "media_id" not in result:
        raise RuntimeError("create draft failed: %s" % result)
    print("draft created, media_id: %s" % result["media_id"])
    return result["media_id"]


def update_state(media_id):
    if not os.path.exists(STATE_FILE):
        print("state file missing, skip update")
        return
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)
    state.setdefault("wechat_draft_created", []).append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "title": TITLE,
        "media_id": media_id,
        "note": "retry script run manually after IP whitelist fix",
    })
    state["wechat_draft_status"] = "created (retry script): " + TITLE
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print("state updated")


def main():
    print("retry wechat draft: %s" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    title, body = parse_md_file(ARTICLE_MD)
    print("article: %s (%d chars)" % (title, len(body)))
    token = get_access_token()
    media_id = upload_cover(token, COVER_PNG)
    html = md_to_html(body)
    final_id = create_draft(token, title, html, media_id)
    update_state(final_id)


if __name__ == "__main__":
    main()
