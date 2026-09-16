# -*- coding: utf-8 -*-
"""
发布「其实你不用假装回复我」到深夜解忧铺草稿箱
用法: D:/python310/python.exe D:/blog/scripts/retry_2026-09-16-pretend-reply.py
"""
import json, re, time, os, urllib.request, urllib.parse, ssl

# === 读取凭证（first file wins，避免 .hermes/.env 覆盖） ===
env = {}
for p in [r"D:\blog\scripts\.env", os.path.expanduser("~/.hermes/.env")]:
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip()
                    if k not in env:
                        env[k] = v
        if "WEIXIN_APP_ID" in env and "WEIXIN_APP_SECRET" in env:
            break

APP_ID = env["WEIXIN_APP_ID"]
APP_SECRET = env["WEIXIN_APP_SECRET"]

# === 文章内容 ===
TITLE = "其实你不用假装回复我"
DIGEST = "如果你不想再和我聊天了，完全可以干脆利落地断开联系。"

MARKDOWN = open(r"D:\blog\content\posts\2026-09-16-其实你不用假装回复我.md", "r", encoding="utf-8").read()

# 去掉 frontmatter
MARKDOWN = re.sub(r'^---.*?---\s*', '', MARKDOWN, flags=re.DOTALL)

# === SSL context ===
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_json(url, data=None, headers=None, timeout=15):
    if data and isinstance(data, dict):
        data = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers or {})
    resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
    raw = resp.read()
    return json.loads(raw.decode("utf-8"))

# === 1. 获取 token ===
print("1. 获取access_token...")
token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
token_data = fetch_json(token_url)
if "access_token" not in token_data:
    print(f"❌ 获取token失败: {token_data}")
    exit(1)
token = token_data["access_token"]
print(f"   ✅ token: {token[:20]}...")

# === 2. 下载封面图 ===
print("2. 下载封面图...")
cover_url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(
    "sad person sitting alone in dimly lit room, warm melancholy atmosphere, cinematic moody lighting, soft shadows, contemplative mood"
) + "?width=900&height=383&nologo=true&seed=" + str(int(time.time()))

cover_path = r"D:\blog\content\posts\cover_2026-09-16.jpg"
for attempt in range(3):
    try:
        req = urllib.request.Request(cover_url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=30, context=ctx)
        with open(cover_path, "wb") as f:
            f.write(resp.read())
        size = os.path.getsize(cover_path)
        if size > 5000:
            print(f"   ✅ 封面已下载: {size} bytes")
            break
        else:
            print(f"   ⚠️ 文件太小({size}), 重试...")
    except Exception as e:
        print(f"   ⚠️ 下载失败(尝试{attempt+1}): {e}")
        time.sleep(2)
else:
    print("❌ 封面下载失败, 尝试用已有封面...")
    # fallback: 用目录下已有的
    import glob
    covers = glob.glob(r"D:\blog\content\posts\cover*.jpg") + glob.glob(r"D:\blog\content\posts\cover*.png")
    if covers:
        cover_path = covers[-1]
        print(f"   使用已有封面: {cover_path}")
    else:
        print("❌ 无可用封面，跳过")
        exit(1)

# === 3. 上传封面图 ===
print("3. 上传封面图...")
upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"

boundary = "----FormBoundary7MA4YWxk" + str(int(time.time()))
file_data = open(cover_path, "rb").read()
filename = os.path.basename(cover_path)
content_type = "image/jpeg" if cover_path.endswith(".jpg") else "image/png"

body = f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"{filename}\"\r\nContent-Type: {content_type}\r\n\r\n".encode()
body += file_data
body += f"\r\n--{boundary}--\r\n".encode()

req = urllib.request.Request(upload_url, data=body, headers={
    "Content-Type": f"multipart/form-data; boundary={boundary}"
})
resp = urllib.request.urlopen(req, timeout=60, context=ctx)
upload_result = json.loads(resp.read().decode("utf-8"))

if "media_id" not in upload_result:
    print(f"❌ 上传封面失败: {upload_result}")
    exit(1)
thumb_media_id = upload_result["media_id"]
print(f"   ✅ media_id: {thumb_media_id}")

# === 4. Markdown 转 HTML ===
print("4. Markdown转HTML...")
content = MARKDOWN

# 小节标题
content = re.sub(r'^## (.+)$',
    r'<h2 style="margin:25px 0 12px;font-size:20px;color:#333;border-left:4px solid #e74c3c;padding-left:10px;">\1</h2>',
    content, flags=re.MULTILINE)

# 加粗 → 红色强调
content = re.sub(r'\*\*(.*?)\*\*',
    r'<strong style="color:#e74c3c;">\1</strong>',
    content)

# 斜体 → 结尾金句
content = re.sub(r'\*(.*?)\*',
    r'<p style="text-align:center;color:#999;font-size:15px;margin-top:30px;">\1</p>',
    content)

# 分割线
content = re.sub(r'^---$', '<hr style="border:none;border-top:1px solid #eee;margin:20px 0;">', content, flags=re.MULTILINE)

# 段落
paragraphs = content.split('\n\n')
html_parts = []
for p in paragraphs:
    p = p.strip()
    if not p:
        continue
    if p.startswith('<h2') or p.startswith('<strong') or p.startswith('<p style="text-align') or p.startswith('<hr'):
        html_parts.append(p)
    else:
        html_parts.append(f'<p style="font-size:16px;color:#555;line-height:1.8;margin:12px 0;">{p}</p>')

html_content = '\n'.join(html_parts)

# 包裹容器
html_content = f'''
<div style="max-width:600px;margin:0 auto;padding:20px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
{html_content}
</div>
'''

# === 5. 创建草稿 ===
print("5. 创建草稿...")
draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
draft_data = {
    "articles": [{
        "title": TITLE,
        "digest": DIGEST,
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }]
}

data_bytes = json.dumps(draft_data, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(draft_url, data=data_bytes, headers={
    "Content-Type": "application/json; charset=utf-8"
})
resp = urllib.request.urlopen(req, timeout=15, context=ctx)
result = json.loads(resp.read().decode("utf-8"))

if "media_id" in result:
    print(f"✅ 草稿创建成功！media_id: {result['media_id']}")
    print(f"📌 去公众号后台 → 草稿箱 → 预览发布")
else:
    print(f"❌ 草稿创建失败: {result}")
