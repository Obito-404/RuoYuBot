# 若愚Bot 打包说明

## 一键打包

### 方法1: 目录模式打包（推荐用于调试）

双击运行 `build_dir.bat` 文件，会创建一个包含所有依赖的文件夹。

**优点：**
- 更容易调试 DLL 问题
- 可以看到所有依赖文件
- 启动速度更快

**缺点：**
- 需要分发整个文件夹
- 文件较多

### 方法2: 单文件模式打包

双击运行 `build.bat` 文件，会创建单个可执行文件。

**优点：**
- 只有一个 exe 文件
- 分发方便

**缺点：**
- 可能遇到 DLL 加载问题
- 首次启动较慢（需要解压）

### 方法3: 使用 Python 脚本

```bash
python build.py
```

## 打包流程

脚本会自动执行以下步骤：

1. **清理旧文件** - 删除 `dist` 和 `build` 目录
2. **检查依赖** - 确认 PyInstaller 和其他依赖已安装
3. **执行打包** - 使用 `若愚Bot.spec` 配置文件打包
4. **显示结果** - 显示打包后的文件信息

## 输出文件

打包成功后，可执行文件位于：
```
dist/若愚Bot.exe
```

## 手动打包

如果需要手动打包，可以运行：

```bash
# 清理旧文件
pyinstaller --clean 若愚Bot.spec

# 或者从头开始
pyinstaller --clean --onefile --noconsole --icon=icon.ico main.py
```

## 常见问题

### 1. DLL load failed 错误

**错误信息：**
```
ImportError: DLL load failed while importing ctypes
```

**解决方案：**

**方案A：使用目录模式打包（推荐）**
```bash
# 运行目录模式打包
build_dir.bat
```

**方案B：安装 comtypes**
```bash
pip install comtypes
```

**方案C：使用修改后的 spec 文件重新打包**
```bash
pyinstaller --clean 若愚Bot.spec
```

**方案D：手动添加 DLL**
1. 找到 Python 安装目录下的 DLLs 文件夹
2. 将以下 DLL 复制到 dist 目录：
   - `python3.dll`
   - `python3xx.dll`（xx 是版本号）
   - `_ctypes.pyd`

### 2. 打包失败：缺少模块

**解决方案：** 安装所有依赖
```bash
pip install -r requirements.txt
```

### 2. 打包后运行出错

**可能原因：**
- 缺少配置文件（config.ini）
- 缺少资源文件（icon.ico）
- 微信未安装或版本不兼容

**解决方案：**
- 确保 `config.ini` 在可执行文件同目录
- 检查微信版本（需要 3.9.x）

### 3. 打包文件太大

**优化方案：**
- 使用 `--exclude-module` 排除不需要的模块
- 使用 UPX 压缩（已在 spec 文件中启用）

### 4. 修改打包配置

编辑 `若愚Bot.spec` 文件，修改以下选项：

- `console=False` - 不显示控制台窗口
- `console=True` - 显示控制台窗口（便于调试）
- `icon=['icon.ico']` - 设置图标
- `upx=True` - 启用 UPX 压缩

## 打包配置说明

当前配置（`若愚Bot.spec`）：

- **打包模式：** 单文件（onefile）
- **控制台：** 隐藏（noconsole）
- **图标：** icon.ico
- **压缩：** 启用 UPX
- **包含文件：** icon.ico
- **隐藏导入：** win32timezone, schedule, wxauto

## 分发说明

打包后需要分发的文件：

1. `若愚Bot.exe` - 主程序（必需）
2. `config.ini` - 配置文件（首次运行会自动创建）
3. `README.md` - 使用说明（可选）

**注意：** 用户需要安装微信 3.9.x 版本才能正常使用。
