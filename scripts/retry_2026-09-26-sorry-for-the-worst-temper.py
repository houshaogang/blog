"""
重试脚本 - 对不起，我总把最差的脾气留给最亲的人
生成时间: 2026-09-26
用途: 将文章发布到微信公众号草稿箱
使用方法: python retry_2026-09-26-sorry-for-the-worst-temper.py
前提: 已将服务器IP添加到微信公众号IP白名单
"""
import os
import sys
import requests
import json
import time

# 加载环境变量
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

APPID = os.environ.get('WECHAT_APPID', '')
APPSECRET = os.environ.get('WECHAT_APPSECRET', '')

if not APPID or not APPSECRET:
    print("❌ 请在 .env 文件中设置 WECHAT_APPID 和 WECHAT_APPSECRET")
    sys.exit(1)

def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
    resp = requests.get(url)
    data = resp.json()
    if 'access_token' in data:
        print(f"✅ 获取 access_token 成功")
        return data['access_token']
    else:
        print(f"❌ 获取 access_token 失败: {data}")
        sys.exit(1)

def upload_image(token, image_path):
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
    with open(image_path, 'rb') as f:
        files = {'media': (os.path.basename(image_path), f, 'image/jpeg')}
        resp = requests.post(url, files=files)
    data = resp.json()
    if 'url' in data:
        print(f"✅ 封面上传成功: {data['url'][:60]}...")
        return data['url']
    else:
        print(f"❌ 封面上传失败: {data}")
        return None

def create_draft(token, title, content, thumb_media_id=None):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    articles = {
        "articles": [{
            "title": title,
            "author": "深夜解忧铺",
            "digest": "我们把最好的耐心给了陌生人，却把最差的脾气留给了最亲的人。",
            "content": content,
            "content_source_url": "https://houshaogang.github.io/blog/",
            "thumb_media_id": thumb_media_id or "",
            "need_open_comment": 1,
            "only_fans_can_comment": 0
        }]
    }
    resp = requests.post(url, json=articles)
    data = resp.json()
    if 'media_id' in data:
        print(f"✅ 草稿创建成功! media_id: {data['media_id']}")
        return data['media_id']
    else:
        print(f"❌ 草稿创建失败: {data}")
        return None

def main():
    print("=" * 50)
    print("📝 重试发布: 对不起，我总把最差的脾气留给最亲的人")
    print("=" * 50)

    # 获取token
    token = get_access_token()

    # 上传封面
    cover_path = r"D:\blog\covers\cover_2026-09-26_对不起我总把最差的脾.jpg"
    if os.path.exists(cover_path):
        thumb_url = upload_image(token, cover_path)
    else:
        print(f"⚠️ 封面文件不存在: {cover_path}")
        thumb_url = None

    # 读取HTML内容
    html_path = r"D:\blog\content\posts\2026-09-26-sorry-for-the-worst-temper.html"
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 创建草稿
    title = "对不起，我总把最差的脾气留给最亲的人"
    media_id = create_draft(token, title, content)

    if media_id:
        print("\n" + "=" * 50)
        print("🎉 发布完成!")
        print(f"标题: {title}")
        print(f"media_id: {media_id}")
        print("请到公众号后台查看草稿箱")
        print("=" * 50)

if __name__ == '__main__':
    main()
