#!/usr/bin/env python3
"""
Markdown → 微信公众号HTML转换 + 发布
用法: python md_to_wechat.py --title "标题" --file article.md
"""

import argparse, json, os, re, sys, urllib.request
from pathlib import Path
from datetime import datetime

BLOG_DIR = Path(r"D:\blog")
POSTS_DIR = BLOG_DIR / "content" / "posts"
COVERS_DIR = BLOG_DIR / "covers"

def load_env():
    env = {}
    for path in [BLOG_DIR / "scripts" / ".env",
                 Path(os.environ.get("USERPROFILE", "")) / "AppData/Local/hermes/.env"]:
        if path.exists():
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def get_token(env):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={env['WEIXIN_APP_ID']}&secret={env['WEIXIN_APP_SECRET']}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8")).get("access_token")

def create_cover(title, output_path):
    from PIL import Image, ImageDraw, ImageFont
    size = (900, 383)
    img = Image.new('RGB', size)
    draw = ImageDraw.Draw(img)
    import random
    palettes = [
        ((30, 41, 59), (71, 85, 105)),
        ((44, 62, 80), (52, 152, 219)),
        ((39, 174, 96), (22, 160, 133)),
        ((142, 68, 173), (192, 57, 43)),
        ((41, 128, 185), (22, 160, 133)),
    ]
    c = random.choice(palettes)
    for y in range(size[1]):
        r = y / size[1]
        draw.line([(0, y), (size[0], y)], fill=tuple(
            int(c[0][i] * (1 - r) + c[1][i] * r) for i in range(3)))
    try:
        font = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", 36)
    except:
        font = ImageFont.load_default()
    max_w = size[0] - 80
    lines, line = [], ""
    for ch in title:
        if draw.textbbox((0, 0), line + ch, font=font)[2] > max_w:
            lines.append(line)
            line = ch
        else:
            line += ch
    if line:
        lines.append(line)
    lines = lines[:3]
    y0 = (size[1] - len(lines) * 50) // 2
    for i, ln in enumerate(lines):
        bb = draw.textbbox((0, 0), ln, font=font)
        draw.text(((size[0] - bb[2] + bb[0]) // 2, y0 + i * 50), ln, fill='white', font=font)
    img.save(output_path, quality=95)

def upload_image(token, path):
    boundary = "----FormBoundary"
    with open(path, "rb") as f:
        data = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"cover.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8")).get("media_id")

def create_draft(token, title, content, thumb_media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    article = {"title": title[:64], "content": content, "thumb_media_id": thumb_media_id,
               "content_source_url": "", "need_open_comment": 1, "only_fans_can_comment": 0}
    payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8")).get("media_id")

# ============ Markdown → WeChat HTML ============

STYLES = {
    'p': 'margin-bottom:15px;font-size:16px;line-height:1.8;color:#333;',
    'h2': 'font-size:20px;font-weight:bold;color:#333;margin:30px 0 15px 0;border-left:4px solid #c0392b;padding-left:12px;',
    'blockquote': 'border-left:4px solid #e74c3c;padding:10px 15px;margin:20px 0;background:#fdf2f2;color:#666;font-style:italic;',
    'bold': 'font-weight:bold;color:#222;',
    'italic': 'font-style:italic;color:#666;',
    'hr': 'border:none;border-top:1px solid #ddd;margin:30px 0;',
    'center': 'text-align:center;font-size:15px;color:#888;margin:20px 0;font-style:italic;',
}

def inline_format(text):
    """行内格式化：**bold** 和 *italic*"""
    text = re.sub(r'\*\*(.+?)\*\*', f'<strong style="{STYLES["bold"]}">\\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', f'<em style="{STYLES["italic"]}">\\1</em>', text)
    return text

def md_to_wechat_html(md_text):
    """Markdown → 微信公众号HTML（内联样式）"""
    lines = md_text.split('\n')
    html_parts = []
    in_blockquote = False

    for line in lines:
        stripped = line.strip()

        # 空行
        if not stripped:
            if in_blockquote:
                html_parts.append('</blockquote>')
                in_blockquote = False
            continue

        # # 标题（跳过，微信用单独标题字段）
        if stripped.startswith('# ') and not stripped.startswith('## '):
            continue

        # ## 小标题 → h2
        if stripped.startswith('## '):
            text = inline_format(stripped[3:])
            html_parts.append(f'<h2 style="{STYLES["h2"]}">{text}</h2>')
            continue

        # --- 分隔线
        if stripped == '---':
            html_parts.append(f'<hr style="{STYLES["hr"]}" />')
            continue

        # > 引用
        if stripped.startswith('>'):
            if not in_blockquote:
                html_parts.append(f'<blockquote style="{STYLES["blockquote"]}">')
                in_blockquote = True
            text = inline_format(stripped.lstrip('> ').strip())
            html_parts.append(f'<p style="{STYLES["p"]}">{text}</p>')
            continue

        # *斜体单独行 → 居中
        if stripped.startswith('*') and stripped.endswith('*') and not stripped.startswith('**'):
            text = stripped.strip('*')
            html_parts.append(f'<p style="{STYLES["center"]}"><em>{text}</em></p>')
            continue

        # 关闭未关闭的 blockquote
        if in_blockquote:
            html_parts.append('</blockquote>')
            in_blockquote = False

        # 普通段落
        text = inline_format(stripped)
        html_parts.append(f'<p style="{STYLES["p"]}">{text}</p>')

    if in_blockquote:
        html_parts.append('</blockquote>')

    return '\n'.join(html_parts)

# ============ Main ============

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument("--no-wechat", action="store_true")
    args = parser.parse_args()

    md_content = open(args.file, "r", encoding="utf-8").read()

    # 转HTML
    html_content = md_to_wechat_html(md_content)
    print(f"📝 HTML转换完成，共 {len(html_content)} 字符")

    # 保存HTML版本
    today = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r'[^\w\u4e00-\u9fff-]', '', args.title[:30]).replace(" ", "-")
    html_path = POSTS_DIR / f"{today}-{slug}.html"
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"💾 HTML保存: {html_path}")

    if not args.no_wechat:
        env = load_env()
        if env.get("WEIXIN_APP_ID") and env.get("WEIXIN_APP_SECRET"):
            token = get_token(env)
            COVERS_DIR.mkdir(parents=True, exist_ok=True)
            cover_path = COVERS_DIR / f"cover_{today}_{slug[:10]}.jpg"
            create_cover(args.title, str(cover_path))
            print(f"🎨 封面生成: {cover_path}")

            thumb_id = upload_image(token, str(cover_path))
            if thumb_id:
                print(f"📤 封面上传成功")
                media_id = create_draft(token, args.title, html_content, thumb_id)
                if media_id:
                    print(f"✅ 微信草稿创建成功! media_id: {media_id[:30]}...")
                else:
                    print("❌ 草稿创建失败")
            else:
                print("❌ 封面上传失败")
        else:
            print("⚠️ 微信配置缺失，跳过推送")

if __name__ == "__main__":
    main()
