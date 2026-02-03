#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
若愚Bot 一键打包工具
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_header(text):
    """打印标题"""
    print("\n" + "=" * 50)
    print(text)
    print("=" * 50 + "\n")

def print_step(step, total, text):
    """打印步骤"""
    print(f"[{step}/{total}] {text}")

def clean_build_files():
    """清理构建文件"""
    print_step(1, 4, "清理旧的构建文件...")

    dirs_to_clean = ["dist", "build"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"  ✓ 已删除 {dir_name} 目录")
            except Exception as e:
                print(f"  ✗ 删除 {dir_name} 失败: {e}")
        else:
            print(f"  - {dir_name} 目录不存在")
    print()

def check_dependencies():
    """检查依赖"""
    print_step(2, 4, "检查依赖...")

    try:
        import PyInstaller
        print(f"  ✓ PyInstaller 已安装 (版本: {PyInstaller.__version__})")
    except ImportError:
        print("  ✗ 未安装 PyInstaller")
        print("  正在安装 PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("  ✓ PyInstaller 安装成功")
        except subprocess.CalledProcessError:
            print("  ✗ 安装失败，请手动运行: pip install pyinstaller")
            return False

    # 检查其他依赖
    required_modules = ["wxauto", "flask", "schedule", "requests"]
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✓ {module} 已安装")
        except ImportError:
            missing.append(module)
            print(f"  ✗ {module} 未安装")

    if missing:
        print(f"\n  警告: 缺少依赖 {', '.join(missing)}")
        print("  请运行: pip install -r requirements.txt")
        return False

    print()
    return True

def build_executable():
    """构建可执行文件"""
    print_step(3, 4, "开始打包...")

    spec_file = "若愚Bot.spec"
    if not os.path.exists(spec_file):
        print(f"  ✗ 未找到配置文件: {spec_file}")
        return False

    print(f"  使用配置文件: {spec_file}")
    print()

    try:
        # 运行 PyInstaller
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", spec_file]
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n  ✗ 打包失败: {e}")
        return False
    except Exception as e:
        print(f"\n  ✗ 发生错误: {e}")
        return False

def show_result():
    """显示打包结果"""
    print_step(4, 4, "打包完成！")

    exe_path = Path("dist/若愚Bot.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n  ✓ 可执行文件: {exe_path}")
        print(f"  ✓ 文件大小: {size_mb:.2f} MB")

        # 检查是否有其他文件
        dist_files = list(Path("dist").iterdir())
        if len(dist_files) > 1:
            print(f"\n  输出目录包含 {len(dist_files)} 个文件:")
            for f in dist_files:
                if f.is_file():
                    print(f"    - {f.name}")

        return True
    else:
        print(f"\n  ✗ 未找到输出文件: {exe_path}")
        return False

def main():
    """主函数"""
    print_header("若愚Bot 一键打包工具")

    # 检查是否在项目根目录
    if not os.path.exists("main.py"):
        print("错误: 请在项目根目录运行此脚本")
        return 1

    # 执行打包流程
    try:
        # 1. 清理
        clean_build_files()

        # 2. 检查依赖
        if not check_dependencies():
            print("\n请先安装所有依赖，然后重新运行打包脚本")
            return 1

        # 3. 打包
        if not build_executable():
            print_header("打包失败！")
            return 1

        # 4. 显示结果
        if show_result():
            print_header("打包成功！")

            # 询问是否打开输出目录
            try:
                response = input("\n是否打开输出目录？(Y/N): ").strip().lower()
                if response == 'y':
                    if sys.platform == 'win32':
                        os.startfile("dist")
                    elif sys.platform == 'darwin':
                        subprocess.run(["open", "dist"])
                    else:
                        subprocess.run(["xdg-open", "dist"])
            except:
                pass

            return 0
        else:
            print_header("打包失败！")
            return 1

    except KeyboardInterrupt:
        print("\n\n用户中断")
        return 1
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\n按回车键退出...")
    sys.exit(exit_code)
