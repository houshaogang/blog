# -*- coding: utf-8 -*-
"""
Retry publish script: 2026-10-07-ci-wei-de-you-ya-duju
Reason: IP not in WeChat whitelist
Fix: login mp.weixin.qq.com -> Settings & Dev -> Basic Config -> IP Whitelist
     add server IP (get via https://api.ipify.org)
Then run: python retry_2026-10-07-ci-wei-de-you-ya-duju.py
"""

import os
import json
import re
import urllib.request
from datetime import datetime
from PIL import Image

POSTS_DIR = r"D:\blog\content\posts"
ENV_PATH = r"D:\blog\scripts\.env"
ARTICLE_FILE = "2026-10-07-ci-wei-de-you-ya-duju.md"
COVER_FILE = "cover_2026-10-07-ci-wei-de-you-ya-duju.png"
TITLE = "那个独居的女人，让我看懂了刺猬的优雅"
DIGEST = "独居第七年，我终于看懂了《刺猬的优雅》里那个看门人——原来她不是冷漠，只是把温柔藏得太深。"


def load_env():
    env = {}
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def get_token(env):
    url = (
        "https://api.weixin.qq.com/cgi-bin/token"
        "?grant_type=client_credential"
        "&appid=" + env["WEIXIN_APP_ID"]
        + "&secret=" + env["WEIXIN_APP_SECRET"]
    )
    with urllib.request.urlopen(url, timeout=10) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "access_token" not in result:
        raise Exception("get token failed: " + str(result))
    return result["access_token"]


def upload_image(token, filepath):
    import mimetypes
    import uuid

    boundary = uuid.uuid4().hex
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        file_data = f.read()
    mime_type = mimetypes.guess_type(filepath)[0] or "image/png"

    head = (
        "--" + boundary + "\r\n"
        'Content-Disposition: form-data; name="media"; filename="' + filename + '"\r\n'
        "Content-Type: " + mime_type + "\r\n\r\n"
    ).encode("utf-8")
    tail = ("\r\n--" + boundary + "--\r\n").encode("utf-8")
    body = head + file_data + tail

    url = (
        "https://api.weixin.qq.com/cgi-bin/material/add_material"
        "?access_token=" + token + "&type=image"
    )
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "multipart/form-data; boundary=" + boundary},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in result:
        raise Exception("upload image failed: " + str(result))
    return result["media_id"]


def md_to_html(md_content):
    lines = md_content.split("\n")
    html_parts = []
    fm_count = 0
    in_fm = False

    for line in lines:
        stripped = line.strip()
        if stripped == "---":
            fm_count += 1
            if fm_count == 1:
                in_fm = True
                continue
            if fm_count == 2:
                in_fm = False
                continue
            html_parts.append('<hr style="border:none;border-top:1px solid #ddd;margin:20px 0;">')
            continue
        if in_fm:
            continue
        if not stripped:
            continue

        if stripped == "**\u6587 / \u6df1\u591c\u89e3\u5fe7\u94fa**":
            html_parts.append(
                '<p style="font-size:16px;line-height:1.8;color:#333;'
                'text-align:center;margin:20px 0;">'
                "<strong>\u6587 / \u6df1\u591c\u89e3\u5fe7\u94fa</strong></p>"
            )
            continue

        if stripped.startswith("## "):
            heading = stripped[3:]
            html_parts.append(
                '<h2 style="font-size:20px;color:#333;margin:30px 0 15px;'
                'font-weight:bold;">' + heading + "</h2>"
            )
            continue

        if stripped.startswith("*") and stripped.endswith("*") and len(stripped) > 2:
            text = stripped[1:-1]
            html_parts.append(
                '<p style="font-size:16px;line-height:1.8;color:#666;'
                'margin:20px 0;font-style:italic;">' + text + "</p>"
            )
            continue

        def bold_repl(m):
            return "<strong>" + m.group(1) + "</strong>"

        processed = re.sub(r"\*\*(.+?)\*\*", bold_repl, stripped)
        html_parts.append(
            '<p style="font-size:16px;line-height:1.8;color:#333;margin:10px 0;">'
            + processed + "</p>"
        )

    footer = (
        '<hr style="border:none;border-top:1px solid #ddd;margin:30px 0;">'
        '<p style="text-align:center;color:#999;font-size:14px;">\u6df1\u591c\u89e3\u5fe7\u94fa</p>'
        '<p style="text-align:center;color:#999;font-size:14px;">\u4f60\u7684\u5fc3\u4e8b\u6709\u4eba\u542c</p>'
    )
    html_parts.append(footer)
    return "".join(html_parts)


def create_draft(token, thumb_media_id, html_content):
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
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    url = "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=" + token
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in result:
        raise Exception("create draft failed: " + str(result))
    return result["media_id"]


def verify_draft(token, media_id):
    payload = json.dumps({"media_id": media_id}, ensure_ascii=False).encode("utf-8")
    url = "https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=" + token
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "news_item" in result:
        actual_title = result["news_item"][0]["title"]
        print("verify title: " + actual_title)
        if "\u523a\u732c" in actual_title or "\u72ec\u5c45" in actual_title:
            print("OK: chinese encoding normal")
            return True
        else:
            print("WARNING: possible encoding issue")
            return False
    return False


def main():
    print("=" * 60)
    print("Retry publish: " + TITLE)
    print("=" * 60)

    env = load_env()
    print("\n1. Getting access_token...")
    token = get_token(env)
    print("   OK token: " + token[:20] + "...")

    cover_path = os.path.join(POSTS_DIR, COVER_FILE)
    print("\n2. Uploading cover: " + COVER_FILE + " ...")
    img = Image.open(cover_path)
    if img.format != "PNG":
        print("   Converting to real PNG...")
        img.save(cover_path, "PNG")
    thumb_media_id = upload_image(token, cover_path)
    print("   OK media_id: " + thumb_media_id[:20] + "...")

    print("\n3. Converting markdown to HTML...")
    article_path = os.path.join(POSTS_DIR, ARTICLE_FILE)
    with open(article_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    html_content = md_to_html(md_content)
    print("   OK html length: " + str(len(html_content)))

    print("\n4. Creating draft...")
    draft_media_id = create_draft(token, thumb_media_id, html_content)
    print("   OK draft created!")
    print("   media_id: " + draft_media_id)

    print("\n5. Verifying draft...")
    if verify_draft(token, draft_media_id):
        print("\n" + "=" * 60)
        print("PUBLISH OK! Check draft in mp.weixin.qq.com")
        print("draft media_id: " + draft_media_id)
        print("=" * 60)
    else:
        print("\nWARNING: verification issue, check draft manually")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\nERROR: " + str(e))
        import traceback
        traceback.print_exc()
