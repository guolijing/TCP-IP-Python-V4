#!/usr/bin/env python3
"""
测试V4版本迁移的简单脚本
"""
import sys
import os

# 添加父目录到路径以导入dobot_api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dobot_api import DobotApiDashboard, DobotApiFeedBack, MyType
    print("✓ 成功导入V4版本的dobot_api模块")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

try:
    from robot_controller import RobotController
    print("✓ 成功导入robot_controller模块")
except ImportError as e:
    print(f"✗ 导入robot_controller失败: {e}")
    sys.exit(1)

try:
    from audio_analyzer import AudioAnalyzer
    from dance_moves import DanceMoveLibrary
    from config import Config
    print("✓ 成功导入其他模块")
except ImportError as e:
    print(f"✗ 导入其他模块失败: {e}")
    sys.exit(1)

print("\n迁移测试通过！所有模块都可以正常导入。")
print("请使用以下命令运行完整的demo:")
print("  python main.py --ip <机器人IP地址>")
print("或运行无界面测试:")
print("  python main.py --ip <机器人IP地址> --no-gui")