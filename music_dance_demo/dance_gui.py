import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import time
import threading
from datetime import datetime
from config import Config


class DanceGUI:
    def __init__(self, robot_controller, audio_analyzer, dance_library):
        self.robot = robot_controller
        self.audio = audio_analyzer
        self.dance_lib = dance_library
        self.config = Config()
        
        self.root = tk.Tk()
        self.root.title("Dobot Nova 2 音乐舞蹈控制面板")
        self.root.geometry("1400x800")
        
        self.is_dancing = False
        self.dance_thread = None
        self.selected_music = None
        self.music_files = []
        self.current_move_name = "未开始"  # 当前舞蹈动作名称
        self.move_count = 0  # 已执行动作计数
        self.dance_start_time = None  # 舞蹈开始时间
        
        self._create_widgets()
        self._load_default_music()
        self._update_thread = threading.Thread(target=self._update_display, daemon=True)
        self._update_thread.start()
    
    def _load_default_music(self):
        default_folder = self.config.get_music_folder()
        if os.path.exists(default_folder):
            self._load_music_from_folder(default_folder)
    
    def _load_music_from_folder(self, folder):
        self.music_files = []
        try:
            for file in os.listdir(folder):
                if file.endswith(('.mp3', '.wav', '.ogg')):
                    self.music_files.append(os.path.join(folder, file))
            self._update_music_list()
            if self.music_files:
                self._log_status(f"已从 {folder} 加载 {len(self.music_files)} 个音乐文件")
        except Exception as e:
            self._log_status(f"加载音乐文件夹失败: {str(e)}")
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        
        self._create_control_panel(main_frame)
        self._create_music_panel(main_frame)
        self._create_current_move_panel(main_frame)
        self._create_info_panel(main_frame)
        self._create_test_panel(main_frame)
    
    def _create_control_panel(self, parent):
        control_frame = ttk.LabelFrame(parent, text="机器人控制", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        self.connect_btn = ttk.Button(control_frame, text="连接机器人", 
                                     command=self._connect_robot)
        self.connect_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.enable_btn = ttk.Button(control_frame, text="启用机器人", 
                                    command=self._enable_robot, state=tk.DISABLED)
        self.enable_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.disconnect_btn = ttk.Button(control_frame, text="断开连接", 
                                        command=self._disconnect_robot, state=tk.DISABLED)
        self.disconnect_btn.grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(control_frame, text="速度控制:").grid(row=1, column=0, padx=5, pady=5)
        # 从配置获取默认速度
        default_speed = self.config.get('default_speed', 50)
        self.speed_var = tk.IntVar(value=default_speed)
        self.speed_scale = ttk.Scale(control_frame, from_=10, to=100, 
                                    variable=self.speed_var, orient=tk.HORIZONTAL,
                                    command=self._update_speed)
        self.speed_scale.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.speed_label = ttk.Label(control_frame, text=f"{default_speed}%")
        self.speed_label.grid(row=1, column=3, padx=5, pady=5)
        
        self.emergency_btn = ttk.Button(control_frame, text="紧急停止", 
                                       command=self._emergency_stop,
                                       style="Emergency.TButton")
        self.emergency_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=10)
        
        self.clear_error_btn = ttk.Button(control_frame, text="清除报警", 
                                        command=self._clear_error, state=tk.DISABLED)
        self.clear_error_btn.grid(row=2, column=2, columnspan=2, padx=5, pady=10)
        
        self.home_btn = ttk.Button(control_frame, text="恢复原始位置", 
                                  command=self._return_to_home, state=tk.DISABLED)
        self.home_btn.grid(row=3, column=0, columnspan=4, padx=5, pady=5)
        
        style = ttk.Style()
        style.configure("Emergency.TButton", foreground="red")
    
    def _create_music_panel(self, parent):
        music_frame = ttk.LabelFrame(parent, text="音乐控制", padding="10")
        music_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        btn_frame = ttk.Frame(music_frame)
        btn_frame.grid(row=0, column=0, columnspan=2, pady=5)
        
        ttk.Button(btn_frame, text="选择音乐文件夹", 
                  command=self._select_music_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="添加音乐文件", 
                  command=self._add_music_file).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(music_frame, text="音乐列表:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        list_frame = ttk.Frame(music_frame)
        list_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        music_frame.rowconfigure(2, weight=1)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.music_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.music_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.music_listbox.bind('<<ListboxSelect>>', self._on_music_select)
        scrollbar.config(command=self.music_listbox.yview)
        
        control_frame = ttk.Frame(music_frame)
        control_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.play_btn = ttk.Button(control_frame, text="播放", 
                                  command=self._play_music, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = ttk.Button(control_frame, text="暂停", 
                                   command=self._pause_music, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="停止", 
                                  command=self._stop_music, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(music_frame, text="音量:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.volume_var = tk.DoubleVar(value=0.7)
        volume_scale = ttk.Scale(music_frame, from_=0, to=1, 
                                variable=self.volume_var, orient=tk.HORIZONTAL,
                                command=self._update_volume)
        volume_scale.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        
        self.dance_btn = ttk.Button(music_frame, text="开始跳舞", 
                                   command=self._toggle_dance, state=tk.DISABLED)
        self.dance_btn.grid(row=5, column=0, columnspan=2, pady=10)
    
    def _create_current_move_panel(self, parent):
        """创建当前动作显示面板"""
        move_frame = ttk.LabelFrame(parent, text="当前动作", padding="10")
        move_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 动作名称标签 - 大字体显示
        self.current_move_label = ttk.Label(move_frame, text="未开始", 
                                          font=('Arial', 24, 'bold'))
        self.current_move_label.pack(pady=(20, 10))
        
        # 动作描述标签
        self.move_description_label = ttk.Label(move_frame, text="等待开始跳舞...", 
                                              font=('Arial', 12))
        self.move_description_label.pack(pady=5)
        
        # 动作进度
        ttk.Label(move_frame, text="动作进度:").pack(anchor=tk.W, pady=(20, 5))
        self.move_progress = ttk.Progressbar(move_frame, mode='determinate')
        self.move_progress.pack(fill=tk.X, padx=10, pady=5)
        
        # 动作统计
        stats_frame = ttk.Frame(move_frame)
        stats_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Label(stats_frame, text="已执行动作:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.move_count_label = ttk.Label(stats_frame, text="0")
        self.move_count_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(stats_frame, text="舞蹈时长:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.dance_time_label = ttk.Label(stats_frame, text="00:00")
        self.dance_time_label.grid(row=1, column=1, sticky=tk.W, padx=5)
    
    def _create_info_panel(self, parent):
        info_frame = ttk.LabelFrame(parent, text="机器人信息", padding="10")
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(info_frame, height=10, width=40)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(info_frame, text="当前位置:").pack(anchor=tk.W, pady=(10, 0))
        self.position_label = ttk.Label(info_frame, text="X: 0, Y: 0, Z: 0, RX: 0, RY: 0, RZ: 0")
        self.position_label.pack(anchor=tk.W)
        
        ttk.Label(info_frame, text="音乐信息:").pack(anchor=tk.W, pady=(10, 0))
        self.music_info_label = ttk.Label(info_frame, text="未加载音乐")
        self.music_info_label.pack(anchor=tk.W)
        
        # 添加报警信息显示
        alarm_frame = ttk.LabelFrame(info_frame, text="报警信息", padding="5")
        alarm_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.alarm_text = scrolledtext.ScrolledText(alarm_frame, height=4, width=40,
                                                   foreground="orange", background="#f5f5f5")
        self.alarm_text.pack(fill=tk.BOTH, expand=True)
        
        error_frame = ttk.Frame(info_frame)
        error_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(error_frame, text="错误日志:").pack(side=tk.LEFT)
        ttk.Button(error_frame, text="清除", 
                  command=self._clear_errors).pack(side=tk.RIGHT)
        
        self.error_text = scrolledtext.ScrolledText(info_frame, height=5, width=40, 
                                                   foreground="red")
        self.error_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_test_panel(self, parent):
        test_frame = ttk.LabelFrame(parent, text="测试动作", padding="10")
        test_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        ttk.Label(test_frame, text="预设测试动作:").pack(anchor=tk.W, pady=5)
        
        test_moves = [
            ("挥手", "test_wave"),
            ("画圆", "test_circle"),
            ("点头", "test_nod"),
            ("摇头", "test_shake")
        ]
        
        for name, move_id in test_moves:
            btn = ttk.Button(test_frame, text=name, 
                           command=lambda m=move_id: self._perform_test_move(m))
            btn.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Separator(test_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Label(test_frame, text="舞蹈动作预览:").pack(anchor=tk.W, pady=5)
        
        dance_moves = [
            ("左右摆动", "wave_right"),
            ("上下摆动", "wave_up"),
            ("旋转", "spin"),
            ("8字形", "figure_eight"),
            ("快速跳动", "pump"),
            ("缓慢摇摆", "sway")
        ]
        
        for name, move_id in dance_moves:
            btn = ttk.Button(test_frame, text=name, 
                           command=lambda m=move_id: self._preview_dance_move(m))
            btn.pack(fill=tk.X, padx=5, pady=2)
    
    def _connect_robot(self):
        dialog = IPDialog(self.root, self.config.get_robot_ip())
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            ip = dialog.result
            self.config.set_robot_ip(ip)
            self.robot.ip = ip
            
            if self.robot.connect():
                self._log_status(f"成功连接到机器人 ({ip})")
                self.connect_btn.config(state=tk.DISABLED)
                self.enable_btn.config(state=tk.NORMAL)
                self.disconnect_btn.config(state=tk.NORMAL)
                self.clear_error_btn.config(state=tk.NORMAL)
                
                # 设置初始速度
                initial_speed = self.speed_var.get()
                self.robot.set_speed(initial_speed)
                self._log_status(f"初始速度设置为: {initial_speed}%")
            else:
                messagebox.showerror("连接失败", "无法连接到机器人")
    
    def _enable_robot(self):
        if self.robot.enable_robot():
            self._log_status("机器人已启用")
            self.enable_btn.config(state=tk.DISABLED)
            self.home_btn.config(state=tk.NORMAL)  # 启用恢复原始位置按钮
            
            # 启用后移动到初始位置
            self._log_status("正在移动到初始位置...")
            threading.Thread(target=self._move_to_home_async, daemon=True).start()
        else:
            messagebox.showerror("启用失败", "无法启用机器人")
    
    def _move_to_home_async(self):
        """异步移动到初始位置"""
        if self.robot.move_to_home_position():
            self.root.after(0, lambda: self._log_status("已到达初始位置"))
        else:
            self.root.after(0, lambda: self._log_status("移动到初始位置失败"))
    
    def _disconnect_robot(self):
        self.robot.disconnect()
        self._log_status("机器人已断开连接")
        self.connect_btn.config(state=tk.NORMAL)
        self.enable_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.clear_error_btn.config(state=tk.DISABLED)
        self.home_btn.config(state=tk.DISABLED)
    
    def _emergency_stop(self):
        self.is_dancing = False
        self.robot.emergency_stop()
        self._stop_music()
        self._log_status("紧急停止已触发")
    
    def _return_to_home(self):
        """恢复到原始位置"""
        if self.robot.is_enabled:
            try:
                self._log_status("正在恢复到原始位置...")
                # 使用基准位置（笛卡尔坐标）
                base_position = self.dance_lib.base_position
                self.robot.move_to_position(base_position)
                # 或者使用初始位置（关节角度）
                # self.robot.move_to_home_position()
                self._log_status("已恢复到原始位置")
            except Exception as e:
                self._log_error(f"恢复原始位置失败: {str(e)}")
                messagebox.showerror("错误", f"恢复原始位置失败: {str(e)}")
        else:
            messagebox.showwarning("未启用", "请先启用机器人")
    
    def _clear_error(self):
        """清除机器人报警"""
        try:
            if self.robot.is_connected:
                # 先获取并显示当前报警信息
                alarm_info = self.robot.get_alarm_info()
                if alarm_info['status'] == 'alarm':
                    self._log_status(f"当前报警: {alarm_info['message']}")
                
                # 清除错误
                self.robot.clear_robot_error()
                self._log_status("正在清除报警...")
                
                # 等待一下让清除生效
                time.sleep(0.5)
                
                # 重新获取报警信息
                new_alarm_info = self.robot.get_alarm_info()
                
                # 检查机器人状态
                status = self.robot.get_robot_status()
                mode = status.get('robot_mode', 'Unknown')
                self._log_status(f"机器人当前模式: {mode}")
                
                if new_alarm_info['status'] == 'normal':
                    self._log_status("报警已清除")
                    # 立即更新报警显示
                    self.alarm_text.delete(1.0, tk.END)
                    self.alarm_text.insert(1.0, "无报警")
                    self.alarm_text.config(foreground="green")
                    messagebox.showinfo("成功", "报警已清除")
                else:
                    self._log_status("报警清除失败，可能需要解决报警原因或重启控制柜")
                    messagebox.showwarning("警告", "报警清除失败，请检查报警原因或重启控制柜")
            else:
                messagebox.showerror("错误", "机器人未连接")
        except Exception as e:
            self._log_status(f"清除报警时出错: {str(e)}")
            messagebox.showerror("错误", f"清除报警失败: {str(e)}")
    
    def _update_speed(self, value):
        speed = int(float(value))
        self.speed_label.config(text=f"{speed}%")
        self.robot.set_speed(speed)
    
    def _update_volume(self, value):
        self.audio.set_volume(float(value))
    
    def _select_music_folder(self):
        folder = filedialog.askdirectory(initialdir=self.config.get_music_folder())
        if folder:
            self.config.set_music_folder(folder)
            self._load_music_from_folder(folder)
    
    def _add_music_file(self):
        files = filedialog.askopenfilenames(
            filetypes=[("音频文件", "*.mp3 *.wav *.ogg")]
        )
        if files:
            self.music_files.extend(files)
            self._update_music_list()
    
    def _update_music_list(self):
        self.music_listbox.delete(0, tk.END)
        for file in self.music_files:
            self.music_listbox.insert(tk.END, os.path.basename(file))
    
    def _on_music_select(self, event):
        selection = self.music_listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_music = self.music_files[index]
            self.play_btn.config(state=tk.NORMAL)
    
    def _play_music(self):
        if self.selected_music and self.audio.load_music(self.selected_music):
            self.audio.play()
            self.play_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.NORMAL)
            self.dance_btn.config(state=tk.NORMAL)
            
            tempo = self.audio.get_tempo()
            self.music_info_label.config(text=f"BPM: {tempo:.1f}")
            self._log_status(f"正在播放: {os.path.basename(self.selected_music)}")
    
    def _pause_music(self):
        self.audio.pause()
        self.play_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
    
    def _stop_music(self):
        self.audio.stop()
        self.play_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.dance_btn.config(state=tk.DISABLED, text="开始跳舞")
        self.is_dancing = False
    
    def _toggle_dance(self):
        if not self.is_dancing:
            self.is_dancing = True
            self.dance_btn.config(text="停止跳舞")
            self.move_count = 0  # 重置动作计数
            self.dance_start_time = time.time()  # 记录开始时间
            self.dance_thread = threading.Thread(target=self._dance_loop)
            self.dance_thread.start()
        else:
            self.is_dancing = False
            self.dance_btn.config(text="开始跳舞")
            # 重置显示
            self.current_move_label.config(text="未开始")
            self.move_description_label.config(text="等待开始跳舞...")
            self.move_progress['value'] = 0
    
    def _dance_loop(self):
        last_move = None
        move_start_time = time.time()
        
        while self.is_dancing and self.audio.is_playing:
            try:
                beat_strength = self.audio.get_current_beat_strength()
                frequency = self.audio.get_current_frequency_profile()
                
                current_move = self.dance_lib.select_move_by_music(beat_strength, frequency)
                
                if current_move != last_move:
                    last_move = current_move
                    move_start_time = time.time()
                    self.move_count += 1
                    
                    # 更新当前动作显示
                    move = self.dance_lib.get_move(current_move)
                    if move:
                        self.current_move_name = move.name
                        self.root.after(0, lambda: self._update_move_display(move))
                
                move = self.dance_lib.get_move(current_move)
                if move:
                    elapsed = time.time() - move_start_time
                    t = (elapsed / move.duration) % 1.0
                    position = move.get_position_at_time(t)
                    
                    # 更新进度条
                    progress = (t * 100) % 100
                    self.root.after(0, lambda p=progress: self._update_move_progress(p))
                    
                    self.robot.move_to_position(position)
                
                time.sleep(0.05)
                
            except Exception as e:
                self._log_error(f"舞蹈错误: {str(e)}")
                break
        
        # 舞蹈结束后，确保回到基准位置
        if self.robot.is_enabled:
            base_position = self.dance_lib.base_position
            self.robot.move_to_position(base_position)
            time.sleep(0.5)  # 等待机器人到达基准位置
        
        self.is_dancing = False
        self.dance_btn.config(text="开始跳舞")
    
    def _perform_test_move(self, move_id):
        if not self.robot.is_enabled:
            messagebox.showwarning("未启用", "请先启用机器人")
            return
        
        move = self.dance_lib.get_move(move_id)
        if move:
            self._log_status(f"执行测试动作: {move.description}")
            threading.Thread(target=self._execute_single_move, args=(move,)).start()
    
    def _preview_dance_move(self, move_id):
        if not self.robot.is_enabled:
            messagebox.showwarning("未启用", "请先启用机器人")
            return
        
        move = self.dance_lib.get_move(move_id)
        if move:
            self._log_status(f"预览舞蹈动作: {move.description}")
            threading.Thread(target=self._execute_single_move, args=(move,)).start()
    
    def _execute_single_move(self, move):
        start_time = time.time()
        duration = move.duration
        
        while time.time() - start_time < duration:
            t = (time.time() - start_time) / duration
            position = move.get_position_at_time(t)
            self.robot.move_to_position(position)
            time.sleep(0.05)
        
        # 确保执行最后一个关键帧（t=1.0），回到原始位置
        final_position = move.get_position_at_time(1.0)
        self.robot.move_to_position(final_position)
        time.sleep(0.5)  # 等待机器人到达最终位置
    
    def _update_display(self):
        while True:
            try:
                if self.robot.is_connected:
                    # 更新位置信息
                    pos = self.robot.get_current_position()
                    pos_text = f"X: {pos[0]:.1f}, Y: {pos[1]:.1f}, Z: {pos[2]:.1f}, "
                    pos_text += f"RX: {pos[3]:.1f}, RY: {pos[4]:.1f}, RZ: {pos[5]:.1f}"
                    self.position_label.config(text=pos_text)
                    
                    # 更新报警信息
                    alarm_info = self.robot.get_alarm_info()
                    if alarm_info['status'] == 'alarm':
                        self.alarm_text.delete(1.0, tk.END)
                        self.alarm_text.insert(1.0, alarm_info['message'])
                        self.alarm_text.config(foreground="red")
                    elif alarm_info['status'] == 'normal':
                        self.alarm_text.delete(1.0, tk.END)
                        self.alarm_text.insert(1.0, "无报警")
                        self.alarm_text.config(foreground="green")
                    
                    # 更新错误日志
                    errors = self.robot.get_recent_errors(5)
                    if errors:
                        error_text = "\n".join(errors)
                        self.error_text.delete(1.0, tk.END)
                        self.error_text.insert(1.0, error_text)
                    
                    # 更新舞蹈时长
                    if self.is_dancing and self.dance_start_time:
                        elapsed = time.time() - self.dance_start_time
                        minutes = int(elapsed // 60)
                        seconds = int(elapsed % 60)
                        self.dance_time_label.config(text=f"{minutes:02d}:{seconds:02d}")
                
                time.sleep(0.1)
            except:
                pass
    
    def _log_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
    
    def _log_error(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.error_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.error_text.see(tk.END)
    
    def _clear_errors(self):
        self.error_text.delete(1.0, tk.END)
        self.robot.clear_errors()
    
    def _update_move_display(self, move):
        """更新当前动作显示"""
        # 动作名称映射到中文
        move_names = {
            "wave_right": "左右摆动",
            "wave_up": "上下摆动",
            "spin": "旋转",
            "figure_eight": "8字形运动",
            "pump": "快速上下",
            "sway": "缓慢摇摆"
        }
        
        display_name = move_names.get(move.name, move.description)
        self.current_move_label.config(text=display_name)
        self.move_description_label.config(text=move.description)
        self.move_count_label.config(text=str(self.move_count))
    
    def _update_move_progress(self, progress):
        """更新动作进度条"""
        self.move_progress['value'] = progress
    
    def run(self):
        self.root.mainloop()

import tkinter.simpledialog as simpledialog


class IPDialog:
    def __init__(self, parent, initial_ip):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("连接机器人")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="请输入机器人IP地址:", font=('', 12)).pack(pady=10)
        
        self.ip_var = tk.StringVar(value=initial_ip)
        self.ip_entry = ttk.Entry(main_frame, textvariable=self.ip_var, 
                                 font=('', 14), width=20)
        self.ip_entry.pack(pady=10)
        self.ip_entry.focus()
        self.ip_entry.select_range(0, tk.END)
        
        quick_frame = ttk.Frame(main_frame)
        quick_frame.pack(pady=5)
        
        ttk.Label(quick_frame, text="快速选择:").pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="192.168.1.198", 
                  command=lambda: self.ip_var.set("192.168.1.198")).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="LAN1 (192.168.5.1)", 
                  command=lambda: self.ip_var.set("192.168.5.1")).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="LAN2 (192.168.100.1)", 
                  command=lambda: self.ip_var.set("192.168.100.1")).pack(side=tk.LEFT, padx=2)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="连接", command=self._ok, 
                  width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self._cancel, 
                  width=10).pack(side=tk.LEFT, padx=5)
        
        self.dialog.bind('<Return>', lambda e: self._ok())
        self.dialog.bind('<Escape>', lambda e: self._cancel())
        
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_x() + (parent.winfo_width() - 400) // 2,
            parent.winfo_y() + (parent.winfo_height() - 200) // 2
        ))
    
    def _ok(self):
        self.result = self.ip_var.get().strip()
        self.dialog.destroy()
    
    def _cancel(self):
        self.dialog.destroy()