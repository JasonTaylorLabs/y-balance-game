# Y-Balance Game Sensor System

This directory contains the complete codebase for the Y-Balance Game, a physical balance and reaction game using laser distance sensors, an Arduino Mega, and a Raspberry Pi running a Pygame UI. This guide explains the project, its components, and how to debug or extend the system.

---

## Project Overview

- **Purpose:** A physical game where players move a slider to match targets in three directions, using real-time feedback from laser distance sensors.
- **Hardware:**
  - Arduino Mega (reads 3 laser sensors, streams data)
  - Raspberry Pi (runs the game UI and logic)
- **Software:**
  - `y_balance_game.ino` (Arduino firmware)
  - `sensors.py` (Python serial interface)
  - `main.py` (Pygame game logic/UI)

---

## System Architecture

```
[Laser Sensors] --(UART)--> [Arduino Mega] --(USB Serial, CSV)--> [Raspberry Pi]
                                                    |
                                                [sensors.py]
                                                    |
                                                [main.py]
```
- **Arduino** reads sensors and streams their values as CSV over USB.
- **Raspberry Pi** runs Python code to read, process, and display the game.

---

## File Outline

### 1. `y_balance_game.ino` (Arduino Mega)
- Reads three U8xLaser distance sensors.
- Streams readings as CSV (`ID,value`) over USB serial.
- Accepts ON/OFF commands to power sensors up/down.
- Sends command feedback (e.g., `1OFF OK`).
- Reports sensor faults as `-99.99`.

### 2. `sensors.py` (Python)
- Provides the `LaserArray` class.
- Connects to Arduino serial port, reads and parses sensor data.
- Maintains latest mm readings for each sensor.
- Handles serial errors and timeouts robustly.

### 3. `main.py` (Python)
- Main game logic and UI using Pygame.
- Reads sensor data via `LaserArray`.
- Provides configuration UI and game mode.
- Handles all user interaction, scoring, and feedback.
- Robust error handling and user-friendly alerts.

---

## API & Method Reference

### `y_balance_game.ino` (Arduino)
- **`setup()`**: Initializes serial, pins, sensors.
- **`loop()`**: Main loop; handles commands, reads sensors, streams data.
- **`readCMFast(laser, pwrenPin)`**: Returns latest reading in cm, or -1.0 if off/fault.
- **`sendCommandFeedback(cmd)`**: Sends confirmation string to host.

### `sensors.py` (Python)
- **Class: `LaserArray`**
  - **`__init__(port, baud)`**: Opens serial port, starts background reader.
  - **`_reader()`**: (private) Thread; reads/parses serial data, updates readings.
  - **`read_distance(idx, timeout=2.0)`**: Returns latest mm reading for sensor 0/1/2, or None if stale/unavailable.

### `main.py` (Python)
- **`show_alert(message, title)`**: Displays a modal error dialog.
- **`load_image(path, fallback_color, size)`**: Loads an image or returns a fallback surface.
- **`reset_game(stage_val=1, start_timer=False)`**: Resets all game state for a new stage or game.
- **`apply_chart_values()`**: Applies user-edited chart/config values.
- **`draw_target_and_slider(i, deg, display_mm, target_mm, unlocked)`**: Draws a target and slider for a direction.
- **`update_and_draw_confetti(dt)`**: Handles confetti animation at game end.
- **`draw_chart()`**: Renders the configuration UI.
- **`draw_game(dt)`**: Renders the main game UI and logic.

---

## How the System Works

1. **Startup:**
   - Arduino powers up, initializes sensors, and waits for commands.
   - Raspberry Pi runs `main.py`, which initializes the UI and attempts to connect to the Arduino via `sensors.py`.
2. **Sensor Data Flow:**
   - Arduino streams sensor readings as CSV over USB serial.
   - `sensors.py` reads and parses these, making latest values available to the game.
3. **Game Play:**
   - User configures game parameters in the chart UI.
   - In game mode, user moves the slider to match targets; must hold within tolerance for a set time.
   - Game tracks progress, time, and score; displays confetti and results at the end.
4. **Error Handling:**
   - If sensors or assets fail to load, user is shown a clear alert and the program exits or recovers gracefully.
   - Sensor faults (e.g., unplugged) are reported as `-99.99` and handled in the UI.

---

## Debugging & Extension Tips

- **To debug sensor data:**
  - Use the serial monitor on Arduino to see raw output.
  - Print or log `LaserArray.dist` and `LaserArray.last_update` in Python.
- **To add new features:**
  - Add new UI elements or game logic in `main.py`.
  - Add new sensor types or logic in `sensors.py`.
  - For new hardware, update `y_balance_game.ino`.
- **Common issues:**
  - Serial port not found: Check cable, permissions, or port name in `sensors.py`.
  - Sensor always reads `-99.99`: Check wiring, power, or sensor health.
  - UI assets missing: Ensure all images are in the `assets/` directory.
- **Error messages and alerts** are designed to be user-friendly and actionable.

---

## Glossary
- **Slider:** The physical part the player moves, tracked by the laser sensors.
- **Target:** The goal position for the slider in each direction.
- **Tolerance:** How close the slider must be to the target to count as a success.
- **Hold Time:** How long the slider must stay within tolerance to unlock a direction.

---

## Contact
For further help or to contribute, contact Mark Rowley or refer to the code comments and this guide.