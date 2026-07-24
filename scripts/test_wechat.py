#!/usr/bin/env python3
"""Test WeChat API connection"""
import json, urllib.request, os
from pathlib import Path

# Load env
env = {}
for p in [Path(r"D:\blog\scripts\.env"), Path(os.environ.get("USERPROFILE","")) / "AppData/Local/hermes/.env"]:
    if p.exists():
        for line in open(p, "r"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")

print("APP_ID:", env.get("WEIXIN_APP_ID", "NOT SET")[:10] + "...")
print("SECRET:", "SET" if env.get("WEIXIN_APP_SECRET") else "NOT SET")

# Get token
appid = env.get("WEIXIN_APP_ID")
secret = env.get("WEIXIN_APP_SECRET")
if not appid or not secret:
    print("Missing credentials!")
    exit(1)

url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
try:
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        token = data.get("access_token")
        if token:
            print("Token OK:", token[:20] + "...")
            # Try upload
            cover_path = r"D:\blog\covers\cover_2026-07-24_讨好型人格的人连生气.jpg"
            boundary = "----FormBoundary"
            with open(cover_path, "rb") as f:
                file_data = f.read()
            body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n").encode() + file_data + f"\r\n--{boundary}--\r\n".encode()
            upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
            req = urllib.request.Request(upload_url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
            with urllib.request.urlopen(req, timeout=30) as resp2:
                result = json.loads(resp2.read().decode("utf-8"))
                print("Upload result:", json.dumps(result, ensure_ascii=False)[:300])
        else:
            print("No token! errcode:", data.get("errcode"), "errmsg:", data.get("errmsg"))
except Exception as e:
    print("Error:", e)
