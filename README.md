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
