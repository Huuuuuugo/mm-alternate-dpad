from pynput.keyboard import Key, Controller
import pygetwindow as gw
import time

keyboard = Controller()


timeout = 3*4
count = 0
while count <= timeout:
    try:
        win = gw.getWindowsWithTitle("Majora's Mask.txt")[0]
        win.activate()
        break
    except IndexError:
        pass
    time.sleep(1/4)
    count += 1

if count >= timeout:
    exit()


with keyboard.pressed(Key.ctrl):
    with keyboard.pressed(Key.cmd):
        keyboard.press('t')
        time.sleep(1/2)
        keyboard.release('t')
