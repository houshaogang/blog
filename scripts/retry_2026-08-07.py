
import os
import re
import json
import urllib.request
import requests
from PIL import Image

def main():
    # Load Credentials
    env_path = "D:/blog/scripts/.env"
    env = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    env[k] = v

    APP_ID = env.get("WEIXIN_APP_ID")
    APP_SECRET = env.get("WEIXIN_APP_SECRET")

    if not APP_ID or not APP_SECRET:
        print("Error: Missing WEIXIN_APP_ID or WEIXIN_APP_SECRET in .env")
        return

    # Get Token
    token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    resp = requests.get(token_url).json()
    access_token = resp.get("access_token")
    
    if not access_token:
        print(f"Error getting token: {resp}")
        return

    # Upload Cover
    cover_path = "D:/blog/content/posts/cover_2026-08-06-人到中年连哭都变成了一种奢侈.png"
    try:
        with Image.open(cover_path) as img:
            if img.size != (900, 383):
                img = img.resize((900, 383), Image.LANCZOS)
                temp_cover = "D:/blog/content/posts/cover_temp.png"
                img.save(temp_cover, "PNG")
                cover_path_to_upload = temp_cover
            else:
                cover_path_to_upload = cover_path
    except Exception as e:
        print(f"Error processing cover: {e}. Using original.")
        cover_path_to_upload = cover_path

    upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=thumb"
    with open(cover_path_to_upload, 'rb') as f:
        files = {'media': ('cover.png', f, 'image/png')}
        upload_resp = requests.post(upload_url, files=files).json()

    thumb_media_id = upload_resp.get("media_id")
    if not thumb_media_id:
        print(f"Error uploading cover: {upload_resp}")
        return

    # Read HTML content
    html_path = "D:/blog/content/posts/2026-08-07-chungking-forever.html"
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Create Draft
    TITLE = "凌晨两点的过期凤梨罐头，和你过期的梦"
    DIGEST = "我们大概也都有一个过期的日期，只是没人告诉我们，那个日期是哪一天。"
    
    article = {
        "title": TITLE,
        "author": "", 
        "digest": DIGEST,
        "content": content,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }

    draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }
    
    req = urllib.request.Request(draft_url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            draft_resp = json.loads(response.read().decode("utf-8"))
        
        media_id = draft_resp.get("media_id")
        if media_id:
            print(f"Draft created successfully: {media_id}")
            
            # Verify
            batchget_url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={access_token}"
            verify_payload = json.dumps({"offset": 0, "count": 1, "no_content": 1}).encode("utf-8")
            verify_req = urllib.request.Request(batchget_url, data=verify_payload, headers=headers)
            with urllib.request.urlopen(verify_req) as v_response:
                verify_resp = json.loads(v_response.read().decode("utf-8"))
            
            if verify_resp.get("item"):
                title_in_draft = verify_resp["item"][0]["content"]["news_item"][0]["title"]
                print(f"Verification: Draft title found: {title_in_draft}")
                if "过期" in title_in_draft:
                    print("Chinese characters verified.")
                else:
                    print("Warning: Title might be garbled or mismatched.")
        else:
            print(f"Error creating draft: {draft_resp}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
