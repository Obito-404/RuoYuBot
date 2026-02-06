#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试任务命令解析器
"""

import sys
from datetime import datetime

# 添加父目录到路径以便导入 main.py 中的类
sys.path.insert(0, '.')

from main import TaskCommandParser

def test_parser():
    """测试各种任务命令格式"""

    test_cases = [
        # 单次任务
        ("单次任务 明天 15:30 提醒开会", "单次任务 - 明天"),
        ("单次任务 2026-02-10 14:00 记得吃药", "单次任务 - 指定日期"),
        ("单次任务 后天 09:00 准备材料", "单次任务 - 后天"),
        ("once 2026-03-15 10:00 Birthday reminder", "单次任务 - 英文"),

        # 每日任务
        ("每日任务 09:00 早安问候", "每日任务"),
        ("每天 18:00 下班提醒", "每日任务 - 别名"),
        ("daily 12:00 Lunch time", "每日任务 - 英文"),

        # 每周任务
        ("每周任务 周一 09:00 周会提醒", "每周任务 - 周一"),
        ("每周 星期三 14:00 部门会议", "每周任务 - 星期三"),
        ("每周任务 周五 17:00 周报提醒", "每周任务 - 周五"),
        ("weekly 周六 10:00 Weekend meeting", "每周任务 - 英文"),

        # 工作日任务
        ("工作日 09:00 打卡提醒", "工作日任务"),
        ("weekday 08:50 Clock in", "工作日任务 - 英文"),

        # 错误格式
        ("单次任务 2025-01-01 10:00 过去的时间", "错误 - 过去时间"),
        ("每日任务 25:00 错误时间", "错误 - 无效时间"),
        ("每周任务 周八 09:00 错误星期", "错误 - 无效星期"),
        ("随便说点什么", "错误 - 无效格式"),
    ]

    print("=" * 80)
    print("任务命令解析器测试")
    print("=" * 80)
    print()

    success_count = 0
    error_count = 0

    for message, description in test_cases:
        print(f"测试: {description}")
        print(f"输入: {message}")

        result = TaskCommandParser.parse_task_command(message, "测试用户")

        if result['success']:
            success_count += 1
            print("✅ 解析成功")
            task_data = result['task_data']
            print(f"   任务类型: {task_data['schedule_type']}")
            print(f"   任务名称: {task_data['name']}")
            print(f"   时间: {task_data.get('time', 'N/A')}")
            if 'date' in task_data:
                print(f"   日期: {task_data['date']}")
            if 'weekday' in task_data and task_data['schedule_type'] == 'weekday':
                weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
                print(f"   星期: {weekday_names[task_data['weekday']]}")
            print(f"   消息内容: {task_data['message']}")
            print(f"   接收者: {task_data['recipient']}")
        else:
            error_count += 1
            print("❌ 解析失败")
            print(f"   错误信息: {result['error']}")

        print("-" * 80)
        print()

    print("=" * 80)
    print(f"测试完成: 成功 {success_count} 个, 失败 {error_count} 个")
    print("=" * 80)

if __name__ == "__main__":
    test_parser()
