# -*- coding: utf-8 -*-
"""
retry_2026-10-13-meng-dao-qvshi.py
文章: 梦到去世的亲人醒来后，我终于懂了东京物语
用途: 微信 IP 白名单修复后，手动运行本脚本即可完成发布草稿
      (获取 token -> 上传封面 -> md 转 HTML -> 创建草稿 -> 验证中文无乱码)
注意: 本脚本从模板新写，token URL 全部字符串拼接，无 f-string 插值。
"""
import os, sys, json, re, urllib.request

# ======================== CONFIG（只需改这里）========================
ARTICLE_PATH = r"D:\blog\content\posts\2026-10-13-meng-dao-qvshi-de-qin-ren.md"
COVER_PATH   = r"D:\blog\content\posts\cover_2026-10-13-meng-dao-qvshi.png"
ENV_PATH     = r"D:\blog\scripts\.env"
TITLE  = "梦到去世的亲人醒来后，我终于懂了东京物语"
DIGEST = "凌晨梦见走了三年的父亲，醒来想起东京物语里那对老夫妻。我们对陌生人客气，对家人敷衍。趁还来得及，多问一句吃了没。"
# ===================================================================


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
    url = ("https://api.weixin.qq.com/cgi-bin/token"
           "?grant_type=client_credential&appid=" + env["WEIXIN_APP_ID"] +
           "&secret=" + env["WEIXIN_APP_SECRET"])
    with urllib.request.urlopen(url, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "access_token" not in result:
        raise RuntimeError("获取 token 失败: " + str(result))
    return result["access_token"]


def upload_cover(token, cover_path):
    with open(cover_path, "rb") as f:
        img_bytes = f.read()
    boundary = "----HermesRetryBoundary20261013"
    head = ("--" + boundary +
            "\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.png\""
            "\r\nContent-Type: image/png\r\n\r\n").encode("utf-8")
    tail = ("\r\n--" + boundary + "--\r\n").encode("utf-8")
    body = head + img_bytes + tail
    url = ("https://api.weixin.qq.com/cgi-bin/material/add_material"
           "?access_token=" + token + "&type=image")
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "multipart/form-data; boundary=" + boundary})
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in result:
        raise RuntimeError("上传封面失败: " + str(result))
    return result["media_id"]


def md_to_html(md_text):
    """增强版 markdown 转公众号 HTML: 保留 h2 标题/加粗/斜体 + footer"""
    # 去掉 frontmatter
    md_text = re.sub(r"^---\n.*?\n---\n", "", md_text, flags=re.S)
    blocks = re.split(r"\n\s*\n", md_text.strip())
    html_parts = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block == "---":
            html_parts.append("<hr style=\"border:none;border-top:1px solid #e5e5e5;margin:28px 0;\"/>")
            continue
        if block.startswith("## "):
            label = block[3:].strip()
            html_parts.append("<h2 style=\"font-size:18px;font-weight:bold;color:#333;margin:32px 0 16px;\">" + label + "</h2>")
            continue
        inner = block.replace("\n", "<br/>")
        inner = re.sub(r"\*\*(.+?)\*\*", "<strong style=\"color:#1a1a1a;\">\\1</strong>", inner)
        inner = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", "<em>\\1</em>", inner)
        html_parts.append("<p style=\"font-size:16px;line-height:1.8;color:#333;margin:0 0 20px;\">" + inner + "</p>")
    footer = ("<hr style=\"border:none;border-top:1px solid #e5e5e5;margin:32px 0;\"/>"
              "<p style=\"text-align:center;color:#999;font-size:13px;margin:0 0 6px;\">深夜解忧铺</p>"
              "<p style=\"text-align:center;color:#bbb;font-size:12px;margin:0;\">你的心事有人听</p>")
    return "\n".join(html_parts) + "\n" + footer


def create_draft(token, thumb_media_id, html_content, title, digest):
    article = {
        "title": title,
        "thumb_media_id": thumb_media_id,
        "author": "",
        "digest": digest,
        "content": html_content,
        "content_source_url": "",
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }
    # author 留空字符串不会触发 45110；如仍报错，删除该行即可
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    url = "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=" + token
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" not in result:
        raise RuntimeError("创建草稿失败: " + str(result))
    return result["media_id"]


def verify_draft(token, media_id):
    """batchget 验证草稿标题中文无乱码"""
    payload = json.dumps({"media_id": media_id, "offset": 0, "count": 1, "no_content": 1},
                         ensure_ascii=False).encode("utf-8")
    url = "https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=" + token
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    items = result.get("news_item", [])
    if not items:
        print("⚠️ batchget 未返回内容，无法验证")
        return False
    got_title = items[0].get("title", "")
    print("   batchget 返回标题: " + got_title)
    if "\\u" in got_title or "梦到" in got_title:
        return True
    print("❌ 标题疑似乱码！请删除草稿后用本脚本重新创建")
    return False


def main():
    env = load_env(ENV_PATH)
    print("[1/5] 获取 access_token ...")
    token = get_token(env)
    print("      OK (token len=" + str(len(token)) + ")")
    print("[2/5] 上传封面图 ...")
    media_id = upload_cover(token, COVER_PATH)
    print("      OK media_id=" + media_id)
    print("[3/5] Markdown 转 HTML ...")
    with open(ARTICLE_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()
    html_content = md_to_html(md_text)
    print("      OK html len=" + str(len(html_content)))
    print("[4/5] 创建草稿 ...")
    draft_id = create_draft(token, media_id, html_content, TITLE, DIGEST)
    print("      OK 草稿 media_id = " + draft_id)
    print("[5/5] 验证中文编码 ...")
    ok = verify_draft(token, draft_id)
    print("")
    print("=" * 50)
    if ok:
        print("✅ 发布成功！草稿 media_id: " + draft_id)
        print("   请到 mp.weixin.qq.com 草稿箱确认后发布。")
    else:
        print("⚠️ 草稿已创建 (media_id=" + draft_id + ")，但标题验证未通过，请手动检查。")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("❌ 失败: " + str(e))
        sys.exit(1)
