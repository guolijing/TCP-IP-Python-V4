#!/usr/bin/env python3
"""
测试所有动作是否都正确回到原始位置
"""
from dance_moves import DanceMoveLibrary
import numpy as np

def test_moves_return_to_base():
    library = DanceMoveLibrary()
    base_position = library.base_position
    
    print(f"基准位置: {base_position}")
    print("=" * 60)
    
    # 测试所有动作
    all_moves = library.get_all_moves()
    
    for move_name, move in all_moves.items():
        print(f"\n测试动作: {move_name} ({move.description})")
        
        # 检查起始位置
        start_pos = move.keyframes[0][0] if move.keyframes else None
        print(f"  起始位置: {start_pos}")
        
        # 检查结束位置
        end_pos = move.keyframes[-1][0] if move.keyframes else None
        print(f"  结束位置: {end_pos}")
        
        # 验证是否回到基准位置
        if start_pos and end_pos:
            start_match = np.allclose(start_pos, base_position, atol=0.1)
            end_match = np.allclose(end_pos, base_position, atol=0.1)
            
            if start_match and end_match:
                print(f"  ✓ 动作正确：从基准位置开始，到基准位置结束")
            else:
                if not start_match:
                    print(f"  ✗ 错误：起始位置不是基准位置")
                if not end_match:
                    print(f"  ✗ 错误：结束位置不是基准位置")
                    
        # 显示所有关键帧
        print(f"  关键帧数量: {len(move.keyframes)}")
        for i, (pos, time_ratio) in enumerate(move.keyframes):
            print(f"    帧{i}: 时间={time_ratio:.2f}, 位置={pos}")

if __name__ == "__main__":
    test_moves_return_to_base()