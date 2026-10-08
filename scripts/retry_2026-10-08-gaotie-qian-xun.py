#!/usr/bin/env python3
"""
深夜解忧铺 - 2026-10-08 文章发布重试脚本
背景：cron job 生成文章时 API 预检失败（40164 IP 不在白名单，当前 IP 115.227.218.122）
修复：登录 mp.weixin.qq.com → 设置与开发 → 基本配置 → IP白名单，添加上述 IP
然后运行：python D:/blog/scripts/retry_2026-10-08-gaotie-qian-xun.py
"""

import json, os, re, urllib.request, urllib.parse, io

ARTICLE_MD_PATH = "D:/blog/content/posts/2026-10-08-gaotie-qian-xun.md"
ARTICLE_TITLE = "假期结束回城那天，我在高铁上突然看懂了千寻"
ARTICLE_DIGEST = "假期结束，从老家返回打工城市的高铁上，车厢里全是沉默的人。小时候看千与千寻只觉得奇幻，长大后才明白，那趟车没有返程票。"
COVER_PATH = "D:/blog/content/posts/cover_2026-10-08-gaotie-qian-xun.png"

# === Step 0: 加载环境变量 + 预检 API ===
print("[0/5] 加载环境变量...")
env = {}
for p in ["D:/blog/scripts/.env", os.path.expanduser("~/AppData/Local/hermes/.env")]:
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    if k.strip() not in env:
                        env[k.strip()] = v.strip().strip('"').strip("'")

app_id = env.get("WEIXIN_APP_ID")
app_secret = env.get("WEIXIN_APP_SECRET")
if not app_id or not app_secret:
    print("❌ 缺少 WEIXIN_APP_ID 或 WEIXIN_APP_SECRET"); raise SystemExit(1)

print("[0/5] 预检 API 连通性...")
token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
try:
    with urllib.request.urlopen(token_url, timeout=10) as resp:
        check = json.loads(resp.read().decode("utf-8"))
    if check.get("errcode") == 40164:
        print("❌ IP 仍不在白名单！请在 mp.weixin.qq.com → 设置与开发 → 基本配置 → IP白名单 添加服务器 IP")
        raise SystemExit(1)
    if "access_token" not in check:
        print(f"❌ API 错误: {check}"); raise SystemExit(1)
    access_token = check["access_token"]
    print("[0/5] ✅ API 连通性正常")
except SystemExit:
    raise
except Exception as e:
    print(f"❌ 网络错误: {e}"); raise SystemExit(1)

# === Step 1: 读取封面 ===
print("[1/5] 读取封面图...")
if not os.path.exists(COVER_PATH):
    print(f"❌ 封面不存在: {COVER_PATH}"); raise SystemExit(1)
with open(COVER_PATH, "rb") as f:
    cover_data = f.read()
if cover_data[:2].hex() == "ffd8":  # JPEG 假 PNG，转真 PNG
    from PIL import Image
    img = Image.open(io.BytesIO(cover_data))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    cover_data = buf.getvalue()
    print(f"[1/5] ⚠️ 封面是 JPEG，已转真 PNG ({len(cover_data)} bytes)")
else:
    print(f"[1/5] ✅ 真 PNG ({len(cover_data)} bytes)")

# === Step 2: 上传封面到微信 ===
print("[2/5] 上传封面...")
boundary = "----FormBoundaryRetry"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode("utf-8") + cover_data + f"\r\n--{boundary}--\r\n".encode("utf-8")
upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
req = urllib.request.Request(upload_url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
with urllib.request.urlopen(req, timeout=60) as resp:
    upload_result = json.loads(resp.read().decode("utf-8"))
thumb_media_id = upload_result.get("media_id", "")
if not thumb_media_id:
    print(f"❌ 上传失败: {upload_result}"); raise SystemExit(1)
print(f"[2/5] ✅ thumb_media_id: {thumb_media_id[:30]}...")

# === Step 3: Markdown → HTML ===
print("[3/5] Markdown → HTML...")
with open(ARTICLE_MD_PATH, "r", encoding="utf-8") as f:
    md_content = f.read()
md_body = re.sub(r"^---\n.*?---\n", "", md_content, flags=re.DOTALL).strip()

def md_to_html(md_text):
    parts = []
    for line in md_text.split("\n"):
        s = line.strip()
        if not s:
            continue
        if s == "---":
            parts.append('<section style="border-top:1px solid #e0e0e0;margin:30px 0;"></section>')
        elif s.startswith("## "):
            num = s[3:].strip()
            parts.append(f'<h2 style="font-size:20px;color:#333;margin:30px 0 15px;font-weight:bold;border-left:4px solid #c0392b;padding-left:12px;">{num}</h2>')
        elif s.startswith("**") and s.endswith("**"):
            parts.append(f'<p style="font-size:16px;line-height:1.8;color:#333;text-align:center;font-weight:bold;margin:20px 0;">{s[2:-2]}</p>')
        elif s.startswith("*") and s.endswith("*") and not s.startswith("**"):
            parts.append(f'<p style="font-size:16px;line-height:1.8;color:#888;text-align:center;font-style:italic;margin:30px 0;">{s[1:-1]}</p>')
        else:
            processed = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
            parts.append(f'<p style="font-size:16px;line-height:1.8;color:#333;margin:12px 0;">{processed}</p>')
    return "\n".join(parts)

body_html = md_to_html(md_body)
full_html = f'''<div style="max-width:677px;margin:0 auto;padding:20px;">
<p style="font-size:16px;line-height:1.8;color:#333;margin:12px 0;"><strong>文 / 深夜解忧铺</strong></p>
<hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
{body_html}
<hr style="border:none;border-top:1px solid #eee;margin:40px 0;">
<p style="font-size:14px;color:#999;text-align:center;">深夜解忧铺</p>
<p style="font-size:13px;color:#bbb;text-align:center;">你的心事，有人听。</p>
</div>'''
print(f"[3/5] ✅ HTML ({len(full_html)} chars)")

# === Step 4: 创建草稿（⚠️ ensure_ascii=False） ===
print("[4/5] 创建草稿...")
article = {
    "title": ARTICLE_TITLE,
    "digest": ARTICLE_DIGEST,
    "content": full_html,
    "thumb_media_id": thumb_media_id,
    # ⚠️ 不传 author 字段（会报 45110）
}
draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(draft_url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as resp:
    draft_result = json.loads(resp.read().decode("utf-8"))
if "media_id" not in draft_result:
    print(f"[4/5] ❌ 失败: {draft_result}"); raise SystemExit(1)
media_id = draft_result["media_id"]
print(f"[4/5] ✅ media_id: {media_id}")

# === Step 5: 验证中文编码 ===
print("[5/5] 验证编码...")
verify_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={access_token}"
v_payload = json.dumps({"offset": 0, "count": 1, "no_content": True}, ensure_ascii=False).encode("utf-8")
v_req = urllib.request.Request(verify_url, data=v_payload, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(v_req, timeout=10) as resp:
    vr = json.loads(resp.read().decode("utf-8"))
if vr.get("item"):
    v_title = vr["item"][0].get("content", {}).get("news_item", [{}])[0].get("title", "")
    ok = any("\u4e00" <= c <= "\u9fff" for c in v_title)
    print(f"[5/5] {'✅' if ok else '⚠️'} 草稿标题: {v_title}")
    if not ok:
        print("⚠️ 标题疑似乱码，请到草稿箱人工检查！")

print("\n" + "=" * 50)
print("✅ 发布完成！")
print(f"   标题: {ARTICLE_TITLE}")
print(f"   草稿 media_id: {media_id}")
print("   请前往 mp.weixin.qq.com → 草稿箱 确认并发布")
print("=" * 50)
