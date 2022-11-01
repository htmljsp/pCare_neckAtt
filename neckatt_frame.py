#-*- coding: utf-8 -*-

# lida2012@foxmail.com
# 2022-06-14
# 坐姿检测工具
# 使用方法： python3 + opencv-contrib-python + Pillow
# 执行脚本  python3 neckatt.py 
# 调整坐姿 后，点击 q ,记录标准坐姿 11
# 程序进入检测： 50秒检测一次，坐姿偏移标准坐姿 140 这弹窗报警，不确定则不再进行后续的报警
# 机制：根据摄像头获取标准坐姿的识别人脸，启动时 设定标准坐姿，即人脸中心坐标。后续定时检测找到当前人脸中心坐标，和标准坐姿的标准坐标 做欧式距离 计算，大于 阈值则报警
# 较Nekoze.app的优势：
# cpu使用率基本为0，Nekoze.app超级占用cpu
# 标准坐姿 视频标注，可以做到心里有数
# 坐姿偏移 程序会给出 定量值
# 无人或不标准后报警一次，报警不解除，不进行后续检测，避免无效功耗

import os
from tkinter import *
from tkinter import messagebox

from PIL import Image, ImageTk

import cv2
import sys
import time
import math
from time import gmtime, strftime
import datetime
from platform import system as platform


#告诉OpenCV使用人脸识别分类器
classfier = cv2.CascadeClassifier("./haarcascade_frontalface_alt2.xml")
is_standard_cap = False   # 是否在标准坐姿检测中
is_check_cap = False   # 是否在检测坐姿
winafterid=None   #循环id
cap = None
cap_pic = None
cap_check_pic = None
sit_pic=os.getcwd() + os.sep +"netatt.png"
init_file=os.getcwd() + os.sep +"netatt.conf"

loop_second_threshold=60
cap_init_index=0
horizontal_dist_threshold=150
vertical_dist_threshold=100

x_standard=1
y_standard=1
width_standard=1
heigth_standard=1

x_now = 1
y_now = 1
width_now = 1
heigth_now = 1

allCheckTimes=0
CheckOkTimes=0
CheckErrorTimes=0

win=Tk()
#保证最小化的图标单击后可以弹出
win.createcommand('tk::mac::ReopenApplication', win.wm_deiconify)

win.geometry("640x480")    # 设置窗口大小
win.title('neckatt 检测')
win.geometry('900x600')
win.resizable(width=False,height=False) # 禁止调节窗口大小 #| win.resizable(0,1)
#win.iconify()   #窗口最小化
#win.resizable(0,0) # 禁止拉伸窗口
#win.overrideredirect(1) # 隐藏标题栏 最大化最小化按钮
#win.attributes("-toolwindow", 2) # 去掉窗口最大化最小化按钮，只保留关闭
#win.attributes("-type", 2)
#禁止最大化按钮  
#win.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)  
#禁止拉伸窗口大小  
#win.setFixedSize(MainWindow.width(), MainWindow.height());  
#win.wm_state('iconic') 窗口最小化
#win.wm_state('iconic')
#win.wm_state('normal')
#win.createcommand('tk::mac::ReopenApplication', win.deiconify)
#win.protocol("WM_DELETE_WINDOW", win.iconify)

#win.wm_attributes('-topmost',1)
#win.lift()
#win.attributes('-topmost',True)
#win.after_idle(win.attributes,'-topmost',False)

image_width = 440
image_height = 300

canvas = Canvas(win,bg = 'white',width = image_width,height = image_height )#绘制画布
canvas.place(x = 10,y = 10)

canvas_new = Canvas(win,bg = 'white',width = image_width,height = image_height )#绘制画布
canvas_new.place(x = 450,y = 10)
Label(win,text = '标准坐姿',font = ("黑体",14),width =10,height = 1).place(x =10,y = 10,anchor = 'nw')
Label(win,text = '当前坐姿',font = ("黑体",14),width =10,height = 1).place(x =450,y = 10,anchor = 'nw')

Label(win,text = '选定摄像头:',font = ("黑体",14),width =10,height = 1).place(x =10,y = 330,anchor = 'nw')
#text = Text(win,bg = '#f6f5ec',bd=0,font=("黑体",14), width=11, height=1).place(x = 100,y = 330,anchor = 'nw')
#text.pack()
#text.insert("insert", "You are good!")
e_cap_set = Entry(win,show=None,font = ("宋体",14)) #,bg = '#f6f5ec')
e_cap_set.delete(0, "end")
e_cap_set.insert(0, "0")
e_cap_set.place(x = 100,y = 330,anchor = 'nw')
print(e_cap_set.get())

Label(win,text = '轮询检测秒:',font = ("黑体",14),width =10,height = 1).place(x =10,y = 360,anchor = 'nw')
e_loopSeond_set = Entry(win,show=None,font = ("宋体",14)) #,bg = '#f6f5ec')
e_loopSeond_set.delete(0, "end")
e_loopSeond_set.insert(0, "60")
e_loopSeond_set.place(x = 100,y = 360,anchor = 'nw')
print(e_loopSeond_set.get())

Label(win,text = '水平差阈值:',font = ("黑体",14),width =10,height = 1).place(x =10,y = 390,anchor = 'nw')
e_horizontalDist_set = Entry(win,show=None,font = ("宋体",14)) #,bg = '#f6f5ec')
e_horizontalDist_set.delete(0, "end")
e_horizontalDist_set.insert(0, "120")
e_horizontalDist_set.place(x = 100,y = 390,anchor = 'nw')
print(e_horizontalDist_set.get())

Label(win,text = '垂直差阈值:',font = ("黑体",14),width =10,height = 1).place(x =10,y = 420,anchor = 'nw')
e_verticalDist_set = Entry(win,show=None,font = ("宋体",14)) #,bg = '#f6f5ec')
e_verticalDist_set.delete(0, "end")
e_verticalDist_set.insert(0, "88")
e_verticalDist_set.place(x = 100,y = 420,anchor = 'nw')
print(e_verticalDist_set.get())

infoText = StringVar()
infoText.set('水平差值:0,垂直差值:0 -- 未触发报警')
infoLabel = Label(win,textvariable = infoText,font = ("Verdana",12),width =50,height = 1,anchor='w')
infoLabel.place(x =120,y = 480,anchor = 'nw')
Label(win,text = '当前检测值:',font = ("黑体",14),width =10,height = 1).place(x =10,y = 480,anchor = 'nw')

infoTime = StringVar()
#infoTime.set(strftime("%Y-%m-%d %H:%M:%S", gmtime(8)))
infoTime.set(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
timeLabel = Label(win,textvariable = infoTime,font = ("Verdana",12),width =45,height = 1,anchor='w')
timeLabel.place(x =120,y = 500,anchor = 'nw')


#global allCheckTimes
#global CheckOkTimes
#global CheckErrorTimes
infoTongji = StringVar()
infoTongji.set('统计次数：%d, 正确坐姿次数：%d, 错误坐姿次数：%d, 正确率 %.1f%%' %(allCheckTimes,CheckOkTimes,CheckErrorTimes,100 * CheckOkTimes/(allCheckTimes if allCheckTimes!=0 else 1)))
tongjiLabel = Label(win,textvariable = infoTongji,font = ("Verdana",12),width =45,height = 1,anchor='w')
tongjiLabel.place(x =120,y = 520,anchor = 'nw')

Label(win,text = 'lida2012@foxmail.com GOOK_LUCK',font = ("宋体",14),width =80,height = 1).place(x =50,y = 550,anchor = 'nw')

def stop_standard_sit_cap():
    global cap
    global is_standard_cap
    cap.release()
    is_standard_cap = False


def set_standard_sit_pose():
    global is_standard_cap
    global b1
    global b2
    global b3
    global canvas

    #按钮修改描述
    #b1.config(text='保存 标准')
    #b1.config(state='normal')
    #b1.config(state='disabled')
    print("start")
    #b1.update()

    b2.config(state='disabled')
    b3.config(state='disabled')


    b1 = Button(win,text="保存 标准",relief=RAISED,width=10,height=2,command=stop_standard_sit_cap)
    b1.place(x = 500,y = 330,anchor = 'nw')
    b1.update()
    #画布展示视频头像
    is_standard_cap = True
    pic_pose = show_frames_for_standard()
    if pic_pose != None:
        #记录最后图片到本地 以备下次打开使用图片
        pic_pose._PhotoImage__photo.write(sit_pic)

    reset_all_value()
    init()
    
    #b1.config(state='normal')
    #b1.config(text="设置标准坐姿")
    #b1.update()
    b1 = Button(win,text="设置标准坐姿",relief=RAISED,width=10,height=2,command=set_standard_sit_pose)
    b1.place(x = 500,y = 330,anchor = 'nw')
    #b1.update()
    b2.config(state='normal')
    b3.config(state='normal')

b1 = Button(win,text="设置标准坐姿",relief=RAISED,width=10,height=2,command=set_standard_sit_pose)
b1.place(x = 500,y = 330,anchor = 'nw')

def reset_all_value():
    global init_file
    global loop_second_threshold
    global cap_init_index
    global horizontal_dist_threshold
    global vertical_dist_threshold

    global x_standard
    global y_standard
    global width_standard
    global heigth_standard


    print(e_cap_set.get()+"#"+e_loopSeond_set.get()+"#"+e_horizontalDist_set.get()+"#"+e_verticalDist_set.get()+"#"+str(x_standard)+"#"+str(y_standard)+"#"+str(width_standard)+"#"+str(heigth_standard))
    with open(init_file,'w') as f:
        f.write(e_cap_set.get()+"#"+e_loopSeond_set.get()+"#"+e_horizontalDist_set.get()+"#"+e_verticalDist_set.get()+"#"+str(x_standard)+"#"+str(y_standard)+"#"+str(width_standard)+"#"+str(heigth_standard))

    loop_second_threshold = int(e_loopSeond_set.get())
    cap_init_index = int(e_cap_set.get())
    horizontal_dist_threshold = int(e_horizontalDist_set.get())
    vertical_dist_threshold = int(e_verticalDist_set.get())


b2 = Button(win,text="保存配置",relief=RAISED,width=10,height=2,command=reset_all_value)
b2.place(x = 650,y = 330,anchor = 'nw')

def stop_check():
    global is_check_cap
    global win
    global winafterid
    global b1
    global b2
    global b3

    is_check_cap = False
    if not winafterid==None:
        win.after_cancel(winafterid)

    b3 = Button(win,text="开始检测",relief=RAISED,width=10,height=2,command=start_check)
    b3.place(x = 500,y = 400,anchor = 'nw')
    b1.config(state='normal')
    b2.config(state='normal')


def show_notification(title, text):
    os.system("""
              osascript -e 'display notification "{}" with title "{}"'
              """.format(text, title))

def dialog(content):
    global win
    global loop_second_threshold
    afterRes = None
    color = '#8cc269'
    myWin = Toplevel(bg = color)
    #myWin.transient(win) #一直在win的上面
    myWin.title("请保持微笑：")

    sw = win.winfo_screenwidth()
    #得到屏幕宽度
    sh = win.winfo_screenheight()
    #得到屏幕高度
    ww = 300
    wh = 200
    #窗口宽高为100
    x = (sw-ww) / 2
    y = (sh-wh) / 3
    myWin.geometry("%dx%d+%d+%d" %(ww,wh,x,y))
    #myWin.geometry("400x200+600+200")

    Label(myWin, text=content , bg = color).pack()

    def exitAndshowMain():
        myWin.destroy() #关闭弹窗
        myWin.quit()
        win.deiconify()

    def tuichu(ev=None):
        myWin.destroy() #关闭弹窗
        myWin.quit()
        print('dialog exit in tuichu')

    showRootB=Button(myWin,text='主  页', fg='#37d3ff', highlightbackground=color,bg = color, command=exitAndshowMain)
    showRootB.pack()

    exitB=Button(myWin,    text='确  定', fg='#37d3ff', highlightbackground=color,bg=color ,command=tuichu)
    exitB.pack()
    
    myWin.protocol('WM_DELETE_WINDOW', myWin.quit)

    def timeout(ev=None):
        myWin.destroy() #关闭弹窗
        myWin.quit()
        print('dialog exit in timeout')
        #dialog(content)

    #os.system("say '%s'" %("请 注意"))
    #60秒后弹窗自动关闭
    afterRes = myWin.after(int(loop_second_threshold*1000/2),timeout)
    print(afterRes)
    
    myWin.bind("<Escape>", tuichu)  #当焦点在整个弹窗上时，绑定ESC退出
    myWin.bind("<Return>", tuichu) 
    myWin.bind("<space>", tuichu) 

    myWin.focus_set()
    myWin.grab_set()
    myWin.mainloop()
    #if not afterRes==None:
    #    myWin.after_cancel(afterRes)
    #myWin.destroy()
    print('dialog exit')


def dist_check():
    global infoText
    global infoLabel
    global win
    #infoText.set('水平差值:0,垂直差值:0 -- 未触发报警')
    #infoLabel = Label(win,textvariable = infoText,font = ("Verdana",12),width =45,height = 1)
    global horizontal_dist_threshold
    global vertical_dist_threshold

    global x_standard
    global y_standard
    global width_standard
    global heigth_standard

    global x_now
    global y_now
    global width_now
    global heigth_now

    global infoTongji
    global infoTime

    global allCheckTimes
    global CheckOkTimes
    global CheckErrorTimes

    print(x_now,y_now,width_now,heigth_now)
    dis = euclidean_distance((x_standard,y_standard),(x_now,y_now))
    print(dis)


    #if platform() == 'Darwin':  # How Mac OS X is identified by Python
    #    print('Darwin')
        #os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')

    #infoTime.set(strftime("%Y-%m-%d %H:%M:%S", gmtime(8)))
    infoTime.set(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    allCheckTimes = allCheckTimes + 1

    if x_now == 1:
        infoText.set("注意坐姿: 未检测到人脸")
        allCheckTimes = allCheckTimes - 1
        #win.update()
        #win.deiconify()
        #win.withdraw()

        #win.iconify()
        #win.update()
        #win.deiconify()
        #win.update()
        #raise_above_all(messagebox)
        #messagebox.showwarning('GOOK LUCK','注意坐姿 \n\n 未检测到人脸') #.focus_set()
        dialog('\n 注意坐姿: \n 未检测到人脸\n\n')
        #show_notification('GOOK LUCK','注意坐姿 \n\n 未检测到人脸')
    elif dis >= horizontal_dist_threshold:
        CheckErrorTimes = CheckErrorTimes + 1
        infoText.set("注意坐姿: 坐姿偏移量为：" + str(int(dis)))
        #win.update()
        #win.deiconify()
        #win.withdraw()
        #win.iconify()
        #win.update()
        #win.deiconify()
        #win.update()
        #raise_above_all(messagebox)
        #messagebox.showwarning('GOOK LUCK','注意坐姿 \n\n 坐姿偏移量为：' + str(int(dis))) #.focus_set()
        dialog('\n注意坐姿: \n 坐姿偏移量为：' + str(int(dis)) + "\n\n")
        #show_notification('GOOK LUCK','注意坐姿 \n\n 坐姿偏移量为：' + str(int(dis)))
    elif width_now - width_standard >= vertical_dist_threshold:
        CheckErrorTimes = CheckErrorTimes + 1
        infoText.set('注意坐姿: 距离屏幕过近，距离偏移为：' + str(width_now - width_standard))
        #win.update()
        #win.deiconify()
        #win.withdraw()
        #win.iconify()
        #win.update()
        #win.deiconify()
        #win.update()
        #raise_above_all(messagebox)
        #messagebox.showwarning('GOOK LUCK','注意坐姿 \n\n 距离屏幕过近，距离偏移为：' + str(width_now - width_standard)) #.focus_set()
        dialog('\n注意坐姿: \n 距离屏幕过近，距离偏移为：' + str(width_now - width_standard) + "\n\n")
        #show_notification('GOOK LUCK','注意坐姿 \n\n 距离屏幕过近，距离偏移为：' + str(width_now - width_standard))
    else:
        CheckOkTimes = CheckOkTimes + 1
        infoText.set("您的坐姿很标准，赞! 水平距离：" + str(int(dis)) + " 前后距离：" + str(width_now - width_standard)) 
        #win.update()
        #win.deiconify()

    print("将更新统计")
    infoTongji.set('统计坐姿次数：%d, 正确次数：%d, 错误次数：%d, 正确率 %.1f%%' %(allCheckTimes,CheckOkTimes,CheckErrorTimes,100 * CheckOkTimes/(allCheckTimes if allCheckTimes!=0 else 1)))
        
def start_check():
    global is_standard_cap
    global is_check_cap
    global b1
    global b2
    global b3
    global canvas
    global win
    global winafterid
    global loop_second_threshold

    is_standard_cap = False

    b1.config(state='disabled')
    b2.config(state='disabled')

    b3 = Button(win,text="停止检测",relief=RAISED,width=10,height=2,command=stop_check)
    b3.place(x = 500,y = 400,anchor = 'nw')
    b3.update()
    is_check_cap = True

    ret = show_frames_for_check()

    if ret=='nostandardsit' or ret=='capopenfail':
        stop_check()
        return 

    dist_check()

    print("loop_second_threshold is : ", loop_second_threshold)
    winafterid = win.after(int(loop_second_threshold)*1000,start_check)

    
b3 = Button(win,text="开始检测",relief=RAISED,width=10,height=2,command=start_check)
b3.place(x = 500,y = 400,anchor = 'nw')


#def exit_pro():
#    global cap
#    global cv2
#    global win
#    if not cap is None:
#        cap.release()
#    cv2.destroyAllWindows()
#    win.destroy()
#    exit(0)
#b4 = Button(win,text="退出程序",relief=RAISED,width=10,height=2,command=exit_pro)
#b4.place(x = 650,y = 400,anchor = 'nw')

def minine():
    #global win
    #win.iconify()
    win.withdraw()

def show():
    win.update()
    win.deiconify()

#有作用但不用
#win.createcommand('tk::mac::ReopenApplication', show) #win.wm_deiconify)

b5 = Button(win,text="最小化",relief=RAISED,width=10,height=2,command=minine)

b5.place(x = 650,y = 400,anchor = 'nw')

def CatchUsbVideo(window_name, camera_idx,testIng):
    cv2.namedWindow(window_name)

    #视频来源，可以来自一段已存好的视频，也可以直接来自USB摄像头
    cap = cv2.VideoCapture(camera_idx)
    time.sleep(1)

    #识别出人脸后要画的边框的颜色，RGB格式
    color = (0, 255, 0)

    init_loc = [1,1]
    empty_count=0

    while cap.isOpened():
        ok, frame = cap.read() #读取一帧数据
        cv2.startWindowThread() 
        if not ok:
            time.sleep(1)
            break

        #将当前帧转换成灰度图像
        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        retval = None
        #人脸检测，1.2和2分别为图片缩放比例和需要检测的有效点数
        faceRects = classfier.detectMultiScale(grey, scaleFactor = 1.2, minNeighbors = 3, minSize = (32, 32))
        if len(faceRects) > 0:            #大于0则检测到人脸                                 
            x, y, w, h = faceRects[0]
            cv2.rectangle(frame, ((x + int(w/2)), (y+int(h/2))), ((x + int(w/2) + 2), (y+int(h/2)+2)), color, 2)

            #print((x + int(w/2)), (y+int(h/2)))
            init_loc=[(x + int(w/2)), (y+int(h/2))]
            #return (x + int(w/2)), (y+int(h/2))
            if testIng==2:
                break
            #显示图像
            cv2.imshow(window_name, frame)
        else:
            if empty_count==5 :
                time.sleep(1)
                print("no face to break")
                break;
            print("no face")
            empty_count = empty_count+1

        if testIng != 2:
            c = cv2.waitKey(10)
            if c & 0xFF == ord('q'):
                break

    #释放摄像头并销毁所有窗口
    print(" cap.release and cv2.destroyAllWindows")
    cap.release()
    cv2.destroyAllWindows()
    print(cap)
    print(cv2)

    return  init_loc

def euclidean_distance(v1, v2):
    return math.sqrt(math.pow((v2[0] - v1[0]), 2) + math.pow((v2[1] - v1[1]), 2))


def show_frames_for_check():
    global is_check_cap
    global cap
    global canvas_new
    global cap_check_pic
    global cap_init_index
    global loop_second_threshold
    global cap_pic
    global x_now
    global y_now
    global width_now
    global heigth_now
    global x_standard
    global y_standard

    if cap_pic is None:
        messagebox.showinfo('GOOK LUCK','请先设置标准坐姿')
        stop_check()
        return 'nostandardsit'

    print("is_check_cap is: " ,is_check_cap)
    print("cap_init_index is: " ,cap_init_index)

    cap = cv2.VideoCapture(cap_init_index)

    no_fact_times = 0

    while is_check_cap:
        # 获取摄像头最新帧并转换为Image
        #cv2image= cv2.cvtColor(cap.read()[1],cv2.COLOR_BGR2RGB)
        #cv2image= cv2.cvtColor(cv2.flip(cap.read()[1],1),cv2.COLOR_BGR2RGB)
        #frame = cv2.flip(frame, 1) #摄像头翻转

        ok, frame = cap.read() #读取一帧数据
        if not ok:
            dialog("打开摄像头失败，需要赋予权限,并重新点击 开始检测")
            #is_check_cap = False
            #cap_check_pic = None
            stop_check()
            return 'capopenfail'

        cv2image= cv2.cvtColor(cv2.flip(frame,1),cv2.COLOR_BGR2RGB)
        #frame = cv2.flip(frame, 1) #摄像头翻转

        #将当前帧转换成灰度图像
        grey = cv2.cvtColor(cv2image, cv2.COLOR_BGR2GRAY)
        #人脸检测，1.2和2分别为图片缩放比例和需要检测的有效点数
        faceRects = classfier.detectMultiScale(grey, scaleFactor = 1.2, minNeighbors = 3, minSize = (32, 32))
        if len(faceRects) > 0:            #大于0则检测到人脸     
            print("检测到人物")                            
            x, y, w, h = faceRects[0]
            if w<= 200:   # 检测到的脸宽度小于120 判定为误识别
                continue;
            cv2.rectangle(cv2image, ((x + int(w/2)-2), (y+int(h/2)-2)), ((x + int(w/2) + 2), (y+int(h/2)+2)), (255, 0, 0), 2)
            cv2.rectangle(cv2image, (x  , y  ), (x + w  , y + h), (0, 255, 0), 2)

            x_now = x + int(w/2)
            y_now = y + int(h/2)
            width_now = w
            heigth_now = h

            cv2.line(cv2image,(x_now,y_now),(x_standard,y_standard),(0,0,255),2)#绿色，3个像素宽度

            is_check_cap = False
        else:
            print("未检测到人物") 
            if no_fact_times >= 5 :
                x_now = 1
                y_now = 1
                width_now = 1
                heigth_now = 1
                is_check_cap = False
            no_fact_times = no_fact_times + 1
            win.after(500)

        img = Image.fromarray(cv2image)
        img = img.resize((image_width, image_height),Image.ANTIALIAS)

        # 将图像转换为 PhotoImage
        cap_check_pic = ImageTk.PhotoImage(image = img)
        print(cap_check_pic)
        canvas_new.create_image(0,0,anchor = 'nw',image = cap_check_pic)
        #win.update()
        
    cap.release()
    return cap_check_pic


def show_frames_for_standard():
    global is_standard_cap
    global cap
    global canvas
    global cap_pic
    global sit_pic
    global cap_init_index
    global x_standard
    global y_standard
    global width_standard
    global heigth_standard

    print("is_standard_cap is: " ,is_standard_cap)
    print("cap_init_index is: " ,cap_init_index)

    cap = cv2.VideoCapture(cap_init_index)
    while is_standard_cap:
        # 获取摄像头最新帧并转换为Image
        #cv2image= cv2.cvtColor(cap.read()[1],cv2.COLOR_BGR2RGB)
        #cv2image= cv2.cvtColor(cv2.flip(cap.read()[1],1),cv2.COLOR_BGR2RGB)

        ok, frame = cap.read() #读取一帧数据
        if not ok:
            dialog("打开摄像头失败，需要赋予权限,并重新点击 设置标准坐姿")
            is_standard_cap = False
            cap_pic = None
            break
        cv2image= cv2.cvtColor(cv2.flip(frame,1),cv2.COLOR_BGR2RGB)
        #frame = cv2.flip(frame, 1) #摄像头翻转

        #将当前帧转换成灰度图像
        grey = cv2.cvtColor(cv2image, cv2.COLOR_BGR2GRAY)
        #人脸检测，1.2和2分别为图片缩放比例和需要检测的有效点数
        faceRects = classfier.detectMultiScale(grey, scaleFactor = 1.2, minNeighbors = 3, minSize = (32, 32))
        if len(faceRects) > 0:            #大于0则检测到人脸     
            print("检测到人物")                            
            x, y, w, h = faceRects[0]
            cv2.rectangle(cv2image, ((x + int(w/2)-2), (y+int(h/2)-2)), ((x + int(w/2) + 2), (y+int(h/2)+2)), (255, 0, 0), 2)
            cv2.rectangle(cv2image, (x  , y  ), (x + w  , y + h), (0, 255, 0), 2)
            x_standard = x + int(w/2)
            y_standard = y + int(h/2)
            width_standard = w
            heigth_standard = h
            img = Image.fromarray(cv2image)
            img = img.resize((image_width, image_height),Image.ANTIALIAS)
            # 将图像转换为 PhotoImage
            cap_pic = ImageTk.PhotoImage(image = img)
            print(cap_pic)
            canvas.create_image(0,0,anchor = 'nw',image = cap_pic)
        else:
            print("未检测到人物") 
            img = Image.fromarray(cv2image)
            img = img.resize((image_width, image_height),Image.ANTIALIAS)
            # 将图像转换为 PhotoImage
            cap_pic1 = ImageTk.PhotoImage(image = img)
            print(cap_pic1)
            canvas.create_image(0,0,anchor = 'nw',image = cap_pic1)

        win.update()
        win.after(10)

    if ok:
        cap.release()

    return cap_pic

def init():
    global cap_pic
    global cap_check_pic
    global canvas
    global canvas_new
    global sit_pic
    global init_file
    global loop_second_threshold
    global cap_init_index
    global horizontal_dist_threshold
    global vertical_dist_threshold

    global x_standard
    global y_standard
    global width_standard
    global heigth_standard

    print(sit_pic)
    print(cap_pic)
    print(os.path.exists(sit_pic))
    print(init_file)

    if cap_pic is None and os.path.exists(sit_pic):
        print("init ")
        cap_pic = PhotoImage(file=sit_pic)
    canvas.create_image(0,0,anchor = 'nw',image = cap_pic)

    if not cap_check_pic is None:
        canvas_new.create_image(0,0,anchor = 'nw',image = cap_check_pic)

    if os.path.exists(init_file):
        with open(init_file,'r') as f:
            itemList = f.readlines()[0].split("#")
            print(itemList)
            print(len(itemList))
            if len(itemList)==8:
                e_cap_set.delete(0, END)
                print(itemList[0].isdigit())
                if not itemList[0].isdigit() or int(itemList[0]) <0 or int(itemList[0])>10:
                    e_cap_set.insert(0,0)
                else:
                    e_cap_set.insert(0,itemList[0])
                    cap_init_index = int(itemList[0])

                e_loopSeond_set.delete(0, END)
                if not itemList[1].isdigit() or int(itemList[1]) < 1 or int(itemList[1])>1000:
                    e_loopSeond_set.insert(0,60)
                else:

                    e_loopSeond_set.insert(0,itemList[1])
                    loop_second_threshold = int(itemList[1])

                e_horizontalDist_set.delete(0, END)
                if not itemList[2].isdigit() or int(itemList[2]) <50 or int(itemList[2])>500:
                    e_horizontalDist_set.insert(0,120)
                else:
                    e_horizontalDist_set.insert(0,itemList[2])
                    horizontal_dist_threshold = int(itemList[2])
                    
                e_verticalDist_set.delete(0, END)
                if not itemList[3].isdigit() or int(itemList[3]) <50 or int(itemList[3])>500:
                    e_verticalDist_set.insert(0,88)
                else:
                    e_verticalDist_set.insert(0,itemList[3].strip())
                    vertical_dist_threshold = int(itemList[3].strip())

                if not itemList[4].isdigit():
                    x_standard=1
                else:
                    x_standard = int(itemList[4].strip())

                if not itemList[5].isdigit():
                    y_standard=1
                else:
                    y_standard = int(itemList[5].strip())
                
                if not itemList[6].isdigit():
                    width_standard=1
                else:
                    width_standard = int(itemList[6].strip())

                if not itemList[7].isdigit():
                    heigth_standard=1
                else:
                    heigth_standard = int(itemList[7].strip())

                
if __name__ == '__main__':

    init()
    win.mainloop()