import sys
import os
import time
import threading
import queue
import logging
from datetime import datetime
from typing import List, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dobot_api import DobotApiDashboard, DobotApiFeedBack, MyType
from config import Config
from alarm_manager import AlarmManager
from singularity_checker import SingularityChecker

class RobotController:
    def __init__(self, ip: str):
        self.ip = ip
        self.config = Config()
        self.alarm_manager = AlarmManager()
        self.singularity_checker = SingularityChecker()
        
        # 设置日志
        self._setup_logger()
        self.dashboard_port = 29999
        self.feed_port = 30004
        
        self.dashboard = None
        self.feed = None
        
        self.is_connected = False
        self.is_enabled = False
        self.current_position = [0, 0, 0, 0, 0, 0]
        self.error_log = []
        self.move_history = []
        
        self.feed_thread = None
        self.stop_feed = False
        self.position_lock = threading.Lock()
        
        self.move_queue = queue.Queue()
        self.move_thread = None
        self.stop_move = False
        
        # 速度设置
        self.current_speed = self.config.get('default_speed', 50)  # 默认速度50%
    
    def _setup_logger(self):
        """设置日志记录器"""
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_filename = os.path.join(log_dir, f'robot_controller_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        self.logger = logging.getLogger('RobotController')
        self.logger.setLevel(logging.DEBUG)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        
        self.logger.info(f"日志文件创建: {log_filename}")
    
    def connect(self) -> bool:
        try:
            self.logger.info(f"正在连接到机器人 {self.ip}...")
            self.dashboard = DobotApiDashboard(self.ip, self.dashboard_port)
            self.logger.info(f"Dashboard连接成功 (端口 {self.dashboard_port})")
            
            self.feed = DobotApiFeedBack(self.ip, self.feed_port)
            self.logger.info(f"Feed连接成功 (端口 {self.feed_port})")
            
            self.is_connected = True
            
            self.feed_thread = threading.Thread(target=self._feed_worker)
            self.feed_thread.daemon = True
            self.feed_thread.start()
            
            self.move_thread = threading.Thread(target=self._move_worker)
            self.move_thread.daemon = True
            self.move_thread.start()
            
            return True
        except Exception as e:
            error_msg = f"Connection error: {str(e)} - {type(e)}"
            self.error_log.append(error_msg)
            self.logger.error(f"连接失败: {str(e)} - {type(e)}")
            self.logger.debug(f"详细错误信息: {error_msg}", exc_info=True)
            self.is_connected = False
            
            # 清理已建立的连接
            if hasattr(self, 'dashboard') and self.dashboard:
                try:
                    self.dashboard.close()
                except:
                    pass
            if hasattr(self, 'feed') and self.feed:
                try:
                    self.feed.close()
                except:
                    pass
                    
            return False
    
    def disconnect(self):
        self.stop_feed = True
        self.stop_move = True
        
        if self.feed_thread:
            self.feed_thread.join(timeout=2)
        if self.move_thread:
            self.move_thread.join(timeout=2)
        
        if self.dashboard:
            self.dashboard.close()
        if self.feed:
            self.feed.close()
        
        self.is_connected = False
    
    def enable_robot(self) -> bool:
        if not self.is_connected:
            return False
        
        try:
            # 启用机器人
            result = self.dashboard.EnableRobot()
            self.logger.debug(f"EnableRobot result: {result}")
            time.sleep(1)
            
            # 清除可能存在的错误
            self.dashboard.ClearError()
            time.sleep(0.5)
            
            # 设置速度和加速度（使用当前速度设置）
            self.dashboard.VelL(self.current_speed)
            self.dashboard.AccL(self.current_speed)
            self.dashboard.VelJ(self.current_speed)
            self.dashboard.AccJ(self.current_speed)
            
            self.is_enabled = True
            self.logger.info("机器人启用成功")
            return True
        except Exception as e:
            error_msg = f"Enable error: {str(e)}"
            self.error_log.append(error_msg)
            self.logger.error(error_msg)
            return False
    
    def disable_robot(self):
        if self.is_connected and self.dashboard:
            try:
                self.dashboard.DisableRobot()
                self.is_enabled = False
            except Exception as e:
                error_msg = f"Disable error: {str(e)}"
                self.error_log.append(error_msg)
                self.logger.error(error_msg)
    
    def _feed_worker(self):
        while not self.stop_feed:
            try:
                data = bytes()
                while len(data) < 1440:
                    chunk = self.feed.socket_dobot.recv(1440 - len(data))
                    if not chunk:
                        break
                    data += chunk
                
                if len(data) == 1440:
                    feed_data = np.frombuffer(data, dtype=MyType)
                    if len(feed_data) > 0:
                        with self.position_lock:
                            self.current_position = [
                                feed_data['ToolVectorActual'][0][0],
                                feed_data['ToolVectorActual'][0][1],
                                feed_data['ToolVectorActual'][0][2],
                                feed_data['ToolVectorActual'][0][3],
                                feed_data['ToolVectorActual'][0][4],
                                feed_data['ToolVectorActual'][0][5]
                            ]
            except Exception as e:
                if not self.stop_feed:
                    error_msg = f"Feed error: {str(e)}"
                    self.error_log.append(error_msg)
                    self.logger.error(error_msg)
                    self.logger.debug(f"Feed线程详细错误", exc_info=True)
            
            time.sleep(0.008)
    
    def _move_worker(self):
        while not self.stop_move:
            try:
                if not self.move_queue.empty():
                    position = self.move_queue.get(timeout=0.1)
                    if self.is_enabled:
                        self._execute_move(position)
                else:
                    time.sleep(0.01)
            except queue.Empty:
                pass
            except Exception as e:
                error_msg = f"Move worker error: {str(e)}"
                self.error_log.append(error_msg)
                self.logger.error(error_msg)
    
    def _execute_move(self, position: List[float]):
        try:
            # 检查目标位置是否安全
            is_safe, warnings = self.singularity_checker.is_position_safe(position)
            if not is_safe:
                self.logger.warning(f"目标位置可能不安全: {warnings}")
                # 可以选择跳过不安全的位置或使用MovJ
                # 这里我们记录警告但继续执行，让机器人自己的保护机制处理
                
            x, y, z, rx, ry, rz = position
            # MovL 使用 speed 参数来控制速度
            self.dashboard.MovL(x, y, z, rx, ry, rz, 0, speed=self.current_speed)
            
            move_cmd = f"MovL({x},{y},{z},{rx},{ry},{rz},speed={self.current_speed})"
            self.move_history.append({
                'time': time.time(),
                'position': position,
                'command': move_cmd
            })
            self.logger.debug(f"执行移动命令: {move_cmd}")
            
            if len(self.move_history) > 1000:
                self.move_history = self.move_history[-500:]
                
        except Exception as e:
            error_msg = f"Move execution error: {str(e)}"
            self.error_log.append(error_msg)
            self.logger.error(error_msg)
            self.logger.debug(f"移动位置: {position}", exc_info=True)
    
    def move_to_position(self, position: List[float]):
        if self.is_enabled:
            self.move_queue.put(position)
    
    def move_to_home_position(self):
        """移动到初始位置"""
        if self.is_enabled:
            try:
                # 从配置中获取初始位置
                home_config = self.config.get_home_position()
                home_joints = home_config.get("joints", [0, 45, 45, 0, 90, 0])
                
                self.logger.info(f"正在移动到初始位置: {home_joints}")
                self.move_j(home_joints)
                time.sleep(3)  # 等待移动完成
                self.logger.info("已到达初始位置")
                return True
            except Exception as e:
                error_msg = f"移动到初始位置失败: {str(e)}"
                self.error_log.append(error_msg)
                self.logger.error(error_msg)
                return False
        return False
    
    def move_j(self, joint_positions: List[float]):
        if self.is_enabled and len(joint_positions) == 6:
            try:
                j1, j2, j3, j4, j5, j6 = joint_positions
                # MovJ 使用 v 参数来控制速度
                self.dashboard.MovJ(j1, j2, j3, j4, j5, j6, 1, v=self.current_speed)
                self.logger.debug(f"执行MovJ命令，速度: {self.current_speed}%")
            except Exception as e:
                error_msg = f"MovJ error: {str(e)}"
                self.error_log.append(error_msg)
                self.logger.error(error_msg)
    
    def get_current_position(self) -> List[float]:
        with self.position_lock:
            return self.current_position.copy()
    
    def get_current_speed(self) -> int:
        """获取当前速度设置"""
        return self.current_speed
    
    def set_speed(self, speed: int):
        """设置机器人移动速度（1-100%）"""
        if self.is_connected and self.dashboard:
            try:
                speed = max(1, min(100, speed))
                self.current_speed = speed
                
                # 立即应用新速度
                self.dashboard.VelL(speed)
                self.dashboard.VelJ(speed)
                self.dashboard.AccL(speed)
                self.dashboard.AccJ(speed)
                
                self.logger.info(f"速度设置为: {speed}%")
            except Exception as e:
                error_msg = f"Set speed error: {str(e)}"
                self.error_log.append(error_msg)
                self.logger.error(error_msg)
    
    def emergency_stop(self):
        if self.is_connected:
            try:
                while not self.move_queue.empty():
                    self.move_queue.get_nowait()
                
                if self.dashboard:
                    self.dashboard.Stop()
            except Exception as e:
                error_msg = f"Emergency stop error: {str(e)}"
                self.error_log.append(error_msg)
                self.logger.error(error_msg)
    
    def get_robot_status(self) -> dict:
        status = {
            'connected': self.is_connected,
            'enabled': self.is_enabled,
            'position': self.get_current_position(),
            'queue_size': self.move_queue.qsize(),
            'error_count': len(self.error_log)
        }
        
        if self.is_connected and self.dashboard:
            try:
                robot_mode = self.dashboard.RobotMode()
                status['robot_mode'] = robot_mode
            except:
                status['robot_mode'] = "Unknown"
        
        return status
    
    def get_recent_errors(self, count: int = 10) -> List[str]:
        return self.error_log[-count:] if self.error_log else []
    
    def clear_errors(self):
        self.error_log.clear()
        if self.is_connected and self.dashboard:
            try:
                self.dashboard.ClearError()
            except:
                pass
    
    def get_error_id(self):
        """获取当前错误ID"""
        if self.is_connected and self.dashboard:
            try:
                result = self.dashboard.GetErrorID()
                self.logger.debug(f"GetErrorID result: {result}")
                return result
            except Exception as e:
                self.logger.error(f"获取错误ID失败: {str(e)}")
                return "Unknown"
        return "Not connected"
    
    def get_alarm_info(self) -> dict:
        """获取详细的报警信息"""
        if not self.is_connected:
            return {'status': 'disconnected', 'message': '机器人未连接'}
            
        try:
            # 获取错误ID
            error_response = self.get_error_id()
            
            # 解析错误ID
            error_ids = self.alarm_manager.parse_error_id(error_response)
            if error_ids:
                controller_id, servo_id = error_ids
                
                # 格式化报警消息
                alarm_message = self.alarm_manager.format_alarm_message(controller_id, servo_id)
                
                return {
                    'status': 'alarm' if (controller_id != 0 or servo_id != 0) else 'normal',
                    'controller_id': controller_id,
                    'servo_id': servo_id,
                    'message': alarm_message,
                    'raw_response': error_response
                }
            else:
                return {
                    'status': 'unknown',
                    'message': '无法解析错误ID',
                    'raw_response': error_response
                }
                
        except Exception as e:
            self.logger.error(f"获取报警信息失败: {str(e)}")
            return {
                'status': 'error',
                'message': f'获取报警信息失败: {str(e)}'
            }
    
    def clear_robot_error(self):
        """清除机器人报警"""
        if self.is_connected and self.dashboard:
            try:
                result = self.dashboard.ClearError()
                self.logger.info(f"清除报警结果: {result}")
                return True
            except Exception as e:
                error_msg = f"清除报警失败: {str(e)}"
                self.error_log.append(error_msg)
                self.logger.error(error_msg)
                return False
        return False

import numpy as np