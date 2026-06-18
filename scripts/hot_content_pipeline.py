#!/usr/bin/env python3
"""
热点内容自动发布流水线
功能：抓取热搜 → AI生成文章 → 推送到微信公众号草稿箱
用法：python hot_content_pipeline.py [--topic "指定话题"] [--count 3] [--dry-run]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

# ============ 配置 ============
BLOG_DIR = Path(r"D:\blog")
POSTS_DIR = BLOG_DIR / "content" / "posts"
SCRIPTS_DIR = BLOG_DIR / "scripts"
COVERS_DIR = BLOG_DIR / "covers"
WEIXIN_ENV = Path(os.environ.get("USERPROFILE", "")) / "AppData/Local/hermes/.env"
WEIXIN_SCRIPT = SCRIPTS_DIR / "wechat_publish.py"

# 微信配置
WEIXIN_APP_ID = ""
WEIXIN_APP_SECRET = ""

def load_weixin_config():
    """加载微信配置"""
    global WEIXIN_APP_ID, WEIXIN_APP_SECRET
    
    # 优先从 .env 读取
    env_paths = [
        SCRIPTS_DIR / ".env",
        WEIXIN_ENV,
    ]
    for env_path in env_paths:
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("WEIXIN_APP_ID=") or line.startswith("WECHAT_APP_ID="):
                        WEIXIN_APP_ID = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("WEIXIN_APP_SECRET=") or line.startswith("WECHAT_APP_SECRET="):
                        WEIXIN_APP_SECRET = line.split("=", 1)[1].strip().strip('"').strip("'")
    
    if not WEIXIN_APP_ID or not WEIXIN_APP_SECRET:
        print("⚠️ 微信配置缺失，将只保存本地文件")
        return False
    return True


# ============ 热搜抓取 ============
def fetch_douyin_hot():
    """抓取抖音热搜（通过第三方API）"""
    hot_list = []
    
    # 方法1：使用聚合API
    apis = [
        "https://apis.tianapi.com/toutiao/index",  # 需要key
        "https://api.vvhan.com/api/hotlist/douyinHot",  # 免费
        "https://tenapi.cn/v2/douyinhot",  # 免费
    ]
    
    for api_url in apis:
        try:
            req = urllib.request.Request(api_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                
                # 解析不同API格式
                items = data.get("data", data.get("result", data.get("list", [])))
                if isinstance(items, dict):
                    items = items.get("list", items.get("data", []))
                
                for item in items[:20]:
                    title = item.get("title", item.get("word", item.get("name", "")))
                    hot = item.get("hot", item.get("hotValue", item.get("num", "")))
                    if title:
                        hot_list.append({"title": title, "hot": hot, "source": "douyin"})
                
                if hot_list:
                    print(f"✅ 抖音热搜获取成功 ({len(hot_list)}条)")
                    return hot_list
        except Exception as e:
            continue
    
    print("⚠️ 抖音热搜获取失败，尝试备用方案")
    return hot_list


def fetch_weibo_hot():
    """抓取微博热搜"""
    hot_list = []
    apis = [
        "https://tenapi.cn/v2/weibohot",
        "https://api.vvhan.com/api/hotlist/wbHot",
    ]
    
    for api_url in apis:
        try:
            req = urllib.request.Request(api_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("data", data.get("result", data.get("list", [])))
                if isinstance(items, dict):
                    items = items.get("list", items.get("data", []))
                
                for item in items[:15]:
                    title = item.get("title", item.get("word", item.get("name", "")))
                    hot = item.get("hot", item.get("hotValue", item.get("num", "")))
                    if title:
                        hot_list.append({"title": title, "hot": hot, "source": "weibo"})
                
                if hot_list:
                    print(f"✅ 微博热搜获取成功 ({len(hot_list)}条)")
                    return hot_list
        except Exception as e:
            continue
    
    return hot_list


def fetch_all_hot():
    """获取所有平台热搜"""
    all_hot = []
    all_hot.extend(fetch_douyin_hot())
    all_hot.extend(fetch_weibo_hot())
    
    # 如果API都失败，用备用方案：直接搜索
    if not all_hot:
        print("📡 使用搜索引擎获取热点...")
        try:
            import urllib.parse
            query = urllib.parse.quote("今日热点新闻")
            url = f"https://www.baidu.com/s?wd={query}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
                # 简单提取标题
                titles = re.findall(r'<h3[^>]*>.*?<a[^>]*>(.*?)</a>', content, re.DOTALL)
                for t in titles[:10]:
                    clean = re.sub(r'<[^>]+>', '', t).strip()
                    if clean and len(clean) > 5:
                        all_hot.append({"title": clean, "hot": "", "source": "baidu"})
        except:
            pass
    
    return all_hot


# ============ AI文章生成 ============
def generate_article(topic, style="informative"):
    """用AI生成文章（调用本地或远程API）"""
    
    prompts = {
        "informative": f"""你是一位专业的自媒体写手。请根据以下热点话题撰写一篇微信公众号文章。

话题：{topic}

要求：
1. 标题吸引人，带emoji，不超过64字
2. 正文800-1500字，分3-5个小节
3. 语言通俗易懂，有观点有分析
4. 适合80后、90后读者
5. 结尾引导互动（点赞、在看、转发）
6. 不要包含frontmatter，直接输出正文
7. 每个小节用 ## 标记

请直接输出文章内容：""",
        
        "emotional": f"""你是一位情感类自媒体写手，风格温暖治愈。请根据以下热点话题撰写一篇情感共鸣类公众号文章。

话题：{topic}

要求：
1. 标题走心，带emoji，不超过64字
2. 正文800-1500字，分3-5个小节
3. 从情感角度切入，引发共鸣
4. 语言温暖，有故事感
5. 结尾引导互动
6. 不要包含frontmatter，直接输出正文
7. 每个小节用 ## 标记

请直接输出文章内容：""",
    }
    
    prompt = prompts.get(style, prompts["informative"])
    
    # 尝试调用AI API
    # 方案1：使用环境变量中的API
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    if api_key:
        try:
            url = f"{api_base}/chat/completions"
            payload = json.dumps({
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.8,
            }).encode("utf-8")
            
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            })
            
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"API调用失败: {e}")
    
    # 方案2：使用subprocess调用hermes或其他CLI
    # 方案3：返回模板（兜底）
    print("⚠️ 无法调用AI API，使用模板生成")
    return generate_template_article(topic)


def generate_template_article(topic):
    """模板文章生成（兜底方案）"""
    today = datetime.now().strftime("%Y年%m月%d日")
    
    article = f"""## {topic}，到底怎么回事？

最近，「{topic}」这个话题在网上引起了不少讨论。今天我们就来聊聊这个事儿。

## 事件回顾

{today}，关于「{topic}」的消息在各大平台刷屏。不少网友表示关注，相关话题阅读量迅速突破千万。

从目前的信息来看，这件事之所以引发热议，主要有以下几个原因：

1. **话题本身具有争议性** — 不同立场的人有不同的看法
2. **涉及面广** — 关系到很多人的切身利益
3. **信息不对称** — 真相扑朔迷离，各种说法满天飞

## 深度分析

说实话，看到这个消息的第一反应，我是挺震惊的。

但冷静下来想想，这件事其实早有端倪。回顾过去几个月的发展，很多迹象都已经暗示了今天的结果。

**从行业角度看：** 这不仅仅是一个孤立事件，而是整个行业发展的必然趋势。

**从个人角度看：** 这提醒我们，在信息爆炸的时代，更需要保持独立思考的能力。

## 网友热议

评论区也是炸开了锅：

> "早就该这样了！"
> "细思极恐..."
> "所以之前说的都是真的？"

不同声音的碰撞，恰恰说明大家都在认真思考这个问题。

## 写在最后

对于「{topic}」，你怎么看？

欢迎在评论区留下你的想法，觉得有用的话点个「在看」，让更多人看到。

---

*每天更新，带你读懂身边事。*
"""
    return article


# ============ 微信发布 ============
def get_wechat_token():
    """获取微信access_token"""
    if not WEIXIN_APP_ID or not WEIXIN_APP_SECRET:
        return None
    
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={WEIXIN_APP_ID}&secret={WEIXIN_APP_SECRET}"
    
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "access_token" in data:
                return data["access_token"]
            else:
                print(f"获取token失败: {data}")
                return None
    except Exception as e:
        print(f"获取token异常: {e}")
        return None


def create_wechat_draft(title, content, tags=None):
    """创建微信公众号草稿"""
    token = get_wechat_token()
    if not token:
        return None, "微信token获取失败"
    
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    
    article = {
        "title": title[:64],
        "content": content,
        "content_source_url": "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }
    
    if tags:
        article["author"] = ""
    
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json; charset=utf-8",
    })
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if "media_id" in result:
                return result["media_id"], None
            else:
                return None, f"创建失败: {result}"
    except Exception as e:
        return None, str(e)


# ============ 主流程 ============
def run_pipeline(topic=None, count=1, style="informative", dry_run=False):
    """执行完整流水线"""
    print("=" * 50)
    print("🚀 热点内容自动发布流水线")
    print("=" * 50)
    
    # 1. 加载配置
    load_weixin_config()
    
    # 2. 获取热点
    if topic:
        topics = [{"title": topic, "hot": "", "source": "manual"}]
    else:
        print("\n📡 正在获取热搜...")
        all_hot = fetch_all_hot()
        if not all_hot:
            print("❌ 无法获取热搜，退出")
            return
        topics = all_hot[:count]
    
    print(f"\n📋 待处理话题 ({len(topics)}个):")
    for i, t in enumerate(topics, 1):
        print(f"  {i}. [{t['source']}] {t['title']}")
    
    # 3. 生成并发布文章
    results = []
    for i, t in enumerate(topics, 1):
        print(f"\n{'='*50}")
        print(f"📝 正在处理第 {i}/{len(topics)} 个话题: {t['title']}")
        print("=" * 50)
        
        # 生成文章
        print("🤖 AI正在生成文章...")
        article = generate_article(t["title"], style=style)
        
        if not article:
            print(f"❌ 文章生成失败，跳过")
            continue
        
        # 提取标题（第一行）
        lines = article.strip().split("\n")
        title = lines[0].lstrip("#").strip() if lines else t["title"]
        title = title[:64]  # 微信标题限制
        
        print(f"📰 标题: {title}")
        print(f"📊 字数: {len(article)}")
        
        if dry_run:
            print("\n[Dry Run] 文章预览:")
            print("-" * 40)
            print(article[:500] + "..." if len(article) > 500 else article)
            print("-" * 40)
            results.append({"title": title, "status": "dry_run"})
            continue
        
        # 保存本地文件
        today = datetime.now().strftime("%Y-%m-%d")
        slug = re.sub(r'[^\w\u4e00-\u9fff-]', '', title[:30]).replace(" ", "-")
        filename = f"{today}-{slug}.md"
        filepath = POSTS_DIR / filename
        
        POSTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(article)
        print(f"💾 已保存: {filepath}")
        
        # 推送到微信草稿箱
        if WEIXIN_APP_ID and WEIXIN_APP_SECRET:
            print("📤 正在推送到微信草稿箱...")
            media_id, err = create_wechat_draft(title, article)
            if media_id:
                print(f"✅ 微信草稿创建成功! media_id: {media_id[:20]}...")
                results.append({"title": title, "status": "success", "media_id": media_id})
            else:
                print(f"❌ 微信草稿创建失败: {err}")
                results.append({"title": title, "status": "failed", "error": err})
        else:
            print("⚠️ 未配置微信，跳过推送")
            results.append({"title": title, "status": "local_only"})
        
        # 间隔避免请求过快
        if i < len(topics):
            time.sleep(2)
    
    # 4. 汇总
    print("\n" + "=" * 50)
    print("📊 执行结果汇总")
    print("=" * 50)
    success = sum(1 for r in results if r["status"] in ["success", "local_only", "dry_run"])
    print(f"✅ 成功: {success}/{len(results)}")
    for r in results:
        status_icon = "✅" if r["status"] in ["success", "local_only", "dry_run"] else "❌"
        print(f"  {status_icon} {r['title']}")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="热点内容自动发布流水线")
    parser.add_argument("--topic", help="指定话题（不指定则自动抓取热搜）")
    parser.add_argument("--count", type=int, default=3, help="处理话题数量（默认3）")
    parser.add_argument("--style", choices=["informative", "emotional"], default="informative", help="文章风格")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际发布")
    args = parser.parse_args()
    
    run_pipeline(
        topic=args.topic,
        count=args.count,
        style=args.style,
        dry_run=args.dry_run,
    )
