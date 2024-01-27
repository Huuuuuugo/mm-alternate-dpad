import pyautogui
import xinput_wrapper as xinput
from pynput.keyboard import Key, Controller
import pygetwindow as gw
from pygetwindow import PyGetWindowException
import threading
import time
import os
import cv2

keyboard = Controller()
ocarina = False


def getOcarinaState():
    global ocarina
    wait = 1/3
    i = 0
    b_img = cv2.imread("B_Stop.png")
    c_img = cv2.imread("c.png")
    while True:
        time.sleep(0.2)
        scale_tbl =  [1, 0.99, 0.985, 0.97, 0.965]
        scale = scale_tbl[i]
        ofst_y = 25*(scale_tbl.index(scale)+1)
        ndl_scale = pow(scale, scale_tbl.index(scale)+1)
        screen_shot = pyautogui.screenshot(region=(int(765*scale), int(ofst_y), int(115*scale), int(695*scale))) #OG

        h = int(b_img.shape[0]*ndl_scale)
        w = int(b_img.shape[1]*ndl_scale)
        new_scale = (w, h)
        b_scaled = cv2.resize(b_img, new_scale, interpolation = cv2.INTER_AREA)

        h = int(c_img.shape[0]*ndl_scale)
        w = int(c_img.shape[1]*ndl_scale)
        new_scale = (w, h)

        *_, alpha = cv2.split(c_img)
        gray_layer = cv2.cvtColor(c_img, cv2.COLOR_BGR2GRAY)
        dst = cv2.merge((gray_layer, gray_layer, gray_layer, alpha))
        c_scaled = cv2.resize(dst, new_scale, interpolation=cv2.INTER_AREA)
        try:
            if pyautogui.locate(b_scaled, screen_shot, confidence=0.70):
                ocarina = True
                print("Found 'B_Stop.png'")
                time.sleep(wait)
                continue
        except pyautogui.ImageNotFoundException:
            try:
                if pyautogui.locate(c_scaled, screen_shot, confidence=0.70):
                    ocarina = True
                    print("Found 'c.png'")
                    time.sleep(wait)
                    continue
            except pyautogui.ImageNotFoundException:
                ocarina = False
        if i == 4:
            time.sleep(wait)
            i = 0
        else:
            i += 1


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