import json
import os
import sys
from typing import Dict, Optional, Tuple

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dobot_api import alarmAlarmJsonFile


class AlarmManager:
    """报警信息管理器"""
    
    def __init__(self):
        self.controller_alarms = {}
        self.servo_alarms = {}
        self.load_alarm_definitions()
        
    def load_alarm_definitions(self):
        """加载报警定义文件"""
        try:
            # 使用dobot_api提供的函数加载报警文件
            controller_data, servo_data = alarmAlarmJsonFile()
            
            # 构建控制器报警字典
            for alarm in controller_data:
                self.controller_alarms[alarm['id']] = alarm
                
            # 构建伺服报警字典
            for alarm in servo_data:
                self.servo_alarms[alarm['id']] = alarm
                
            print(f"加载了 {len(self.controller_alarms)} 个控制器报警定义")
            print(f"加载了 {len(self.servo_alarms)} 个伺服报警定义")
            
        except Exception as e:
            print(f"加载报警定义失败: {e}")
            # 加载备用的报警定义
            self._load_fallback_definitions()
    
    def _load_fallback_definitions(self):
        """加载备用报警定义"""
        try:
            # 直接定位到files目录
            files_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'files')
            
            # 加载控制器报警
            controller_path = os.path.join(files_dir, 'alarmController.json')
            if os.path.exists(controller_path):
                with open(controller_path, 'r', encoding='utf-8') as f:
                    controller_data = json.load(f)
                    for alarm in controller_data:
                        self.controller_alarms[alarm['id']] = alarm
                        
            # 加载伺服报警
            servo_path = os.path.join(files_dir, 'alarmServo.json')
            if os.path.exists(servo_path):
                with open(servo_path, 'r', encoding='utf-8') as f:
                    servo_data = json.load(f)
                    for alarm in servo_data:
                        self.servo_alarms[alarm['id']] = alarm
                        
        except Exception as e:
            print(f"加载备用报警定义失败: {e}")
    
    def parse_error_id(self, error_response: str) -> Optional[Tuple[int, int]]:
        """
        解析GetErrorID的返回值
        返回: (控制器报警ID, 伺服报警ID) 或 None
        """
        try:
            # GetErrorID返回格式: "0,{controller_id,servo_id},GetErrorID()"
            # 提取大括号中的内容
            if '{' in error_response and '}' in error_response:
                start = error_response.find('{')
                end = error_response.find('}')
                content = error_response[start+1:end]
                
                # 分割控制器和伺服报警ID
                parts = content.split(',')
                if len(parts) >= 2:
                    controller_id = int(parts[0])
                    servo_id = int(parts[1])
                    return (controller_id, servo_id)
                    
        except Exception as e:
            print(f"解析错误ID失败: {e}")
            
        return None
    
    def get_alarm_info(self, alarm_id: int, is_servo: bool = False, language: str = 'zh_CN') -> Dict[str, str]:
        """
        获取报警信息
        
        参数:
            alarm_id: 报警ID
            is_servo: 是否是伺服报警
            language: 语言代码 ('zh_CN', 'en', 'ja', 等)
            
        返回:
            包含 description, cause, solution 的字典
        """
        alarm_dict = self.servo_alarms if is_servo else self.controller_alarms
        
        if alarm_id in alarm_dict:
            alarm = alarm_dict[alarm_id]
            lang_data = alarm.get(language, alarm.get('zh_CN', {}))
            
            return {
                'id': alarm_id,
                'level': alarm.get('level', 0),
                'description': lang_data.get('description', f'未知报警 ID: {alarm_id}'),
                'cause': lang_data.get('cause', ''),
                'solution': lang_data.get('solution', '')
            }
        else:
            return {
                'id': alarm_id,
                'level': 0,
                'description': f'未知报警 ID: {alarm_id}',
                'cause': '',
                'solution': ''
            }
    
    def get_alarm_level_text(self, level: int) -> str:
        """获取报警级别文本"""
        level_map = {
            1: "提示",
            2: "警告", 
            3: "一般错误",
            4: "严重错误",
            5: "致命错误"
        }
        return level_map.get(level, f"级别{level}")
    
    def format_alarm_message(self, controller_id: int, servo_id: int, language: str = 'zh_CN') -> str:
        """格式化报警消息"""
        messages = []
        
        # 处理控制器报警
        if controller_id != 0:
            info = self.get_alarm_info(controller_id, False, language)
            level_text = self.get_alarm_level_text(info['level'])
            messages.append(f"【控制器报警】[{level_text}] {info['description']}")
            if info['cause']:
                messages.append(f"  原因: {info['cause']}")
            if info['solution']:
                messages.append(f"  解决方案: {info['solution']}")
                
        # 处理伺服报警
        if servo_id != 0:
            info = self.get_alarm_info(servo_id, True, language)
            level_text = self.get_alarm_level_text(info['level'])
            messages.append(f"【伺服报警】[{level_text}] {info['description']}")
            if info['cause']:
                messages.append(f"  原因: {info['cause']}")
            if info['solution']:
                messages.append(f"  解决方案: {info['solution']}")
                
        return '\n'.join(messages) if messages else "无报警"


# 测试代码
if __name__ == "__main__":
    manager = AlarmManager()
    
    # 测试解析错误ID
    test_response = "0,{16,0},GetErrorID()"
    result = manager.parse_error_id(test_response)
    if result:
        controller_id, servo_id = result
        print(f"控制器报警ID: {controller_id}, 伺服报警ID: {servo_id}")
        
        # 获取报警信息
        message = manager.format_alarm_message(controller_id, servo_id)
        print("\n报警信息:")
        print(message)