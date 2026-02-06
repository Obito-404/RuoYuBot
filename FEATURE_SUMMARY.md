# 通过微信消息添加定时任务功能 - 开发文档

## 功能概述

本次更新为 RuoYuBot 添加了通过微信私聊消息直接添加定时任务的功能，用户无需打开程序界面即可快速创建任务。

## 新增文件

1. **MESSAGE_TASK.md** - 用户使用手册
2. **EXAMPLES.md** - 使用示例和场景演示
3. **CONFIG_GUIDE.md** - 配置指南
4. **test_parser.py** - 解析器测试脚本

## 代码修改

### 1. Config 类扩展 (main.py)

**新增配置项：**
```python
'task_admin_list': ''  # 允许通过消息添加任务的用户列表
```

**新增方法：**
- `get_task_admin_list()` - 获取任务管理员列表
- `set_task_admin_list(admins)` - 设置任务管理员列表

### 2. TaskCommandParser 类 (main.py)

全新的任务命令解析器类，支持：

**日期解析：**
- 自然语言：今天、明天、后天
- 标准格式：2026-02-10, 2026/02/10, 2026.02.10
- 简短格式：02-10, 02/10（自动补充年份）

**时间解析：**
- HH:MM 格式：09:00, 9:00
- 中文格式：09时00分, 9点00分

**星期解析：**
- 周一~周日
- 星期一~星期日
- 礼拜一~礼拜日

**支持的任务类型：**
1. **单次任务** - `单次任务 日期 时间 内容`
2. **每日任务** - `每日任务 时间 内容`
3. **每周任务** - `每周任务 星期 时间 内容`
4. **工作日任务** - `工作日 时间 内容`（自动创建5个任务）

**关键方法：**
- `parse_natural_date(date_str)` - 解析自然语言日期
- `parse_time(time_str)` - 解析时间格式
- `parse_weekday(weekday_str)` - 解析星期
- `parse_task_command(message, sender)` - 主解析方法

### 3. 消息处理逻辑扩展 (main.py)

在 `handle_message_callback` 方法的私聊消息处理部分添加：

**权限检查：**
```python
task_admin_list = self.config.get_task_admin_list()
if task_admin_list and who in task_admin_list:
    # 处理任务命令
```

**任务添加流程：**
1. 解析消息内容
2. 验证格式和参数
3. 添加任务到任务管理器
4. 重新调度所有任务
5. 回复用户成功或失败消息

**特殊处理：**
- 工作日任务自动创建5个独立任务（周一到周五）
- 单次任务验证时间不能是过去
- 格式错误时提供帮助信息

**回复消息格式：**
```
✅ 已成功添加���次任务
📅 日期: 2026-02-10
⏰ 时间: 15:30
📝 内容: 提醒开会
```

## 技术实现细节

### 1. 正则表达式匹配

使用多个正则表达式模式匹配不同的任务格式：

```python
# 单次任务
r'^(单次任务|一次性任务|once)\s+(\S+)\s+(\S+)\s+(.+)$'

# 每日任务
r'^(每日任务|每天|daily)\s+(\S+)\s+(.+)$'

# 每周任务
r'^(每周任务|每周|weekly)\s+(\S+)\s+(\S+)\s+(.+)$'

# 工作日任务
r'^(工作日|weekday)\s+(\S+)\s+(.+)$'
```

### 2. 日期时间处理

使用 `datetime` 模块进行日期时间计算：

```python
# 自然语言日期
today = datetime.now()
tomorrow = today + timedelta(days=1)

# 验证时间不在过去
task_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
if task_datetime < datetime.now():
    return {'success': False, 'error': '任务时间不能是过去的时间'}
```

### 3. 工作日任务处理

工作日任务需要创建5个独立的任务：

```python
if task_data.get('schedule_type') == 'workday':
    weekday_names = ['周一', '周二', '周三', '周四', '周五']
    for i in range(5):
        workday_task = task_data.copy()
        workday_task['schedule_type'] = 'weekday'
        workday_task['weekday'] = i
        workday_task['name'] = f"[消息添加] {weekday_names[i]} {task_data['message'][:15]}"
        self.task_manager.add_task(workday_task)
```

### 4. 任务重新调度

添加任务后需要重新调度：

```python
if self.task_manager.is_running:
    self.task_manager.reschedule_all_tasks()
```

### 5. 错误处理

提供友好的错误提示：

```python
if any(keyword in content for keyword in task_keywords):
    error_msg = f"❌ {parse_result['error']}\n\n"
    error_msg += "📖 支持的格式:\n"
    error_msg += "• 单次任务 日期 时间 内容\n"
    # ... 更多格式说明
    self.message_queue.put((who, error_msg, None))
```

## 安全性考虑

1. **权限控制**：只有在 `task_admin_list` 中的用户才能添加任务
2. **时间验证**：单次任务不允许设置过去的时间
3. **接收者限制**：通过消息添加的任务只能发送给命令发送者本人
4. **格式验证**：严格的格式验证防止恶意输入

## 测试

### 测试脚本

`test_parser.py` 包含17个测试用例：
- 13个成功案例（各种格式的任务）
- 4个失败案例（错误格式和无效参数）

### 运行测试

```bash
python test_parser.py
```

### 测试结果

所有测试用例均通过，解析器工作正常。

## 用户文档

### MESSAGE_TASK.md
- 功能说明
- 配置方法
- 支持的任务格式
- 使用流程
- 回复消息示例
- 注意事项
- 常见问题

### EXAMPLES.md
- 5个实际使用场景
- 2个错误处理示例
- 高级用法说明
- 配置示例

### CONFIG_GUIDE.md
- 完整配置示例
- 各配置项详细说明
- 快速配置步骤
- 常见配置错误及解决方案
- 配置测试方法

## 更新的文档

### README.md
- 在功能特点中添加新功能
- 添加定时任务功能章节
- 添加通过微信消息添加任务的说明

## 兼容性

- 完全向后兼容，不影响现有功能
- 配置文件自动添加新字段
- 如果不配置 `task_admin_list`，功能不会启用

## 性能影响

- 解析器使用正则表达式，性能开销极小
- 只在私聊消息中进行解析，不影响群聊消息处理
- 任务添加后立即生效，无需重启程序

## 未来改进方向

1. **支持更多日期格式**
   - 相对日期：下周一、下个月
   - 节假日：春节、国庆节

2. **支持更多任务类型**
   - 间隔任务：每隔N小时/天
   - 条件任务：基于某些条件触发

3. **任务管理命令**
   - 查看任务列表
   - 删除任务
   - 修改任务

4. **群聊支持**
   - 在群聊中添加任务
   - 为群成员添加任务

5. **任务模板**
   - 预定义常用任务模板
   - 快速创建任务

## 总结

本次更新成功实现了通过微信消息添加定时任务的功能，大大提升了用户体验。用户无需打开程序界面，只需发送一条消息即可快速创建任务。功能设计考虑了安全性、易用性和扩展性，为未来的功能扩展打下了良好的基础。
