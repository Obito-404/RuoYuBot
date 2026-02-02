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
from tkinter import ttk, scrolledtext
import socket
import queue
import logging
from datetime import datetime
from typing import Dict, List, Optional
import configparser
import os
from pathlib import Path
import sys
from werkzeug.serving import make_server
import chardet

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
            'api_token': ''  # API Token
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
        self.root.geometry("900x1000")

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

        # 创建GUI元素
        self.create_widgets()

        # 启动日志更新
        self.update_logs()

        # 显示GUI窗口
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.configure(style='Main.TFrame')

        # 创建样式
        style = ttk.Style()
        style.configure('Main.TFrame', background=self.bg_color)
        style.configure('Title.TLabel', font=self.title_font, foreground=self.primary_color, background=self.bg_color)
        style.configure('Label.TLabel', font=self.label_font, foreground=self.primary_color,
                        background=self.bg_color)
        style.configure('Button.TButton', font=self.button_font, background=self.accent_color)
        style.configure('Log.TFrame', background='white', relief='solid', borderwidth=1)
        style.configure('URL.TLabel', font=self.label_font, foreground=self.accent_color, background=self.bg_color)

        # 标题
        title_label = ttk.Label(main_frame, text="若愚Bot", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Webhook URL输入区域
        webhook_frame = ttk.Frame(main_frame, style='Main.TFrame')
        webhook_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(webhook_frame, text="回调地址 (每行一个):", style='Label.TLabel').grid(row=0, column=0, sticky=tk.W)
        self.webhook_text = scrolledtext.ScrolledText(webhook_frame, height=4, width=80,
                                                     font=self.log_font, bg='white',
                                                     relief='solid', borderwidth=1)
        self.webhook_text.grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky=(tk.W, tk.E))
        self.webhook_text.insert(tk.END, "\n".join(self.external_webhook_urls))

        update_webhook_button = ttk.Button(webhook_frame, text="更新", command=self.update_webhook_urls,
                                         style='Button.TButton', width=8)
        update_webhook_button.grid(row=2, column=0, sticky=tk.E, pady=(5, 0))

        # API Token输入区域
        api_token_frame = ttk.Frame(main_frame, style='Main.TFrame')
        api_token_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(api_token_frame, text="API Token:", style='Label.TLabel').grid(row=0, column=0, sticky=tk.W)
        self.api_token_var = tk.StringVar(value=config.get_api_token())
        api_token_entry = ttk.Entry(api_token_frame, textvariable=self.api_token_var, width=60)
        api_token_entry.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))

        update_token_button = ttk.Button(api_token_frame, text="更新", command=self.update_api_token,
                                       style='Button.TButton', width=10)
        update_token_button.grid(row=0, column=2, padx=(10, 0))

        # 本地Webhook设置区域
        local_webhook_frame = ttk.Frame(main_frame, style='Main.TFrame')
        local_webhook_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(local_webhook_frame, text="本地端口:", style='Label.TLabel').grid(row=0, column=0, sticky=tk.W)
        port_entry = ttk.Entry(local_webhook_frame, textvariable=self.local_port, width=10)
        port_entry.grid(row=0, column=1, padx=(10, 0), sticky=tk.W)

        self.update_port_button = ttk.Button(local_webhook_frame, text="更新", command=self.update_webhook_url,
                                   style='Button.TButton', width=8)
        self.update_port_button.grid(row=0, column=2, padx=(10, 0))

        # 当前Webhook URL显示
        self.current_webhook_label = ttk.Label(main_frame, textvariable=self.current_webhook_url, style='URL.TLabel')
        self.current_webhook_label.grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=(0, 15))

        # 初始化当前webhook URL
        self.update_webhook_url()

        # 监听对象输入区域
        listen_frame = ttk.Frame(main_frame, style='Main.TFrame')
        listen_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(listen_frame, text="监听对象 (每行一个，名称严格区分大小写):", style='Label.TLabel').grid(row=0,
                                                                                                           column=0,
                                                                                                           sticky=tk.W)
        self.listen_text = scrolledtext.ScrolledText(listen_frame, height=4, width=60,
                                                     font=self.log_font, bg='white',
                                                     relief='solid', borderwidth=1)
        self.listen_text.grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky=(tk.W, tk.E))
        self.listen_text.insert(tk.END, "\n".join(config.get_listen_list()))

        # 控制按钮
        button_frame = ttk.Frame(main_frame, style='Main.TFrame')
        button_frame.grid(row=7, column=0, columnspan=3, pady=15)

        self.start_button = ttk.Button(button_frame, text="开始", command=self.start_service,
                                       style='Button.TButton', width=10)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_service,
                                      style='Button.TButton', width=10, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)

        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="日志", style='Log.TFrame', padding="10")
        log_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))

        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, width=80,
                                                  font=self.log_font, bg='white',
                                                  relief='flat')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 状态标签
        self.status_label = ttk.Label(main_frame, text="状态: 已停止", style='Label.TLabel')
        self.status_label.grid(row=9, column=0, columnspan=3, sticky=tk.W)

        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(8, weight=1)
        listen_frame.columnconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        # 设置窗口最小大小
        self.root.minsize(900, 800)

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

            logging.info("服务启动成功")

    def stop_service(self):
        if self.is_running:
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="状态: 已停止")

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
            sender = msg.sender if hasattr(msg, 'sender') else chat.name
            who = chat.name
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
        # 获取监听对象列表
        listen_list = self.get_listen_list()

        # 启动消息队列处理线程
        queue_thread = threading.Thread(target=self.process_message_queue)
        queue_thread.daemon = True
        queue_thread.start()

        # 获取自己的昵称
        my_nickname = wx.nickname
        logging.info(f"我的昵称: {my_nickname}")

        # 添加监听对象（使用新的API）
        for who in listen_list:
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
