#!/usr/bin/env python
# -*- coding: utf-8 -*-
# r-string docstring: retry publish script for 2026-10-15 article.
# NOTE: this docstring is intentionally an r-string so that any literal
# backslash-u sequences below do not trigger a unicodeescape SyntaxError.
r"""Retry WeChat draft creation for 2026-10-15 前任好友申请 article.
Run manually after fixing IP whitelist:
    D:/python310/python.exe retry_2026-10-15-hao-you-shen-qing.py
Token URL uses plain string concatenation (no f-string) to avoid
redaction-substitution of the token variable.
"""

import json
import os
import re
import sys
import urllib.request

POST_PATH = "D:/blog/content/posts/2026-10-15-ta-fa-lai-hao-you-shen-qing-wo-you-yu-le-san-tian.md"
COVER_PATH = "D:/blog/covers/cover_2026-10-15.png"
ENV_PATH = "D:/blog/scripts/.env"
ARTICLE_TITLE = "她发来好友申请，我犹豫了三天"
DIGEST = "好友申请挂了三天，最后我还是点了拒绝。"


def load_env(path):
    env = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def get_token(env):
    url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential"
           "&appid=" + env["WEIXIN_APP_ID"] + "&secret=" + env["WEIXIN_APP_SECRET"])
    with urllib.request.urlopen(url, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "access_token" not in result:
        raise RuntimeError("token failed: " + json.dumps(result, ensure_ascii=False))
    return result["access_token"]


def upload_image(token, path):
    boundary = "----hermesretryboundary7f3a"
    filename = os.path.basename(path)
    with open(path, "rb") as f:
        img = f.read()
    body = (
        ("--" + boundary + "\r\n").encode()
        + ('Content-Disposition: form-data; name="media"; filename="' + filename + '"\r\n').encode()
        + b"Content-Type: image/png\r\n\r\n"
        + img + b"\r\n"
        + ("--" + boundary + "--\r\n").encode()
    )
    url = ("https://api.weixin.qq.com/cgi-bin/material/add_material?access_token="
           + token + "&type=image")
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in result:
        raise RuntimeError("upload failed: " + json.dumps(result, ensure_ascii=False))
    return result["media_id"]


def md_to_html(md_text):
    lines = md_text.split("\n")
    # strip YAML frontmatter
    if lines and lines[0].strip() == "---":
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        if end is not None:
            lines = lines[end + 1:]
    out = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("**文 /"):
            continue
        if line == "---":
            out.append('<p style="text-align:center;color:#bbb;">— · —</p>')
            continue
        m = re.match(r"^##\s+(\d+)\s*$", line)
        if m:
            out.append('<h2 style="font-size:18px;color:#444;margin:2.2em 0 1em;">'
                       + m.group(1) + "</h2>")
            continue
        html = line
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", html)
        out.append('<p style="font-size:16px;line-height:1.8;color:#333;margin:0 0 1.4em;">'
                   + html + "</p>")
    footer = ('<p style="text-align:center;color:#999;font-size:13px;margin-top:2.5em;'
              'border-top:1px solid #eee;padding-top:1.5em;">深夜解忧铺<br/>'
              '<span style="color:#bbb;">你的心事有人听</span></p>')
    return "".join(out) + footer


def create_draft(token, thumb_media_id, html_content):
    article = {
        "title": ARTICLE_TITLE,
        "content": html_content,
        "digest": DIGEST,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    url = ("https://api.weixin.qq.com/cgi-bin/draft/add?access_token=" + token)
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in result:
        raise RuntimeError("draft failed: " + json.dumps(result, ensure_ascii=False))
    return result["media_id"]


def main():
    env = load_env(ENV_PATH)
    print("[1/4] getting token...")
    token = get_token(env)
    print("      token ok")
    print("[2/4] uploading cover...")
    thumb = upload_image(token, COVER_PATH)
    print("      thumb_media_id ok")
    print("[3/4] converting markdown to html...")
    with open(POST_PATH, "r", encoding="utf-8") as f:
        body = f.read()
    html = md_to_html(body)
    print("      html length:", len(html))
    print("[4/4] creating draft...")
    draft_id = create_draft(token, thumb, html)
    print("DRAFT OK, media_id =", draft_id)
    print("去 mp.weixin.qq.com 草稿箱发布，发布时间建议 21:00-22:00")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("FAILED:", repr(e))
        sys.exit(1)
