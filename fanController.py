#!/usr/bin/env python

import threading
import tkinter as tk
from time import monotonic, sleep

import RPi.GPIO as GPIO
from gpiozero import CPUTemperature
from simple_pid import PID

TACH_PIN = 17
FAN_PWM_PIN = 18
FAN_PWM_FEQUENCY = 1000

DESIRED_TEMPERATURE = 35  # In celsius

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
    pid = PID(-10, -1, -0.5)
    pid.setpoint = DESIRED_TEMPERATURE
    pid.output_limits = (0, 100)
    pid.sample_time = 1.0
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

        pid.setpoint = DESIRED_TEMPERATURE
        fan_duty_cycle = pid(current_temperature)
        lbl_duty_cycle["text"] = f'Duty Cycle = {fan_duty_cycle:.0f}%'
        pwm.ChangeDutyCycle(fan_duty_cycle)
        lbl_rpm["text"] = f'RPMs = {current_tach_counter * 30:d} rpm'

        sleep_time = 1.0 - (monotonic() - begin_time)
        sleep(sleep_time)

    GPIO.remove_event_detect(TACH_PIN)
    GPIO.cleanup()
    print("Exiting the Control Loop")

def increase():
    global DESIRED_TEMPERATURE
    if (DESIRED_TEMPERATURE < 100):
        DESIRED_TEMPERATURE += 1
    displaySetPoint(DESIRED_TEMPERATURE)

def decrease():
    global DESIRED_TEMPERATURE
    if (DESIRED_TEMPERATURE > 0):
        DESIRED_TEMPERATURE -= 1
    displaySetPoint(DESIRED_TEMPERATURE)

def displaySetPoint(setpoint: int):
    lbl_setpoint["text"] = f'Set Point = {setpoint:d}' + degree_sign

if __name__ == "__main__":
    try:
        mywindow = tk.Tk()
        mywindow.title('Fan Control')
        #mywindow.geometry('50x16+0+36')
        global lbl_setpoint
        lbl_setpoint = tk.Label(text=f'Set Point = {DESIRED_TEMPERATURE:d}' + degree_sign, font=("Arial 14 bold"))
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
        lbl_rpm = tk.Label(text="RPMs = 0", font=("Arial 14 bold"))
        lbl_rpm.pack()
        #tk.Button(text="quit", font=('Courier', 18), command=quit).pack()
        #mywindow.overrideredirect(1)

        is_running = True
        controlLoopThread = threading.Thread(target=controlLoop)
        controlLoopThread.start()

        mywindow.mainloop()
        print('Finished')
    except KeyboardInterrupt:
        print('Interrupted')

    is_running = False
    if (controlLoopThread.isAlive == True):
        controlLoopThread.join(2.0)
