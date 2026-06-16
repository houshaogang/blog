#!/usr/bin/env python3
"""
AI副业实验室 - 公众号自动发布流水线
功能：自动生成文章 + 发布到公众号
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# ============== 配置区 ==============
WECHAT_APP_ID = os.environ.get("WECHAT_APP_ID", "你的AppID")
WECHAT_APP_SECRET = os.environ.get("WECHAT_APP_SECRET", "你的AppSecret")

# 文章模板目录
TEMPLATE_DIR = Path(r"D:\blog\content\posts")
# 发布记录
PUBLISH_LOG = Path(r"D:\blog\scripts\publish_log.json")
# =====================================

def get_access_token():
    """获取微信公众号 access_token"""
    import urllib.request
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={WECHAT_APP_ID}&secret={WECHAT_APP_SECRET}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            if "access_token" in data:
                print(f"✅ 获取access_token成功")
                return data["access_token"]
            else:
                print(f"❌ 获取token失败: {data}")
                return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def create_draft(token, title, content, author="AI副业实验室"):
    """创建公众号草稿"""
    import urllib.request
    
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    
    # 组装文章内容（HTML格式）
    article = {
        "title": title,
        "author": author,
        "content": content,
        "content_source_url": "",
        "need_open_comment": 0,
        "only_fans_can_comment": 0
    }
    
    data = json.dumps({"articles": [article]}, ensure_ascii=False).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json; charset=utf-8"
    })
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if "media_id" in result:
                print(f"✅ 草稿创建成功! media_id: {result['media_id']}")
                return result["media_id"]
            else:
                print(f"❌ 创建草稿失败: {result}")
                return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def publish_draft(token, media_id):
    """发布草稿"""
    import urllib.request
    
    url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={token}"
    data = json.dumps({"media_id": media_id}).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json"
    })
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if result.get("errcode", 0) == 0:
                print(f"✅ 发布成功!")
                return True
            else:
                print(f"❌ 发布失败: {result}")
                return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def log_publish(title, status):
    """记录发布日志"""
    log = []
    if PUBLISH_LOG.exists():
        log = json.loads(PUBLISH_LOG.read_text(encoding='utf-8'))
    
    log.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": title,
        "status": status
    })
    
    PUBLISH_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')

def main():
    print("=" * 50)
    print(f"📰 AI副业实验室 - 自动发布")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 检查配置
    if WECHAT_APP_ID == "你的AppID":
        print("⚠️  请先配置 WECHAT_APP_ID 和 WECHAT_APP_SECRET")
        print("   设置环境变量或直接修改脚本顶部的配置区")
        print("   获取方式：登录 mp.weixin.qq.com → 开发 → 基本配置")
        sys.exit(1)
    
    # 1. 获取token
    token = get_access_token()
    if not token:
        sys.exit(1)
    
    # 2. 读取最新文章
    # 这里可以接入AI自动生成文章的逻辑
    # 暂时使用手动指定或模板
    print("📝 请指定要发布的文章内容...")
    # TODO: 接入AI自动生成
    
    # 3. 创建草稿
    # media_id = create_draft(token, "文章标题", "<p>文章内容</p>")
    
    # 4. 发布
    # publish_draft(token, media_id)
    
    print("✅ 流水线就绪，等待配置完成")

if __name__ == "__main__":
    main()
