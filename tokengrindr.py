import pyautogui as pag
import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import os
import signal

pag.FAILSAFE = True  # move mouse to upper left to auto abort
pag.PAUSE = 0.25

screenshot_path = 'ss.png'
screen_h = 1080 #1050  # osx
screen_w = 1920 #1680  # osx
test_ss = pag.screenshot(screenshot_path)
ss_h = test_ss.height
ss_w = test_ss.width
coord_scale = screen_w / ss_w #usually 1.0, but OSX is fucky so not always true

def convert_coords(x, y, scale=coord_scale):
    return (int(x * scale), int(y * scale))

def click_button(tl, br,loc=0.5):
    click_x_ss, click_y_ss = np.mean((tl, br), axis=0).astype('int').tolist()
    if loc!=0.5:
        click_x_ss = tl[0]+loc*(br[0]-tl[0])
    # convert from ss coord to screen coord due to osx scaling
    click_x, click_y = convert_coords(click_x_ss, click_y_ss)
    pag.moveTo(click_x, click_y, duration=0.1)
    #pag.click(clicks=2, interval=1.0, button='left')
    pag.mouseDown()
    time.sleep(0.25)
    pag.mouseUp()
    pag.moveTo(click_x, click_y-200, duration=0.25) #need to move cursor to avoid blocking screenshot

template_names = ['accept', 'play', 'playagain','playagain2','start','exitnow','check']#,'open','riot','signin']
templates = {}
for tn in template_names:
    template_file = 'bs_images\\'+tn + '.png'
    temp_img = cv2.imread(template_file, cv2.IMREAD_COLOR)
    templates[tn] = cv2.cvtColor(temp_img, cv2.COLOR_BGR2RGB)

counter = 0
start = time.time()
total_time = 0
last_button = 'play'
while True:
    # take screenshot
    raw_ss = pag.screenshot(screenshot_path)
    #grayscale_ss = raw_ss.convert('L')
    #ss = np.array(grayscale_ss)
    ss = np.array(raw_ss)

    # figure out phase by searching for buttons
    all_minval = []
    all_res = []
    all_tl_br = []
    for t in template_names:
        if last_button=='start':
            if t not in ['accept','start','check']:

                 continue
        # load template
        template = templates[t]
        h, w = template.shape[:2]
        # template matching
        res = cv2.matchTemplate(ss, template, cv2.TM_SQDIFF_NORMED)
        all_res.append(res)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        all_minval.append(min_val)
        top_left = min_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)
        all_tl_br.append((top_left, bottom_right))

    detect_threshold = 0.09
    matched_template_idx = np.argmin(np.array(all_minval))
    (tl, br) = all_tl_br[matched_template_idx]
    if all(np.array(all_minval) >= detect_threshold):# and last_button not in ['start','exitnow']:  # if no templates found, wait
        # pag.click(x=278, y=473)
        # time.sleep(1)
        # pag.click(x=293, y=595)
        # time.sleep(1)
        continue
    elif template_names[matched_template_idx] in ['signin']:
        last_button = 'signin'
        print('logging in...'+str(all_minval[matched_template_idx]))
        click_button(tl, br)
        pag.typewrite('', interval=0.1)
        pag.press('tab')
        pag.typewrite('', interval=0.1)
        pag.press('enter')
        time.sleep(8)
        # if in lobby, main screen, queue pop, or missed queue notification
    elif template_names[matched_template_idx] in ['play','start','accept','check','open','riot']:
        print(template_names[matched_template_idx].upper()+
              ' button detected: ' + str(all_minval[matched_template_idx]))
        # click it
        click_button(tl, br)
        last_button = template_names[matched_template_idx]
    #if in result screen
    elif template_names[matched_template_idx] in ['playagain','playagain2']:
        last_button = 'playagain'
        print('PLAY AGAIN button detected: ' + str(all_minval[matched_template_idx]))
        # click play
        click_button(tl, br)
        counter += 1
        print('game ' + str(counter) + ' finished')
        elapsed = time.time()-start
        total_time+=elapsed
        print('\t%.2f minutes (including queue)' % (elapsed/60.0))
        print('\t\t%.2f minutes average' % ((total_time)/60.0/counter))
        start = time.time()
    #if in game
    elif template_names[matched_template_idx] == 'buyxp':
        pass #todo
        # print('BUY XP button detected: '+str(all_minval[matched_template_idx]))
        # buy xp
        # click_button(tl,br)
        # pag.mouseDown()
        # pag.mouseUp()
    #if at greyscreen
    elif template_names[matched_template_idx] in ['exitnow']:
        last_button = 'exitnow'
        print('EXIT NOW button detected: ' + str(all_minval[matched_template_idx]))
        # click play
        click_button(tl, br,0.25)
        pag.mouseDown()  # clicking in the game requires mousedown/up, click doesnt work for some reason
        pag.mouseUp()
        # os.kill(93444,signal.SIGTERM)


def validate(ss=ss, tl=tl, br=br, all_res=all_res):
    cv2.rectangle(ss, tl, br, 255, 20)

    plt.subplot(121), plt.imshow(all_res[matched_template_idx], cmap='gray')
    plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
    plt.subplot(122), plt.imshow(ss, cmap='gray')
    plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
    plt.show()