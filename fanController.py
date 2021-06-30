#!/usr/bin/python3

import threading
import tkinter as tk
from time import monotonic, sleep

import RPi.GPIO as GPIO
from gpiozero import CPUTemperature
from simple_pid import PID
import configparser
#from formattedSpinbox import FormattedSpinbox

TACH_PIN = 17
FAN_PWM_PIN = 18
FAN_PWM_FEQUENCY = 1000

DESIRED_TEMPERATURE_DEFAULT = 35  # In celsius
DESIRED_TEMPERATURE_MIN = 0
DESIRED_TEMPERATURE_MAX = 100

DUTY_CYCLE_MIN = 0
DUTY_CYCLE_MAX = 100

PID_SAMPLE_TIME = 1.0  # In seconds 

# Default PID arguments...actual values to be retrieved from the ini file
KP_DEFAULT = 10.0
KI_DEFAULT = 1.0
KD_DEFAULT = 0.5

CONFIGURATION_FILE = "/home/pi/Projects/Python/config.ini"
config_parser = configparser.ConfigParser()

degree_sign = "℃"
up_arrow = "▲"
down_arrow = "▼"

desired_temperature = DESIRED_TEMPERATURE_DEFAULT

def TachFallingEdgeDetectedEvent(n):
    global tach_counter
    tach_counter += 1 

def ControlLoop():
    print("Starting the Control Loop")
    # Set up the GPIO Pins
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(TACH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(FAN_PWM_PIN, GPIO.OUT)
    # Set up the PID object
    kp = GetPidKValueFromConfigFile('p')
    ki = GetPidKValueFromConfigFile('i')
    kd = GetPidKValueFromConfigFile('d')
    pid = PID(-kp, -ki, -kd)  # use negative value sinces we want to have the reverse effect (i.e. cooling)
    pid.setpoint = desired_temperature
    pid.output_limits = (DUTY_CYCLE_MIN, DUTY_CYCLE_MAX)
    pid.sample_time = PID_SAMPLE_TIME
    # Set up the CPU Temperature object
    cpu = CPUTemperature()
    # Set up PWM on the Fan Pin
    pwm = GPIO.PWM(FAN_PWM_PIN, FAN_PWM_FEQUENCY)
    pwm.start(0)

    global tach_counter
    tach_counter = 0  
    # Attach the Tach Falling Edge Event method
    GPIO.add_event_detect(TACH_PIN, GPIO.FALLING, TachFallingEdgeDetectedEvent)

    global is_running
    while is_running:
        begin_time = monotonic()
        current_tach_counter = tach_counter
        tach_counter = 0

        current_temperature = cpu.temperature
        DisplayTemperature(cpu.temperature)

        pid.setpoint = desired_temperature
        fan_duty_cycle = pid(current_temperature)
        DisplayFanDutyCycle(fan_duty_cycle)
        pwm.ChangeDutyCycle(fan_duty_cycle)
        DisplayFanSpeed(current_tach_counter)

        sleep_time = PID_SAMPLE_TIME - (monotonic() - begin_time)
        sleep(sleep_time)

    GPIO.remove_event_detect(TACH_PIN)
    GPIO.cleanup()
    print("Exiting the Control Loop")

def DisplayTemperature(temperature:float):
    lbl_temperature["text"] = f'Temperature = {temperature:.0f}' + degree_sign

def DisplayFanDutyCycle(duty_cycle:float):
    lbl_duty_cycle["text"] = f'Duty Cycle = {duty_cycle:.0f}%'

def DisplayFanSpeed(tach_counter):
    lbl_rpm["text"] = f'Fan Speed = {tach_counter * 30:d} rpm'

def DisplaySetPoint(setpoint: int):
    lbl_setpoint["text"] = f'Set Point = {setpoint:.0f}' + degree_sign

def UpArrowClickedEvent():
    global desired_temperature
    if (desired_temperature < DESIRED_TEMPERATURE_MAX):
        desired_temperature += 1
        SetSetPointInConfigFile(desired_temperature)
    DisplaySetPoint(desired_temperature)

def DownArrowClickedEvent():
    global desired_temperature
    if (desired_temperature > DESIRED_TEMPERATURE_MIN):
        desired_temperature -= 1
        SetSetPointInConfigFile(desired_temperature)
    DisplaySetPoint(desired_temperature)

def GetSetPointFromConfigFile() -> int:
    config_parser.read(CONFIGURATION_FILE)
    return config_parser.getint('configuration', 'set_point')

def SetSetPointInConfigFile(setpoint:int):
    config_file = open(CONFIGURATION_FILE, "w")
    config_parser.set('configuration', 'set_point', str(setpoint))
    config_parser.write(config_file)
    config_file.close()

def GetPidKValueFromConfigFile(k_value:str) -> float:
    config_parser.read(CONFIGURATION_FILE)
    return config_parser.getfloat('configuration', 'k' + k_value)

if __name__ == "__main__":
    try:
        # Create and Populate the Main Window
        root = tk.Tk()
        root.title('Fan Control')
        root.geometry('250x120')
        frame = tk.Frame(root)
        frame.grid(columnspan=3, rowspan=4, padx=7, pady=7)

        # Create the Setpoint label and Up/Down buttons
        desired_temperature = GetSetPointFromConfigFile()
        global lbl_setpoint
        lbl_setpoint = tk.Label(master=frame, font=("Arial 14 bold"))
        lbl_setpoint.grid(column=0, row=0, sticky="w")
        DisplaySetPoint(desired_temperature)

        btn_increase = tk.Button(master=frame, text=up_arrow, font=("Arial 8 bold"), height=1, width=1, command=UpArrowClickedEvent)
        btn_increase.grid(row=0, column=1, sticky="w", padx=(5,0))

        btn_decrease = tk.Button(master=frame, text=down_arrow, font=("Arial 8 bold"), height=1, width=1, command=DownArrowClickedEvent)
        btn_decrease.grid(row=0, column=2, sticky="w")

        # Create the Current Temperature label
        global lbl_temperature
        lbl_temperature = tk.Label(master=frame, font=("Arial 14 bold"))
        lbl_temperature.grid(row=2, column=0, columnspan=3, sticky="w", pady=(5,0))

        # Create the Fan Duty Cycle label
        global lbl_duty_cycle
        lbl_duty_cycle = tk.Label(master=frame, font=("Arial 14 bold"))
        lbl_duty_cycle.grid(row=3, column=0, columnspan=3, sticky="w")

        # Create the Fan Speed (RPM) label
        global lbl_rpm
        lbl_rpm = tk.Label(master=frame, font=("Arial 14 bold"))
        lbl_rpm.grid(row=4, column=0, columnspan=3, sticky="w")

        # Start up the fan controller thread
        is_running = True
        controlLoopThread = threading.Thread(target=ControlLoop)
        controlLoopThread.start()

        # Start up the window's event loop...will not return until the window is closed
        root.mainloop()
        print('Exiting Mainloop')
    except KeyboardInterrupt:
        print('Interrupted')

    # Stop the fan controller thread and wait for it to exit
    is_running = False
    print('Waiting for Control Loop to Exit')
    controlLoopThread.join(2.0)

    print('Exiting Program')
