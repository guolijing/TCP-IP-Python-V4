import json
import os


class Config:
    def __init__(self):
        self.config_file = "dance_config.json"
        self.default_config = {
            "robot_ip": "192.168.1.198",
            "music_folder": os.path.join(os.path.dirname(__file__), "music"),
            "default_speed": 50,
            "default_volume": 0.7,
            "home_position": {
                "joints": [0, 45, 45, 0, 90, 0],  # J1-J6的角度
                "description": "机器人初始位置（关节角度）"
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    config = self.default_config.copy()
                    config.update(loaded_config)
                    return config
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self.default_config.copy()
        else:
            return self.default_config.copy()
    
    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()
    
    def get_robot_ip(self):
        return self.config.get("robot_ip", self.default_config["robot_ip"])
    
    def set_robot_ip(self, ip):
        self.set("robot_ip", ip)
    
    def get_music_folder(self):
        folder = self.config.get("music_folder", self.default_config["music_folder"])
        # 创建音乐文件夹如果不存在
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except:
                pass
        return folder
    
    def set_music_folder(self, folder):
        self.set("music_folder", folder)
    
    def get_home_position(self):
        return self.config.get("home_position", self.default_config["home_position"])
    
    def set_home_position(self, joints):
        self.set("home_position", {"joints": joints, "description": "用户自定义初始位置"})