# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a music-synchronized dance demo for the Dobot Nova 2 robotic arm. The system analyzes music in real-time and translates audio features into robot movements.

## Development Commands

### Running the Application
```bash
# Run with GUI (default mode)
python main.py

# Specify robot IP address
python main.py --ip 192.168.1.198

# Test mode without GUI
python main.py --no-gui
```

### Testing
```bash
# Test module imports
python test_v4.py

# Test dance move safety (all moves return to base position)
python test_moves_safety.py

# Test alarm manager
python alarm_manager.py
```

### Suppress API Debug Output
The dobot_api.py prints "ErrorId is -7" messages. To suppress:
```bash
python main.py --ip 192.168.1.198 2>/dev/null
```

## Architecture

### Core Component Relationships
- `main.py` → `dance_gui.py` → `robot_controller.py` → `dobot_api.py`
- `dance_gui.py` → `audio_analyzer.py` → Music analysis using librosa
- `dance_gui.py` → `dance_moves.py` → Movement definitions
- `robot_controller.py` → `alarm_manager.py` → Error handling

### Key API Differences (V4 vs V3)
- Movement commands are in `DobotApiDashboard` (not separate `DobotApiMove`)
- Method names: `SpeedL()` → `VelL()`, `SpeedJ()` → `VelJ()`
- `MovL/MovJ` require coordinateMode parameter (0=Cartesian, 1=Joint)
- Feedback attribute: `feed.socket_feed` → `feed.socket_dobot`
- Field name: `tool_vector_actual` → `ToolVectorActual`

### Robot Communication
- Dashboard Port: 29999 (control commands)
- Feedback Port: 30004 (real-time position data)
- Default IP: 192.168.1.198

### Movement System
All dance movements follow this pattern:
1. Start at base position: `[-350, 0, 200, 180, 0, 0]`
2. Execute movement keyframes
3. Return to base position

This ensures safety and prevents position drift during continuous operation.

### Configuration
`dance_config.json` stores:
- Robot IP address
- Music folder path
- Default speed (1-100%)
- Home position (6 joint angles)

### Alarm System
- Controller alarms: `/files/alarmController.json` (341 definitions)
- Servo alarms: `/files/alarmServo.json` (46 definitions)
- Real-time monitoring via `GetErrorID()`
- Clear alarms with `ClearError()`

## Common Tasks

### Adding New Dance Moves
1. Edit `dance_moves.py`
2. Add movement in `_create_basic_moves()` or `_create_test_moves()`
3. Ensure first and last keyframes use `self.base_position`
4. Add move name to `get_dance_moves()` or `get_test_moves()`

### Modifying Robot Speed
- GUI: Use speed slider (10-100%)
- Code: `robot_controller.set_speed(speed_percentage)`
- Config: Set `default_speed` in `dance_config.json`

### Handling Robot Errors
1. Check alarm display in GUI for detailed error message
2. Click "清除报警" (Clear Alarm) button
3. If persistent, check `logs/robot_controller_*.log`
4. Common fixes:
   - Reduce movement angles in `dance_moves.py`
   - Lower speed setting
   - Ensure robot isn't near singularity points

## Important Notes

- The robot must be in TCP/IP control mode (not teaching mode)
- All movements use MovL with coordinateMode=0 (Cartesian)
- Joint movements use MovJ with coordinateMode=1
- Logs are saved in `logs/` directory with timestamps
- Audio analysis runs in a separate thread to avoid blocking