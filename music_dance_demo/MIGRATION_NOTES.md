# 音乐舞蹈Demo V3到V4迁移说明

## 迁移日期
2025-08-04

## 主要变更

### 1. API结构变化
- **V3**: 使用独立的 `DobotApiMove` 类处理运动命令
- **V4**: 运动命令集成到 `DobotApiDashboard` 类中

### 2. 连接方式变化
- **V3**: 需要建立三个独立连接（Dashboard、Move、Feed）
- **V4**: 只需要建立两个连接（Dashboard、Feed）

### 3. 方法调用变化
- `send_recv_msg()` → 直接调用对应方法
  - `dashboard.send_recv_msg("EnableRobot()")` → `dashboard.EnableRobot()`
  - `dashboard.send_recv_msg("ClearError()")` → `dashboard.ClearError()`
  - `dashboard.send_recv_msg("SpeedL(100)")` → `dashboard.VelL(100)`
  - `dashboard.send_recv_msg("SpeedJ(100)")` → `dashboard.VelJ(100)`
  
- 运动命令参数变化
  - `MovL(x,y,z,rx,ry,rz)` → `MovL(x,y,z,rx,ry,rz,coordinateMode)`
  - `MovJ(j1,j2,j3,j4,j5,j6)` → `MovJ(j1,j2,j3,j4,j5,j6,coordinateMode)`
  - coordinateMode: 0=笛卡尔坐标，1=关节坐标

- 其他方法名变化
  - `MoveStop()` → `Stop()`
  - `SpeedL()` → `VelL()`
  - `SpeedJ()` → `VelJ()`

### 4. 属性名变化
- `feed.socket_feed` → `feed.socket_dobot`
- `feed_data['tool_vector_actual']` → `feed_data['ToolVectorActual']`

### 5. 新增功能
- 添加了本地日志记录功能
  - 日志保存在 `music_dance_demo/logs/` 目录
  - 包含详细的错误信息和调试信息
  - 同时输出到控制台和文件

## 运行方式
```bash
cd TCP-IP-Python-V4/music_dance_demo
python main.py --ip <机器人IP地址>
```

## 测试命令
```bash
# 测试导入
python test_v4.py

# 无界面连接测试
python main.py --ip <机器人IP地址> --no-gui

# 完整GUI运行
python main.py --ip <机器人IP地址>
```

## 故障排除
1. 如遇到连接错误，请检查日志文件：`logs/robot_controller_YYYYMMDD_HHMMSS.log`
2. 确保机器人IP地址正确且网络可达
3. 确保机器人已开启TCP/IP模式