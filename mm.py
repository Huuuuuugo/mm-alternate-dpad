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
        high < 1000 or high > 15000):
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


def searchLines(image):
    last_red_pixel_pos = [] # pos: y, x
    bin_img = np.array(image)
    for i, line in enumerate(bin_img):
        for j, pixel in enumerate(line):
            # print(pixel)
            if pixel[0] > 100 and pixel[1] < 50 and pixel[2] < 50:
                bin_img[i][j] = [255, 255, 255]
                last_red_pixel_pos = [i, j]
            else:
                bin_img[i][j] = [0, 0, 0]
    # cv.imwrite("other/__binary.png", bin_img)

    ofst = 0
    while ofst <= 200:
        height = bin_img[0:, ofst:ofst+1]
        lines = []
        line = [0, 0]
        get_line = 0

        # get occurences of possible lines on the image
        if np.count_nonzero(height) < 40:
            ofst += 10
            continue
        for i, x in enumerate(height):
            # print(i, x)
            # input()
            if not get_line and x[0][0]:
                line[0] = i
                line[1] = i
                # print(line)
                get_line = 1
            elif get_line and not x[0][0]:
                line[1] = i-1
                # print(line)
                lines.append(line.copy())
                get_line = 0
        # print(lines)
        if len(lines) < 4:
            ofst += 10
            continue

        density = 0
        while len(lines) == 4:
            rtrn = True
            for line in lines:
                width = bin_img[line[0]:line[1], ofst:ofst+60]
                # cv.imwrite("other/__width.png", width)
                line_height = line[1]-line[0]
                if not line_height:
                    rtrn = False
                    break
                density = (np.count_nonzero(width)//3)/(line_height*60)
                # print(ofst, line, density)
                # input()
                if density < 0.4:
                    rtrn = False
                    break
            if rtrn:
                return True, last_red_pixel_pos
            break
        ofst += 10
    return False, last_red_pixel_pos


def getOcarinaState():
    global ocarina
    wait = 1/10
    count = 1
    img1 = cv.imread('B_Stop.png',cv.IMREAD_GRAYSCALE)
    kp1, b_img = sift.detectAndCompute(img1,None)
    while True:
        if not ocarina:
            # print(ocarina)
            lrp_pos = [0, 0]
            screen = pyautogui.screenshot(region=(755, 25, 125, 200))
            screen = np.array(screen)
            # cv.imwrite("other/__screen.png", screen)
            ocarina = searchBStop(screen, b_img)
            if ocarina:
                continue

            if count >= 15:
                screen2 = pyautogui.screenshot(region=(1000, 720, 180, 260))
                ocarina, lrp_pos = searchLines(screen2)
                count = 1
            else:
                count += 1
                time.sleep(wait)
        else:
            screen = np.array(pyautogui.screenshot(region=(785, 840, 1, 240)))
            gray = cv.cvtColor(screen, cv.COLOR_RGB2GRAY)
            # cv.imwrite("__gray.png", gray)

            # gets initial value for textbox_check
            if lrp_pos[0]:
                screen2 = np.array(pyautogui.screenshot(region=(1000+lrp_pos[1], 720+lrp_pos[0], 1, 1)))
                # cv.imwrite("other/__lrp.png", screen2)
                textbox_check = [screen2[0][0], None]
            else:
                textbox_check = [screen[0][0], None]
            # print(textbox_check[0])

            #gets initial value for the size of the black bar
            for i, x in enumerate(reversed(gray)):
                if x[0]:
                    size = i
                    break

            while True: 
                # print(ocarina)   
                screen = np.array(pyautogui.screenshot(region=(785, 840, 1, 240)))
                gray = cv.cvtColor(screen, cv.COLOR_RGB2GRAY)
                # cv.imwrite("other/__gray.png", gray)

                # gets current texbox_check value
                if lrp_pos[0]:
                    screen2 = np.array(pyautogui.screenshot(region=(1000+lrp_pos[1], 720+lrp_pos[0], 1, 1)))
                    # cv.imwrite("other/__lrp.png", screen2)
                    textbox_check[1] = screen2[0][0]
                    # check if new texbox_check value is darker than before
                    for i in range(3):
                        old = textbox_check[0][i]
                        new = textbox_check[1][i]
                        if new < old//2:
                            # print("Textbox")
                            ocarina = False
                            break
                    if not ocarina:
                        break
                else:
                    textbox_check[1] = screen[0][0]
                    # check if new texbox_check value is darker than before
                    for i in range(3):
                        old = textbox_check[0][i]
                        new = textbox_check[1][i]
                        if new < old//2:
                            # print("Textbox")
                            ocarina = False
                            break
                    if not ocarina:
                        break

                    # check if new texbox_check is now red
                    r, g, b = textbox_check[1][0], textbox_check[1][1], textbox_check[1][2]
                    if r > 100 and g < 50 and b < 50:
                        print("Textbox RED")
                        ocarina = False
                        break

                # gets current size of black bar
                for i, x in enumerate(reversed(gray)):
                    # print(i, x[0])
                    if x[0]:
                        new_size = i
                        break
                print(size, new_size)
                if size != new_size:
                    # print("Black bar")
                    ocarina = False
                    break
                time.sleep(5*wait)

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