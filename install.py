#!/usr/bin/env python3
"""
双语字幕工具安装脚本
自动检测环境并安装相应的依赖
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(command, check=True):
    """运行命令并返回结果"""
    print(f"执行命令: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check, 
            capture_output=True, 
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        if check:
            raise
        return e


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")


def check_ffmpeg():
    """检查ffmpeg是否安装"""
    try:
        result = run_command("ffmpeg -version", check=False)
        if result.returncode == 0:
            print("✅ ffmpeg已安装")
            return True
        else:
            print("❌ ffmpeg未安装")
            return False
    except FileNotFoundError:
        print("❌ ffmpeg未安装")
        return False


def install_ffmpeg():
    """安装ffmpeg"""
    system = platform.system().lower()
    
    if system == "windows":
        print("请手动安装ffmpeg:")
        print("1. 访问 https://ffmpeg.org/download.html")
        print("2. 下载Windows版本")
        print("3. 将ffmpeg.exe添加到系统PATH")
        
    elif system == "darwin":  # macOS
        print("尝试使用Homebrew安装ffmpeg...")
        try:
            run_command("brew install ffmpeg")
            print("✅ ffmpeg安装成功")
        except:
            print("❌ 安装失败，请手动安装:")
            print("brew install ffmpeg")
            
    elif system == "linux":
        print("尝试安装ffmpeg...")
        try:
            # 尝试不同的包管理器
            if os.path.exists("/usr/bin/apt"):
                run_command("sudo apt update && sudo apt install -y ffmpeg")
            elif os.path.exists("/usr/bin/yum"):
                run_command("sudo yum install -y ffmpeg")
            elif os.path.exists("/usr/bin/dnf"):
                run_command("sudo dnf install -y ffmpeg")
            else:
                print("请手动安装ffmpeg")
                return False
            print("✅ ffmpeg安装成功")
        except:
            print("❌ 安装失败，请手动安装ffmpeg")
            return False
    
    return check_ffmpeg()


def install_dependencies():
    """安装Python依赖"""
    print("安装Python依赖...")
    
    # 检查是否有uv包管理器
    try:
        run_command("uv --version", check=False)
        print("使用uv安装依赖...")
        run_command("uv pip install -r requirements.txt")
    except:
        print("使用pip安装依赖...")
        run_command(f"{sys.executable} -m pip install -r requirements.txt")
    
    print("✅ Python依赖安装完成")


def create_env_file():
    """创建.env文件"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("创建.env配置文件...")
        with open(env_example, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ .env文件已创建")
        print("请编辑.env文件，填入您的百度翻译API密钥")
    else:
        print("✅ .env文件已存在")


def create_directories():
    """创建必要的目录"""
    directories = ["temp", "output"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ 目录创建完成")


def main():
    """主安装函数"""
    print("🎬 双语字幕工具安装程序")
    print("=" * 50)
    
    # 检查Python版本
    check_python_version()
    
    # 检查并安装ffmpeg
    if not check_ffmpeg():
        print("正在安装ffmpeg...")
        install_ffmpeg()
    
    # 安装Python依赖
    install_dependencies()
    
    # 创建配置文件
    create_env_file()
    
    # 创建目录
    create_directories()
    
    print("\n" + "=" * 50)
    print("🎉 安装完成！")
    print("\n使用方法:")
    print("1. 编辑.env文件，填入百度翻译API密钥")
    print("2. 运行: python main.py")
    print("3. 在浏览器中打开显示的地址")
    print("\n注意事项:")
    print("- 首次运行会下载Whisper模型，请耐心等待")
    print("- 如果有NVIDIA GPU，建议安装CUDA版本的PyTorch以获得更好性能")


if __name__ == "__main__":
    main()
