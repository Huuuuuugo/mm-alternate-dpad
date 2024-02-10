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
    #TODO: figure out why exactly knnMatch raises exceptions when image has too many similar pixels
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
    try:
        kp3, haystack = sift.detectAndCompute(haystack_img,None)
        matches = bf.knnMatch(needle_img, haystack, k=2)
        # print(len(matches))
    except cv.error:
        return False
    count = 0
    # print(matches, len(matches))
    if len(matches[0]) < 2:
        return False
    for m,n in matches:
        # print(m,n)
        if m.distance < 0.7*n.distance:
            return True
        count += 1
        if count > 5:
            break
    return False


def searchLines(image):
    last_red_pixel_pos = [0, 0] # pos: y, x
    bin_img = np.array(image)
    min_y = len(bin_img)*0.35
    # cv.imwrite("other/__binary.png", bin_img)
    for y, line in enumerate(bin_img):
        if y > min_y and not last_red_pixel_pos[0]:
            return False, last_red_pixel_pos
        for x, pixel in enumerate(line):
            # print(pixel)
            if pixel[0] > 100 and pixel[1] < 50 and pixel[2] < 50:
                bin_img[y][x] = [255, 255, 255]
                last_red_pixel_pos = [y, x]
            else:
                bin_img[y][x] = [0, 0, 0]

    ofst = 0
    while ofst <= 200:
        height = bin_img[0:, ofst:ofst+1]
        lines = []
        line = [0, 0]
        get_line = 0

        # get occurences of possible lines on the image
        if np.count_nonzero(height) < 40:
            ofst += 20
            continue
        for i, x in enumerate(height):
            # print(i, x)
            # input()
            if not get_line and x[0][0]: # get white pixel and set it's position it to line[0]
                line[0] = i
                line[1] = i
                # print(line)
                get_line = 1
            elif get_line and not x[0][0]: # get black pixel and set previous position as line[1]
                line[1] = i-1
                # print(line)
                if line[0] != line[1]:
                    lines.append(line.copy())
                get_line = 0
        # print(lines)
        if len(lines) != 4:
            ofst += 20
            continue

        density = 0
        rtrn = True
        for line in lines:
            width = bin_img[line[0]:line[1], ofst:ofst+60]
            # cv.imwrite("other/__width.png", width)
            line_height = line[1]-line[0]
            density = (np.count_nonzero(width)//3)/(line_height*60)
            # print(ofst, line, density)
            # input()
            if density < 0.4:
                rtrn = False
                break
        if rtrn:
            return True, last_red_pixel_pos
        ofst += 20
    return False, last_red_pixel_pos


def getOcarinaState():
    global ocarina
    wait = 1/8
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

            if count >= 16:
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
                        # print("Textbox RED")
                        ocarina = False
                        break

                # gets current size of black bar
                for i, x in enumerate(reversed(gray)):
                    # print(i, x[0])
                    if x[0]:
                        new_size = i
                        break
                # print(size, new_size)
                if size != new_size:
                    # print("Black bar")
                    ocarina = False
                    break
                time.sleep(4*wait)

def sendInput():
    global ocarina
    wait = 1/40
    toggle = 0
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
                    if toggle:
                        keyboard.release('w')
                        keyboard.release('s')
                        keyboard.release('a')
                        keyboard.release('d')
                        toggle = 0
                    keyboard.touch(Key.up, buttons[1])
                    keyboard.touch(Key.down, buttons[2])
                    keyboard.touch(Key.left, buttons[3])
                    keyboard.touch(Key.right, buttons[4])
                else:
                    if not toggle:
                        keyboard.release(Key.up)
                        keyboard.release(Key.down)
                        keyboard.release(Key.left)
                        keyboard.release(Key.right)
                        toggle = 1
                    keyboard.touch('w', buttons[1])
                    keyboard.touch('s', buttons[2])
                    keyboard.touch('a', buttons[3])
                    keyboard.touch('d', buttons[4])
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
        time.sleep(5)