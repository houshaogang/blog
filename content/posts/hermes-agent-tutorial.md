---
title: "🔧 Hermes Agent 安装教程：你的第一个AI助手"
date: 2026-05-22T23:00:00+08:00
tags: ["AI", "Hermes", "教程", "Agent"]
categories: ["AI工具"]
summary: "手把手教你安装 Hermes Agent —— 一个能在终端、微信、飞书、Telegram 等平台运行的开源AI助手框架。"
---

## 什么是 Hermes Agent？

Hermes Agent 是由 Nous Research 开发的开源 AI 代理框架。它能运行在你的终端、微信、飞书、Telegram、Discord 等 10+ 个平台上，拥有完整的工具调用能力。

简单来说：**它是一个能帮你干活的 AI 助手，不只是聊天。**

## 为什么选择 Hermes？

- 🌐 **多平台** — 同一个 Agent 跑在微信、飞书、Telegram 上
- 🧠 **有记忆** — 跨会话记住你的偏好和习惯
- 🔧 **能操作** — 执行命令、读写文件、浏览网页、生成代码
- 📚 **可学习** — 通过 Skills 系统积累经验
- 🤖 **可扩展** — 插件、MCP 服务器、Cron 定时任务

## 安装步骤

### 1. 一键安装

**Linux / macOS:**

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

**Windows:**

```powershell
# 使用 winget（推荐）
winget install Hermes.Agent

# 或手动下载
# 从 https://github.com/NousResearch/hermes-agent/releases 下载最新版
```

### 2. 启动交互

```bash
hermes
```

首次启动会进入设置向导，选择模型和 API Key。

### 3. 配置模型

Hermes 支持 20+ 个模型提供商：

```bash
# 交互式选择
hermes model

# 或直接设置
hermes config set model.default "anthropic/claude-sonnet-4"
hermes config set model.provider "anthropic"
```

### 4. 配置消息平台（可选）

```bash
hermes gateway setup
```

支持的平台：

| 平台 | 说明 |
|------|------|
| Telegram | Bot 模式 |
| Discord | Bot 模式 |
| 微信 | iLink 接入 |
| 飞书 | WebSocket 模式 |
| Slack | Bot 模式 |
| WhatsApp | Bridge 接入 |
| Email | IMAP/SMTP |

### 5. 启动 Gateway

```bash
# 前台运行
hermes gateway run

# 后台运行（Linux）
hermes gateway install
hermes gateway start

# 后台运行（Windows）
# Gateway 会自动处理微信/飞书连接
```

## 常用命令

```bash
# 单次查询
hermes chat -q "帮我写一个 Python 快排"

# 加载技能
hermes -s heartmula "生成一首歌"

# 查看状态
hermes doctor
hermes gateway status

# 管理定时任务
hermes cron list
hermes cron create "every 9am"
```

## 技能系统

Hermes 通过 Skills 积累经验：

```bash
# 搜索技能
hermes skills search "music"

# 安装技能
hermes skills install heartmula

# 查看已安装
hermes skills list
```

## 实际应用场景

**内容创作：**
- 自动生成抖音视频脚本
- AI 作曲（HeartMuLa / Suno）
- 博客文章自动发布

**开发辅助：**
- 代码审查和重构
- GitHub PR 管理
- 自动化测试

**日常效率：**
- 微信/飞书消息自动回复
- 定时任务（天气播报、内容监控）
- 笔记管理和知识库

## 常见问题

**Q: 支持哪些模型？**
A: OpenRouter、Anthropic、OpenAI、DeepSeek、小米 MiMo、通义千问等 20+ 家。

**Q: 微信怎么接入？**
A: 需要 iLink 账号，`hermes gateway setup` 选择 Weixin 平台配置。

**Q: 免费吗？**
A: Hermes 本身免费开源。模型调用费用取决于你选择的提供商。

**Q: 数据安全吗？**
A: 所有数据在你本地，模型调用通过 API，不经过第三方。

---

*本文由 AI 自动生成并发布。Hermes Agent 开源地址：https://github.com/NousResearch/hermes-agent*
