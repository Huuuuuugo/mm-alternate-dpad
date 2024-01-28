import pyautogui
import xinput_wrapper as xinput
from pynput.keyboard import Key, Controller
import numpy as np
import cv2 as cv
import pygetwindow as gw
import threading
import time
import os

keyboard = Controller()
sift = cv.SIFT_create()
bf = cv.BFMatcher()
ocarina = False


def searchBStop(haystack_img, needle_img):
    # avoid error on sift.detectAndCompute
    gray = cv.cvtColor(np.array(haystack_img), cv.COLOR_RGB2GRAY)
    low = 25000 - np.count_nonzero(gray >= 5)
    high = np.count_nonzero(gray >= 127)
    # print("B low: ", low)
    # print("B high: ", high)
    if (low < 1000 or low > 16000 or
        high < 2500 or high > 15000):
        # print("Caught")
        # input()
        return False
    kp3, haystack = sift.detectAndCompute(haystack_img,None)
    matches = bf.knnMatch(needle_img, haystack, k=2)
    # print(len(matches))

    count = 0
    for m,n in matches:
        # print(m,n)
        
        if m.distance < 0.6*n.distance:
            return True
        count += 1
        if count > 5:
            break
    return False


def searchLines(gray_img, thresh_val: float):
    ofst = 0
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (40,5))
    thresh = cv.threshold(gray_img, thresh_val, 255, cv.THRESH_BINARY)[1]
    morph = cv.morphologyEx(thresh, cv.MORPH_RECT, kernel)
    # cv.imwrite("other/__thresh.png", thresh)
    # cv.imwrite("other/__morph.png", morph)
    while ofst <= 280:
        height = morph[0:, ofst:ofst+1]
        # cv2.imwrite("other/__height.png", height)
        lines = []
        line = [0, 0]
        get_line = 0

        # get occurences of possible lines on the image
        for i, x in enumerate(height):
            # print(i, x)
            # input()
            if not get_line and x[0]:
                line[0] = i
                line[1] = i
                # print(line)
                get_line = 1
            elif get_line and not x[0]:
                line[1] = i-1
                # print(line)
                lines.append(line.copy())
                get_line = 0
        # print(lines)
        if len(lines) < 4:
            ofst += 20
            continue
        # limit line height to avoid catching huge white stains
        remove = []
        for i, line in enumerate(lines):
            line_height = line[1]-line[0]
            # print(line, line_height)
            if line_height < 2 or line_height > 12:
                remove.append(i)
        for i, n in enumerate(remove):
            lines.pop(n-i)
        # print(ofst, "height lim: ", lines, len(lines))

        # keep only lines within a limit of spacing between them
        remove = []
        for i, _ in enumerate(lines):
            # print(lines[i])
            if not i:
                if len(lines) < 2:
                    break
                prv = lines[i][0] - 0
                nxt = lines[i+1][0] - lines[i][1]
            elif i == len(lines)-1:
                prv = lines[i][0] - lines[i-1][1]
                nxt = 280 - lines[i][1]
            else:
                prv = lines[i][0] - lines[i-1][1]
                nxt = lines[i+1][0] - lines[i][1]
            # print(prv, nxt, (prv < 18 or prv > 38) and (nxt < 18 or nxt > 38))
            if (prv < 18 or prv > 38) and (nxt < 18 or nxt > 38):
                remove.append(i)
        for i, n in enumerate(remove):
            lines.pop(n-i)
        # print(ofst, "spacing lim: ", lines, len(lines))

        # get density of white pixels do define if it's a vaid line
        density = 0
        while len(lines) == 4:
            rtrn = True
            for line in lines:
                width = morph[line[0]:line[1], ofst:]
                # cv.imwrite("other/__width.png", width)
                line_height = line[1]-line[0]
                density = (np.count_nonzero(width))/(line_height*(400-ofst))
                # print(ofst, line, density)
                # input()
                if density < 0.4:
                    rtrn = False
                    break
            if rtrn:
                cv.imwrite("other/__morph.png", morph)
                cv.imwrite("other/__gray.png", gray_img)
                return True
            break
        ofst += 20
    return False


def getOcarinaState():
    global ocarina
    wait = 1/3
    img1 = cv.imread('B_Stop.png',cv.IMREAD_GRAYSCALE)
    kp1, b_img = sift.detectAndCompute(img1,None)
    while True:
        if not ocarina:
            print(ocarina)
            screen = pyautogui.screenshot(region=(755, 25, 125, 200))
            screen = cv.cvtColor(np.array(screen), cv.COLOR_RGB2BGR)
            # cv.imwrite("other/__screen.png", screen)
            ocarina = searchBStop(screen, b_img)
            if ocarina:
                continue

            screen = pyautogui.screenshot(region=(780, 750, 400, 280))
            gray = cv.cvtColor(np.array(screen), cv.COLOR_RGB2GRAY)
            for num in [20, 30, 40]:
                ocarina = searchLines(gray, num)
            time.sleep(wait)
        else:
            screen = pyautogui.screenshot(region=(750, 0, 1, 240))
            gray = cv.cvtColor(np.array(screen), cv.COLOR_RGB2GRAY)
            # cv.imwrite("__gray.png", gray)
            for i, x in enumerate(gray):
                if x[0]:
                    size = i
                    break
            while True: 
                print(ocarina)   
                screen = pyautogui.screenshot(region=(750, 0, 1, 240))
                gray = cv.cvtColor(np.array(screen), cv.COLOR_RGB2GRAY)
                # cv.imwrite("__gray.png", gray)
                for i, x in enumerate(gray):
                    if x[0]:
                        new_size = i
                        break
                # print(size, new_size)
                if size != new_size:
                    ocarina = False
                    break
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
                except gw.PyGetWindowException:
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