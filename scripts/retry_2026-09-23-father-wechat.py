#!/usr/bin/env python3
"""Retry script for WeChat article publish. Run after adding IP 125.121.126.197 to whitelist."""
import json, urllib.request, os, re, time

ENV_PATH = "D:/blog/scripts/.env"
COVER_PATH = "D:/blog/content/posts/cover_2026-09-23-father-wechat.png"
POST_PATH = "D:/blog/content/posts/2026-09-23-那个从不回我微信的父亲其实一直在等我说话.md"
TITLE = "那个从不回我微信的父亲，其实一直在等我说话"
DIGEST = "有些人的爱，藏在那些你永远不会发现的角落里。父亲从不回微信，但他一直在等你先开口。"

env = {}
with open(ENV_PATH, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={env['WEIXIN_APP_ID']}&secret={env['WEIXIN_APP_SECRET']}"
with urllib.request.urlopen(token_url, timeout=10) as resp:
    result = json.loads(resp.read().decode("utf-8"))
if "access_token" not in result:
    print(f"Token error: {result}")
    exit(1)
token = result["access_token"]
print(f"Token OK: {token[:10]}...")
time.sleep(1)

boundary = "----FB7MA4"
file_data = open(COVER_PATH, "rb").read()
body = f"--{boundary}\r\n".encode()
body += b'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'
body += b"Content-Type: image/png\r\n\r\n"
body += file_data
body += f"\r\n--{boundary}--\r\n".encode()

upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
req = urllib.request.Request(upload_url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
with urllib.request.urlopen(req, timeout=30) as resp:
    upload_result = json.loads(resp.read().decode("utf-8"))
if "media_id" not in upload_result:
    print(f"Upload failed: {upload_result}")
    exit(1)
thumb_media_id = upload_result["media_id"]
print(f"Cover uploaded: {thumb_media_id}")

with open(POST_PATH, "r", encoding="utf-8") as f:
    md_content = f.read()
body_md = md_content.split("---", 2)[2].strip()

html = body_md
html = re.sub(r'## (\d+)', lambda m: f'<h2 style="font-size:20px;color:#333;margin-top:30px;margin-bottom:15px;font-weight:bold;">{m.group(1)}</h2>', html)
html = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#333;">\1</strong>', html)
html = re.sub(r'\*(.+?)\*', r'<em style="color:#666;">\1</em>', html)
html = html.replace('---', '<hr style="border:none;border-top:1px solid #eee;margin:20px 0;">')

paras = html.split('\n\n')
out = []
for p in paras:
    p = p.strip()
    if not p: continue
    if p.startswith('<h2') or p.startswith('<hr') or p.startswith('<strong'):
        out.append(p)
    else:
        text = '<br>'.join(l.strip() for l in p.split('\n') if l.strip())
        if text:
            out.append(f'<p style="font-size:16px;line-height:1.8;color:#333;margin-bottom:15px;">{text}</p>')
html_content = '\n'.join(out)
html_content += '<br><hr style="border:none;border-top:1px solid #eee;margin:30px 0;">'
html_content += '<p style="font-size:14px;color:#999;text-align:center;">深夜解忧铺</p>'
html_content += '<p style="font-size:13px;color:#aaa;text-align:center;">你的心事有人听</p>'

article = {"title": TITLE, "digest": DIGEST, "content": html_content, "thumb_media_id": thumb_media_id}
draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(draft_url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as resp:
    dr = json.loads(resp.read().decode("utf-8"))
if "media_id" in dr:
    print(f"\nDraft created! media_id: {dr['media_id']}")
else:
    print(f"Draft failed: {dr}")
