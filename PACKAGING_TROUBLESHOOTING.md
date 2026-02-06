# PyInstaller 打包故障排除

## 问题：DLL load failed while importing ctypes

### 原因
这是 PyInstaller 打包 wxauto 时的常见问题，因为 ctypes 依赖的 DLL 文件没有被正确打包。

### 解决方案

#### 方案1：使用改进的 spec 文件（推荐）

1. 使用提供的 `若愚Bot_onedir.spec` 文件
2. 运行打包脚本：
   ```bash
   build_fixed.bat
   ```

#### 方案2：手动打包

```bash
# 清理旧文件
rmdir /s /q build dist

# 使用改进的 spec 文件打包
pyinstaller --clean 若愚Bot_onedir.spec
```

#### 方案3：使用命令行参数

```bash
pyinstaller --clean ^
    --onedir ^
    --windowed ^
    --name "若愚Bot" ^
    --icon "icon.ico" ^
    --collect-all wxauto ^
    --collect-all comtypes ^
    --hidden-import ctypes ^
    --hidden-import ctypes.wintypes ^
    --hidden-import _ctypes ^
    --hidden-import comtypes ^
    --hidden-import comtypes.stream ^
    --hidden-import comtypes.gen ^
    --hidden-import win32com ^
    --hidden-import win32com.client ^
    main.py
```

## 常见问题

### Q1: 打包后运行提示缺少模块

**解决方案**：
1. 检查 requirements.txt 中的所有依赖是否已安装
2. 在 spec 文件的 hiddenimports 中添加缺少的模块
3. 使用 `--collect-all` 收集整个包

### Q2: 打包后程序无法启动

**解决方案**：
1. 使用 onedir 模式（文件夹模式）而不是 onefile
2. 在 spec 文件中设置 `console=True` 查看错误信息
3. 检查杀毒软件是否阻止了程序运行

### Q3: 打包文件太大

**解决方案**：
1. 使用虚拟环境，只安装必要的依赖
2. 在 spec 文件中添加 excludes 排除不需要的模块
3. 使用 UPX 压缩（已在 spec 中启用）

### Q4: 打包后配置文件丢失

**解决方案**：
1. 程序会自动创建默认配置文件
2. 或者手动复制 config.ini 到 dist 目录
3. 使用打包脚本会自动复制配置文件

## 推荐的打包流程

### 1. 准备环境

```bash
# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装 PyInstaller
pip install pyinstaller
```

### 2. 测试程序

```bash
# 确保程序能正常运行
python main.py
```

### 3. 打包（onedir 模式）

```bash
# 使用提供的脚本
build_fixed.bat

# 或手动打包
pyinstaller --clean 若愚Bot_onedir.spec
```

### 4. 测试打包结果

```bash
# 运行打包后的程序
dist\若愚Bot\若愚Bot.exe
```

### 5. 打包（onefile 模式）- 可选

如果 onedir 模式成功，可以尝试 onefile：

```bash
pyinstaller --clean 若愚Bot_onefile.spec
```

## spec 文件说明

### onedir vs onefile

**onedir（推荐）**：
- ✅ 启动速度快
- ✅ 更容易调试
- ✅ 兼容性好
- ❌ 文件较多

**onefile**：
- ✅ 单个文件，方便分发
- ❌ 启动速度慢（需要解压）
- ❌ 可能有兼容性问题
- ❌ 杀毒软件更容易误报

### 关键配置

```python
# 隐藏导入 - 确保所有依赖被包含
hiddenimports = [
    'ctypes',
    'ctypes.wintypes',
    '_ctypes',
    'wxauto',
    'comtypes',
    # ...
]

# 收集所有资源
tmp_ret = collect_all('wxauto')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# 手动添加 DLL
python_dir = os.path.dirname(sys.executable)
dlls_dir = os.path.join(python_dir, 'DLLs')
ctypes_pyd = os.path.join(dlls_dir, '_ctypes.pyd')
if os.path.exists(ctypes_pyd):
    binaries.append((ctypes_pyd, '.'))
```

## 调试技巧

### 1. 启用控制台输出

在 spec 文件中设置：
```python
console=True
```

### 2. 查看详细日志

```bash
pyinstaller --clean --log-level DEBUG 若愚Bot_onedir.spec
```

### 3. 检查打包内容

```bash
# 查看打包了哪些文件
pyi-archive_viewer dist\若愚Bot\若愚Bot.exe
```

### 4. 测试导入

在打包前测试所有导入：
```python
import ctypes
import wxauto
import comtypes
print("All imports successful!")
```

## 环境要求

- Python 3.9+
- PyInstaller 5.0+
- Windows 10+
- 微信 PC 版 3.9.x

## 相关链接

- [PyInstaller 文档](https://pyinstaller.org/)
- [wxauto GitHub](https://github.com/cluic/wxauto)
- [常见问题解答](https://github.com/pyinstaller/pyinstaller/wiki)

## 获取帮助

如果以上方案都无法解决问题：

1. 查看完整的错误日志
2. 检查 Python 和依赖版本
3. 尝试在虚拟环境中打包
4. 提交 Issue 并附上详细错误信息
