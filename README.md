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

输入日记：
> 最近课太多了，学习计划被打乱。买了资料到了，想好好学。

生成评论：
> 满课把计划全搅碎了，回到图书馆刚进入状态就得走——这种被打断的疲惫感，不是懒，是真的被消耗够了。你不是效率低，是根本没有完整的时间去沉进去学。想锁手机说明你已经意识到问题在哪了，这份清醒很珍贵。

> 资料到了就好，哪怕只是多两本纸质书，心里也会觉得离目标又近了一点点。不用急，见缝插针也是一种策略。

## 注意事项

- 日记日期需在 `2026-06-12` 及之后才会生成评论
- 空日记（正文不足10字）不会生成评论
- 每次运行只处理**当天**的日记
