# 若愚Bot (RuoYuBot)

一个基于Python的wxauto库的微信消息转发机器人，支持群聊和私聊消息的转发与处理。

## 功能特点

- 🚀 支持群聊和私聊消息转发
- 🔔 支持@消息识别和处理
- 🔄 支持消息队列和重试机制
- 🔒 支持API Token认证
- 🌐 支持多Webhook地址配置
- 📝 实时日志显示
- 🎯 支持自定义监听对象
- 💾 配置文件自动保存
- 🔄 自动重连和错误恢复
- 🔍 支持文件编码自动检测
- ⏰ 支持定时任务（每日、每周、单次、工作日）
- 💬 **支持通过微信消息添加定时任务**

## 系统要求

- Windows 10 或更高版本
- Python 3.9 或更高版本（仅源码运行需要）
- 微信 PC 版 3.9.x

## 教程
https://zerotrue.xyz/article/1d6484d9-4c67-80eb-926d-ff6fb1588f60

## 安装步骤

### 方式一：直接运行（推荐）

1. 从 [Releases](https://github.com/Obito-404/RuoYuBot/releases) 页面下载最新版本的 `RuoYuBot.exe`
2. 双击运行 `RuoYuBot.exe`
3. 首次运行会自动创建配置文件

### 方式二：源码运行

1. 克隆仓库：
```bash
git clone https://github.com/Obito-404/RuoYuBot.git
cd ruoyubot
```

2. 安装依赖：
```bash
# 创建虚拟环境（推荐）
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

3. 运行程序：
```bash
python main.py
```

4. 打包命令：
```bash
 pyinstaller --noconfirm --onefile --windowed --name "RuoYuBot" --icon "D:/ruoyubot/icon.ico" --hidden-import comtypes --hidden-import comtypes.stream --hidden-import comtypes.gen --hidden-import win32com --hidden-import win32com.client "D:/ruoyubot/main.py"
```

## 依赖说明

主要依赖包：
- wxauto: 微信自动化操作
- requests: HTTP请求
- flask: Web服务器
- pywin32: Windows系统API
- chardet: 文件编码检测
- werkzeug: Flask服务器组件

## 配置说明

程序首次运行时会自动创建`config.ini`配置文件，包含以下配置项：

- `listen_list`: 需要监听的群聊或好友名称（用逗号分隔）
- `webhook_urls`: 消息转发目标地址（每行一个）
- `port`: 本地webhook服务器端口
- `retry_count`: 消息发送重试次数
- `retry_delay`: 重试延迟时间（秒）
- `log_level`: 日志级别
- `api_token`: API认证令牌
- `task_admin_list`: 允许通过消息添加任务的用户列表（逗号分隔）

## 定时任务功能

### 通过界面添加任务

在程序界面的"定时任务"标签页中，可以添加和管理定时任务：
- **每日任务**：每天在指定时间执行
- **每周任务**：每周在指定星期和时间执行
- **单次任务**：在指定日期和时间执行一次
- **工作日任务**：周一到周五每天执行

### 通过微信消息添加任务 ⭐新功能

现在可以直接通过微信私聊消息添加定时任务，无需打开程序界面！

**配置方法（两种方式）：**

**方式一：GUI 界面配置（推荐）**
1. 在程序主界面的"主控制"标签页中找到"任务管理员"输入框
2. 输入允许添加任务的微信用户名称（每行一个）
3. 点击"更新"按钮保存
4. 配置立即生效，无需重启

**方式二：手动编辑配置文件**
1. 在 `config.ini` 中设置 `task_admin_list`，添加允许管理任务的微信好友名称
2. 保存并重启程序

**支持的格式：**
```
# 单次任务
单次任务 明天 15:30 提醒开会
单次任务 2026-02-10 14:00 记得吃药

# 每日任务
每日任务 09:00 早安问候
每天 18:00 下班提醒

# 每周任务
每周任务 周一 09:00 周会提醒
每周 星期三 14:00 部门会议

# 工作日任务（自动创建周一到周五5个任务）
工作日 09:00 打卡提醒
```

详细说明请查看：
- [GUI_CONFIG.md](GUI_CONFIG.md) - GUI 界面配置指南
- [MESSAGE_TASK.md](MESSAGE_TASK.md) - 完整使用手册
- [QUICKSTART.md](QUICKSTART.md) - 快速开始指南

## 使用方法

1. 启动程序后，会自动打开微信（如果未运行）
2. 在GUI界面中配置：
   - 添加需要监听的群聊或好友
   - 设置webhook回调地址
   - 配置API Token
   - 设置本地端口

3. 点击"开始"按钮启动服务

## Webhook接口说明

### 接收消息格式

```json
{
    "target_user": "群聊名称/好友名称",
    "message": "消息内容",
    "timestamp": "2024-01-01 12:00:00",
    "is_group": true/false,
    "sender": "发送者名称",
    "chat_name": "群聊名称",
    "is_at_me": true/false
}
```

### 发送消息格式

```json
{
    "target_user": "群聊名称/好友名称",
    "message": "要发送的消息",
    "is_group": true/false,
    "at_list": ["要@的成员列表"]
}
```

## 注意事项

1. 确保微信已登录并保持在线
2. 监听对象名称需要严格匹配（区分大小写）
3. 建议定期检查日志，及时处理异常情况
4. 请妥善保管API Token，避免泄露
5. 配置文件使用UTF-8编码，支持中文

## 常见问题

1. Q: 程序无法启动微信，提示无效窗口句柄？
   A: 请确保已安装微信PC版3.9.x版本，并且已经登录。

2. Q: 消息转发失败？
   A: 检查webhook地址是否正确，网络连接是否正常，API Token是否配置正确。

3. Q: 无法收到群聊消息？
   A: 确认群聊名称是否正确，是否已添加到监听列表。

4. Q: 配置文件出现乱码？
   A: 程序会自动检测并转换配置文件编码为UTF-8。

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目。

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue。 
