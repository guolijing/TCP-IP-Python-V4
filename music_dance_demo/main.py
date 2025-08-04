#!/usr/bin/env python3
import sys
import os
import argparse
from robot_controller import RobotController
from audio_analyzer import AudioAnalyzer
from dance_moves import DanceMoveLibrary
from dance_gui import DanceGUI
from config import Config


def main():
    parser = argparse.ArgumentParser(description='Dobot Nova 2 音乐舞蹈Demo')
    parser.add_argument('--ip', type=str, default=None,
                       help='机器人IP地址 (不指定则使用保存的配置)')
    parser.add_argument('--no-gui', action='store_true',
                       help='不启动图形界面，仅测试连接')
    args = parser.parse_args()
    
    config = Config()
    robot_ip = args.ip if args.ip else config.get_robot_ip()
    
    print("=" * 50)
    print("Dobot Nova 2 音乐舞蹈Demo")
    print("=" * 50)
    print(f"机器人IP: {robot_ip}")
    print(f"音乐文件夹: {config.get_music_folder()}")
    print()
    
    robot_controller = RobotController(robot_ip)
    audio_analyzer = AudioAnalyzer()
    dance_library = DanceMoveLibrary()
    
    if args.no_gui:
        print("测试模式：仅测试机器人连接")
        if robot_controller.connect():
            print("✓ 成功连接到机器人")
            if robot_controller.enable_robot():
                print("✓ 机器人已启用")
                print("✓ 当前位置:", robot_controller.get_current_position())
                robot_controller.disable_robot()
            else:
                print("✗ 无法启用机器人")
            robot_controller.disconnect()
        else:
            print("✗ 无法连接到机器人")
    else:
        print("启动图形界面...")
        gui = DanceGUI(robot_controller, audio_analyzer, dance_library)
        try:
            gui.run()
        except KeyboardInterrupt:
            print("\n程序被用户中断")
        finally:
            if robot_controller.is_connected:
                robot_controller.disconnect()
            print("程序已退出")


if __name__ == "__main__":
    main()