#!/usr/bin/env python

import threading
import tkinter as tk
from time import sleep

import RPi.GPIO as GPIO
from gpiozero import CPUTemperature, exc
from simple_pid import PID

TACH_PIN = 17
FAN_PWM_PIN = 18
FAN_PWM_FEQUENCY = 1000

DESIRED_TEMPERATURE = 35  # In celsius

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
    # Attach the Tach Falling Edge Event method
    GPIO.add_event_detect(TACH_PIN, GPIO.FALLING, TachFallingEdgeDetectedEvent)

    degree_sign = u"\N{DEGREE SIGN}"

    global is_running
    while is_running:
        global tach_counter
        tach_counter = 0        
        sleep(1)
        currentTemperature = cpu.temperature
        print(f'Temperature = {currentTemperature:.2f}' + degree_sign + 'C')
        fan_duty_cycle = pid(currentTemperature)
        print(f'Duty Cycle = {fan_duty_cycle:.0f}%')
        pwm.ChangeDutyCycle(fan_duty_cycle)
        print(f'RPMs = {tach_counter * 30:d} rpm')

    GPIO.remove_event_detect(TACH_PIN)
    GPIO.cleanup()
    print("Exiting the Control Loop")

if __name__ == "__main__":
    is_running = True;
    controlLoopThread = threading.Thread(target=controlLoop)
    controlLoopThread.start();

    try:
        mywindow = tk.Tk()
        mywindow.title('Fan Control')
        mywindow.geometry('400x300')
        mywindow.mainloop()
    except KeyboardInterrupt:
        print('Interrupted')

    is_running = False;
    controlLoopThread.join(1.2)
