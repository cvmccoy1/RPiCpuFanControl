#!/usr/bin/env python

import threading
import tkinter as tk
from time import monotonic, sleep

import RPi.GPIO as GPIO
from gpiozero import CPUTemperature
from simple_pid import PID
import configparser

TACH_PIN = 17
FAN_PWM_PIN = 18
FAN_PWM_FEQUENCY = 1000
DUTY_CYCLE_MIN = 0
DUTY_CYCLE_MAX = 100

PID_SAMPLE_TIME = 1.0  # In seconds 

# Default PID arguments...actual values to be retrieved from the ini file
desired_temperature = 35  # In celsius
kp = 10.0
ki = 1.0
kd = 0.5

degree_sign = "℃"
up_arrow = "▲"
down_arrow = "▼"

def TachFallingEdgeDetectedEvent(n):
    global tach_counter
    tach_counter += 1 

def controlLoop():
    print("Starting the Control Loop")
    # Set up the GPIO Pins
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(TACH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(FAN_PWM_PIN, GPIO.OUT)
    # Set up the PID object
    kp = getPidKValue('p')
    ki = getPidKValue('i')
    kd = getPidKValue('d')
    print(f'kp = {kp}; ki = {ki}; kd = {kd}')
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
        lbl_temperature["text"] = f'Temperature = {current_temperature:.2f}' + degree_sign

        pid.setpoint = desired_temperature
        fan_duty_cycle = pid(current_temperature)
        lbl_duty_cycle["text"] = f'Duty Cycle = {fan_duty_cycle:.0f}%'
        pwm.ChangeDutyCycle(fan_duty_cycle)
        lbl_rpm["text"] = f'Fan Running at {current_tach_counter * 30:d} rpm'

        sleep_time = 1.0 - (monotonic() - begin_time)
        sleep(sleep_time)

    GPIO.remove_event_detect(TACH_PIN)
    GPIO.cleanup()
    print("Exiting the Control Loop")

def increase():
    global desired_temperature
    if (desired_temperature < 100):
        desired_temperature += 1
        setSetPoint(desired_temperature)
    displaySetPoint(desired_temperature)

def decrease():
    global desired_temperature
    if (desired_temperature > 0):
        desired_temperature -= 1
        setSetPoint(desired_temperature)
    displaySetPoint(desired_temperature)

def displaySetPoint(setpoint: int):
    lbl_setpoint["text"] = f'Set Point = {setpoint:d}' + degree_sign

ini_file = './config.ini'
choices = configparser.ConfigParser()

def getSetPoint() -> int:
    choices.read(ini_file)
    return choices.getint('configuration', 'set_point')

def setSetPoint(setpoint:int):
    config_file = open(ini_file, "w")
    choices.set('configuration', 'set_point', str(setpoint))
    choices.write(config_file)
    config_file.close()

def getPidKValue(k_value:str) -> float:
    choices.read(ini_file)
    return choices.getfloat('configuration', 'k' + k_value)

if __name__ == "__main__":
    try:
        mywindow = tk.Tk()
        mywindow.title('Fan Control')
        #mywindow.geometry('50x16+0+36')

        desired_temperature = getSetPoint()
        global lbl_setpoint
        lbl_setpoint = tk.Label(text=f'Set Point = {desired_temperature:d}' + degree_sign, font=("Arial 14 bold"))
        lbl_setpoint.pack()

        btn_decrease = tk.Button(master=mywindow, text=down_arrow, command=decrease)
        #btn_decrease.grid(row=0, column=0, sticky="nsew")
        btn_decrease.pack()

        btn_increase = tk.Button(master=mywindow, text=up_arrow, command=increase)
        #btn_increase.grid(row=0, column=2, sticky="nsew")
        btn_increase.pack()

        global lbl_temperature
        lbl_temperature = tk.Label(text="Temperature = 0", font=("Arial 14 bold"))
        lbl_temperature.pack()
        global lbl_duty_cycle
        lbl_duty_cycle = tk.Label(text="Duty Cycle = 0", font=("Arial 14 bold"))
        lbl_duty_cycle.pack()
        global lbl_rpm
        lbl_rpm = tk.Label(text="Fan Running at 0 rpm", font=("Arial 14 bold"))
        lbl_rpm.pack()
        #tk.Button(text="quit", font=('Courier', 18), command=quit).pack()
        #mywindow.overrideredirect(1)

        # Start up the fan controller thread
        is_running = True
        controlLoopThread = threading.Thread(target=controlLoop)
        controlLoopThread.start()

        # Start up the window's event loop...will not return until the window is closed
        mywindow.mainloop()
        print('Exiting Mainloop')
    except KeyboardInterrupt:
        print('Interrupted')

    # Stop the fan controller thread and wait for it to exit
    is_running = False
    print('Waiting for Control Loop to Exit')
    controlLoopThread.join(2.0)

    print('Exiting Program')
