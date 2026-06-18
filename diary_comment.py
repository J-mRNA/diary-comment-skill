#!/usr/bin/env python3
"""
每日碎碎念AI评论脚本
- 每3小时检查一次
- AI读取日记内容,生成个性化评论
- 在「碎碎念」小标题下方添加评论
"""

import subprocess
import re
import urllib.parse
import json
import os
import sys
from datetime import datetime

# WebDAV 配置
AUTH = "YOUR_EMAIL:YOUR_WEBDAV_PASSWORD"
BASE_URL = "https://dav.jianguoyun.com/dav/Obsidian/%e4%b8%aa%e4%ba%ba%e4%bb%93%e5%ba%93"
DIARY_FOLDER = "%e6%af%8f%e6%97%a5%e7%a2%8e%e7%a2%8e%e5%bf%b5"

# LongCat API 配置
LONGCAT_API_KEY = "YOUR_LONGCAT_API_KEY"
LONGCAT_API_BASE = "https://api.longcat.chat/openai/v1"

# 调用AI生成评论
def generate_comment_with_ai(diary_content, date_str):
    """调用AI读取日记,生成个性化评论"""

    prompt = f"""你是温和的情绪陪伴AI，基于用户日记做情绪解读+温柔评论，全程中立包容，不做专业心理诊断。

子楠是一个考研学生,说话风格:直接犀利,喜欢吐槽,爱用"呵呵"表达无语/嘲讽,偶爆粗口,喜欢表情包和emoji。

他的日记内容:
---
{diary_content}
---

请生成两条评论，格式如下：

### 每日碎碎念：
---
第一条评论（侧重共情当下心情，贴合日记里的具体小事）

第二条评论（侧重温柔鼓励/温柔复盘，给松弛感）

要求：
1. 第一条精准捕捉日记核心情绪，自然融入评语，不单独罗列情绪标签；
2. 充分共情：所有负面情绪都是合理的，不否定、不强行开导；
3. 结合日记具体事件回应，不空洞安慰；
4. 第二条给予微小、松弛的正向暗示，不给用户压力；
5. 整体语气安静治愈，像深夜独处时的自我对话；
6. 不输出建议类指令（如"你明天要加油"），重在接纳与陪伴；
7. 两条内容不能重复，各有侧重。
8. **两条评论合并后总字数控制在 300~500 字之间**，精简表达，不啰嗦。

只输出最终评论，不要任何说明文字。"""

    payload = {
        "model": "LongCat-2.0-Preview",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 600
    }

    cmd = [
        'curl', '-s', '-X', 'POST',
        f'{LONGCAT_API_BASE}/chat/completions',
        '-H', f'Authorization: Bearer {LONGCAT_API_KEY}',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(payload)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        print(f"API调用失败: {result.stderr}")
        return None

    try:
        response = json.loads(result.stdout)
        if 'choices' in response and len(response['choices']) > 0:
            comment = response['choices'][0]['message']['content'].strip()
            return comment
        else:
            print(f"API返回异常: {result.stdout}")
            return None
    except json.JSONDecodeError:
        print(f"JSON解析失败: {result.stdout}")
        return None

def get_file(path):
    """获取文件内容"""
    encoded = urllib.parse.quote(path, safe='/')
    url = f"{BASE_URL}/{encoded}"
    cmd = f'curl -s --max-time 30 -u "{AUTH}" "{url}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    return result.stdout

def put_file(path, content):
    """上传文件"""
    encoded = urllib.parse.quote(path, safe='/')
    url = f"{BASE_URL}/{encoded}"
    temp_file = f"/tmp/diary_comment_{os.getpid()}.md"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)

    cmd = f'curl -s --max-time 60 -u "{AUTH}" -X PUT --data-binary @{temp_file} "{url}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=90)
    os.remove(temp_file)
    return not result.stdout.startswith('<?xml')

def get_diary_list():
    """获取日记文件列表"""
    url = f"{BASE_URL}/{DIARY_FOLDER}/"
    cmd = f'curl -s --max-time 30 -u "{AUTH}" -X PROPFIND "{url}" -H "Depth: 1"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)

    files = re.findall(r'(\d{4}-\d{2}-\d{2}\.md)', result.stdout)
    return sorted(set(files))

def process_diary(filename):
    """处理单篇日记（仅当天日记会传入此函数）"""
    # 从文件名中提取日期
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if not date_match:
        return False, False
    file_date = date_match.group(1)

    # 检查日期是否在允许范围内
    if file_date < '2026-06-12':
        print(f"跳过 {file_date} 的日记(太旧)")
        return False, False

    # 获取日记内容
    diary_path = f"{urllib.parse.unquote(DIARY_FOLDER)}/{filename}"
    content = get_file(diary_path)

    if content.startswith('<?xml'):
        print(f"获取日记失败: {filename}")
        return False, False

    # 提取正文内容（去掉所有评论）
    lines = content.split('\n')
    body_lines = []
    
    for i, line in enumerate(lines):
        # 遇到评论标题，停止收集正文
        if line.startswith('### 每日碎碎念') or line.startswith('## 每日碎碎念'):
            break
        # 跳过空行和分隔符
        if line.strip() in ('', '---'):
            continue
        # 收集正文
        body_lines.append(line)

    diary_body = '\n'.join(body_lines).strip()

    # 检查是否有实质内容
    if len(diary_body) < 10:
        print(f"日记内容太少,跳过评论")
        return False, False

    # 计算正文内容的哈希，判断是否有变化
    body_hash = hash(diary_body)
    last_hash_file = f"/tmp/diary_hash_{file_date}.txt"
    last_hash = None
    
    if os.path.exists(last_hash_file):
        with open(last_hash_file, 'r') as f:
            last_hash = f.read().strip()
    
    # 如果哈希没变，不重新生成评论
    if str(body_hash) == last_hash:
        print(f"日记内容无变化,跳过评论")
        return False, False

    # 调用AI生成评论
    print(f"📖 AI正在读取日记...")
    ai_output = generate_comment_with_ai(diary_body, file_date)

    if not ai_output:
        print(f"评论生成失败")
        return False, False

    # 解析两条评论
    # AI输出格式：
    # ### 每日碎碎念：
    # ---
    # 第一条评论
    # ---
    # 第二条评论
    
    # 直接按 --- 分割，取中间部分
    all_parts = ai_output.split('---\n')
    
    # 去掉标题部分，取评论部分
    comment_parts = []
    for part in all_parts:
        if '### 每日碎碎念' in part or '## 每日碎碎念' in part:
            continue
        if part.strip():
            comment_parts.append(part.strip())
    
    if len(comment_parts) >= 2:
        first_comment = comment_parts[0].replace('\n', ' ').strip()
        second_comment = comment_parts[1].replace('\n', ' ').strip()
    elif len(comment_parts) == 1:
        first_comment = comment_parts[0].replace('\n', ' ').strip()
        second_comment = ''
    else:
        first_comment = ai_output.replace('\n', ' ').strip()
        second_comment = ''
    
    # 清理评论内容（去掉可能的引用符号）
    first_comment = first_comment.replace('> ', '')
    second_comment = second_comment.replace('> ', '')
    
    print(f"💬 第一条: {first_comment[:80]}...")
    print(f"💬 第二条: {second_comment[:80]}...")

    # 字数检查，超了则调用 skill 脚本让AI重写（最多重试2次）
    condense_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   'scripts/condense_comment.py')
    for attempt in range(3):
        total_len = len(first_comment) + len(second_comment)
        if total_len <= 500:
            break
        print(f"⚠️  评论总字数({total_len})超过500字，正在精简...")
        result = subprocess.run(
            ['python3', condense_script, first_comment, second_comment],
            capture_output=True, text=True, timeout=90
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split('\x00')
            if len(parts) >= 2:
                first_comment = parts[0]
                second_comment = parts[1]
                print(f"💬 精简后第一条: {first_comment[:80]}...")
                print(f"💬 精简后第二条: {second_comment[:80]}...")
            else:
                break
        else:
            print(f"精简脚本失败: {result.stderr}")
            break
    else:
        print(f"⚠️  字数精简已达上限，但仍上传当前结果")

    # 构建新的文件内容：正文 + 空两行 + 标题 + 分隔线 + 两条评论
    new_lines = list(body_lines)
    new_lines.append('')  # 空一行
    new_lines.append('')  # 再空一行
    new_lines.append('### 每日碎碎念：')
    new_lines.append('---')
    new_lines.append('')
    
    if first_comment:
        # 第一条按段落分割保存
        for para in first_comment.split('\n'):
            if para.strip():
                new_lines.append(para.strip())
    
    if second_comment:
        new_lines.append('')
        # 第二条按段落分割保存
        for para in second_comment.split('\n'):
            if para.strip():
                new_lines.append(para.strip())

    new_content = '\n'.join(new_lines)
    success = put_file(diary_path, new_content)

    if success:
        # 保存哈希
        with open(last_hash_file, 'w') as f:
            f.write(str(body_hash))
        print(f"✅ 评论已更新")
    else:
        print(f"❌ 上传失败")

    return success, True

def main():
    now = datetime.now()
    print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] === 日记AI评论检查 ===")

    # 获取日记列表
    diaries = get_diary_list()

    if not diaries:
        print("未找到日记文件")
        return

    print(f"找到 {len(diaries)} 个日记文件")

    # 只处理今天的日记：系统日期必须和文件名日期一致
    today = datetime.now().strftime('%Y-%m-%d')
    today_file = f"{today}.md"
    
    # 从文件名中提取日期
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', today_file)
    if date_match:
        file_date = date_match.group(1)
        if file_date != today:
            print(f"系统日期 {today} != 日记日期 {file_date}，跳过评论")
            return
    else:
        print(f"无法解析日期，跳过")
        return

    if today_file in diaries:
        print(f"检查今天的日记: {today_file}")
        success, should_notify = process_diary(today_file)
        if should_notify:
            print("NOTIFY:评论已完成,去日记里看看吧~")
        else:
            print("无新评论,不通知")
    else:
        print(f"今天还没写日记({today_file})")

if __name__ == "__main__":
    main()
