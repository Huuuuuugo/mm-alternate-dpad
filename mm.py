import pyautogui
import xinput_wrapper as xinput
from pynput.keyboard import Key, Controller
import pygetwindow as gw
from pygetwindow import PyGetWindowException
import threading
import time
import os

keyboard = Controller()
ocarina = False


def getOcarinaState():
    global ocarina
    wait = 1/3
    while True:
        screen_shot = pyautogui.screenshot(region=(765, 25, 115, 695))
        # screen_shot = pyautogui.screenshot()
        try:
            if pyautogui.locate("B_Stop.png", screen_shot, confidence=0.75):
                ocarina = True
                print("Found 'B_Stop.png'")
        except pyautogui.ImageNotFoundException:
            try:
                if pyautogui.locate("c.png", screen_shot, confidence=0.75):
                    ocarina = True
                    print("Found 'c.png'")
            except pyautogui.ImageNotFoundException:
                ocarina = False
        time.sleep(wait)


def sendInput():
    global ocarina
    wait = 1/40
    while True:
        while True:
            gamepads = xinput.GamepadControls.list_gamepads()
            if not len(gamepads):
                time.sleep(1)
                break
            with gamepads[0] as gamepad_input:
                buttons = gamepad_input.get_button()
                try:
                    act_win = gw.getActiveWindowTitle()
                except PyGetWindowException:
                    print("WHY DOES THIS FUNCTION KEEPS SUDDENLY TRHOWING DIFFERENT ERRORS?????")
                    pass
                if type(act_win) == str and 'RetroArch' not in act_win:
                    for button in buttons:
                        if buttons[button]:
                            try:
                                win = gw.getWindowsWithTitle('RetroArch')[0]
                                win.activate()
                            except IndexError:
                                pass
                # 1: up, 2: down, 3: left, 4: right
                if ocarina:
                    keyboard.release('w')
                    keyboard.release('s')
                    keyboard.release('a')
                    keyboard.release('d')
                    if buttons[1]:
                        keyboard.press(Key.up)
                    else:
                        keyboard.release(Key.up)
                    if buttons[2]:
                        keyboard.press(Key.down)
                    else:
                        keyboard.release(Key.down)
                    if buttons[3]:
                        keyboard.press(Key.left)
                    else:
                        keyboard.release(Key.left)
                    if buttons[4]:
                        keyboard.press(Key.right)
                    else:
                        keyboard.release(Key.right)
                else:
                    keyboard.release(Key.up)
                    keyboard.release(Key.down)
                    keyboard.release(Key.left)
                    keyboard.release(Key.right)
                    if buttons[1]:
                        keyboard.press('w')
                    else:
                        keyboard.release('w')
                    if buttons[2]:
                        keyboard.press('s')
                    else:
                        keyboard.release('s')
                    if buttons[3]:
                        keyboard.press('a')
                    else:
                        keyboard.release('a')
                    if buttons[4]:
                        keyboard.press('d')
                    else:
                        keyboard.release('d')
                time.sleep(wait)


T_getOcarinaState = threading.Thread(target=getOcarinaState, daemon=True)
T_sendInput = threading.Thread(target=sendInput, daemon=True)

print("RUNNING, EXIT RETROARCH TO STOP\n")

# wait for retroarch to open
timeout = 5
count = 0
while count <= timeout:
    try:
        gw.getWindowsWithTitle('RetroArch')[0]
        break
    except IndexError:
        pass
    time.sleep(1)
    count += 1

T_getOcarinaState.start()
T_sendInput.start()

T_getOcarinaState.join(0)
T_sendInput.join(0)

if count <= timeout:
    while True:
        if not T_sendInput.is_alive():
            T_sendInput = None
            T_sendInput = threading.Thread(target=sendInput, daemon=True)
            T_sendInput.start()
            T_sendInput.join(0)
        if not T_getOcarinaState.is_alive():
            T_getOcarinaState = None
            T_getOcarinaState = threading.Thread(target=getOcarinaState, daemon=True)
            T_getOcarinaState.start()
            T_getOcarinaState.join(0)
            
        # check if retroarch still running
        try:
            gw.getWindowsWithTitle('RetroArch')[0]
        except IndexError:
            os.system("taskkill /FI \"WINDOWTITLE eq Majora's Mask.txt*\" /T")
            break
        time.sleep(3)