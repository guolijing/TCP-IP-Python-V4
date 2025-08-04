#!/usr/bin/env python3
"""
测试速度控制功能
"""
import time
from robot_controller import RobotController
from config import Config

def test_speed_control(robot_ip="192.168.1.198"):
    print("速度控制测试")
    print("=" * 50)
    
    # 创建机器人控制器
    robot = RobotController(robot_ip)
    config = Config()
    
    print(f"默认速度设置: {config.get('default_speed', 50)}%")
    print(f"机器人初始速度: {robot.get_current_speed()}%")
    
    if not robot.connect():
        print("无法连接到机器人")
        return
    
    print("成功连接到机器人")
    
    if not robot.enable_robot():
        print("无法启用机器人")
        robot.disconnect()
        return
    
    print("机器人已启用")
    
    # 测试不同速度
    test_speeds = [20, 50, 80, 100]
    base_position = [-350, 0, 200, 180, 0, 0]
    test_position = [-350, 50, 200, 180, 0, 0]
    
    for speed in test_speeds:
        print(f"\n测试速度: {speed}%")
        robot.set_speed(speed)
        print(f"当前速度设置: {robot.get_current_speed()}%")
        
        # 移动到测试位置
        start_time = time.time()
        robot.move_to_position(test_position)
        time.sleep(2)  # 等待移动完成
        
        # 返回基准位置
        robot.move_to_position(base_position)
        time.sleep(2)  # 等待移动完成
        
        elapsed_time = time.time() - start_time
        print(f"移动耗时: {elapsed_time:.2f}秒")
    
    # 清理
    robot.disable_robot()
    robot.disconnect()
    print("\n测试完成")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='测试机器人速度控制')
    parser.add_argument('--ip', type=str, default='192.168.1.198',
                       help='机器人IP地址')
    args = parser.parse_args()
    
    test_speed_control(args.ip)