import math
import time
import numpy as np
from typing import List, Tuple, Dict
from singularity_checker import SingularityChecker


class DanceMove:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.keyframes = []
        self.duration = 1.0
    
    def add_keyframe(self, position: List[float], time_ratio: float):
        self.keyframes.append((position, time_ratio))
    
    def get_position_at_time(self, t: float) -> List[float]:
        if not self.keyframes:
            return [0, 0, 0, 0, 0, 0]
        
        t = t % 1.0
        
        for i in range(len(self.keyframes) - 1):
            _, t1 = self.keyframes[i]
            _, t2 = self.keyframes[i + 1]
            
            if t1 <= t <= t2:
                ratio = (t - t1) / (t2 - t1)
                pos1 = self.keyframes[i][0]
                pos2 = self.keyframes[i + 1][0]
                
                return [
                    pos1[j] + (pos2[j] - pos1[j]) * ratio
                    for j in range(6)
                ]
        
        return self.keyframes[-1][0]


class DanceMoveLibrary:
    def __init__(self):
        self.moves = {}
        self.base_position = [-350, 0, 200, 180, 0, 0]
        self.singularity_checker = SingularityChecker()
        self._create_basic_moves()
        self._create_test_moves()
        self._validate_all_moves()
    
    def _create_basic_moves(self):
        wave_right = DanceMove("wave_right", "左右摆动")
        wave_right.add_keyframe(self.base_position, 0.0)
        wave_right.add_keyframe([-400, -50, 200, 180, 0, 0], 0.2)
        wave_right.add_keyframe([-400, 50, 200, 180, 0, 0], 0.5)
        wave_right.add_keyframe([-400, -50, 200, 180, 0, 0], 0.8)
        wave_right.add_keyframe(self.base_position, 1.0)
        self.moves["wave_right"] = wave_right
        
        wave_up = DanceMove("wave_up", "上下摆动")
        wave_up.add_keyframe(self.base_position, 0.0)
        wave_up.add_keyframe([-350, 0, 150, 180, 0, 0], 0.2)
        wave_up.add_keyframe([-350, 0, 250, 180, 0, 0], 0.5)
        wave_up.add_keyframe([-350, 0, 150, 180, 0, 0], 0.8)
        wave_up.add_keyframe(self.base_position, 1.0)
        self.moves["wave_up"] = wave_up
        
        spin = DanceMove("spin", "旋转")
        spin.add_keyframe(self.base_position, 0.0)
        spin.add_keyframe([-350, 0, 200, 180, 0, 90], 0.2)
        spin.add_keyframe([-350, 0, 200, 180, 0, 180], 0.4)
        spin.add_keyframe([-350, 0, 200, 180, 0, 270], 0.6)
        spin.add_keyframe([-350, 0, 200, 180, 0, 360], 0.8)
        spin.add_keyframe(self.base_position, 1.0)
        self.moves["spin"] = spin
        
        figure_eight = DanceMove("figure_eight", "8字形运动")
        figure_eight.add_keyframe(self.base_position, 0.0)
        figure_eight.add_keyframe([-400, 50, 200, 180, 0, 45], 0.25)
        figure_eight.add_keyframe([-350, 0, 200, 180, 0, 0], 0.5)
        figure_eight.add_keyframe([-300, -50, 200, 180, 0, -45], 0.75)
        figure_eight.add_keyframe(self.base_position, 1.0)
        self.moves["figure_eight"] = figure_eight
        
        pump = DanceMove("pump", "快速上下运动")
        pump.duration = 0.5
        pump.add_keyframe(self.base_position, 0.0)
        pump.add_keyframe([-350, 0, 180, 180, 0, 0], 0.2)
        pump.add_keyframe([-350, 0, 220, 180, 0, 0], 0.5)
        pump.add_keyframe([-350, 0, 180, 180, 0, 0], 0.8)
        pump.add_keyframe(self.base_position, 1.0)
        self.moves["pump"] = pump
        
        sway = DanceMove("sway", "缓慢摇摆")
        sway.duration = 2.0
        sway.add_keyframe(self.base_position, 0.0)
        sway.add_keyframe([-350, -30, 200, 175, 0, -10], 0.2)
        sway.add_keyframe([-350, 30, 200, 185, 0, 10], 0.5)
        sway.add_keyframe([-350, -30, 200, 175, 0, -10], 0.8)
        sway.add_keyframe(self.base_position, 1.0)
        self.moves["sway"] = sway
    
    def _create_test_moves(self):
        wave_hand = DanceMove("wave_hand", "挥手")
        wave_hand.add_keyframe(self.base_position, 0.0)
        wave_hand.add_keyframe([-300, 0, 300, 180, 0, 0], 0.1)
        wave_hand.add_keyframe([-300, 0, 300, 170, 15, 0], 0.3)
        wave_hand.add_keyframe([-300, 0, 300, 190, -15, 0], 0.5)
        wave_hand.add_keyframe([-300, 0, 300, 170, 15, 0], 0.7)
        wave_hand.add_keyframe([-300, 0, 300, 180, 0, 0], 0.9)
        wave_hand.add_keyframe(self.base_position, 1.0)
        self.moves["test_wave"] = wave_hand
        
        draw_circle = DanceMove("draw_circle", "画圆")
        draw_circle.add_keyframe(self.base_position, 0.0)  # 开始位置
        steps = 12
        for i in range(1, steps):
            angle = (i / steps) * 2 * math.pi
            x = -350 + 50 * math.cos(angle)
            y = 50 * math.sin(angle)
            z = 200
            # 调整时间，为最后回到原位留出空间
            draw_circle.add_keyframe([x, y, z, 180, 0, 0], i / (steps + 1))
        draw_circle.add_keyframe(self.base_position, 1.0)  # 结束位置
        self.moves["test_circle"] = draw_circle
        
        nod = DanceMove("nod", "点头")
        nod.add_keyframe(self.base_position, 0.0)
        nod.add_keyframe([-350, 0, 200, 160, 0, 0], 0.25)
        nod.add_keyframe([-350, 0, 200, 200, 0, 0], 0.5)
        nod.add_keyframe([-350, 0, 200, 160, 0, 0], 0.75)
        nod.add_keyframe(self.base_position, 1.0)
        self.moves["test_nod"] = nod
        
        shake_head = DanceMove("shake_head", "摇头")
        shake_head.add_keyframe(self.base_position, 0.0)
        shake_head.add_keyframe([-350, 0, 200, 180, 0, -30], 0.25)
        shake_head.add_keyframe([-350, 0, 200, 180, 0, 30], 0.5)
        shake_head.add_keyframe([-350, 0, 200, 180, 0, -30], 0.75)
        shake_head.add_keyframe(self.base_position, 1.0)
        self.moves["test_shake"] = shake_head
    
    def get_move(self, name: str) -> DanceMove:
        return self.moves.get(name)
    
    def get_all_moves(self) -> Dict[str, DanceMove]:
        return self.moves
    
    def get_dance_moves(self) -> List[str]:
        return ["wave_right", "wave_up", "spin", "figure_eight", "pump", "sway"]
    
    def get_test_moves(self) -> List[str]:
        return ["test_wave", "test_circle", "test_nod", "test_shake"]
    
    def select_move_by_music(self, beat_strength: float, frequency: str) -> str:
        if beat_strength > 0.7:
            if frequency == "high":
                return "pump"
            else:
                return "spin"
        elif beat_strength > 0.4:
            if frequency == "low":
                return "wave_right"
            else:
                return "figure_eight"
        else:
            if frequency == "high":
                return "wave_up"
            else:
                return "sway"
    
    def _validate_all_moves(self):
        """验证所有动作的安全性"""
        print("验证舞蹈动作安全性...")
        unsafe_moves = []
        
        for move_name, move in self.moves.items():
            for i, (position, _) in enumerate(move.keyframes):
                is_safe, warnings = self.singularity_checker.is_position_safe(position)
                if not is_safe:
                    unsafe_moves.append({
                        'move': move_name,
                        'frame': i,
                        'position': position,
                        'warnings': warnings
                    })
        
        if unsafe_moves:
            print("警告：发现不安全的动作位置：")
            for unsafe in unsafe_moves:
                print(f"  动作: {unsafe['move']}, 帧: {unsafe['frame']}")
                for warning in unsafe['warnings']:
                    print(f"    - {warning}")
        else:
            print("✓ 所有动作位置都在安全范围内")
    
    def validate_move(self, move_name: str) -> Tuple[bool, List[str]]:
        """验证单个动作的安全性"""
        move = self.moves.get(move_name)
        if not move:
            return False, ["动作不存在"]
        
        all_warnings = []
        for i, (position, _) in enumerate(move.keyframes):
            is_safe, warnings = self.singularity_checker.is_position_safe(position)
            if not is_safe:
                for warning in warnings:
                    all_warnings.append(f"帧{i}: {warning}")
        
        return len(all_warnings) == 0, all_warnings