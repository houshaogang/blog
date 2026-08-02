#!/usr/bin/env python3
"""
重试脚本：2026-08-02 《三十岁重看〈当幸福来敲门〉》
IP白名单添加后执行此脚本创建草稿。

使用方法：
    python D:/blog/scripts/retry_2026-08-02.py
"""
import json, os, sys, urllib.request

# ========== 配置 ==========
APP_ID = "wx4f7ec5527892c5d6"
APP_SECRET = "e50936...1be9"
TITLE = "三十岁重看《当幸福来敲门》，每一帧都是自己的生活"
DIGEST = "三十岁重看经典电影，每一帧都是自己的生活。成年人的体面，是在最难的时候假装一切正常。"
COVER_PATH = r"D:/blog/content/posts/cover_2026-08-02-pursuit-of-happyness.png"
HTML_PATH = r"D:/blog/content/posts/2026-08-02-thirty-rewatch-pursuit-of-happyness.html"

# ========== 获取 access_token ==========
def get_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "access_token" in data:
        print(f"  ✓ Token: {data['access_token'][:15]}...")
        return data["access_token"]
    raise Exception(f"Token失败: {data}")

# ========== 上传封面图 ==========
def upload_cover(token):
    boundary = "----RetryBoundary2026"
    with open(COVER_PATH, "rb") as f:
        file_data = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()
    
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" in result:
        print(f"  ✓ 封面上传: {result['media_id'][:30]}...")
        return result["media_id"]
    raise Exception(f"封面上传失败: {result}")

# ========== 创建草稿 ==========
def create_draft(token, thumb_media_id):
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    article = {
        "title": TITLE,
        "digest": DIGEST,
        "content": html_content,
        "thumb_media_id": thumb_media_id,
        "content_source_url": "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0
        # ⚠️ 不要传 author 字段，会报 45110 错误
    }
    
    # ⚠️ 关键：用 ensure_ascii=False 防止中文变 \uXXXX 乱码
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json; charset=utf-8"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "media_id" in result:
        print(f"  ✓ 草稿创建: {result['media_id']}")
        return result["media_id"]
    raise Exception(f"草稿创建失败: {result}")

# ========== 验证草稿 ==========
def verify_draft(token, media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
    payload = json.dumps({"offset": 0, "count": 5, "no_content": 1}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json; charset=utf-8"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    
    for item in result.get("item", []):
        if item.get("media_id") == media_id:
            news = item.get("content", {}).get("news_item", [{}])[0]
            title = news.get("title", "")
            if "\\u" in repr(title):
                print(f"  ⚠️ 标题可能乱码: {title}")
                return False
            print(f"  ✓ 验证通过: {title}")
            return True
    print(f"  ⚠️ 未找到该草稿")
    return False

# ========== 主流程 ==========
if __name__ == "__main__":
    print("=" * 50)
    print("重试创建草稿：三十岁重看《当幸福来敲门》，每一帧都是自己的生活")
    print("=" * 50)
    
    print("\n1. 获取 access_token...")
    token = get_token()
    
    print("\n2. 上传封面图...")
    thumb_id = upload_cover(token)
    
    print("\n3. 创建草稿...")
    draft_id = create_draft(token, thumb_id)
    
    print("\n4. 验证草稿...")
    ok = verify_draft(token, draft_id)
    
    print("\n" + "=" * 50)
    if ok:
        print(f"✅ 成功！media_id: {draft_id}")
    else:
        print(f"⚠️ 草稿已创建 media_id: {draft_id}，但验证未通过")
    print("请登录公众号后台 → 草稿箱 → 发表")
    print("=" * 50)
