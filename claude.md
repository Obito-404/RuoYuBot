# 项目参考资料

## wxauto

微信自动化库

- GitHub: https://github.com/cluic/wxauto.git

### API 变更说明 (v1.0.0+)

wxauto 的新版本 API 有重大变更，从轮询模式改为回调模式：

**旧 API (已废弃):**
```python
wx.AddListenChat(who=name, savepic=False)
msgs = wx.GetListenMessage()  # 轮询获取消息
```

**新 API (当前使用):**
```python
# 添加监听需要提供回调函数
wx.AddListenChat(nickname=name, callback=callback_function)

# 启动/停止监听
wx.StartListening()
wx.StopListening()

# 或者手动获取消息
wx.GetNewMessage()  # 获取当前聊天窗口的新消息
wx.GetAllMessage()  # 获取当前聊天窗口的所有消息
```

**回调函数签名:**
```python
def callback(msg: Message, chat: Chat) -> None:
    # msg: 消息对象
    # chat: 聊天对象
    pass
```

### 常用方法

- `AddListenChat(nickname, callback)` - 添加监听的聊天
- `RemoveListenChat(nickname)` - 移除监听
- `StartListening()` - 开始监听
- `StopListening(remove=True)` - 停止监听
- `SendMsg(msg, who, at=None)` - 发送消息
- `GetNewMessage()` - 获取新消息
- `GetAllMessage()` - 获取所有消息
