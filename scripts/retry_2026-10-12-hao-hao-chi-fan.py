# -*- coding: utf-8 -*-
"""
重试发布脚本 - 2026-10-12《我已经很久没有好好吃过一顿饭了》
原因：40164 IP 不在白名单（当前出口 IP 183.159.115.101，连续第5天）
修复：到 mp.weixin.qq.com -> 设置与开发 -> 基本配置 -> IP白名单 添加该 IP 后运行：
    D:/python310/python.exe D:/blog/scripts/retry_2026-10-12-hao-hao-chi-fan.py
封面：已预生成（Pollinations，真 PNG 219KB，900x383）
"""
import json
import os
import urllib.request

ENV_FILE = "D:/blog/scripts/.env"
ARTICLE = "D:/blog/content/posts/2026-10-12-hao-hao-chi-fan.md"
COVER = "D:/blog/content/posts/cover_2026-10-12-chifan.png"
STATE_FILE = "D:/toutiao_auto/daily_state.json"
DIGEST = "人到中年，认真吃完的饭一年不到十顿。《小森林》里那句话说得对：把一顿饭吃好，就是生活本身。今晚煮碗面，别糊弄。"


def load_env():
    env = {}
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def api_get(url):
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_post(url, payload_bytes):
    req = urllib.request.Request(url, data=payload_bytes,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def upload_material(token, image_path):
    """multipart/form-data 上传永久素材（纯 urllib 实现）"""
    boundary = "----hermesretry20261012"
    filename = os.path.basename(image_path)
    with open(image_path, "rb") as f:
        file_data = f.read()
    body = (
        "--" + boundary + "\r\n"
        'Content-Disposition: form-data; name="media"; filename="' + filename + '"\r\n'
        "Content-Type: image/png\r\n\r\n"
    ).encode("utf-8") + file_data + ("\r\n--" + boundary + "--\r\n").encode("utf-8")
    url = "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=" + token + "&type=image"
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def md_to_html(md_content):
    """增强版转换：保留 ## 标题、加粗、斜体、引用、分隔线"""
    html_lines = []
    for raw in md_content.split("\n"):
        line = raw.rstrip()
        if not line:
            html_lines.append("<p><br/></p>")
            continue
        if line == "---":
            html_lines.append('<hr style="border:none;border-top:1px solid #eee;margin:25px 0;"/>')
            continue
        if line.startswith("## "):
            html_lines.append(
                '<h2 style="font-size:20px;font-weight:bold;color:#333;margin:25px 0 12px;">'
                + line[3:] + "</h2>")
            continue
        if line.startswith("### "):
            html_lines.append(
                '<h3 style="font-size:18px;font-weight:bold;color:#333;margin:20px 0 10px;">'
                + line[4:] + "</h3>")
            continue
        if line.startswith("> "):
            html_lines.append(
                '<blockquote style="border-left:3px solid #ddd;padding-left:12px;color:#888;margin:15px 0;">'
                + line[2:] + "</blockquote>")
            continue
        # inline formatting
        text = line
        text = text.replace("**", "\x01").split("\x01")
        out = ""
        for i, seg in enumerate(text):
            if i % 2 == 1:
                out += "<strong>" + seg + "</strong>"
            else:
                seg2 = ""
                parts = seg.split("*")
                for j, p2 in enumerate(parts):
                    if j % 2 == 1:
                        seg2 += "<em>" + p2 + "</em>"
                    else:
                        seg2 += p2
                out += seg2
        html_lines.append(
            '<p style="font-size:16px;line-height:1.8;color:#333;margin:0 0 16px;">'
            + out + "</p>")
    footer = (
        '<hr style="border:none;border-top:1px solid #eee;margin:30px 0 20px;"/>'
        '<p style="font-size:13px;color:#999;text-align:center;">深夜解忧铺</p>'
        '<p style="font-size:13px;color:#999;text-align:center;">你的心事有人听</p>'
    )
    return "\n".join(html_lines) + footer


def main():
    env = load_env()
    token_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid="
                 + env["WEIXIN_APP_ID"] + "&secret=" + env["WEIXIN_APP_SECRET"])
    result = api_get(token_url)
    if "access_token" not in result:
        if result.get("errcode") == 40164:
            print("IP 仍在白名单外。请到 mp.weixin.qq.com -> 设置与开发 -> 基本配置 -> IP白名单 添加 183.159.115.101")
        else:
            print("获取token失败: " + str(result))
        raise SystemExit(1)
    token = result["access_token"]
    print("API 连通性正常，token 获取成功")

    if not os.path.exists(COVER):
        print("找不到封面图: " + COVER)
        raise SystemExit(1)
    print("使用封面: " + COVER)

    up = upload_material(token, COVER)
    if "media_id" not in up:
        print("封面上传失败: " + str(up))
        raise SystemExit(1)
    thumb_media_id = up["media_id"]
    print("封面上传成功: " + thumb_media_id)

    with open(ARTICLE, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---", 2)
    front, body = parts[1], parts[2].strip()
    title = None
    for line in front.strip().split("\n"):
        if line.startswith("title:"):
            title = line.split(":", 1)[1].strip().strip('"').strip("'")
    if not title:
        print("解析不到标题")
        raise SystemExit(1)
    html_content = md_to_html(body)
    print("标题: " + title)

    # 不传 author 字段（避免 45110）；ensure_ascii=False 防中文乱码
    article = {
        "title": title,
        "digest": DIGEST,
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "content_source_url": "",
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    draft_url = "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=" + token
    result = api_post(draft_url, payload)

    if "media_id" in result:
        print("草稿创建成功！media_id: " + result["media_id"])
        print("请到公众号后台 -> 草稿箱 -> 发布")
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
            state.setdefault("wechat_draft_created", []).append({
                "date": "2026-10-12", "title": title, "media_id": result["media_id"],
            })
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            print("daily_state.json 已更新")
        except Exception as e:
            print("状态更新失败（不影响草稿）: " + str(e))
    else:
        print("草稿创建失败: " + str(result))


if __name__ == "__main__":
    main()
