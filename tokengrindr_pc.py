import pyautogui as pag
import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import os
import signal

pag.FAILSAFE = True  # move mouse to upper left to auto abort
pag.PAUSE = 0.1

client_w = 1024
client_h = 768
screenshot_path = 'ss.png'

def click_button(pt1, pt2,button='left',xloc=0.5,yloc=0.5,reset=True):
    if type(pt1) is tuple:
        tl, br = pt1, pt2
        click_x, click_y = np.mean((tl, br), axis=0).astype('int').tolist()
        if xloc!=0.5:
            click_x = tl[0]+xloc*(br[0]-tl[0])
        if yloc!=0.5:
            click_y = tl[1]+yloc*(br[1]-tl[1])
    else:
        click_x, click_y = pt1, pt2
    random_duration = max(0.05,0.1*np.random.randn()+0.5)
    pag.moveTo(click_x, click_y, duration=random_duration)
    pag.mouseDown(button=button)
    random_delay = max(0.01, 0.1 * np.random.randn() + 0.2)
    time.sleep(random_delay)
    pag.mouseUp(button=button)
    if reset:
        pag.moveTo(click_x, click_y-200, duration=random_duration/2) #need to move cursor to avoid blocking screenshot

inclient_template_names = ['tft','confirm','findmatch','play','playagain','exitnow','exitnow2']
inqueue_template_names = ['accept','findmatch','sprite']
ingame_template_names = ['buyxprefresh','exitnow','exitnow2','playagain'] #exitnow only appears finishing below 2nd
#need to include playagain in case of 1 or 2 place finish since exitnow wont show up to end ingame phase
template_names = list(set(inclient_template_names+inqueue_template_names+ingame_template_names))
templates = {}
for tn in template_names:
    template_file = 'pc_images\\'+tn + '.png'
    temp_img = cv2.imread(template_file, cv2.IMREAD_COLOR)
    templates[tn] = cv2.cvtColor(temp_img, cv2.COLOR_BGR2RGB)

counter = 0 #number of games botted
start = time.time()
total_time = 0 #time spent botting
last_button = 'play'
inclient, inqueue, ingame = True, True, True
last_buy_time=0 #last time of xp buy
buyxp_loc = 0

while True:
    print('inclient: %s, inqueue: %s, ingame: %s' % (inclient,inqueue,ingame),end='\r')
    # take screenshot
    raw_ss = pag.screenshot(screenshot_path)
    ss = np.array(raw_ss)

    # figure out phase by searching for buttons
    all_minval = []
    all_res = []
    all_tl_br = []
    valid_templates = []
    if inqueue:
        #accept is handled separately because of time-sensitive nature in processing
        valid_templates += inqueue_template_names
    if inclient:
        valid_templates += inclient_template_names
    if ingame:
        valid_templates += ingame_template_names
    for t in valid_templates:
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
    #import pdb;pdb.set_trace()
    if ingame and not inclient and not inqueue and buyxp_loc!=0:
        buyxp_w = buyxp_loc[1][0]-buyxp_loc[0][0]
        buyxp_h = buyxp_loc[1][1]-buyxp_loc[0][1]
        buyxp_bl = (buyxp_loc[0][0],buyxp_loc[1][1])
        client_tl = (buyxp_bl[0],buyxp_bl[1]-client_h)
        client_br = (buyxp_bl[0]+client_w,buyxp_bl[1])
        #define clickable region as the center 3x3 "buyxp" block range: https://i.imgur.com/fY5VFwv.png
        clickarea_tl = (int(client_tl[0]+client_w*0.3),int(client_tl[1]+client_h*0.3))
        clickarea_br = (int(client_br[0] - client_w * 0.3), int(client_br[1]-client_h * 0.3))
        #click around randomly, for ref: https://i.imgur.com/mhFvwzP.jpeg
        for i in range(15+int(10*np.random.random())):
            #uniformly dist
            rand_x = int(clickarea_tl[0]+np.random.random()*(clickarea_br[0]-clickarea_tl[0]))
            rand_y = int(clickarea_tl[1]+np.random.random()*(clickarea_br[1]-clickarea_tl[1]))
            click_button(rand_x,rand_y,button='right',reset=False)

        #buy champ next to xp button
        champ_tl = (buyxp_loc[1][0],buyxp_loc[0][1])
        champ_br = (buyxp_loc[1][0]+buyxp_w,buyxp_loc[0][1]+buyxp_h)
        click_button(champ_tl,champ_br)

    if all(np.array(all_minval) >= detect_threshold):# if no templates found, wait
        continue
    elif valid_templates[matched_template_idx] in ['play','tft','confirm']:
        inclient, inqueue, ingame = True, False, False
        print(valid_templates[matched_template_idx].upper()+
              ' button detected: ' + str(all_minval[matched_template_idx]))
        # click it
        click_button(tl, br)
    elif valid_templates[matched_template_idx] in ['accept','findmatch']:
        inclient, inqueue, ingame = False, True, False
        print(valid_templates[matched_template_idx].upper()+
              ' button detected: ' + str(all_minval[matched_template_idx]))
        # click it
        click_button(tl, br)
    elif valid_templates[matched_template_idx] in ['sprite']:
        print('River Sprite detected, game now in loading screen!')
        inclient, inqueue, ingame = False, False, True
    #if in result screen
    elif valid_templates[matched_template_idx] in ['playagain','playagain2']:
        inclient, inqueue, ingame = True, False, False
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
    elif valid_templates[matched_template_idx] == 'buyxprefresh':
        inclient, inqueue, ingame = False, False, True
        time_since_last_buy = time.time()-last_buy_time
        buy_freq = 75
        buyxp_loc = (tl,br)
        if last_buy_time==0:
            last_buy_time = time.time()
        elif time_since_last_buy>buy_freq:
            print('BUY XP button detected: ' + str(all_minval[matched_template_idx]))
            print('%.1f seconds since last buy' % time_since_last_buy)
            click_button(tl,br,yloc=0.25)
            last_buy_time=time.time()
    #if at greyscreen
    elif valid_templates[matched_template_idx] in ['exitnow','exitnow2']:
        inclient, inqueue, ingame = True, False, False
        buyxp_loc=0
        print('EXIT NOW button detected: ' + str(all_minval[matched_template_idx]))
        # click play
        #cannot use inbuilt click function when clicking on this button for some reason, need to manually move mouse up and down
        click_x, click_y = np.mean((tl, br), axis=0).astype('int').tolist()
        pag.moveTo(tl[0]+0.25*(br[0]-tl[0]),click_y)
        pag.mouseDown()
        pag.mouseUp()
        pag.mouseDown()
        pag.mouseUp()
        # os.kill(93444,signal.SIGTERM)


def validate(ss=ss, tl=tl, br=br, all_res=all_res):
    cv2.rectangle(ss, tl, br, 255, 20)

    plt.subplot(121), plt.imshow(all_res[matched_template_idx], cmap='gray')
    plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
    plt.subplot(122), plt.imshow(ss, cmap='gray')
    plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
    plt.show()