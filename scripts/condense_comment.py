#!/usr/bin/env python3
"""
AI日记评论字数精简脚本
当两条评论合并后超过500字时，调用AI重新精简，保持语义完整不断句。
"""

import subprocess
import json
import sys

# LongCat API 配置
LONGCAT_API_KEY = "YOUR_LONGCAT_API_KEY"
LONGCAT_API_BASE = "https://api.longcat.chat/openai/v1"

def condense_comments(first_comment, second_comment, max_chars=500, max_retries=3):
    """
    精简两条评论，总字数不超过 max_chars。
    通过调用AI重新生成/精简，不硬截断。
    返回 (first_comment, second_comment)
    """
    for attempt in range(max_retries):
        total_len = len(first_comment) + len(second_comment)
        if total_len <= max_chars:
            break

        print(f"⚠️  评论总字数({total_len})超过{max_chars}字，正在精简... (第{attempt+1}次)", file=sys.stderr)

        payload = {
            "model": "LongCat-2.0-Preview",
            "messages": [
                {"role": "user", "content":
                    f"请把以下两条评论精简合并，**总字数不超过{max_chars}字**，保持原有情感和语气，每条语义完整不断句：\n\n"
                    f"第一条：{first_comment}\n"
                    f"第二条：{second_comment}\n\n"
                    f"直接输出精简后的两条评论，用 --- 分隔，不要其他说明。"
                }
            ],
            "temperature": 0.6,
            "max_tokens": 500
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
            print(f"精简API调用失败: {result.stderr}", file=sys.stderr)
            break

        try:
            resp = json.loads(result.stdout)
            if 'choices' not in resp or len(resp['choices']) == 0:
                break
            revised = resp['choices'][0]['message']['content'].strip()
            parts = revised.split('---\n')
            if len(parts) >= 2:
                first_comment = parts[0].replace('\n', ' ').strip()
                second_comment = parts[1].replace('\n', ' ').strip()
            elif len(parts) == 1:
                first_comment = parts[0].replace('\n', ' ').strip()
                second_comment = ''
            print(f"精简后第一条: {first_comment[:80]}...", file=sys.stderr)
            print(f"精简后第二条: {second_comment[:80]}...", file=sys.stderr)
        except (json.JSONDecodeError, IndexError) as e:
            print(f"精简解析失败: {e}", file=sys.stderr)
            break
    else:
        print(f"⚠️  字数精简已达上限次数，但仍返回当前结果", file=sys.stderr)

    return first_comment, second_comment

if __name__ == "__main__":
    # 命令行调用: condense_comment.py "第一条评论" "第二条评论"
    if len(sys.argv) < 3:
        print("用法: condense_comment.py <第一条评论> <第二条评论>", file=sys.stderr)
        sys.exit(1)

    first = sys.argv[1]
    second = sys.argv[2]

    f, s = condense_comments(first, second)
    # 输出两个结果，用 \x00 分隔（避免内容中有特殊字符干扰）
    print(f + '\x00' + s)
