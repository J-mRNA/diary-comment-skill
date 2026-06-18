# diary-comment-skill

AI 日记评论生成技能，为每日碎碎念自动生成情绪共情 + 温柔鼓励的个性化评论。

## 功能特性

- 🤖 调用 LongCat API 生成评论内容
- 💬 两条评论：**共情**（精准捕捉情绪）+ **鼓励**（松弛正向暗示）
- ✂️ 字数控制在 300~500 字之间，超限自动精简
- 📝 自动追加到日记文件，不打扰正常记录
- ⏰ 支持定时任务（每3小时自动检查）

## 文件说明

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 技能说明文档 |
| `diary_comment.py` | 主脚本（生成 + 上传评论） |
| `scripts/condense_comment.py` | 字数精简逻辑（字数超限时调用） |

## 快速开始

### 1. 配置

编辑 `diary_comment.py`，填入以下配置：

```python
# WebDAV 配置（坚果云）
AUTH = "YOUR_EMAIL:YOUR_WEBDAV_PASSWORD"
BASE_URL = "https://dav.jianguoyun.com/dav/Obsidian/个人仓库"
DIARY_FOLDER = "每日碎碎念"

# LongCat API 配置
LONGCAT_API_KEY = "YOUR_LONGCAT_API_KEY"
```

### 2. 运行

```bash
python3 diary_comment.py
```

### 3. 定时任务（systemd）

创建服务文件 `/etc/systemd/system/diary_comment.service`：

```ini
[Unit]
Description=每日碎碎念评论

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /path/to/diary_comment.py
```

创建定时器 `/etc/systemd/system/diary_comment.timer`：

```ini
[Unit]
Description=每3小时执行日记评论

[Timer]
OnBootSec=5min
OnCalendar=*:0/3

[Install]
WantedBy=timers.target
```

启用：
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now diary_comment.timer
```

## 评论示例

输入日记（虚构）：
> 今天天气不错，心情舒畅。学会了做一道新菜，很有成就感。

生成评论：

> 学会一道新菜那种"原来我也可以"的成就感，真的很让人开心。不是大成就，但足够真实，值得好好品味一下。

> 做菜这种事，慢慢来就好，做砸了也不亏，明天再试。今天的小确幸先收好，明天又是新的一天。

## 注意事项

- 日记日期需在 `2026-06-12` 及之后才会生成评论
- 空日记（正文不足10字）不会生成评论
- 每次运行只处理**当天**的日记
