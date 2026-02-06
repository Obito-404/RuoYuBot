from wxauto import WeChat
import time
import traceback
import requests
import json
from flask import Flask, request, jsonify
import threading
import win32gui
import win32con
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import queue
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import configparser
import os
from pathlib import Path
import sys
from werkzeug.serving import make_server
import chardet
import schedule
import uuid

try:
    from icon import icon_img  # Import the base64 encoded icon
except ImportError:
    icon_img = None


# 配置管理
class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = Path("config.ini")
        self.load_config()

    def detect_encoding(self, file_path):
        """检测文件编码"""
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            return result['encoding']

    def convert_to_utf8(self, file_path):
        """将文件转换为UTF-8编码"""
        try:
            # 检测当前编码
            current_encoding = self.detect_encoding(file_path)
            if current_encoding and current_encoding.lower() != 'utf-8':
                # 读取文件内容
                with open(file_path, 'r', encoding=current_encoding) as f:
                    content = f.read()
                # 以UTF-8编码重写文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logging.info(f"已将配置文件从 {current_encoding} 转换为 UTF-8 编码")
        except Exception as e:
            logging.error(f"转换配置文件编码时出错: {str(e)}")
            # 如果转换失败，创建新的配置文件
            self.create_default_config()

    def load_config(self):
        if not self.config_path.exists():
            self.create_default_config()
        else:
            try:
                # 尝试转换文件编码
                self.convert_to_utf8(self.config_path)
                # 读取配置文件
                self.config.read(self.config_path, encoding='utf-8')
            except Exception as e:
                logging.error(f"读取配置文件失败: {str(e)}")
                # 如果读取失败，创建新的配置文件
                self.create_default_config()

        # 确保api_token字段存在
        if 'api_token' not in self.config['DEFAULT']:
            self.config['DEFAULT']['api_token'] = ''
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)

        # 处理旧版本的webhook_url配置
        if 'webhook_url' in self.config['DEFAULT'] and 'webhook_urls' not in self.config['DEFAULT']:
            old_url = self.config['DEFAULT']['webhook_url']
            self.config['DEFAULT']['webhook_urls'] = old_url
            del self.config['DEFAULT']['webhook_url']
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            logging.info("已将旧版webhook_url配置迁移到新版webhook_urls")

    def create_default_config(self):
        self.config['DEFAULT'] = {
            'listen_list': '好友名称或备注,群名称',  # 默认监听的群或用户列表
            'webhook_urls': 'http://ip:port',  # 外部webhook地址列表
            'port': '5000',  # 本地webhook服务器端口
            'retry_count': '3',  # 消息发送重试次数
            'retry_delay': '5',  # 重试延迟时间（秒）
            'log_level': 'INFO',  # 日志级别
            'api_token': '',  # API Token
            'task_admin_list': ''  # 允许通过消息添加任务的用户列表（逗号分隔）
        }
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except Exception as e:
            logging.error(f"创建默认配置文件失败: {str(e)}")
            # 如果写入失败，尝试使用系统默认编码
            with open(self.config_path, 'w') as f:
                self.config.write(f)

    def get_listen_list(self) -> List[str]:
        return [x.strip() for x in self.config['DEFAULT']['listen_list'].split(',')]

    def get_webhook_urls(self) -> List[str]:
        return [x.strip() for x in self.config['DEFAULT']['webhook_urls'].split('\n') if x.strip()]

    def set_webhook_urls(self, urls: List[str]):
        self.config['DEFAULT']['webhook_urls'] = '\n'.join(urls)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def get_port(self) -> int:
        return int(self.config['DEFAULT']['port'])

    def get_retry_count(self) -> int:
        return int(self.config['DEFAULT']['retry_count'])

    def get_retry_delay(self) -> int:
        return int(self.config['DEFAULT']['retry_delay'])

    def get_log_level(self) -> str:
        return self.config['DEFAULT']['log_level']

    def get_api_token(self) -> str:
        return self.config['DEFAULT'].get('api_token', '')

    def set_api_token(self, token: str):
        self.config['DEFAULT']['api_token'] = token
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def get_task_admin_list(self) -> List[str]:
        """获取任务管理员列表"""
        admin_list = self.config['DEFAULT'].get('task_admin_list', '')
        if not admin_list:
            return []
        return [x.strip() for x in admin_list.split(',') if x.strip()]

    def set_task_admin_list(self, admins: List[str]):
        """设置任务管理员列表"""
        self.config['DEFAULT']['task_admin_list'] = ','.join(admins)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def get_scheduled_tasks_path(self) -> Path:
        """获取定时任务配置文件路径"""
        return Path("scheduled_tasks.json")

    def load_scheduled_tasks(self) -> dict:
        """从JSON文件加载定时任务"""
        tasks_path = self.get_scheduled_tasks_path()
        if not tasks_path.exists():
            return {"tasks": []}
        try:
            with open(tasks_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"加载定时任务失败: {str(e)}")
            return {"tasks": []}

    def save_scheduled_tasks(self, tasks_data: dict):
        """保存定时任务到JSON文件"""
        tasks_path = self.get_scheduled_tasks_path()
        try:
            with open(tasks_path, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存定时任务失败: {str(e)}")


# 任务命令解析器
class TaskCommandParser:
    """解析微信消息中的任务命令"""

    # 星期映射
    WEEKDAY_MAP = {
        '周一': 0, '星期一': 0, '礼拜一': 0,
        '周二': 1, '星期二': 1, '礼拜二': 1,
        '周三': 2, '星期三': 2, '礼拜三': 2,
        '周四': 3, '星期四': 3, '礼拜四': 3,
        '周五': 4, '星期五': 4, '礼拜五': 4,
        '周六': 5, '星期六': 5, '礼拜六': 5,
        '周日': 6, '星期日': 6, '礼拜日': 6, '周天': 6, '星期天': 6
    }

    @staticmethod
    def parse_natural_date(date_str: str) -> str:
        """解析自然语言日期（今天、明天、后天）"""
        today = datetime.now()
        if date_str in ['今天', '今日']:
            return today.strftime('%Y-%m-%d')
        elif date_str in ['明天', '明日']:
            return (today + timedelta(days=1)).strftime('%Y-%m-%d')
        elif date_str in ['后天']:
            return (today + timedelta(days=2)).strftime('%Y-%m-%d')
        else:
            # 尝试解析标准日期格式
            try:
                # 支持多种日期格式
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%m-%d', '%m/%d']:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        # 如果只有月日，补充年份
                        if fmt in ['%m-%d', '%m/%d']:
                            parsed_date = parsed_date.replace(year=today.year)
                            # 如果日期已过，使用明年
                            if parsed_date < today:
                                parsed_date = parsed_date.replace(year=today.year + 1)
                        return parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            except:
                pass
        return None

    @staticmethod
    def parse_time(time_str: str) -> str:
        """解析时间格式"""
        import re
        # 匹配 HH:MM 或 HH时MM分 格式
        patterns = [
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})时(\d{2})分',
            r'(\d{1,2})点(\d{2})分',
        ]

        for pattern in patterns:
            match = re.match(pattern, time_str)
            if match:
                hour, minute = match.groups()
                hour = int(hour)
                minute = int(minute)
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return f"{hour:02d}:{minute:02d}"
        return None

    @staticmethod
    def parse_weekday(weekday_str: str) -> int:
        """解析星期"""
        return TaskCommandParser.WEEKDAY_MAP.get(weekday_str, None)

    @staticmethod
    def parse_task_command(message: str, sender: str) -> dict:
        """
        解析任务命令
        返回格式: {
            'success': bool,
            'task_data': dict,  # 如果成功
            'error': str  # 如果失败
        }
        """
        import re

        message = message.strip()

        # 单次任务格式: 单次任务 日期 时间 消息内容
        # 例: 单次任务 2026-02-10 15:30 提醒开会
        # 例: 单次任务 明天 15:30 提醒开会
        once_patterns = [
            r'^(单次任务|一次性任务|once)\s+(\S+)\s+(\S+)\s+(.+)$',
        ]

        for pattern in once_patterns:
            match = re.match(pattern, message, re.IGNORECASE)
            if match:
                _, date_str, time_str, msg_content = match.groups()

                # 解析日期
                date = TaskCommandParser.parse_natural_date(date_str)
                if not date:
                    return {'success': False, 'error': f'无法识别日期格式: {date_str}'}

                # 检查日期是否在过去
                task_datetime = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M")
                if task_datetime < datetime.now():
                    return {'success': False, 'error': '任务时间不能是过去的时间'}

                # 解析时间
                time = TaskCommandParser.parse_time(time_str)
                if not time:
                    return {'success': False, 'error': f'无法识别时间格式: {time_str}'}

                return {
                    'success': True,
                    'task_data': {
                        'name': f'[消息添加] {msg_content[:20]}',
                        'schedule_type': 'once',
                        'date': date,
                        'time': time,
                        'recipient': sender,
                        'message': msg_content,
                        'is_group': False,
                        'at_list': None
                    }
                }

        # 每日任务格式: 每日任务 时间 消息内容
        # 例: 每日任务 09:00 早安问候
        daily_patterns = [
            r'^(每日任务|每天|daily)\s+(\S+)\s+(.+)$',
        ]

        for pattern in daily_patterns:
            match = re.match(pattern, message, re.IGNORECASE)
            if match:
                _, time_str, msg_content = match.groups()

                # 解析时间
                time = TaskCommandParser.parse_time(time_str)
                if not time:
                    return {'success': False, 'error': f'无法识别时间格式: {time_str}'}

                return {
                    'success': True,
                    'task_data': {
                        'name': f'[消息添加] {msg_content[:20]}',
                        'schedule_type': 'daily',
                        'time': time,
                        'recipient': sender,
                        'message': msg_content,
                        'is_group': False,
                        'at_list': None
                    }
                }

        # 每周任务格式: 每周任务 星期 时间 消息内容
        # 例: 每周任务 周一 09:00 周会提醒
        weekly_patterns = [
            r'^(每周任务|每周|weekly)\s+(\S+)\s+(\S+)\s+(.+)$',
        ]

        for pattern in weekly_patterns:
            match = re.match(pattern, message, re.IGNORECASE)
            if match:
                _, weekday_str, time_str, msg_content = match.groups()

                # 解析星期
                weekday = TaskCommandParser.parse_weekday(weekday_str)
                if weekday is None:
                    return {'success': False, 'error': f'无法识别星期格式: {weekday_str}'}

                # 解析时间
                time = TaskCommandParser.parse_time(time_str)
                if not time:
                    return {'success': False, 'error': f'无法识别时间格式: {time_str}'}

                return {
                    'success': True,
                    'task_data': {
                        'name': f'[消息添加] {msg_content[:20]}',
                        'schedule_type': 'weekday',
                        'weekday': weekday,
                        'time': time,
                        'recipient': sender,
                        'message': msg_content,
                        'is_group': False,
                        'at_list': None
                    }
                }

        # 工作日任务格式: 工作日 时间 消息内容
        # 例: 工作日 09:00 打卡提醒
        # 注意：这里使用 weekday 类型，但需要为每个工作日（周一到周五）创建5个任务
        # 为了简化，我们返回一个特殊标记，让调用者处理
        workday_patterns = [
            r'^(工作日|weekday)\s+(\S+)\s+(.+)$',
        ]

        for pattern in workday_patterns:
            match = re.match(pattern, message, re.IGNORECASE)
            if match:
                _, time_str, msg_content = match.groups()

                # 解析时间
                time = TaskCommandParser.parse_time(time_str)
                if not time:
                    return {'success': False, 'error': f'无法识别时间格式: {time_str}'}

                # 返回特殊标记，表示需要创建多个工作日任务
                return {
                    'success': True,
                    'task_data': {
                        'name': f'[消息添加] {msg_content[:20]}',
                        'schedule_type': 'workday',  # 特殊标记
                        'time': time,
                        'recipient': sender,
                        'message': msg_content,
                        'is_group': False,
                        'at_list': None
                    }
                }

        # 没有匹配任何格式
        return {'success': False, 'error': '无法识别任务格式'}


# 定时任务管理器
class ScheduledTaskManager:
    def __init__(self, config: Config, message_queue: queue.Queue):
        self.config = config
        self.message_queue = message_queue
        self.tasks = []
        self.is_running = False
        self.load_tasks()

    def load_tasks(self):
        """从配置文件加载任务"""
        try:
            tasks_data = self.config.load_scheduled_tasks()
            self.tasks = tasks_data.get("tasks", [])
            logging.info(f"已加载 {len(self.tasks)} 个定时任务")
        except Exception as e:
            logging.error(f"加载定时任务失败: {str(e)}")
            self.tasks = []

    def save_tasks(self):
        """保存任务到配置文件"""
        try:
            tasks_data = {"tasks": self.tasks}
            self.config.save_scheduled_tasks(tasks_data)
            logging.info("定时任务已保存")
        except Exception as e:
            logging.error(f"保存定时任务失败: {str(e)}")

    def add_task(self, task_data: dict) -> str:
        """添加新任务"""
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "name": task_data.get("name", ""),
            "enabled": True,
            "schedule_type": task_data.get("schedule_type", "daily"),
            "time": task_data.get("time", "09:00"),
            "weekday": task_data.get("weekday", 0),
            "recipient": task_data.get("recipient", ""),
            "message": task_data.get("message", ""),
            "is_group": task_data.get("is_group", False),
            "at_list": task_data.get("at_list", None),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_run": None,
            "next_run": None
        }

        # 如果是单次任务，添加日期字段
        if task["schedule_type"] == "once":
            task["date"] = task_data.get("date", datetime.now().strftime("%Y-%m-%d"))

        task["next_run"] = self.calculate_next_run(task)
        self.tasks.append(task)
        self.save_tasks()
        logging.info(f"已添加定时任务: {task['name']}")
        return task_id

    def update_task(self, task_id: str, task_data: dict):
        """更新任务"""
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                task["name"] = task_data.get("name", task["name"])
                task["schedule_type"] = task_data.get("schedule_type", task["schedule_type"])
                task["time"] = task_data.get("time", task["time"])
                task["weekday"] = task_data.get("weekday", task["weekday"])
                task["recipient"] = task_data.get("recipient", task["recipient"])
                task["message"] = task_data.get("message", task["message"])
                task["is_group"] = task_data.get("is_group", task["is_group"])
                task["at_list"] = task_data.get("at_list", task["at_list"])

                # 如果是单次任务，更新日期字段
                if task["schedule_type"] == "once":
                    task["date"] = task_data.get("date", task.get("date", datetime.now().strftime("%Y-%m-%d")))

                task["next_run"] = self.calculate_next_run(task)
                self.save_tasks()
                logging.info(f"已更新定时任务: {task['name']}")
                return True
        return False

    def delete_task(self, task_id: str):
        """删除任务"""
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                task_name = task["name"]
                self.tasks.pop(i)
                self.save_tasks()
                logging.info(f"已删除定时任务: {task_name}")
                return True
        return False

    def toggle_task_enabled(self, task_id: str):
        """切换任务启用状态"""
        for task in self.tasks:
            if task["id"] == task_id:
                task["enabled"] = not task["enabled"]
                if task["enabled"]:
                    task["next_run"] = self.calculate_next_run(task)
                self.save_tasks()
                status = "启用" if task["enabled"] else "禁用"
                logging.info(f"已{status}定时任务: {task['name']}")
                return True
        return False

    def get_all_tasks(self) -> List[dict]:
        """获取所有任务"""
        return self.tasks

    def calculate_next_run(self, task: dict) -> str:
        """计算下次运行时间"""
        try:
            schedule_type = task["schedule_type"]
            time_str = task["time"]
            hour, minute = map(int, time_str.split(":"))

            now = datetime.now()
            today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            if schedule_type == "daily":
                # 每天执行
                if today <= now:
                    next_run = today + timedelta(days=1)
                else:
                    next_run = today
            elif schedule_type == "weekly":
                # 每周执行（从今天开始算7天后）
                if today <= now:
                    next_run = today + timedelta(weeks=1)
                else:
                    next_run = today
            elif schedule_type == "weekday":
                # 特定星期几执行
                target_weekday = task["weekday"]
                current_weekday = now.weekday()
                days_ahead = target_weekday - current_weekday

                if days_ahead < 0 or (days_ahead == 0 and today <= now):
                    days_ahead += 7

                next_run = today + timedelta(days=days_ahead)
            elif schedule_type == "once":
                # 单次执行
                date_str = task.get("date", "")
                if not date_str:
                    logging.error("单次任务缺少日期信息")
                    return None

                year, month, day = map(int, date_str.split("-"))
                next_run = datetime(year, month, day, hour, minute, 0)

                # 如果时间已过，返回 None（任务已完成）
                if next_run <= now:
                    return None
            else:
                next_run = today

            return next_run.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logging.error(f"计算下次运行时间失败: {str(e)}")
            return None

    def execute_task(self, task: dict):
        """执行任务"""
        try:
            logging.info(f"执行定时任务: {task['name']}")

            # 获取接收者列表（支持多个接收者，用逗号分隔）
            recipients_str = task['recipient']
            recipients = [r.strip() for r in recipients_str.split(',') if r.strip()]

            if not recipients:
                logging.error(f"定时任务 {task['name']} 没有有效的接收者")
                return

            # 为每个接收者添加消息到队列
            for recipient in recipients:
                self.message_queue.put({
                    'who': recipient,
                    'content': task['message'],
                    'is_group': task['is_group'],
                    'at_list': task['at_list'],
                    'chat_name': recipient
                })
                logging.info(f"已为接收者 {recipient} 添加消息到队列")

            # 更新最后运行时间
            task['last_run'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 如果是单次任务，执行后自动禁用
            if task['schedule_type'] == 'once':
                task['enabled'] = False
                task['next_run'] = None
                logging.info(f"单次任务 {task['name']} 已执行完成，自动禁用")
            else:
                task['next_run'] = self.calculate_next_run(task)

            self.save_tasks()

            logging.info(f"定时任务已加入发送队列: {task['name']} (共 {len(recipients)} 个接收者)")
        except Exception as e:
            logging.error(f"执行定时任务失败: {str(e)}")
            logging.error(traceback.format_exc())

    def schedule_task(self, task: dict):
        """使用schedule库注册任务"""
        try:
            schedule_type = task["schedule_type"]
            time_str = task["time"]

            if schedule_type == "daily":
                schedule.every().day.at(time_str).do(self.execute_task, task=task)
            elif schedule_type == "weekly":
                schedule.every().week.at(time_str).do(self.execute_task, task=task)
            elif schedule_type == "weekday":
                weekday = task["weekday"]
                weekday_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                if 0 <= weekday < 7:
                    getattr(schedule.every(), weekday_names[weekday]).at(time_str).do(self.execute_task, task=task)
            elif schedule_type == "once":
                # 单次任务：创建一个包装函数，执行后自动取消
                date_str = task.get("date", "")
                if date_str:
                    year, month, day = map(int, date_str.split("-"))
                    hour, minute = map(int, time_str.split(":"))
                    target_datetime = datetime(year, month, day, hour, minute, 0)

                    # 计算距离目标时间的秒数
                    now = datetime.now()
                    if target_datetime > now:
                        seconds_until = (target_datetime - now).total_seconds()

                        # 创建包装函数，执行后返回 schedule.CancelJob 来取消任务
                        def execute_once():
                            self.execute_task(task)
                            return schedule.CancelJob  # 执行后自动取消

                        # 使用 schedule.every(N).seconds 并在执行后取消
                        job = schedule.every(int(seconds_until)).seconds.do(execute_once)
                        # 给任务添加标签，方便识别
                        job.tag(f"once_{task['id']}")
                        logging.info(f"已调度单次任务: {task['name']} - 将在 {target_datetime} 执行")
                    else:
                        logging.warning(f"单次任务 {task['name']} 的时间已过，跳过调度")
                        return

            logging.info(f"已调度任务: {task['name']} - {schedule_type} at {time_str}")
        except Exception as e:
            logging.error(f"调度任务失败: {str(e)}")
            logging.error(traceback.format_exc())

    def reschedule_all_tasks(self):
        """重新调度所有任务"""
        schedule.clear()
        for task in self.tasks:
            if task["enabled"]:
                self.schedule_task(task)
        logging.info(f"已重新调度 {len([t for t in self.tasks if t['enabled']])} 个启用的任务")

    def run_scheduler(self):
        """调度器主循环（在独立线程中运行）"""
        self.is_running = True
        self.reschedule_all_tasks()
        logging.info("定时任务调度器已启动")

        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logging.error(f"调度器运行出错: {str(e)}")
                logging.error(traceback.format_exc())
                time.sleep(5)

        logging.info("定时任务调度器已停止")


# 初始化配置
config = Config()

# 添加全局变量用于控制服务器
server = None
server_thread = None

# 初始化Flask应用
flask_app = Flask(__name__)

# 初始化微信
wx = WeChat()

# 创建日志队列
log_queue = queue.Queue()


class CustomHandler(logging.Handler):
    def emit(self, record):
        log_queue.put(self.format(record))


# 配置日志
logger = logging.getLogger()
logger.setLevel(getattr(logging, config.get_log_level()))
handler = CustomHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def shutdown_server():
    """关闭Flask服务器"""
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('未运行Werkzeug服务器')
    func()


@flask_app.route('/shutdown', methods=['POST'])
def shutdown():
    """关闭服务器的路由"""
    shutdown_server()
    return '服务器正在关闭...'


def auto_open_wechat():
    """自动打开微信"""
    try:
        # 检查微信是否已经运行
        hwnd = win32gui.FindWindow("WeChatMainWndForPC", None)
        if not hwnd:
            # 微信未运行，尝试启动
            os.startfile("C:\\Program Files (x86)\\Tencent\\WeChat\\WeChat.exe")
            logging.info("正在启动微信...")
            # 等待微信启动
            time.sleep(5)

            # 再次检查微信是否成功启动
            hwnd = win32gui.FindWindow("WeChatMainWndForPC", None)
            if not hwnd:
                logging.error("微信启动失败，请检查：")
                logging.error("1. 是否已安装微信 3.9.x 版本")
                logging.error("2. 微信是否已登录")
                return False
        else:
            logging.info("微信已经在运行")

        # 激活微信窗口
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            logging.info("已激活微信窗口")
            return True
        except:
            logging.warning("无法激活微信窗口，请手动激活")
            return False

    except Exception as e:
        logging.error(f"自动打开微信失败: {str(e)}")
        logging.error(traceback.format_exc())
        return False


class WeChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("若愚")
        self.root.geometry("900x750")

        # 设置主题颜色
        self.bg_color = "#f5f5f5"
        self.primary_color = "#2c3e50"
        self.accent_color = "#3498db"
        self.text_color = "#2c3e50"
        self.success_color = "#27ae60"
        self.error_color = "#e74c3c"

        # 设置字体
        self.title_font = ("Segoe UI", 12, "bold")
        self.label_font = ("Segoe UI", 10)
        self.button_font = ("Segoe UI", 10, "bold")
        self.log_font = ("Consolas", 9)

        # 配置根窗口
        self.root.configure(bg=self.bg_color)

        # 控制变量
        self.is_running = False
        self.webhook_thread = None
        self.listener_thread = None
        self.external_webhook_urls = config.get_webhook_urls()
        self.local_port = tk.StringVar(value=str(config.get_port()))
        self.current_webhook_url = tk.StringVar()

        # 获取本地IP地址
        self.local_ip = self.get_local_ip()

        # 其他变量保持不变...
        self.sessions = []
        self.last_session_update = 0
        self.session_update_interval = 60

        # 消息处理相关
        self.message_queue = queue.Queue()
        self.message_processing = False
        self.message_wait_time = 1.5
        self.last_send_time = 0
        self.min_send_interval = 2

        # 消息去重相关
        self.processed_messages = {}
        self.message_cache_time = 300  # 5分钟
        self.last_cache_cleanup = 0
        self.cache_cleanup_interval = 60  # 1分钟
        self.message_id_counter = 0  # 用于生成消息ID

        # 昵称相关
        self.nickname_var = tk.StringVar(value="")

        # 初始化定时任务管理器
        self.task_manager = ScheduledTaskManager(config, self.message_queue)
        self.scheduler_thread = None

        # 创建GUI元素
        self.create_widgets()

        # 启动日志更新
        self.update_logs()

        # 刷新定时任务列表
        self.refresh_scheduled_tasks()

        # 显示GUI窗口
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def create_widgets(self):
        # 创建样式
        style = ttk.Style()
        style.configure('Main.TFrame', background=self.bg_color)
        style.configure('Title.TLabel', font=self.title_font, foreground=self.primary_color, background=self.bg_color)
        style.configure('Label.TLabel', font=self.label_font, foreground=self.primary_color,
                        background=self.bg_color)
        style.configure('Button.TButton', font=self.button_font, background=self.accent_color)
        style.configure('Log.TFrame', background='white', relief='solid', borderwidth=1)
        style.configure('URL.TLabel', font=self.label_font, foreground=self.accent_color, background=self.bg_color)

        # 创建主框架
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 标题
        title_label = ttk.Label(main_container, text="若愚Bot", style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 10))

        # 创建标签页
        self.notebook = ttk.Notebook(main_container)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Tab 1: 主控制
        main_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(main_tab, text="主控制")

        # Tab 2: 定时任务
        scheduled_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(scheduled_tab, text="定时任务")

        # 配置主容器网格权重
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # 创建主控制标签页内容
        self.create_main_tab(main_tab)

        # 创建定时任务标签页内容
        self.create_scheduled_tab(scheduled_tab)

    def create_main_tab(self, parent):
        """创建主控制标签页"""
        row = 0

        # Webhook URL输入区域
        webhook_frame = ttk.Frame(parent, style='Main.TFrame')
        webhook_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(webhook_frame, text="回调地址 (每行一个):", style='Label.TLabel').grid(row=0, column=0, sticky=tk.W)
        self.webhook_text = scrolledtext.ScrolledText(webhook_frame, height=4, width=80,
                                                     font=self.log_font, bg='white',
                                                     relief='solid', borderwidth=1)
        self.webhook_text.grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky=(tk.W, tk.E))
        self.webhook_text.insert(tk.END, "\n".join(self.external_webhook_urls))

        update_webhook_button = ttk.Button(webhook_frame, text="更新", command=self.update_webhook_urls,
                                         style='Button.TButton', width=8)
        update_webhook_button.grid(row=2, column=0, sticky=tk.E, pady=(5, 0))
        row += 1

        # API Token输入区域
        api_token_frame = ttk.Frame(parent, style='Main.TFrame')
        api_token_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(api_token_frame, text="API Token:", style='Label.TLabel').grid(row=0, column=0, sticky=tk.W)
        self.api_token_var = tk.StringVar(value=config.get_api_token())
        api_token_entry = ttk.Entry(api_token_frame, textvariable=self.api_token_var, width=60)
        api_token_entry.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))

        update_token_button = ttk.Button(api_token_frame, text="更新", command=self.update_api_token,
                                       style='Button.TButton', width=10)
        update_token_button.grid(row=0, column=2, padx=(10, 0))
        row += 1

        # 本地Webhook设置区域
        local_webhook_frame = ttk.Frame(parent, style='Main.TFrame')
        local_webhook_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(local_webhook_frame, text="本地端口:", style='Label.TLabel').grid(row=0, column=0, sticky=tk.W)
        port_entry = ttk.Entry(local_webhook_frame, textvariable=self.local_port, width=10)
        port_entry.grid(row=0, column=1, padx=(10, 0), sticky=tk.W)

        self.update_port_button = ttk.Button(local_webhook_frame, text="更新", command=self.update_webhook_url,
                                   style='Button.TButton', width=8)
        self.update_port_button.grid(row=0, column=2, padx=(10, 0))
        row += 1

        # 当前Webhook URL显示
        self.current_webhook_label = ttk.Label(parent, textvariable=self.current_webhook_url, style='URL.TLabel')
        self.current_webhook_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15))
        row += 1

        # 初始化当前webhook URL
        self.update_webhook_url()

        # 任务管理员列表输入区域
        task_admin_frame = ttk.Frame(parent, style='Main.TFrame')
        task_admin_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(task_admin_frame, text="任务管理员 (允许通过消息添加任务的用户，每行一个):", style='Label.TLabel').grid(row=0, column=0, sticky=tk.W)
        self.task_admin_text = scrolledtext.ScrolledText(task_admin_frame, height=3, width=60,
                                                         font=self.log_font, bg='white',
                                                         relief='solid', borderwidth=1)
        self.task_admin_text.grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky=(tk.W, tk.E))
        # 加载现有的任务管理员列表
        task_admins = config.get_task_admin_list()
        if task_admins:
            self.task_admin_text.insert(tk.END, "\n".join(task_admins))

        update_admin_button = ttk.Button(task_admin_frame, text="更新", command=self.update_task_admin_list,
                                        style='Button.TButton', width=8)
        update_admin_button.grid(row=2, column=0, sticky=tk.E, pady=(5, 0))
        row += 1

        # 监听对象输入区域
        listen_frame = ttk.Frame(parent, style='Main.TFrame')
        listen_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(listen_frame, text="监听对象 (每行一个，名称严格区分大小写):", style='Label.TLabel').grid(row=0,
                                                                                                           column=0,
                                                                                                           sticky=tk.W)
        self.listen_text = scrolledtext.ScrolledText(listen_frame, height=4, width=60,
                                                     font=self.log_font, bg='white',
                                                     relief='solid', borderwidth=1)
        self.listen_text.grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky=(tk.W, tk.E))
        self.listen_text.insert(tk.END, "\n".join(config.get_listen_list()))
        row += 1

        # 控制按钮
        button_frame = ttk.Frame(parent, style='Main.TFrame')
        button_frame.grid(row=row, column=0, columnspan=3, pady=15)

        self.start_button = ttk.Button(button_frame, text="开始", command=self.start_service,
                                       style='Button.TButton', width=10)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_service,
                                      style='Button.TButton', width=10, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        row += 1

        # 日志显示区域
        log_frame = ttk.LabelFrame(parent, text="日志", style='Log.TFrame', padding="10")
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))

        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80,
                                                  font=self.log_font, bg='white',
                                                  relief='flat')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        row += 1

        # 状态标签
        self.status_label = ttk.Label(parent, text="状态: 已停止", style='Label.TLabel')
        self.status_label.grid(row=row, column=0, columnspan=3, sticky=tk.W)

        # 配置网格权重
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(row-1, weight=1)  # 日志区域可扩展
        listen_frame.columnconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

    def create_scheduled_tab(self, parent):
        """创建定时任务标签页"""
        row = 0

        # 说明文本
        info_label = ttk.Label(parent, text="在此管理定时发送的消息任务", style='Label.TLabel')
        info_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        row += 1

        # 定时任务列表
        list_frame = ttk.LabelFrame(parent, text="任务列表", style='Log.TFrame', padding="10")
        list_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))

        columns = ("id", "name", "type", "time", "recipient", "status", "next_run")
        self.scheduled_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        # 设置列标题
        self.scheduled_tree.heading("id", text="ID")
        self.scheduled_tree.heading("name", text="任务名称")
        self.scheduled_tree.heading("type", text="类型")
        self.scheduled_tree.heading("time", text="时间")
        self.scheduled_tree.heading("recipient", text="接收者")
        self.scheduled_tree.heading("status", text="状态")
        self.scheduled_tree.heading("next_run", text="下次运行")

        # 设置列宽
        self.scheduled_tree.column("id", width=0, stretch=False)  # 隐藏ID列
        self.scheduled_tree.column("name", width=150)
        self.scheduled_tree.column("type", width=100)
        self.scheduled_tree.column("time", width=80)
        self.scheduled_tree.column("recipient", width=150)
        self.scheduled_tree.column("status", width=80)
        self.scheduled_tree.column("next_run", width=180)

        # 添加滚动条
        scheduled_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.scheduled_tree.yview)
        self.scheduled_tree.configure(yscrollcommand=scheduled_scrollbar.set)

        self.scheduled_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scheduled_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        row += 1

        # 定时任务按钮
        button_frame = ttk.Frame(parent, style='Main.TFrame')
        button_frame.grid(row=row, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(button_frame, text="添加任务", command=self.open_add_task_dialog,
                  style='Button.TButton', width=12).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="编辑任务", command=self.open_edit_task_dialog,
                  style='Button.TButton', width=12).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="删除任务", command=self.delete_selected_task,
                  style='Button.TButton', width=12).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="启用/禁用", command=self.toggle_task_enabled,
                  style='Button.TButton', width=12).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="刷新列表", command=self.refresh_scheduled_tasks,
                  style='Button.TButton', width=12).grid(row=0, column=4, padx=5)

        # 配置网格权重
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)  # 任务列表可扩展

        # 设置窗口最小大小
        self.root.minsize(900, 700)

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def update_logs(self):
        while not log_queue.empty():
            log_message = log_queue.get()
            self.log_text.insert(tk.END, log_message + "\n")
            self.log_text.see(tk.END)
        self.root.after(100, self.update_logs)

    def get_listen_list(self):
        """从文本框获取监听对象列表"""
        text = self.listen_text.get("1.0", tk.END).strip()
        if not text:
            return []
        # 按行分割，去除空行和空白字符
        return [line.strip() for line in text.split('\n') if line.strip()]

    def start_service(self):
        if not self.is_running:
            # 获取监听对象列表
            listen_list = self.get_listen_list()
            if not listen_list:
                logging.error("请至少添加一个监听对象")
                return

            # 保存当前设置到配置文件
            self.save_listen_list()
            self.update_webhook_urls()
            logging.info("配置已保存")

            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="状态: 运行中")

            # 启动webhook服务器线程
            self.webhook_thread = threading.Thread(target=self.start_webhook_server)
            self.webhook_thread.daemon = True
            self.webhook_thread.start()

            # 启动消息监听线程
            self.listener_thread = threading.Thread(target=self.message_listener)
            self.listener_thread.daemon = True
            self.listener_thread.start()

            # 启动定时任务调度器线程
            self.scheduler_thread = threading.Thread(target=self.task_manager.run_scheduler)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()

            logging.info("服务启动成功")

    def stop_service(self):
        if self.is_running:
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="状态: 已停止")

            # 停止定时任务调度器
            if self.task_manager:
                self.task_manager.is_running = False

            # 关闭Flask服务器
            try:
                global server
                if server:
                    server.shutdown()
                    server = None
                    logging.info("Webhook服务器已停止")
            except Exception as e:
                logging.error(f"停止Webhook服务器时出错: {str(e)}")

            logging.info("服务已停止")

    def start_webhook_server(self):
        """启动webhook服务器"""
        try:
            port = int(self.local_port.get())
            if port < 1 or port > 65535:
                raise ValueError("端口号无效")

            global server
            server = make_server('0.0.0.0', port, flask_app)
            server.serve_forever()
        except Exception as e:
            logging.error(f"启动webhook服务器失败: {str(e)}")
            server = None

    def update_sessions(self):
        """更新会话列表"""
        try:
            current_time = time.time()
            if current_time - self.last_session_update >= self.session_update_interval:
                self.sessions = wx.GetSession()
                self.last_session_update = current_time
                logging.info("会话列表已更新")

                # 检查新会话并添加到监听列表
                for session in self.sessions:
                    if session.isnew and session.name not in config.get_listen_list():
                        try:
                            # 检查是否已经在监听列表中
                            if session.name not in self.get_listen_list():
                                wx.AddListenChat(nickname=session.name, callback=self.handle_message_callback)
                                logging.info(f"已添加新会话监听: {session.name}")
                        except Exception as e:
                            logging.error(f"添加新会话监听失败: {str(e)}")
        except Exception as e:
            logging.error(f"更新会话列表失败: {str(e)}")

    def generate_message_id(self, chat_name, sender, content, timestamp):
        """生成消息唯一ID"""
        self.message_id_counter += 1
        return f"{chat_name}_{sender}_{content}_{timestamp}_{self.message_id_counter}"

    def is_duplicate_message(self, chat_name, sender, content, timestamp):
        """检查消息是否重复"""
        current_time = time.time()

        # 定期清理过期缓存
        if current_time - self.last_cache_cleanup >= self.cache_cleanup_interval:
            self.cleanup_message_cache(current_time)
            self.last_cache_cleanup = current_time

        # 生成消息唯一ID
        message_id = self.generate_message_id(chat_name, sender, content, timestamp)

        # 检查消息是否已处理
        if message_id in self.processed_messages:
            return True

        # 将消息添加到已处理列表
        self.processed_messages[message_id] = current_time
        return False

    def cleanup_message_cache(self, current_time):
        """清理过期的消息缓存"""
        expired_keys = [
            key for key, timestamp in self.processed_messages.items()
            if current_time - timestamp > self.message_cache_time
        ]
        for key in expired_keys:
            del self.processed_messages[key]
        if expired_keys:
            logging.info(f"已清理 {len(expired_keys)} 条过期消息缓存")

    def send_message_with_retry(self, who, content, max_retries=3, is_group=False, at_list=None, chat_name=None):
        for attempt in range(max_retries):
            try:
                logging.info(f"\n尝试发送消息 (第 {attempt + 1} 次):")
                logging.info(f"- 发送给: {who}")
                logging.info(f"- 内容: {content}")
                if is_group:
                    logging.info(f"- 群聊消息")
                    if at_list:
                        logging.info(f"- @列表: {at_list}")

                # 根据是否是群聊和是否有@列表来决定发送方式
                if is_group:
                    # 群聊消息
                    if at_list:
                        if at_list == ['all']:
                            # @所有人
                            wx.SendMsg(msg=content, who=who, at=at_list)
                        else:
                            # @指定成员
                            wx.SendMsg(msg=content, who=who, at=at_list)
                    else:
                        # 普通群聊消息
                        wx.SendMsg(msg=content, who=who)
                else:
                    # 私聊消息
                    wx.SendMsg(msg=content, who=who)

                # 发送后等待一段时间，确保消息发送完成
                time.sleep(0.5)
                logging.info("消息发送成功")
                return True

            except Exception as e:
                logging.error(f"发送消息失败 (尝试 {attempt + 1}/{max_retries}):")
                logging.error(f"错误类型: {type(e).__name__}")
                logging.error(f"错误信息: {str(e)}")
                logging.error(traceback.format_exc())

                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)  # 递增等待时间
                    logging.info(f"等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    logging.error("达到最大重试次数，发送失败")
                    return False

    def process_message_queue(self):
        """处理消息队列"""
        while self.is_running:
            try:
                if not self.message_queue.empty():
                    current_time = time.time()
                    if current_time - self.last_send_time >= self.min_send_interval:
                        message_data = self.message_queue.get()
                        self.send_message_with_retry(**message_data)
                        self.last_send_time = current_time
                time.sleep(0.1)
            except Exception as e:
                logging.error(f"处理消息队列时出错: {str(e)}")
                logging.error(traceback.format_exc())
                time.sleep(1)

    def handle_message_callback(self, msg, chat):
        """处理接收到的消息的回调函数"""
        try:
            msgtype = msg.type
            content = msg.content

            # 获取聊天名称（兼容不同版本的wxauto）
            if hasattr(chat, 'name'):
                who = chat.name
            elif hasattr(chat, 'nickname'):
                who = chat.nickname
            elif hasattr(chat, 'title'):
                who = chat.title
            else:
                # 如果都没有，尝试从消息对象获取
                who = getattr(msg, 'chat_name', 'Unknown')
                # 记录调试信息
                logging.debug(f"Chat对象属性: {dir(chat)}")
                logging.debug(f"Message对象属性: {dir(msg)}")

            # 获取发送者（兼容不同版本）
            if hasattr(msg, 'sender'):
                sender = msg.sender
            else:
                sender = who

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            # 检查是否是重复消息
            if self.is_duplicate_message(who, sender, content, timestamp):
                return

            # 处理系统消息
            if msgtype == 'sys':
                logging.info(f"【系统消息】{content}")
                return

            # 处理时间消息
            if msgtype == 'time':
                logging.info(f"【时间消息】{msg.time if hasattr(msg, 'time') else content}")
                return

            # 处理撤回消息
            if msgtype == 'recall':
                logging.info(f"【撤回消息】{content}")
                return

            # 已发送的消息
            if msgtype == 'self':
                logging.info(f"【已发送的消息】{content}")
                return

            # 获取自己的昵称用于@检测
            my_nickname = wx.nickname
            AtMe = "@" + my_nickname

            # 判断是否是群聊（发送人和窗口名字不同）
            is_group = sender != who

            if is_group:
                # 检查是否被@
                is_at_me = AtMe in content or my_nickname in content
                # 检查是否是自己的回复消息
                if "收到你的消息:" in content:
                    logging.info(f"忽略自己的回复消息: {content}")
                    return

                logging.info(f"消息内容: {content}")

                if is_at_me:
                    logging.info(f"在群 {who} 中被 {sender} @了，消息内容: {content}")
                    try:
                        # 发送到所有webhook
                        data = {
                            "target_user": who,
                            "message": content,
                            "timestamp": timestamp,
                            "is_group": True,
                            "sender": sender,
                            "chat_name": who,
                            "is_at_me": True
                        }

                        # 发送到所有配置的webhook地址
                        for webhook_url in self.external_webhook_urls:
                            try:
                                response = requests.post(
                                    webhook_url,
                                    json=data,
                                    headers={'Content-Type': 'application/json'}
                                )

                                if response.status_code == 200:
                                    logging.info(f"群@消息已成功发送到webhook: {webhook_url}")
                                else:
                                    logging.error(f"发送群@消息到webhook失败，状态码: {response.status_code}")
                                    logging.error(f"响应内容: {response.text}")
                            except Exception as e:
                                logging.error(f"发送到webhook {webhook_url} 失败: {str(e)}")

                    except Exception as e:
                        logging.error(f"处理群@消息失败: {str(e)}")
                        logging.error(traceback.format_exc())
                else:
                    # 群消息未被@，只记录日志
                    logging.info(f"收到来自群 {who} 的消息，发送者: {sender}, 内容: {content}，未被@，忽略处理")
            else:
                # 私聊消息
                logging.info(f"收到来自 {who} 的私聊消息: {content}")

                # 首先检查是否是任务命令
                task_admin_list = self.config.get_task_admin_list()
                if task_admin_list and who in task_admin_list:
                    # 尝试解析任务命令
                    parse_result = TaskCommandParser.parse_task_command(content, who)
                    if parse_result['success']:
                        try:
                            task_data = parse_result['task_data']

                            # 处理工作日任务（需要创建5个任务）
                            if task_data.get('schedule_type') == 'workday':
                                # 为周一到周五创建5个任务
                                weekday_names = ['周一', '周二', '周三', '周四', '周五']
                                added_count = 0
                                for i in range(5):
                                    workday_task = task_data.copy()
                                    workday_task['schedule_type'] = 'weekday'
                                    workday_task['weekday'] = i
                                    workday_task['name'] = f"[消息添加] {weekday_names[i]} {task_data['message'][:15]}"
                                    self.task_manager.add_task(workday_task)
                                    added_count += 1

                                # 重新调度所有任务
                                if self.task_manager.is_running:
                                    self.task_manager.reschedule_all_tasks()

                                # 回复成功消息
                                reply_msg = f"✅ 已成功添加工作日任务（周一至周五共{added_count}个任务）\n"
                                reply_msg += f"⏰ 时间: {task_data['time']}\n"
                                reply_msg += f"📝 内容: {task_data['message']}"
                                self.message_queue.put((who, reply_msg, None))
                                logging.info(f"已为 {who} 添加工作日任务")
                                return  # 不再继续处理webhook
                            else:
                                # 添加单个任务
                                task_id = self.task_manager.add_task(task_data)

                                # 重新调度所有任务
                                if self.task_manager.is_running:
                                    self.task_manager.reschedule_all_tasks()

                                # 构建回复消息
                                schedule_type_names = {
                                    'once': '单次任务',
                                    'daily': '每日任务',
                                    'weekday': '每周任务'
                                }
                                type_name = schedule_type_names.get(task_data['schedule_type'], '任务')

                                reply_msg = f"✅ 已成功添加{type_name}\n"
                                if task_data['schedule_type'] == 'once':
                                    reply_msg += f"📅 日期: {task_data['date']}\n"
                                elif task_data['schedule_type'] == 'weekday':
                                    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
                                    reply_msg += f"📅 星期: {weekday_names[task_data['weekday']]}\n"
                                reply_msg += f"⏰ 时间: {task_data['time']}\n"
                                reply_msg += f"📝 内容: {task_data['message']}"

                                self.message_queue.put((who, reply_msg, None))
                                logging.info(f"已为 {who} 添加任务: {task_data['name']}")
                                return  # 不再继续处理webhook

                        except Exception as e:
                            error_msg = f"❌ 添加任务失败: {str(e)}"
                            self.message_queue.put((who, error_msg, None))
                            logging.error(f"添加任务失败: {str(e)}")
                            logging.error(traceback.format_exc())
                            return
                    else:
                        # 解析失败，但可能是任务命令格式错误
                        # 检查是否包含任务关键词
                        task_keywords = ['任务', 'task', '每日', '每周', '单次', '一次性', '工作日', 'daily', 'weekly', 'once', 'weekday']
                        if any(keyword in content for keyword in task_keywords):
                            error_msg = f"❌ {parse_result['error']}\n\n"
                            error_msg += "📖 支持的格式:\n"
                            error_msg += "• 单次任务 日期 时间 内容\n"
                            error_msg += "  例: 单次任务 明天 15:30 提醒开会\n"
                            error_msg += "• 每日任务 时间 内容\n"
                            error_msg += "  例: 每日任务 09:00 早安问候\n"
                            error_msg += "• 每周任务 星期 时间 内容\n"
                            error_msg += "  例: 每周任务 周一 09:00 周会提醒\n"
                            error_msg += "• 工作日 时间 内容\n"
                            error_msg += "  例: 工作日 09:00 打卡提醒"
                            self.message_queue.put((who, error_msg, None))
                            logging.info(f"任务命令格式错误: {parse_result['error']}")
                            return

                # 如果不是任务命令或用户无权限，继续正常的webhook处理
                try:
                    data = {
                        "target_user": who,
                        "message": content,
                        "timestamp": timestamp,
                        "is_group": False,
                        "chat_name": who
                    }

                    # 发送到所有配置的webhook地址
                    for webhook_url in self.external_webhook_urls:
                        try:
                            response = requests.post(
                                webhook_url,
                                json=data,
                                headers={'Content-Type': 'application/json'}
                            )

                            if response.status_code == 200:
                                logging.info(f"私聊消息已成功发送到webhook: {webhook_url}")
                            else:
                                logging.error(f"发送到webhook失败，状态码: {response.status_code}")
                                logging.error(f"响应内容: {response.text}")
                        except Exception as e:
                            logging.error(f"发送到webhook {webhook_url} 失败: {str(e)}")

                except Exception as e:
                    logging.error(f"发送到webhook失败: {str(e)}")
                    logging.error(traceback.format_exc())

        except Exception as e:
            logging.error(f"处理消息回调时出错: {str(e)}")
            logging.error(traceback.format_exc())

    def message_listener(self):
        # 获取主控制页面的监听对象列表
        listen_list = self.get_listen_list()

        # 获取定时任务的所有接收者
        scheduled_recipients = []
        if self.task_manager:
            tasks = self.task_manager.get_all_tasks()
            for task in tasks:
                if task.get('enabled', False):  # 只添加启用的任务的接收者
                    recipient = task.get('recipient', '')
                    if recipient and recipient not in scheduled_recipients:
                        scheduled_recipients.append(recipient)

        # 合并并去重监听列表
        combined_list = list(set(listen_list + scheduled_recipients))

        if scheduled_recipients:
            logging.info(f"从定时任务中添加了 {len(scheduled_recipients)} 个接收者到监听列表")
            logging.info(f"定时任务接收者: {', '.join(scheduled_recipients)}")

        logging.info(f"最终监听列表（共 {len(combined_list)} 个）: {', '.join(combined_list)}")

        # 启动消息队列处理线程
        queue_thread = threading.Thread(target=self.process_message_queue)
        queue_thread.daemon = True
        queue_thread.start()

        # 获取自己的昵称
        my_nickname = wx.nickname
        logging.info(f"我的昵称: {my_nickname}")

        # 添加监听对象（使用新的API）
        for who in combined_list:
            try:
                wx.AddListenChat(nickname=who, callback=self.handle_message_callback)
                logging.info(f"已添加监听: {who}")
            except Exception as e:
                logging.error(f"添加监听 {who} 失败: {str(e)}")

        logging.info("开始监听消息...")

        # 启动监听
        try:
            wx.StartListening()
            logging.info("监听已启动")
        except Exception as e:
            logging.error(f"启动监听失败: {str(e)}")

        # 保持运行
        while self.is_running:
            try:
                time.sleep(1)
            except Exception as e:
                logging.error(f"监听循环出错: {str(e)}")
                logging.error(traceback.format_exc())
                time.sleep(5)

        # 停止监听
        try:
            wx.StopListening()
            logging.info("监听已停止")
        except Exception as e:
            logging.error(f"停止监听失败: {str(e)}")

    def update_webhook_url(self):
        """更新当前webhook URL显示"""
        try:
            port = int(self.local_port.get())
            if port < 1 or port > 65535:
                raise ValueError("端口号无效")
            self.current_webhook_url.set(f"当前Webhook地址: http://{self.local_ip}:{port}/webhook")

            # 保存端口到配置文件
            config.config['DEFAULT']['port'] = str(port)
            with open(config.config_path, 'w', encoding='utf-8') as f:
                config.config.write(f)
            logging.info(f"端口设置已更新为: {port}")
        except ValueError:
            self.current_webhook_url.set("端口号无效")
            logging.error("输入的端口号无效")

    def update_api_token(self):
        """更新API Token"""
        try:
            token = self.api_token_var.get().strip()
            if not token:
                logging.warning("API Token不能为空")
                return
            config.set_api_token(token)
            logging.info("API Token已更新")
        except Exception as e:
            logging.error(f"更新API Token失败: {str(e)}")

    def save_listen_list(self):
        """保存监听列表到配置文件"""
        try:
            listen_list = self.get_listen_list()
            config.config['DEFAULT']['listen_list'] = ','.join(listen_list)
            with open(config.config_path, 'w', encoding='utf-8') as f:
                config.config.write(f)
            logging.info("监听列表已更新")
        except Exception as e:
            logging.error(f"保存监听列表失败: {str(e)}")

    def update_webhook_urls(self):
        """更新webhook URLs"""
        try:
            urls = [url.strip() for url in self.webhook_text.get("1.0", tk.END).split('\n') if url.strip()]
            if not urls:
                logging.warning("至少需要添加一个回调地址")
                return
            config.set_webhook_urls(urls)
            self.external_webhook_urls = urls
            logging.info("回调地址已更新")
        except Exception as e:
            logging.error(f"更新回调地址失败: {str(e)}")

    def update_task_admin_list(self):
        """更新任务管理员列表"""
        try:
            admins = [admin.strip() for admin in self.task_admin_text.get("1.0", tk.END).split('\n') if admin.strip()]
            config.set_task_admin_list(admins)
            if admins:
                logging.info(f"任务管理员列表已更新: {', '.join(admins)}")
            else:
                logging.info("任务管理员列表已清空（消息添加任务功能已禁用）")
        except Exception as e:
            logging.error(f"更新任务管理员列表失败: {str(e)}")

    def refresh_scheduled_tasks(self):
        """刷新定时任务列表"""
        try:
            # 清空现有列表
            for item in self.scheduled_tree.get_children():
                self.scheduled_tree.delete(item)

            # 重新加载任务
            self.task_manager.load_tasks()
            tasks = self.task_manager.get_all_tasks()

            # 添加任务到列表
            for task in tasks:
                schedule_type_map = {
                    "daily": "每天",
                    "weekly": "每周",
                    "weekday": f"周{['一', '二', '三', '四', '五', '六', '日'][task['weekday']]}",
                    "once": f"单次({task.get('date', '未设置')})"
                }
                schedule_type = schedule_type_map.get(task["schedule_type"], task["schedule_type"])
                status = "启用" if task["enabled"] else "禁用"
                next_run = task.get("next_run", "未设置")

                # 如果是单次任务且已执行，显示"已完成"
                if task["schedule_type"] == "once" and not task["enabled"]:
                    next_run = "已完成"

                self.scheduled_tree.insert("", tk.END, values=(
                    task["id"],
                    task["name"],
                    schedule_type,
                    task["time"],
                    task["recipient"],
                    status,
                    next_run
                ))

            logging.info(f"已刷新定时任务列表，共 {len(tasks)} 个任务")
        except Exception as e:
            logging.error(f"刷新定时任务列表失败: {str(e)}")
            logging.error(traceback.format_exc())

    def open_add_task_dialog(self):
        """打开添加任务对话框"""
        try:
            dialog = TaskDialog(self.root, self, None)
        except Exception as e:
            logging.error(f"打开添加任务对话框失败: {str(e)}")
            logging.error(traceback.format_exc())

    def open_edit_task_dialog(self):
        """打开编辑任务对话框"""
        try:
            selected = self.scheduled_tree.selection()
            if not selected:
                messagebox.showwarning("提示", "请先选择要编辑的任务")
                return

            task_id = self.scheduled_tree.item(selected[0])["values"][0]
            tasks = self.task_manager.get_all_tasks()
            task = next((t for t in tasks if t["id"] == task_id), None)

            if task:
                dialog = TaskDialog(self.root, self, task)
            else:
                messagebox.showerror("错误", "未找到选中的任务")
        except Exception as e:
            logging.error(f"打开编辑任务对话框失败: {str(e)}")
            logging.error(traceback.format_exc())

    def delete_selected_task(self):
        """删除选中的任务"""
        try:
            selected = self.scheduled_tree.selection()
            if not selected:
                messagebox.showwarning("提示", "请先选择要删除的任务")
                return

            if messagebox.askyesno("确认", "确定要删除选中的任务吗？"):
                task_id = self.scheduled_tree.item(selected[0])["values"][0]
                if self.task_manager.delete_task(task_id):
                    self.refresh_scheduled_tasks()
                    # 重新调度所有任务
                    if self.is_running:
                        self.task_manager.reschedule_all_tasks()
                    messagebox.showinfo("成功", "任务已删除")
                else:
                    messagebox.showerror("错误", "删除任务失败")
        except Exception as e:
            logging.error(f"删除任务失败: {str(e)}")
            logging.error(traceback.format_exc())
            messagebox.showerror("错误", f"删除任务失败: {str(e)}")

    def toggle_task_enabled(self):
        """切换任务启用状态"""
        try:
            selected = self.scheduled_tree.selection()
            if not selected:
                messagebox.showwarning("提示", "请先选择要启用/禁用的任务")
                return

            task_id = self.scheduled_tree.item(selected[0])["values"][0]
            if self.task_manager.toggle_task_enabled(task_id):
                self.refresh_scheduled_tasks()
                # 重新调度所有任务
                if self.is_running:
                    self.task_manager.reschedule_all_tasks()
                messagebox.showinfo("成功", "任务状态已更新")
            else:
                messagebox.showerror("错误", "更新任务状态失败")
        except Exception as e:
            logging.error(f"切换任务状态失败: {str(e)}")
            logging.error(traceback.format_exc())
            messagebox.showerror("错误", f"切换任务状态失败: {str(e)}")


# 任务对话框
class TaskDialog:
    def __init__(self, parent, gui: WeChatGUI, task: Optional[dict] = None):
        self.parent = parent
        self.gui = gui
        self.task = task
        self.is_edit = task is not None

        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑任务" if self.is_edit else "添加任务")
        self.dialog.geometry("600x700")
        self.dialog.resizable(False, False)

        # 设置为模态窗口
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.create_widgets()

        # 如果是编辑模式，填充现有数据
        if self.is_edit:
            self.load_task_data()

        # 居中显示
        self.center_window()

    def center_window(self):
        """将窗口居中显示"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """创建对话框组件"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        row = 0

        # 任务名称
        ttk.Label(main_frame, text="任务名称:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1

        # 调度类型
        ttk.Label(main_frame, text="调度类型:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.schedule_type_var = tk.StringVar(value="daily")
        schedule_type_combo = ttk.Combobox(main_frame, textvariable=self.schedule_type_var,
                                          values=["daily", "weekly", "weekday", "once"],
                                          state="readonly", width=37)
        schedule_type_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        schedule_type_combo.bind("<<ComboboxSelected>>", self.on_schedule_type_changed)
        ttk.Label(main_frame, text="(daily=每天, weekly=每周, weekday=特定星期, once=单次)").grid(row=row+1, column=1, sticky=tk.W)
        row += 2

        # 日期选择（仅once类型显示）
        ttk.Label(main_frame, text="日期:").grid(row=row, column=0, sticky=tk.W, pady=5)
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)

        # 获取当前日期作为默认值
        now = datetime.now()
        self.year_var = tk.StringVar(value=str(now.year))
        self.month_var = tk.StringVar(value=str(now.month))
        self.day_var = tk.StringVar(value=str(now.day))

        ttk.Label(date_frame, text="年:").grid(row=0, column=0, padx=(0, 5))
        self.year_spinbox = ttk.Spinbox(date_frame, from_=2024, to=2030, textvariable=self.year_var,
                                        width=6, format="%04.0f")
        self.year_spinbox.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(date_frame, text="月:").grid(row=0, column=2, padx=(0, 5))
        self.month_spinbox = ttk.Spinbox(date_frame, from_=1, to=12, textvariable=self.month_var,
                                         width=4, format="%02.0f")
        self.month_spinbox.grid(row=0, column=3, padx=(0, 10))

        ttk.Label(date_frame, text="日:").grid(row=0, column=4, padx=(0, 5))
        self.day_spinbox = ttk.Spinbox(date_frame, from_=1, to=31, textvariable=self.day_var,
                                       width=4, format="%02.0f")
        self.day_spinbox.grid(row=0, column=5)

        self.date_label = ttk.Label(main_frame, text="(仅单次任务需要设置)")
        self.date_label.grid(row=row+1, column=1, sticky=tk.W)
        row += 2

        # 时间设置
        ttk.Label(main_frame, text="时间:").grid(row=row, column=0, sticky=tk.W, pady=5)
        time_frame = ttk.Frame(main_frame)
        time_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)

        self.hour_var = tk.StringVar(value="09")
        self.minute_var = tk.StringVar(value="00")

        ttk.Label(time_frame, text="小时:").grid(row=0, column=0, padx=(0, 5))
        hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var,
                                   width=5, format="%02.0f")
        hour_spinbox.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(time_frame, text="分钟:").grid(row=0, column=2, padx=(0, 5))
        minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var,
                                     width=5, format="%02.0f")
        minute_spinbox.grid(row=0, column=3)
        row += 1

        # 星期选择（仅weekday类型显��）
        ttk.Label(main_frame, text="星期:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.weekday_var = tk.StringVar(value="0")
        self.weekday_combo = ttk.Combobox(main_frame, textvariable=self.weekday_var,
                                         values=["0", "1", "2", "3", "4", "5", "6"],
                                         state="readonly", width=37)
        self.weekday_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        self.weekday_label = ttk.Label(main_frame, text="(0=周一, 1=周二, ..., 6=周日)")
        self.weekday_label.grid(row=row+1, column=1, sticky=tk.W)
        row += 2

        # 接收者（支持多选）
        ttk.Label(main_frame, text="接收者:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)

        recipient_frame = ttk.Frame(main_frame)
        recipient_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)

        # 接收者输入框（显示已选择的接收者，用逗号分隔）
        self.recipient_var = tk.StringVar()
        recipient_entry = ttk.Entry(recipient_frame, textvariable=self.recipient_var, width=30)
        recipient_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        # 清空按钮
        ttk.Button(recipient_frame, text="清空", command=self.clear_recipients, width=6).grid(row=0, column=1)

        recipient_frame.columnconfigure(0, weight=1)

        # 提示标签
        ttk.Label(main_frame, text="(多个接收者用逗号分隔，或从下方列表双击添加)").grid(row=row+1, column=1, sticky=tk.W)
        row += 2

        # 可选接收者列表
        ttk.Label(main_frame, text="可选列表:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)

        listbox_frame = ttk.Frame(main_frame)
        listbox_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)

        # 从监听列表获取可选接收者
        listen_list = self.gui.get_listen_list()
        self.recipient_listbox = tk.Listbox(listbox_frame, height=5, width=30)
        self.recipient_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 添加滚动条
        recipient_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.recipient_listbox.yview)
        self.recipient_listbox.configure(yscrollcommand=recipient_scrollbar.set)
        recipient_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 填充监听列表
        for item in listen_list:
            self.recipient_listbox.insert(tk.END, item)

        # 双击添加到接收者
        self.recipient_listbox.bind('<Double-Button-1>', self.add_recipient_from_list)

        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)
        row += 1

        # 是否群聊
        self.is_group_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="群聊消息", variable=self.is_group_var,
                       command=self.on_is_group_changed).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        # @列表（仅群聊显示）
        ttk.Label(main_frame, text="@列表:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.at_list_var = tk.StringVar()
        self.at_list_entry = ttk.Entry(main_frame, textvariable=self.at_list_var, width=40)
        self.at_list_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        self.at_list_label = ttk.Label(main_frame, text="(多个用逗号分隔，all表示@所有人)")
        self.at_list_label.grid(row=row+1, column=1, sticky=tk.W)
        row += 2

        # 消息内容
        ttk.Label(main_frame, text="消息内容:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)
        self.message_text = scrolledtext.ScrolledText(main_frame, height=10, width=40)
        self.message_text.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1

        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="保存", command=self.save_task, width=10).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy, width=10).grid(row=0, column=1, padx=5)

        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)

        # 初始化显示状态
        self.on_schedule_type_changed()
        self.on_is_group_changed()

    def on_schedule_type_changed(self, event=None):
        """调度类型改变时的处理"""
        schedule_type = self.schedule_type_var.get()

        # 控制星期选择器
        if schedule_type == "weekday":
            self.weekday_combo.config(state="readonly")
            self.weekday_label.config(foreground="black")
        else:
            self.weekday_combo.config(state="disabled")
            self.weekday_label.config(foreground="gray")

        # 控制日期选择器
        if schedule_type == "once":
            self.year_spinbox.config(state="normal")
            self.month_spinbox.config(state="normal")
            self.day_spinbox.config(state="normal")
            self.date_label.config(foreground="black")
        else:
            self.year_spinbox.config(state="disabled")
            self.month_spinbox.config(state="disabled")
            self.day_spinbox.config(state="disabled")
            self.date_label.config(foreground="gray")

    def on_is_group_changed(self):
        """群聊选项改变时的处理"""
        is_group = self.is_group_var.get()
        if is_group:
            self.at_list_entry.config(state="normal")
            self.at_list_label.config(foreground="black")
        else:
            self.at_list_entry.config(state="disabled")
            self.at_list_label.config(foreground="gray")

    def add_recipient_from_list(self, event=None):
        """从列表中添加接收者"""
        try:
            selection = self.recipient_listbox.curselection()
            if not selection:
                return

            selected_item = self.recipient_listbox.get(selection[0])
            current_recipients = self.recipient_var.get().strip()

            # 检查是否已经存在
            if current_recipients:
                recipients_list = [r.strip() for r in current_recipients.split(',')]
                if selected_item not in recipients_list:
                    recipients_list.append(selected_item)
                    self.recipient_var.set(', '.join(recipients_list))
            else:
                self.recipient_var.set(selected_item)

        except Exception as e:
            logging.error(f"添加接收者失败: {str(e)}")

    def clear_recipients(self):
        """清空接收者列表"""
        self.recipient_var.set("")

    def load_task_data(self):
        """加载任务数据到表单"""
        if not self.task:
            return

        self.name_var.set(self.task.get("name", ""))
        self.schedule_type_var.set(self.task.get("schedule_type", "daily"))

        time_str = self.task.get("time", "09:00")
        hour, minute = time_str.split(":")
        self.hour_var.set(hour)
        self.minute_var.set(minute)

        self.weekday_var.set(str(self.task.get("weekday", 0)))

        # 加载日期（如果是单次任务）
        if self.task.get("schedule_type") == "once" and "date" in self.task:
            date_str = self.task.get("date", "")
            if date_str:
                try:
                    year, month, day = date_str.split("-")
                    self.year_var.set(year)
                    self.month_var.set(month)
                    self.day_var.set(day)
                except:
                    pass

        self.recipient_var.set(self.task.get("recipient", ""))
        self.is_group_var.set(self.task.get("is_group", False))

        at_list = self.task.get("at_list")
        if at_list:
            if isinstance(at_list, list):
                self.at_list_var.set(",".join(at_list))
            else:
                self.at_list_var.set(str(at_list))

        self.message_text.delete("1.0", tk.END)
        self.message_text.insert("1.0", self.task.get("message", ""))

        # 更新显示状态
        self.on_schedule_type_changed()
        self.on_is_group_changed()

    def save_task(self):
        """保存任务"""
        try:
            # 验证输入
            name = self.name_var.get().strip()
            if not name:
                messagebox.showerror("错误", "请输入任务名称")
                return

            recipient = self.recipient_var.get().strip()
            if not recipient:
                messagebox.showerror("错误", "请选择接收者")
                return

            message = self.message_text.get("1.0", tk.END).strip()
            if not message:
                messagebox.showerror("错误", "请输入消息内容")
                return

            # 构建任务数据
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            time_str = f"{hour:02d}:{minute:02d}"

            at_list = None
            if self.is_group_var.get():
                at_list_str = self.at_list_var.get().strip()
                if at_list_str:
                    if at_list_str.lower() == "all":
                        at_list = ["all"]
                    else:
                        at_list = [x.strip() for x in at_list_str.split(",") if x.strip()]

            task_data = {
                "name": name,
                "schedule_type": self.schedule_type_var.get(),
                "time": time_str,
                "weekday": int(self.weekday_var.get()),
                "recipient": recipient,
                "message": message,
                "is_group": self.is_group_var.get(),
                "at_list": at_list
            }

            # 如果是单次任务，添加日期
            if self.schedule_type_var.get() == "once":
                year = int(self.year_var.get())
                month = int(self.month_var.get())
                day = int(self.day_var.get())

                # 验证日期
                try:
                    target_date = datetime(year, month, day)
                    # 检查日期是否在过去
                    if target_date.date() < datetime.now().date():
                        messagebox.showerror("错误", "日期不能是过去的日期")
                        return
                    task_data["date"] = f"{year:04d}-{month:02d}-{day:02d}"
                except ValueError as e:
                    messagebox.showerror("错误", f"无效的日期: {str(e)}")
                    return

            # 保存任务
            if self.is_edit:
                self.gui.task_manager.update_task(self.task["id"], task_data)
                messagebox.showinfo("成功", "任务已更新")
            else:
                self.gui.task_manager.add_task(task_data)
                messagebox.showinfo("成功", "任务已添加")

            # 刷新任务列表
            self.gui.refresh_scheduled_tasks()

            # 如果服务正在运行，重新调度所有任务
            if self.gui.is_running:
                self.gui.task_manager.reschedule_all_tasks()

            # 关闭对话框
            self.dialog.destroy()

        except Exception as e:
            logging.error(f"保存任务失败: {str(e)}")
            logging.error(traceback.format_exc())
            messagebox.showerror("错误", f"保存任务失败: {str(e)}")


# 本地webhook路由
@flask_app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        # 验证API Token（标准 Authorization: Bearer <token>）
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logging.warning(f"缺少或格式错误的 Authorization 头: {auth_header}")
            return jsonify({'error': '缺少或格式错误的 Authorization 头'}), 401
        token = auth_header.split(' ', 1)[1]
        if token != config.get_api_token():
            logging.warning(f"无效的 API Token: {token}")
            return jsonify({'error': '无效的 API Token'}), 401

        data = request.json
        if not data:
            return jsonify({'error': '未收到JSON数据'}), 400

        # 检查是否是数组格式
        if isinstance(data, list):
            messages = data
        else:
            messages = [data]

        results = []
        for message in messages:
            try:
                # 获取必要字段
                sender = message.get('target_user')
                content = message.get('message')
                is_group = message.get('is_group', False)
                at_list = message.get('at_list', None)
                chat_name = message.get('chat_name', sender)  # 如果没有chat_name，使用sender

                if not sender or not content:
                    results.append({
                        'error': '缺少必要字段',
                        'received_data': message,
                        'expected_fields': ['target_user', 'message']
                    })
                    continue

                # 确保content是字符串类型
                if content is not None:
                    content = str(content)
                    # 处理可能的编码问题
                    content = content.encode('utf-8', errors='ignore').decode('utf-8')

                # 记录接收到的消息内容（用于调试）
                logging.info(f"收到webhook消息: 发送给 {sender}, 内容长度: {len(content)}")

                # 将消息添加到队列
                app.message_queue.put({
                    'who': sender,
                    'content': content,
                    'is_group': is_group,
                    'at_list': at_list,
                    'chat_name': chat_name
                })

                results.append({
                    'status': 'success',
                    'message': '消息已加入发送队列',
                    'target_user': sender,
                    'content_length': len(content),
                    'is_group': is_group,
                    'at_list': at_list
                })

            except Exception as e:
                logging.error(f"处理单条消息时出错: {str(e)}")
                logging.error(f"问题消息内容: {message}")
                results.append({
                    'error': f'处理消息时出错: {str(e)}',
                    'message': message
                })

        return jsonify(results), 200

    except Exception as e:
        logging.error(f"处理webhook请求失败: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


if __name__ == "__main__":
    # 自动打开微信
    if not auto_open_wechat():
        logging.error("请确保微信已正确安装并登录后再运行程序")
        time.sleep(5)  # 给用户时间查看错误信息
        sys.exit(1)  # 退出程序

    # 创建并显示GUI协助
    root = tk.Tk()
    app = WeChatGUI(root)
    root.mainloop()
