"""
Nova 2 机械臂奇异点检测和避免模块
"""
import math
import numpy as np
from typing import List, Tuple, Dict


class SingularityChecker:
    """奇异点检测器"""
    
    def __init__(self):
        # Nova 2 工作空间限制（单位：mm）
        self.workspace_limits = {
            'x_min': -500,
            'x_max': 500,
            'y_min': -500,
            'y_max': 500,
            'z_min': -50,
            'z_max': 600
        }
        
        # 安全边界（距离工作空间边界的缓冲区）
        self.safety_margin = 50  # mm
        
        # 奇异点危险区域定义
        self.singularity_zones = {
            'shoulder': {
                'description': '肩奇异点：当机械臂手腕中心接近或穿过基座轴线',
                'check_radius': 100  # mm，基座轴线周围的危险半径
            },
            'wrist': {
                'description': '腕奇异点：当第4轴和第6轴同轴',
                'angle_threshold': 5  # 度，接近同轴的角度阈值
            },
            'elbow': {
                'description': '肘奇异点：当机械臂完全伸直或折叠',
                'extension_threshold': 0.95  # 伸直程度阈值（0-1）
            }
        }
        
        # 推荐的安全位置
        self.safe_positions = [
            [-350, 0, 200, 180, 0, 0],    # 默认基准位置
            [-300, 100, 250, 180, 0, 0],  # 安全位置1
            [-300, -100, 250, 180, 0, 0], # 安全位置2
            [-400, 0, 300, 180, 0, 0],    # 安全位置3
        ]
    
    def check_workspace_limits(self, position: List[float]) -> Tuple[bool, str]:
        """
        检查位置是否在工作空间内
        
        参数:
            position: [x, y, z, rx, ry, rz]
            
        返回:
            (is_safe, message)
        """
        x, y, z = position[:3]
        
        # 检查工作空间限制
        if x < self.workspace_limits['x_min'] + self.safety_margin:
            return False, f"X坐标({x})接近最小限制"
        if x > self.workspace_limits['x_max'] - self.safety_margin:
            return False, f"X坐标({x})接近最大限制"
        if y < self.workspace_limits['y_min'] + self.safety_margin:
            return False, f"Y坐标({y})接近最小限制"
        if y > self.workspace_limits['y_max'] - self.safety_margin:
            return False, f"Y坐标({y})接近最大限制"
        if z < self.workspace_limits['z_min'] + self.safety_margin:
            return False, f"Z坐标({z})接近最小限制"
        if z > self.workspace_limits['z_max'] - self.safety_margin:
            return False, f"Z坐标({z})接近最大限制"
            
        return True, "位置在安全工作空间内"
    
    def check_shoulder_singularity(self, position: List[float]) -> Tuple[bool, str]:
        """
        检查肩奇异点
        当手腕中心接近基座轴线（X=0, Y=0）时发生
        """
        x, y = position[:2]
        distance_to_axis = math.sqrt(x**2 + y**2)
        
        threshold = self.singularity_zones['shoulder']['check_radius']
        if distance_to_axis < threshold:
            return False, f"接近肩奇异点（距离基座轴线: {distance_to_axis:.1f}mm）"
            
        return True, "远离肩奇异点"
    
    def check_wrist_singularity(self, position: List[float]) -> Tuple[bool, str]:
        """
        检查腕奇异点
        当RY接近±90度时，第4轴和第6轴可能同轴
        """
        _, _, _, _, ry, _ = position
        
        # 检查RY是否接近±90度
        danger_angles = [90, -90, 270, -270]
        threshold = self.singularity_zones['wrist']['angle_threshold']
        
        for angle in danger_angles:
            if abs(ry - angle) < threshold:
                return False, f"接近腕奇异点（RY={ry}°接近{angle}°）"
                
        return True, "远离腕奇异点"
    
    def check_elbow_singularity(self, position: List[float]) -> Tuple[bool, str]:
        """
        检查肘奇异点
        基于机械臂的伸展程度估算
        """
        x, y, z = position[:3]
        
        # 计算到基座的距离
        distance = math.sqrt(x**2 + y**2 + z**2)
        
        # Nova 2的大致臂长范围
        min_reach = 200  # mm
        max_reach = 600  # mm
        
        if distance < min_reach:
            return False, f"机械臂过度折叠（距离: {distance:.1f}mm）"
        if distance > max_reach * self.singularity_zones['elbow']['extension_threshold']:
            return False, f"机械臂过度伸展（距离: {distance:.1f}mm）"
            
        return True, "远离肘奇异点"
    
    def check_all_singularities(self, position: List[float]) -> Dict[str, Tuple[bool, str]]:
        """
        检查所有奇异点和限制
        
        返回:
            {'workspace': (bool, str), 'shoulder': (bool, str), ...}
        """
        results = {
            'workspace': self.check_workspace_limits(position),
            'shoulder': self.check_shoulder_singularity(position),
            'wrist': self.check_wrist_singularity(position),
            'elbow': self.check_elbow_singularity(position)
        }
        
        return results
    
    def is_position_safe(self, position: List[float]) -> Tuple[bool, List[str]]:
        """
        综合检查位置是否安全
        
        返回:
            (is_safe, warnings)
        """
        results = self.check_all_singularities(position)
        warnings = []
        is_safe = True
        
        for check_type, (safe, message) in results.items():
            if not safe:
                is_safe = False
                warnings.append(f"[{check_type}] {message}")
                
        return is_safe, warnings
    
    def suggest_safe_path(self, start: List[float], end: List[float]) -> List[List[float]]:
        """
        建议安全的运动路径
        如果直接路径可能经过奇异点，返回包含中间点的路径
        """
        # 检查起点和终点
        start_safe, start_warnings = self.is_position_safe(start)
        end_safe, end_warnings = self.is_position_safe(end)
        
        if not start_safe:
            print(f"警告：起始位置不安全 - {start_warnings}")
        if not end_safe:
            print(f"警告：目标位置不安全 - {end_warnings}")
            
        # 简单的路径规划：如果直线路径可能有问题，添加中间点
        path = [start]
        
        # 检查是否需要绕过基座轴线（肩奇异点）
        x1, y1 = start[:2]
        x2, y2 = end[:2]
        
        # 如果路径穿过基座附近
        if (x1 * x2 < 0 or y1 * y2 < 0) and min(abs(x1), abs(x2), abs(y1), abs(y2)) < 100:
            # 添加一个绕过基座的中间点
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            
            # 确保中间点远离基座
            if abs(mid_x) < 150:
                mid_x = 150 if mid_x >= 0 else -150
            if abs(mid_y) < 150:
                mid_y = 150 if mid_y >= 0 else -150
                
            mid_point = [mid_x, mid_y, (start[2] + end[2])/2] + end[3:]
            path.append(mid_point)
            
        path.append(end)
        return path
    
    def get_nearest_safe_position(self, current: List[float]) -> List[float]:
        """
        获取最近的安全位置
        """
        min_distance = float('inf')
        nearest_safe = self.safe_positions[0]
        
        for safe_pos in self.safe_positions:
            distance = np.linalg.norm(np.array(current[:3]) - np.array(safe_pos[:3]))
            if distance < min_distance:
                min_distance = distance
                nearest_safe = safe_pos
                
        return nearest_safe


# 测试代码
if __name__ == "__main__":
    checker = SingularityChecker()
    
    # 测试一些位置
    test_positions = [
        [-350, 0, 200, 180, 0, 0],      # 安全位置
        [-50, 50, 200, 180, 0, 0],      # 接近肩奇异点
        [-350, 0, 200, 180, 90, 0],     # 接近腕奇异点
        [-600, 0, 200, 180, 0, 0],      # 超出工作空间
        [-480, 0, 400, 180, 0, 0],      # 接近最大伸展
    ]
    
    print("奇异点检测测试")
    print("=" * 60)
    
    for i, pos in enumerate(test_positions):
        print(f"\n测试位置 {i+1}: {pos[:3]}")
        is_safe, warnings = checker.is_position_safe(pos)
        
        if is_safe:
            print("✓ 位置安全")
        else:
            print("✗ 位置不安全:")
            for warning in warnings:
                print(f"  - {warning}")
                
    # 测试路径规划
    print("\n\n路径规划测试")
    print("=" * 60)
    start = [-350, -100, 200, 180, 0, 0]
    end = [-350, 100, 200, 180, 0, 0]
    path = checker.suggest_safe_path(start, end)
    
    print(f"从 {start[:3]} 到 {end[:3]} 的建议路径:")
    for i, point in enumerate(path):
        print(f"  {i+1}. {point[:3]}")