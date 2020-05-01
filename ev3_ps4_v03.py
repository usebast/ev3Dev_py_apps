#!/usr/bin/env python3

__author__ = 'Sebastiaans adaptations after a Artur Poznanski program.'
## also thanks for help to https://gist.github.com/Quantum357 ##

## Import libraries ##
import evdev
import ev3dev.auto as ev3
import threading
import time

## Some helpers ##
def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

def scale(val, src, dst):
    return (float(val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0]

def scale_stick(value):
    return scale(value,(0,255),(-500,500))

def dc_clamp(value):
    return clamp(value,-500,500)

## Initializing ##
print("Finding ps4 controller...")
devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
ps4dev = devices[0].fn

gamepad = evdev.InputDevice(ps4dev)

forward_speed = 0
side_speed = 0
grab_speed = 0
running = True

## The Motors ##
class MotorThread(threading.Thread):
    def __init__(self):
        self.right_motor = ev3.LargeMotor(ev3.OUTPUT_C)
        self.left_motor = ev3.LargeMotor(ev3.OUTPUT_B)
        self.claw_motor = ev3.MediumMotor(ev3.OUTPUT_A)
        threading.Thread.__init__(self)

    def run(self):
        print("Engine running! for Stefan")
        while running:
            self.right_motor.run_forever(speed_sp=dc_clamp(forward_speed+side_speed))
            self.left_motor.run_forever(speed_sp=dc_clamp(-forward_speed+side_speed))
            self.claw_motor.run_forever(speed_sp=dc_clamp(grab_speed))
        self.right_motor.stop()
        self.left_motor.stop()
        self.claw_motor.stop()

motor_thread = MotorThread()
motor_thread.setDaemon(True)
motor_thread.start()

## The PS4 Controller Mapping ##

for event in gamepad.read_loop():   #this loops infinitely
    # map the controller left analog stick to the two driving motors
    if event.type == 3:             #left stick is moved
        if event.code == 0:         #X axis on left stick
            forward_speed = -scale_stick(event.value)
        if event.code == 1:         #Y axis on left stick
            side_speed = scale_stick(event.value)
        if side_speed < 100 and side_speed > -100:
            side_speed = 0
        if forward_speed < 100 and forward_speed > -100:
            forward_speed = 0

    # map the controller right analog stick to the grab claw/LargeMotor
    if event.type == 3:
        if event.code == 2:
            grab_speed = scale_stick(event.value)
        if grab_speed < 100 and -grab_speed > -100:
            grab_speed = 0
    if event.type == 3:
        if event.code == 4:
            grab_speed = -scale_stick(event.value)
        if grab_speed < 100 and grab_speed > -100:
            grab_speed = 0

    # button O exits the Program
    if event.type == 1 and event.code == 305 and event.value == 1:
        print("X button is pressed. Stopping.")
        running = False
        time.sleep(0.5) # Wait for the motor thread to finish
        break 