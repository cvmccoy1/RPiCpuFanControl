# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RPiCpuFanControl is a Raspberry Pi CPU fan controller with a Tkinter GUI. It reads CPU temperature via `gpiozero`, runs a PID control loop to vary fan speed via PWM on GPIO 18, and counts tachometer pulses on GPIO 17 to display RPM. A live Matplotlib chart shows the last 60 seconds of temperature and duty cycle.

## Running the Application

```bash
# Run directly (requires Raspberry Pi hardware and GPIO access)
python3 fanController.py
```

There is no build step — this is a plain Python 3 application.

## Autostart

The app autostarts via `~/.config/autostart/fan.desktop` (desktop session autostart), which launches `fanController.py` directly when the Pi desktop loads. This is the correct approach for a GUI app — the systemd service (`fancontrol.service`) is intentionally disabled because system services run before a display is available.

## Installation

The production install path is `/usr/local/projects/RPiCpuFanControl/`. The config file is read from that fixed path (`CONFIGURATION_FILE` constant in `fanController.py`). See `scripts/readme.txt` for full installation steps including systemd service setup.

## Architecture

The app runs two concurrent threads:

- **Main thread** — Tkinter GUI: displays temperature, duty cycle %, and RPM labels; up/down buttons to adjust setpoint; Matplotlib chart embedded via `FigureCanvasTkAgg`.
- **Control loop thread** — 1-second loop: reads CPU temp, counts tach pulses, runs the PID controller (`simple_pid`), writes PWM duty cycle, and calls back into the GUI to update labels and chart data.

GPIO pin assignments (defined as module-level constants in `fanController.py`):
- `FAN_PWM_PIN = 18` — PWM output to fan (1 kHz)
- `TACH_PIN = 17` — Tachometer pulse input

## Configuration

`config.ini` (INI format, `[configuration]` section) stores:
- `set_point` — target CPU temperature in °C
- `kp`, `ki`, `kd` — PID gains

The GUI writes updated setpoint values back to `config.ini` when the user presses the up/down buttons.

## Dependencies

Not in a requirements.txt; install manually:
```bash
pip3 install matplotlib simple-pid gpiozero
sudo apt-get install -y pigpiod
sudo systemctl enable pigpiod && sudo systemctl start pigpiod
```
`tkinter` and `configparser` are standard library.

`pigpiod` is the GPIO backend used by `gpiozero` (via `PiGPIOFactory`). `RPi.GPIO` is not used — it breaks on kernel 6.x because `/proc/cpuinfo` no longer includes the `Hardware` field it requires for Pi detection.

## Key Files

- `fanController.py` — entire application (GUI + control loop)
- `formattedSpinbox.py` — small custom Tkinter spinbox widget used by the GUI
- `config.ini` — runtime configuration (PID gains, setpoint)
- `scripts/fancontrol.service` — systemd unit for autostart
- `scripts/readme.txt` — installation guide
