# -*- coding: utf-8 -*-
"""
重试发布脚本: 2026-10-09 文章「回了趟老家我才明白，我怀念的不是故乡，是那时候的自己」
背景: 2026-10-09 07:00 自动发布时 API 预检失败 (errcode 40164, IP 不在白名单)
使用: 将当前服务器 IP 添加到 mp.weixin.qq.com -> 设置与开发 -> 基本配置 -> IP白名单 后，
      运行: python retry_2026-10-09-hui-lao-jia.py
"""
import json, os, re, urllib.request

# ===== 配置 =====
ENV_PATH = r"D:\blog\scripts\.env"
MD_PATH = r"D:\blog\content\posts\2026-10-09-hui-lao-jia-xiao-wang-zi.md"
COVER_PATH = r"D:\blog\content\posts\cover_2026-10-09-hui-lao-jia.png"
TITLE = "回了趟老家我才明白，我怀念的不是故乡，是那时候的自己"
DIGEST = "巷口的门牌全换了，王叔家的门锁锈了。我们这代人，故乡是用来离开的，离开了才开始往回还。"

# ===== 1. 读取 .env =====
env = {}
with open(ENV_PATH, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
APP_ID = env["WEIXIN_APP_ID"]
APP_SECRET = env["WEIXIN_APP_SECRET"]

# ===== 2. 获取 access_token =====
token_url = (f"https://api.weixin.qq.com/cgi-bin/token"
             f"?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}")
with urllib.request.urlopen(token_url, timeout=15) as resp:
    result = json.loads(resp.read().decode("utf-8"))
if "access_token" not in result:
    raise SystemExit(f"获取 token 失败: {result} (40164 = IP 仍不在白名单)")
TOKEN = result["access_token"]
print("✅ token 获取成功")

# ===== 3. 上传封面图 =====
boundary = "----HermesBoundary7MA4YWxkTrZu0gW"
with open(COVER_PATH, "rb") as f:
    cover_data = f.read()
body = (b"--" + boundary.encode() + b"\r\n"
        b'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'
        b"Content-Type: image/png\r\n\r\n"
        + cover_data + b"\r\n"
        b"--" + boundary.encode() + b"--\r\n")
upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={TOKEN}&type=image"
req = urllib.request.Request(upload_url, data=body,
                             headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
with urllib.request.urlopen(req, timeout=60) as resp:
    up_result = json.loads(resp.read().decode("utf-8"))
if "media_id" not in up_result:
    raise SystemExit(f"上传封面失败: {up_result}")
THUMB_MEDIA_ID = up_result["media_id"]
print(f"✅ 封面上传成功: {THUMB_MEDIA_ID}")

# ===== 4. Markdown -> HTML (保留 ## 标题/加粗/斜体) =====
def md_to_html(md_text):
    # 去掉 frontmatter
    md_text = re.sub(r"^---\n.*?\n---\n", "", md_text, flags=re.S)
    lines = md_text.split("\n")
    html_parts = []
    p_style = 'style="font-size: 16px; line-height: 1.8; color: #333; margin: 0 0 20px 0;"'
    h_style = 'style="font-size: 18px; font-weight: bold; color: #333; margin: 30px 0 15px 0;"'
    hr = '<hr style="border: none; border-top: 1px solid #e5e5e5; margin: 25px 0;">'

    def inline(t):
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", t)
        return t

    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s == "---":
            html_parts.append(hr)
        elif s.startswith("## "):
            html_parts.append(f"<h2 {h_style}>{inline(s[3:].strip())}</h2>")
        elif s.startswith("**文 / 深夜解忧铺**"):
            html_parts.append(f'<p {p_style} style="text-align:center;color:#888;">文 / 深夜解忧铺</p>')
        else:
            html_parts.append(f"<p {p_style}>{inline(s)}</p>")

    footer = (hr
              + f'<p {p_style} style="text-align:center;color:#999;font-size:14px;">深夜解忧铺</p>'
              + f'<p {p_style} style="text-align:center;color:#999;font-size:14px;">你的心事，有人听</p>')
    return "\n".join(html_parts) + footer

with open(MD_PATH, "r", encoding="utf-8") as f:
    md_content = f.read()
content_html = md_to_html(md_content)
print(f"✅ HTML 生成完成 ({len(content_html)} 字符)")

# ===== 5. 创建草稿 (关键: ensure_ascii=False 防中文乱码) =====
article = {
    "title": TITLE,
    "digest": DIGEST,
    "content": content_html,
    "thumb_media_id": THUMB_MEDIA_ID,
    "need_open_comment": 1,
    "only_fans_can_comment": 0,
    # 注意: 不传 author 字段 (会报 45110)
}
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={TOKEN}"
req = urllib.request.Request(draft_url, data=payload,
                             headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=60) as resp:
    draft_result = json.loads(resp.read().decode("utf-8"))
if "media_id" not in draft_result:
    raise SystemExit(f"创建草稿失败: {draft_result}")
MEDIA_ID = draft_result["media_id"]
print(f"✅ 草稿创建成功: {MEDIA_ID}")

# ===== 6. 验证草稿标题无乱码 =====
check_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={TOKEN}"
check_payload = json.dumps({"media_id": MEDIA_ID}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(check_url, data=check_payload,
                             headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as resp:
    check = json.loads(resp.read().decode("utf-8"))
got_title = check.get("news_item", [{}])[0].get("title", "")
if got_title == TITLE and "老家" in got_title:
    print(f"✅ 标题验证通过 (无乱码): {got_title}")
else:
    # 乱码则删除重建
    print(f"⚠️ 标题疑似乱码: {got_title!r}，正在删除重建...")
    del_payload = json.dumps({"media_id": MEDIA_ID}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.weixin.qq.com/cgi-bin/draft/delete?access_token={TOKEN}",
        data=del_payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        print("删除结果:", resp.read().decode("utf-8"))
    raise SystemExit("标题乱码，请检查编码后重跑")

print("\n===== 发布完成 =====")
print(f"文章: {TITLE}")
print(f"草稿 media_id: {MEDIA_ID}")
print("请到 mp.weixin.qq.com 草稿箱确认后排版发布。")
