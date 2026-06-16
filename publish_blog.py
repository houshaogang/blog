#!/usr/bin/env python3
"""
博客自动发布脚本
用法:
  python publish_blog.py --title "标题" --tags "tag1,tag2" --file content.md
  echo "文章内容" | python publish_blog.py --title "标题" --tags "tag1,tag2" --stdin
  python publish_blog.py --title "标题" --tags "tag1,tag2"  # 空内容，仅建文件+推送
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BLOG_DIR = Path(r"D:\blog")
POSTS_DIR = BLOG_DIR / "content" / "posts"
WEIXIN_SCRIPT = BLOG_DIR / "scripts" / "wechat_publish.py"


def find_github_token():
    """查找 GitHub token"""
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        return token
    env_path = os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "hermes", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GITHUB_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    cred_file = os.path.expanduser("~/.git-credentials")
    if os.path.exists(cred_file):
        with open(cred_file, "r") as f:
            for line in f:
                if "github.com" in line and "@" in line:
                    return line.split("//")[1].split("@")[0]
    return ""


def git_cmd(args, check=True):
    """Run git command in BLOG_DIR"""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(BLOG_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    if check and result.returncode != 0:
        print(f"git {' '.join(args)} failed: {result.stderr[:500]}")
    return result


def git_push():
    """智能 git push，自动处理冲突"""
    git_cmd(["fetch", "origin", "main"], check=False)

    result = git_cmd(["rev-list", "--count", "HEAD..origin/main"], check=False)
    behind = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0

    if behind > 0:
        print(f"本地落后远程 {behind} 个提交，先 pull...")
        git_cmd(["stash", "push", "-u", "-m", "auto-publish"], check=False)
        pull_result = git_cmd(["pull", "--rebase", "origin", "main"], check=False)
        if pull_result.returncode != 0:
            print(f"pull 失败: {pull_result.stderr[:200]}")
        git_cmd(["stash", "pop"], check=False)

    git_cmd(["add", "-A"])

    result = git_cmd(["diff", "--cached", "--quiet"], check=False)
    if result.returncode == 0:
        print("没有新变更需要提交")
        return True

    today = datetime.now().strftime("%Y-%m-%d")
    git_cmd(["commit", "-m", f"feat: 自动发布文章 {today}"])

    result = git_cmd(["push", "origin", "main"])
    if result.returncode == 0:
        print("Git push 成功! GitHub Actions 将自动部署")
        return True
    else:
        print(f"Git push 失败: {result.stderr[:300]}")
        return False


def try_wechat_draft(title, content_md, tags):
    """尝试上传到微信公众号草稿箱"""
    env_path = os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "hermes", ".env")
    wechat_config = {}
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("WEIXIN_APP_ID="):
                    wechat_config["app_id"] = line.split("=", 1)[1].strip().strip('"')
                elif line.startswith("WEIXIN_APP_SECRET="):
                    wechat_config["app_secret"] = line.split("=", 1)[1].strip().strip('"')

    if not wechat_config.get("app_id") or not wechat_config.get("app_secret"):
        return False, "微信配置缺失"

    try:
        import urllib.request
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={wechat_config['app_id']}&secret={wechat_config['app_secret']}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            if "access_token" not in data:
                return False, f"获取token失败: {data}"
            token = data["access_token"]

        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
        article = {
            "title": title[:64],
            "content": content_md,
            "content_source_url": "",
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
        }
        data = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json; charset=utf-8"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if "media_id" in result:
                print(f"微信草稿创建成功! media_id: {result['media_id']}")
                return True, result["media_id"]
            else:
                return False, f"草稿创建失败: {result}"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="博客自动发布")
    parser.add_argument("--title", required=True, help="文章标题")
    parser.add_argument("--tags", default="AI,科技", help="标签，逗号分隔")
    parser.add_argument("--file", help="从文件读取内容（markdown）")
    parser.add_argument("--stdin", action="store_true", help="从stdin读取内容")
    parser.add_argument("--no-git", action="store_true", help="不执行git push")
    parser.add_argument("--wechat", action="store_true", help="同时发布到微信公众号草稿箱")
    args = parser.parse_args()

    today = datetime.now().strftime("%Y-%m-%d")
    slug = args.title[:30].replace(" ", "-").replace("：", "-").replace("，", "-")
    slug = "".join(c for c in slug if c.isalnum() or c in "-_")
    filename = f"{today}-{slug}.md"

    content = ""
    if args.stdin:
        content = sys.stdin.read()
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()

    tags_list = [t.strip() for t in args.tags.split(",")]
    frontmatter = f'---\ntitle: "{args.title}"\ndate: {today}\ndraft: false\ntags: {json.dumps(tags_list, ensure_ascii=False)}\ncategories: ["AI资讯"]\nsummary: "{args.title}"\n---\n\n'
    full_content = frontmatter + content

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = POSTS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)
    print(f"文章已保存: {filepath}")

    if args.wechat:
        ok, msg = try_wechat_draft(args.title, content, tags_list)
        print(f"微信草稿: {'成功' if ok else '失败'} - {msg}")

    if not args.no_git:
        git_push()

    print(f"文件: {filepath}")
    print(f"博客: https://houshaogang.github.io/blog/")


if __name__ == "__main__":
    main()
