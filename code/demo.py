# coding:utf-8
import sys,os,cv2
import typing
import math
import numpy as np
import cgitb
import win32api,win32con
from math import fabs,sqrt
from PyQt5.QtMultimedia import QSound
from PyQt5 import QtCore,QtWidgets,QtGui
from PyQt5.QtCore import QThread,pyqtSignal,QTimer,Qt, QRect,QEasingCurve,QSize,QUrl
from PyQt5.QtGui import QIcon, QPainter, QImage, QBrush, QColor, QFont,QPixmap,QMovie,QLinearGradient,QDesktopServices
from PyQt5.QtWidgets import QApplication,QMainWindow,QCommandLinkButton, QFrame, QStackedWidget, QHBoxLayout, QLabel,QVBoxLayout,QWidget,QPushButton,QGridLayout

from qfluentwidgets import (NavigationInterface,NavigationItemPosition, NavigationWidget, MessageBox,InfoBar,InfoBarPosition,ColorPickerButton,IndeterminateProgressBar, ProgressBar,
                            isDarkTheme, setTheme, Theme,PushButton,LineEdit,TextEdit,SpinBox,DoubleSpinBox,ToolButton,SwitchButton,PrimaryPushButton,StateToolTip,qrouter,HyperlinkButton)
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow import FramelessWindow, TitleBar
from qfluentwidgets import FlowLayout
import time
import mediapipe as mp
import pyautogui as wigi
wigi.PAUSE=0.01#autoGUI刷新率
windowW,windowH=wigi.size()
pTime=0
cTime=0#FPS计算
W=920;H=680
mpHands=mp.solutions.hands
hands=hands1=None
#hands=mpHands.Hands(static_image_mode=False,max_num_hands=2,min_detection_confidence=0.75,min_tracking_confidence=0.75)
hands1=mpHands.Hands(static_image_mode=False,max_num_hands=1,min_detection_confidence=0.7,min_tracking_confidence=0.7)#手势解决方案
mpDraw=mp.solutions.drawing_utils#绘图控件


class WelcomeWindow(QMainWindow):#无边框加载界面
    '''
    无边框加载界面
    '''
    def __init__(self):
        #self.app=QApplication(sys.argv)
        super().__init__()
        self.setWindowIcon(QIcon(os.path.abspath('res/PIC/2.png')))
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Tool)
        self.resize(498,277)
        self.setStyleSheet("background: transparent;border:0px")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.0)
        self.label=QLabel(self)
        self.label.resize(498,277)
        self.gif=QMovie(os.path.abspath('res/GIF/dishonored.gif'))
        self.label.setMovie(self.gif)
        self.gif.start()
        self.count=0
        self.opacity=0.0
        self.time=QTimer(self)
        self.time.setInterval(30)
        self.time.timeout.connect(self.ImgRefresh)
        self.time.start()
        self.show()
    
    def ImgRefresh(self):
        if self.opacity<=1.0:
            self.setWindowOpacity(self.opacity)
            self.opacity+=0.01
        elif self.opacity<=1.6:
            self.opacity+=0.01
        else:
            self.time.stop()
            w.show()
            w.WelcomeInterface.logoGIF.start()
            self.close()

class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.label = QLabel(text, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)

        # leave some space for title bar
        self.hBoxLayout.setContentsMargins(0, 32, 0, 0)

class AvatarWidget(NavigationWidget):#Avatar widget from pyqt-fluentwidgets demo
    '''
    Avatar widget
    '''

    def __init__(self, parent=None):
        super().__init__(isSelectable=False, parent=parent)
        self.avatar = QImage('res/PIC/avatar').scaled(
            24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.SmoothPixmapTransform | QPainter.Antialiasing)

        painter.setPen(Qt.NoPen)

        if self.isPressed:
            painter.setOpacity(0.7)

        # draw background
        if self.isEnter:
            c = 255 if isDarkTheme() else 0
            painter.setBrush(QColor(c, c, c, 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

        # draw avatar
        painter.setBrush(QBrush(self.avatar))
        painter.translate(8, 6)
        painter.drawEllipse(0, 0, 24, 24)
        painter.translate(-8, -6)

        if not self.isCompacted:
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)
            font = QFont('Segoe UI')
            font.setPixelSize(14)
            painter.setFont(font)
            painter.drawText(QRect(44, 0, 255, 36), Qt.AlignVCenter, 'Señor Ji')

class CustomTitleBar(TitleBar):#Title bar with icon and title from pyqt-fluentwidgets demo
    ''' 
    Title bar with icon and title
    '''

    def __init__(self, parent):
        super().__init__(parent)
        # add window icon
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(18, 18)
        self.hBoxLayout.insertSpacing(0, 10)
        self.hBoxLayout.insertWidget(1, self.iconLabel, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.window().windowIconChanged.connect(self.setIcon)

        # add title label
        self.titleLabel = QLabel(self)
        self.hBoxLayout.insertWidget(2, self.titleLabel, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.titleLabel.setObjectName('titleLabel')
        self.window().windowTitleChanged.connect(self.setTitle)
        #self.maxBtn.clicked.disconnect(self.__toggleMaxState)
        #self.maxBtn.clicked.connect(self.toggleMaxState)

    def _TitleBar__toggleMaxState(self):
        w.showMaxnotice()

    def setTitle(self, title):
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def setIcon(self, icon):
        self.iconLabel.setPixmap(QIcon(icon).pixmap(18, 18))

R,G,B=0,255,0
PaintFPS=True;PaintPara=True;PaintKeypoints=True
class Ui_Form(object):#手势识别窗口基类
    '''
    手势识别窗口基类
    '''
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(870, 670)
        
        self.timer=QTimer(self)
        self.timer.timeout.connect(self.RefreshBar)
        self.switchbar=ProgressBar(self)
        self.switchbar.setGeometry(100,410,640,10)
        self.switchbar.setValue(0)
        self.progressBar = IndeterminateProgressBar(self)
        self.progressBar.setGeometry(100,410,640,10)
        self.progressBar.hide()
        
        self.BG1=QLabel(Form)
        self.BG1.setGeometry(10,140,100,90)
        self.BG1.setScaledContents(True)
        #self.BG1.setPixmap(QPixmap(os.path.abspath('res/PIC/stone1.png')))
        self.DisplayWindow = QtWidgets.QLabel(Form)
        self.DisplayWindow.setGeometry(QtCore.QRect(100, 50, 640, 360))
        #self.label.setStyleSheet("background: rgb(216, 230, 153);")
        self.DisplayWindow.setObjectName("DisplayWindow")
        self.DisplayWindow.setScaledContents(True)
        self.DisplayWindow.setStyleSheet('border: 2px solid #4CAF50;border-radius: 5px;background-color: #333333;color: #FFFFFF;font-size: 18px;font-weight: bold;padding: 10px;text-align: center;')
        #self.label.setPixmap(QPixmap(os.path.abspath('1.jpeg')))
        
        self.QuestionButton = ToolButton(FIF.HELP,Form)
        self.QuestionButton.setGeometry(QtCore.QRect(620, 462, 30, 30))
        self.QuestionButton.clicked.connect(self.SetFocus)
        self.QuestionButton.setToolTip('转到该功能详细说明')
        #ft=self.QuestionButton.font()
        #ft.setPointSize(11)
        self.title1 = LineEdit(Form)
        self.title1.setGeometry(QtCore.QRect(130, 460, 150, 20))
        self.title1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.title1.setObjectName('title1')
        self.title1.setText('拇指弯曲判定阈值:')
        #self.title1.setToolTip('拇指弯曲则大于这个值')
        self.title1.setStyleSheet('''background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
        #self.title1.setFont(ft)

        self.thumbvalue = SpinBox(Form)
        self.thumbvalue.move(280, 460)
        self.thumbvalue.setObjectName("thumbvalue")
        self.thumbvalue.setRange(40,100)
        self.thumbvalue.setValue(51)
        self.thumbvalue.setToolTip('拇指弯曲则大于这个值,值越小越容易识别到拇指弯曲')
        self.thumbvalue.valueChanged.connect(self.ChangeThreshold1)
        
        self.title2 = LineEdit(Form)
        self.title2.setGeometry(QtCore.QRect(130, 520, 150, 20))
        self.title2.setObjectName("title2")
        self.title2.setText('四指弯曲判定阈值:')
        self.title2.setFocusPolicy(QtCore.Qt.NoFocus)
        self.title2.setStyleSheet('''background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
        #self.title2.setFont(ft)
        
        self.fingervalue = SpinBox(Form)
        self.fingervalue.move(280, 520)
        self.fingervalue.setObjectName("fingervalue")
        self.fingervalue.setRange(50,150)
        self.fingervalue.setValue(65)
        self.fingervalue.setToolTip('除拇指外的四指弯曲则大于这个值,值越小越容易识别到四指弯曲')
        self.fingervalue.valueChanged.connect(self.ChangeThreshold2)
        
        self.title3 = LineEdit(Form)
        self.title3.setGeometry(QtCore.QRect(130, 580, 150, 20))
        self.title3.setObjectName("title3")
        self.title3.setText('手指张开判定阈值:')
        self.title3.setFocusPolicy(QtCore.Qt.NoFocus)
        self.title3.setStyleSheet('''background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
        #self.title3.setFont(ft)
        
        self.openvalue = SpinBox(Form)
        self.openvalue.move(280, 580)
        self.openvalue.setObjectName("openvalue")
        self.openvalue.setRange(15,70)
        self.openvalue.setValue(49)
        self.openvalue.setToolTip('手指张开则小于这个值，值越大越容易判定手指伸直了')
        self.openvalue.valueChanged.connect(self.ChangeThreshold3)
        
        self.PaintSwitch=SwitchButton(Form)
        self.PaintSwitch.setChecked(True)
        self.PaintSwitch.setText('手部骨骼绘制:开')
        self.PaintSwitch.move(510,510)
        self.PaintSwitch.checkedChanged.connect(self.oncheckChanged)

        self.FPSwitch=SwitchButton(Form)
        self.FPSwitch.setChecked(True)
        self.FPSwitch.setText('显示帧率')
        self.FPSwitch.move(510,550)
        self.FPSwitch.checkedChanged.connect(self.oncheckChanged2)

        self.ParaSwitch=SwitchButton(Form)
        self.ParaSwitch.setChecked(True)
        self.ParaSwitch.setText('显示参数')
        self.ParaSwitch.move(510,590)
        self.ParaSwitch.checkedChanged.connect(self.oncheckChanged3)
        
        self.retranslateUi(Form)
        self.RefreshWindow()
        QtCore.QMetaObject.connectSlotsByName(Form)

    def RefreshWindow(self):
        if isDarkTheme():
            self.DisplayWindow.setPixmap(QPixmap(os.path.abspath('res/PIC/night.jpg')))
        else:
            self.DisplayWindow.setPixmap(QPixmap(os.path.abspath('res/PIC/day.jpg')))

    def ResetPara(self):
        global thr_angle_thumb,thr_angle,thr_angle_s
        self.thumbvalue.setValue(thr_angle_thumb)
        self.fingervalue.setValue(thr_angle)
        self.openvalue.setValue(thr_angle_s)

    def RefreshButton(self):
        self.thumbvalue.setValue(51)
        self.fingervalue.setValue(65)
        self.openvalue.setValue(49)

    def RefreshBar(self):
        if self.cnt<=100:
            self.switchbar.setValue(self.cnt)
            self.cnt+=1
        else:
            self.timer.stop()

    def SwitchBar(self):
        self.cnt=0
        self.switchbar.show()
        self.timer.start(3)

    def SetFocus(self):
        w.switchTo(w.TutorInterface_1)
        
    def ChangeThreshold1(self,val):
        global thr_angle_thumb
        thr_angle_thumb=val
    def ChangeThreshold2(self,val):
        global thr_angle
        thr_angle=val
    def ChangeThreshold3(self,val):
        global thr_angle_s
        thr_angle_s=val

    def oncheckChanged(self, isChecked: bool):
        global PaintKeypoints
        PaintKeypoints=isChecked
        if isChecked:
            self.PaintSwitch.setText('手部骨骼绘制:开')
        else:
            self.PaintSwitch.setText('手部骨骼绘制:关')
    def oncheckChanged2(self, isChecked: bool):
        global PaintFPS
        PaintFPS=isChecked
        if isChecked:
            self.FPSwitch.setText('显示帧率')
        else:
            self.FPSwitch.setText('不显示帧率')
    def oncheckChanged3(self, isChecked: bool):
        global PaintPara
        PaintPara=isChecked
        if isChecked:
            self.ParaSwitch.setText('显示参数')
        else:
            self.ParaSwitch.setText('关闭参数显示')
            
    def setQss(self):
        if isDarkTheme():
            self.title1.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.title2.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.title3.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
        else:
            self.title1.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.title2.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.title3.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.DisplayWindow.setText(_translate("Form", "DisplayWindow"))

pressLevel=0.92;sensity=15.0;mouseControl=False
class Ui_Form2(object):#手势控制窗口基类
    '''
    手势控制窗口基类
    '''
    def setupUi(self, Form):
        Form.setObjectName("Form2")
        Form.resize(870, 670)
        
        self.timer=QTimer(self)
        self.timer.timeout.connect(self.RefreshBar)
        self.switchbar=ProgressBar(self)
        self.switchbar.setGeometry(100,410,640,10)
        self.switchbar.setValue(0)
        self.progressBar = IndeterminateProgressBar(self)
        self.progressBar.setGeometry(100,410,640,10)
        self.progressBar.hide()
        
        self.DisplayWindow = QtWidgets.QLabel(Form)
        self.DisplayWindow.setGeometry(QtCore.QRect(100, 50, 640, 360))
        #self.label.setStyleSheet("background: rgb(216, 230, 153);")
        self.DisplayWindow.setObjectName("DisplayWindow")
        self.DisplayWindow.setScaledContents(True)
        self.DisplayWindow.setStyleSheet('border: 2px solid #4CAF50;border-radius: 5px;background-color: #333333;color: #FFFFFF;font-size: 18px;font-weight: bold;padding: 10px;text-align: center;')
        #self.label.setPixmap(QPixmap(os.path.abspath('1.jpeg')))

        self.QuestionButton = ToolButton(FIF.HELP,Form)
        self.QuestionButton.setGeometry(QtCore.QRect(620, 462, 30, 30))
        self.QuestionButton.clicked.connect(self.SetFocus)
        self.QuestionButton.setToolTip('转到功能详细说明')
        
        self.title1 = LineEdit(Form)
        self.title1.setGeometry(QtCore.QRect(130, 460, 150, 20))
        self.title1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.title1.setObjectName('title1')
        self.title1.setText('手指捏合判定容易度:')
        
        self.thumbvalue = DoubleSpinBox(Form)
        self.thumbvalue.move(280, 460)
        self.thumbvalue.setObjectName("thumbvalue")
        self.thumbvalue.setRange(0.02,1.5)
        self.thumbvalue.setSingleStep(0.01)
        self.thumbvalue.setValue(0.92)
        self.thumbvalue.valueChanged.connect(self.ChangeThreshold1)
        self.thumbvalue.setToolTip('手指捏合则小于这个值，值越大越容易判定捏合，但更容易出现误检')
        
        self.title2 = LineEdit(Form)
        self.title2.setGeometry(QtCore.QRect(130, 520, 150, 20))
        self.title2.setObjectName("title2")
        self.title2.setText('鼠标移动灵敏度:')
        self.title2.setFocusPolicy(QtCore.Qt.NoFocus)
        
        self.fingervalue = DoubleSpinBox(Form)
        self.fingervalue.move(280, 520)
        self.fingervalue.setObjectName("fingervalue")
        self.fingervalue.setRange(0.1,50.0)
        self.fingervalue.setSingleStep(0.10)
        self.fingervalue.setValue(15.0)
        self.fingervalue.valueChanged.connect(self.ChangeThreshold2)
        self.fingervalue.setToolTip('操控鼠标的灵敏度，值越大移动手指鼠标动得越多')
        
        self.title3 = LineEdit(Form)
        self.title3.setGeometry(QtCore.QRect(130, 580, 150, 20))
        self.title3.setFocusPolicy(QtCore.Qt.NoFocus)
        self.title3.setObjectName('title3')
        self.title3.setText('握拳判定容易度:')
        self.title3.setFocusPolicy(QtCore.Qt.NoFocus)
        
        self.fistvalue = DoubleSpinBox(Form)
        self.fistvalue.move(280, 580)
        self.fistvalue.setObjectName("thumbvalue")
        self.fistvalue.setRange(0.6,1.2)
        self.fistvalue.setValue(1.05)
        self.fistvalue.setSingleStep(0.01)
        self.fistvalue.valueChanged.connect(self.ChangeThreshold3)
        self.fistvalue.setToolTip('值越大越容易识别为握拳，但也增加误检率')
        
        self.ControlSwitch=SwitchButton(Form)
        self.ControlSwitch.setChecked(False)
        self.ControlSwitch.setText('已停用控制接管')
        self.ControlSwitch.move(510,510)
        self.ControlSwitch.checkedChanged.connect(self.oncheckChanged2)
        
        self.setQss()
        self.retranslateUi(Form)
        self.RefreshWindow()
        QtCore.QMetaObject.connectSlotsByName(Form)

    def RefreshWindow(self):
        if isDarkTheme():
            self.DisplayWindow.setPixmap(QPixmap(os.path.abspath('res/PIC/night.jpg')))
        else:
            self.DisplayWindow.setPixmap(QPixmap(os.path.abspath('res/PIC/day.jpg')))

    def ResetPara(self):
        global pressLevel,sensity,FistLevel
        self.thumbvalue.setValue(pressLevel)
        self.fingervalue.setValue(sensity)
        self.fistvalue.setValue(FistLevel)

    def RefreshButton(self):
        self.fistvalue.setValue(1.05)
        self.fingervalue.setValue(15.0)
        self.thumbvalue.setValue(0.92)

    def RefreshBar(self):
        if self.cnt<=100:
            self.switchbar.setValue(self.cnt)
            self.cnt+=1
        else:
            self.timer.stop()

    def SwitchBar(self):
        self.cnt=0
        self.switchbar.show()
        self.timer.start(3)
            
    def ChangeThreshold1(self,val):
        global pressLevel
        pressLevel=val
    def ChangeThreshold2(self,val):
        global sensity
        sensity=val
    def ChangeThreshold3(self,val):
        global FistLevel
        FistLevel=val
        w.PPTInterface.thumbvalue.setValue(val)
        
    def createCustomInfoBar(self,isOpen: bool):
        w = InfoBar.new(
            icon=FIF.ACCEPT if isOpen else FIF.CLOSE,
            title='注意',
            content="已开启控制接管,请小心操作" if isOpen else "已关闭控制接管,可放心调试",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=2000,
            parent=self
        )
        w.setCustomBackgroundColor('white', '#202020')
        
    def oncheckChanged2(self, isChecked: bool):
        global mouseControl
        mouseControl=isChecked     
        if isChecked:
            self.ControlSwitch.setText('已启用控制接管')
        else:
            self.ControlSwitch.setText('已停用控制接管')
        self.createCustomInfoBar(isChecked)
            
    def setQss(self):
        if isDarkTheme():
            self.title1.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.title2.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.title3.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
        else:
            self.title1.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.title2.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.title3.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')

    def SetFocus(self):
        w.switchTo(w.TutorInterface_2)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form2", "Form2"))
        self.DisplayWindow.setText(_translate("Form2", "DisplayWindow"))
PPTcontrol=False;FistLevel=1.05;ScrollLevel=13;CooldownTime=15;PaintHux=True
class Ui_Form3(object):#PPT助手窗口基类
    '''
    PPT助手窗口基类
    '''
    def setupUi(self, Form):
        Form.setObjectName("Form3")
        Form.resize(870, 670)
        
        self.timer=QTimer(self)
        self.timer.timeout.connect(self.RefreshBar)
        self.switchbar=ProgressBar(self)
        self.switchbar.setGeometry(100,410,640,10)
        self.switchbar.setValue(0)
        self.progressBar = IndeterminateProgressBar(self)
        self.progressBar.setGeometry(100,410,640,10)
        self.progressBar.hide()
        
        self.BG=QLabel(Form)
        self.BG.setGeometry(0,40,900,700)
        self.BG.setScaledContents(True)
        #self.BG.setPixmap(QPixmap(os.path.abspath('res/PIC/BG1.jpg')))
        self.DisplayWindow = QtWidgets.QLabel(Form)
        self.DisplayWindow.setGeometry(QtCore.QRect(100, 50, 640, 360))
        #self.label.setStyleSheet("background: rgb(216, 230, 153);")
        self.DisplayWindow.setObjectName("DisplayWindow")
        self.DisplayWindow.setScaledContents(True)
        self.DisplayWindow.setStyleSheet('border: 2px solid #4CAF50;border-radius: 5px;background-color: #333333;color: #FFFFFF;font-size: 18px;font-weight: bold;padding: 10px;text-align: center;')
        
        self.QuestionButton = ToolButton(FIF.HELP,Form)
        self.QuestionButton.setGeometry(QtCore.QRect(620, 462, 30, 30))
        self.QuestionButton.clicked.connect(self.SetFocus)
        self.QuestionButton.setToolTip('转到功能详细说明')
        
        self.title1 = LineEdit(Form)
        self.title1.setGeometry(QtCore.QRect(130, 460, 150, 20))
        self.title1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.title1.setObjectName('title1')
        self.title1.setText('握拳判定容易度:')
        
        self.thumbvalue = DoubleSpinBox(Form)
        self.thumbvalue.move(280, 460)
        self.thumbvalue.setObjectName("thumbvalue")
        self.thumbvalue.setRange(0.6,1.2)
        self.thumbvalue.setValue(1.05)
        self.thumbvalue.setSingleStep(0.01)
        self.thumbvalue.valueChanged.connect(self.ChangeThreshold1)
        self.thumbvalue.setToolTip('值越大越容易识别为握拳，但也增加误检率')
        
        self.title2 = LineEdit(Form)
        self.title2.setGeometry(QtCore.QRect(130, 520, 150, 20))
        self.title2.setObjectName("title2")
        self.title2.setText('翻页响应灵敏度:')
        self.title2.setFocusPolicy(QtCore.Qt.NoFocus)
        
        self.fingervalue = SpinBox(Form)
        self.fingervalue.move(280, 520)
        self.fingervalue.setObjectName("fingervalue")
        self.fingervalue.setRange(8,17)
        self.fingervalue.setValue(13)
        self.fingervalue.valueChanged.connect(self.ChangeThreshold2)
        self.fingervalue.setToolTip('灵敏度越高识别翻页需要的手部移动越短')
        
        self.title3 = LineEdit(Form)
        self.title3.setGeometry(QtCore.QRect(130, 580, 150, 20))
        self.title3.setObjectName("title3")
        self.title3.setText('两次翻页间冷却时间:')
        self.title3.setFocusPolicy(QtCore.Qt.NoFocus)
        
        self.openvalue = SpinBox(Form)
        self.openvalue.move(280, 580)
        self.openvalue.setObjectName("openvalue")
        self.openvalue.setRange(1,40)
        self.openvalue.setValue(15)
        self.openvalue.valueChanged.connect(self.ChangeThreshold3)
        self.openvalue.setToolTip('冷却时间越久，识别下次翻页间隔越久，冷却时间能有效防止高灵敏度下一次挥手翻页多次')
        
        self.PaintSwitch=SwitchButton(Form)
        self.PaintSwitch.setChecked(True)
        self.PaintSwitch.setText('手部凸包绘制:开')
        self.PaintSwitch.move(510,550)
        self.PaintSwitch.checkedChanged.connect(self.oncheckChanged)
        
        self.ControlSwitch=SwitchButton(Form)
        self.ControlSwitch.setChecked(False)
        self.ControlSwitch.setText('已停用翻页控制')
        self.ControlSwitch.move(510,510)
        self.ControlSwitch.checkedChanged.connect(self.oncheckChanged2)
        
        self.setQss()
        self.retranslateUi(Form)
        self.RefreshWindow()
        QtCore.QMetaObject.connectSlotsByName(Form)

    def RefreshWindow(self):
        if isDarkTheme():
            self.DisplayWindow.setPixmap(QPixmap(os.path.abspath('res/PIC/night.jpg')))
        else:
            self.DisplayWindow.setPixmap(QPixmap(os.path.abspath('res/PIC/day.jpg')))

    def ResetPara(self):
        global FistLevel,ScrollLevel,CooldownTime
        self.thumbvalue.setValue(FistLevel)
        self.fingervalue.setValue(ScrollLevel)
        self.openvalue.setValue(CooldownTime)

    def RefreshButton(self):
        self.openvalue.setValue(15)
        self.fingervalue.setValue(13)
        self.thumbvalue.setValue(1.05)

    def setQss(self):
        if isDarkTheme():
            self.title1.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.title2.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.title3.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
        else:
            self.title1.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.title2.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.title3.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')

    def RefreshBar(self):
        if self.cnt<=100:
            self.switchbar.setValue(self.cnt)
            self.cnt+=1
        else:
            self.timer.stop()

    def SwitchBar(self):
        self.cnt=0
        self.switchbar.show()
        self.timer.start(3)

    def SetFocus(self):
        w.switchTo(w.TutorInterface_3)
        
    def ChangeThreshold1(self,val):
        global FistLevel
        FistLevel=val
    def ChangeThreshold2(self,val):
        global ScrollLevel
        ScrollLevel=val
    def ChangeThreshold3(self,val):
        global CooldownTime
        CooldownTime=val

    def oncheckChanged(self, isChecked: bool):
        global PaintHux
        PaintHux=isChecked
        if isChecked:
            self.PaintSwitch.setText('手部凸包绘制:开')
        else:
            self.PaintSwitch.setText('手部凸包绘制:关')
            
    def createCustomInfoBar(self,isOpen: bool):
        w = InfoBar.new(
            icon=FIF.ACCEPT if isOpen else FIF.CLOSE,
            title='注意',
            content="已开启翻页控制" if isOpen else "已关闭翻页控制",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=2000,
            parent=self
        )
        w.setCustomBackgroundColor('white', '#202020')
            
    def oncheckChanged2(self, isChecked: bool):
        global PPTcontrol
        PPTcontrol=isChecked     
        if isChecked:
            self.ControlSwitch.setText('已启用翻页控制')
        else:
            self.ControlSwitch.setText('已停用翻页控制')
        self.createCustomInfoBar(isChecked)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form3", "Form3"))
        self.DisplayWindow.setText(_translate("Form3", "DisplayWindow"))

class Setting_Form(object):#设置窗口基类
    '''
    设置窗口基类
    '''
    def setupUi(self, Form):
        Form.setObjectName("Setting_Form")
        Form.resize(870, 670)
        
        self.DisplayWindow = QtWidgets.QLabel(Form)
        #self.DisplayWindow.setGeometry(360, 475, 230, 251)
        self.DisplayWindow.setObjectName("DisplayWindow")
        self.DisplayWindow.setScaledContents(True)
        #self.DisplayWindow.setPixmap(QPixmap(os.path.abspath('res/PIC/emily.png')))
        #self.GIF=QMovie(os.path.abspath('res/GIF/spinning_2.gif'))
        #self.DisplayWindow.setMovie(self.GIF)
        #self.GIF.start()
        self.font=QFont('Microsoft YaHei')
        self.font.setPixelSize(25)
        #self.font.setBold(True)
        self.title=QLabel(Form)
        self.title.setText('设置')
        self.title.setGeometry(50,40,100,100)
        self.title.setFont(self.font)
        
        self.ThemeBox=TextEdit(Form)
        self.ThemeBox.setGeometry(QtCore.QRect(50, 120, 750, 60))
        self.ThemeBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.icon1=PushButton(Form)
        self.icon1.setStyleSheet('border:none;')
        self.icon1.setGeometry(40,120,60,60)
        self.icon1.setIcon(FIF.BRUSH)
        self.icon1.setIconSize(QSize(20,20))
        self.text1=LineEdit(Form)
        self.text1.setText('应用主题')
        self.text1.move(95,125)
        self.text1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.text1.setStyleSheet('border:none;')
        self.text1F=QLabel(Form)
        self.text1F.setText('调整该应用全局外观')
        self.text1F.setGeometry(95,150,230,17)
        #self.ThemeBox.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.ThemeSwitch=SwitchButton(Form)
        self.ThemeSwitch.move(730,130)
        self.ThemeSwitch.setText('')
        self.ThemeSwitch.checkedChanged.connect(self.onCheckedChanged)
        self.ThemeSwitchText=LineEdit(Form)
        self.ThemeSwitchText.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ThemeSwitchText.setText("暗夜主题：关")
        self.ThemeSwitchText.move(620,132)
        
        self.ColorBox=TextEdit(Form)
        self.ColorBox.setGeometry(QtCore.QRect(50, 190, 750, 60))
        self.ColorBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.icon2=PushButton(Form)
        self.icon2.setStyleSheet('border:none;')
        self.icon2.setGeometry(40,190,60,60)
        self.icon2.setIcon(FIF.PALETTE)
        self.icon2.setIconSize(QSize(20,20))
        self.text2=LineEdit(Form)
        self.text2.setText('参数颜色')
        self.text2.move(95,195)
        self.text2.setFocusPolicy(QtCore.Qt.NoFocus)
        self.text2.setStyleSheet('border:none;')
        self.text2F=QLabel(Form)
        self.text2F.setText('调整识别窗口的输出参数颜色')
        self.text2F.setGeometry(95,220,260,17)
        self.ColorText=LineEdit(Form)
        self.ColorText.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ColorText.move(620,205)
        self.ColorText.setText('当前颜色:')
        self.ColorButton = ColorPickerButton(QColor("#00ff00"), 'Background Color', self, enableAlpha=False)
        self.ColorButton.move(690,205)
        self.ColorButton.clicked.connect(self.changeColor)
        
        self.ResetBox=TextEdit(Form)
        self.ResetBox.setGeometry(QtCore.QRect(50, 260, 750, 60))
        self.ResetBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.icon3=PushButton(Form)
        self.icon3.setStyleSheet('border:none;')
        self.icon3.setGeometry(40,260,60,60)
        self.icon3.setIcon(FIF.UPDATE)
        self.icon3.setIconSize(QSize(20,20))
        self.text3=LineEdit(Form)
        self.text3.setText('参数重置')
        self.text3.move(95,265)
        self.text3.setFocusPolicy(QtCore.Qt.NoFocus)
        self.text3.setStyleSheet('border:none;')
        self.text3F=QLabel(Form)
        self.text3F.setText('一键将所有阈值等参数恢复到默认值')
        self.text3F.setGeometry(95,290,300,17)
        self.ResetButton=ToolButton(FIF.SYNC,Form)
        self.ResetButton.move(740,275)
        self.ResetButton.clicked.connect(self.ResetPara)
        self.ResetText=LineEdit(Form)
        self.ResetText.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ResetText.setGeometry(620,275,130,40)
        #self.ResetText.move(620,275)
        self.ResetText.setText('进行重置(仅参数):')
        
        self.ReviewBox=TextEdit(Form)
        self.ReviewBox.setGeometry(QtCore.QRect(50, 330, 750, 60))
        self.ReviewBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.icon4=PushButton(Form)
        self.icon4.setStyleSheet('border:none;')
        self.icon4.setGeometry(40,330,60,60)
        self.icon4.setIcon(FIF.FEEDBACK)
        self.icon4.setIconSize(QSize(20,20))
        self.text4=LineEdit(Form)
        self.text4.setText('用户反馈')
        self.text4.move(95,335)
        self.text4.setFocusPolicy(QtCore.Qt.NoFocus)
        self.text4.setStyleSheet('border:none;')
        self.text4F=QLabel(Form)
        self.text4F.setText('提供反馈帮助开发者改进HAND WIGI')
        self.text4F.setGeometry(95,360,300,17)
        self.ReviewButton=PrimaryPushButton('提供反馈',Form,FIF.SEND)
        self.ReviewButton.move(680,345)
        self.ReviewButton.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/George-Attano/HAND-WIGI/issues')))

        self.ProjectBox=TextEdit(Form)
        self.ProjectBox.setGeometry(QtCore.QRect(50, 400, 750, 60))
        self.ProjectBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.icon5=PushButton(Form)
        self.icon5.setStyleSheet('border:none;')
        self.icon5.setGeometry(40,400,60,60)
        self.icon5.setIcon(FIF.INFO)
        self.icon5.setIconSize(QSize(20,20))
        self.text5=LineEdit(Form)
        self.text5.setText('关于')
        self.text5.move(95,405)
        self.text5.setFocusPolicy(QtCore.Qt.NoFocus)
        self.text5.setStyleSheet('border:none;')
        self.text5F=QLabel(Form)
        self.text5F.setText('License:MIT © George-Attano 当前版本 0.2.6')
        self.text5F.setGeometry(95,430,400,17)
        self.ProjectLink=HyperlinkButton(
            url='https://github.com/George-Attano/HAND-WIGI',
            text='Github 工程页面',
            parent=self
        )
        self.ProjectLink.move(665,415)
        self.GitIcon=ToolButton(FIF.GITHUB,Form)
        self.GitIcon.move(650,420)
        self.GitIcon.setFocusPolicy(QtCore.Qt.NoFocus)
        self.GitIcon.setStyleSheet('border:none;')

        self.setQss()
        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def changeColor(self):
        global B,G,R
        B,G,R=self.ColorButton.color.blue(),self.ColorButton.color.green(),self.ColorButton.color.red()

    def ResetPara(self):
        global pressLevel,sensity,FistLevel,ScrollLevel,CooldownTime,thr_angle,thr_angle_thumb,thr_angle_s
        pressLevel=0.92;sensity=15.0;FistLevel=1.05;ScrollLevel=13;CooldownTime=15
        thr_angle=65;thr_angle_thumb=51;thr_angle_s=49
        w.ResetPara()
        InfoBar.success(
            title='重置成功',
            content="所有参数已经恢复到推荐值",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=2000,
            parent=self
        )

    def setQss(self):
        self.icon1.setStyleSheet("border:none;")
        self.icon2.setStyleSheet("border:none;")
        self.icon3.setStyleSheet("border:none;")
        self.icon4.setStyleSheet("border:none;")
        self.icon5.setStyleSheet("border:none;")
        self.GitIcon.setStyleSheet('border:none;')
        if isDarkTheme():
            self.text1.setStyleSheet("color:white;background-color: rgba(0, 0, 0, 0);border:none;")
            self.text2.setStyleSheet("color:white;background-color: rgba(0, 0, 0, 0);border:none;")
            self.text3.setStyleSheet("color:white;background-color: rgba(0, 0, 0, 0);border:none;")
            self.text4.setStyleSheet("color:white;background-color: rgba(0, 0, 0, 0);border:none;")
            self.text5.setStyleSheet("color:white;background-color: rgba(0, 0, 0, 0);border:none;")
            self.ColorText.setStyleSheet("color:white;background-color: rgba(0, 0, 0, 0);border:none;")
            self.ResetText.setStyleSheet("color:white;background-color: rgba(0, 0, 0, 0);border:none;")
            self.ThemeSwitchText.setStyleSheet("color:white;background-color: rgba(0, 0, 0, 0);border:none;")
            self.DisplayWindow.setGeometry(350, 445, 136, 246)
            self.DisplayWindow.setPixmap(QPixmap(os.path.abspath('res/PIC/devil2.png')))
        else:
            self.text1.setStyleSheet("color:blank;background-color: rgba(0, 0, 0, 0);border:none;")
            self.text2.setStyleSheet("color:blank;background-color: rgba(0, 0, 0, 0);border:none;")
            self.text3.setStyleSheet("color:blank;background-color: rgba(0, 0, 0, 0);border:none;")
            self.text4.setStyleSheet("color:blank;background-color: rgba(0, 0, 0, 0);border:none;")
            self.text5.setStyleSheet("color:blank;background-color: rgba(0, 0, 0, 0);border:none;")
            self.ColorText.setStyleSheet("color:blank;background-color: rgba(0, 0, 0, 0);border:none;")
            self.ResetText.setStyleSheet("color:blank;background-color: rgba(0, 0, 0, 0);border:none;")
            self.ThemeSwitchText.setStyleSheet("color:blank;background-color: rgba(0, 0, 0, 0);border:none;")
            self.DisplayWindow.setGeometry(360, 475, 143, 211)
            self.DisplayWindow.setPixmap(QPixmap(os.path.abspath('res/PIC/devil.png')))
        
    def onCheckedChanged(self, isChecked: bool):
        if isChecked:
            text = '暗夜主题：开'
            setTheme(Theme.DARK)
            w.setQss()
            self.setQss()
            w.RecInterface.setQss()
            w.ControlInterface.setQss()
            w.PPTInterface.setQss()
            w.WelcomeInterface.setQss()
            w.setWindowIcon(QIcon(os.path.abspath('res/PIC/3.png')))
            #self.DisplayWindow.setPixmap(QPixmap(os.path.abspath('res/PIC/night.jpg')))
        else:
            text = '暗夜主题：关'
            setTheme(Theme.LIGHT)
            w.setQss()
            self.setQss()
            w.RecInterface.setQss()
            w.ControlInterface.setQss()
            w.PPTInterface.setQss()
            w.WelcomeInterface.setQss()
            w.setWindowIcon(QIcon(os.path.abspath('res/PIC/2.png')))
            #self.DisplayWindow.setPixmap(QPixmap(os.path.abspath('res/PIC/day.jpg')))
        w.RecInterface.RefreshWindow()
        w.ControlInterface.RefreshWindow()
        w.PPTInterface.RefreshWindow()
        w.TutorInterface.setqss()
        self.ThemeSwitch.setText('')
        self.ThemeSwitchText.setText(text)
    
    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Setting_Form", "Setting_Form"))
        #self.DisplayWindow.setText(_translate("Setting_Form", "DisplayWindow"))

class Setting_Window(QWidget, Setting_Form):
    def __init__(self, parent=None):
        super(Setting_Window, self).__init__(parent)
        self.setupUi(self)

class Welcome_Form(object):#首页界面基类
    '''
    首页界面基类
    '''
    def setupUi(self, Form):
        Form.setObjectName("Welcome_Form")
        Form.resize(900, 700)
        
        #self.WelcomeText.setText("Steel Ball Run\nJohnny Joestar 🦄\nGyro Zeppeli 🐴")
        #self.WelcomeText.append('<b><font size="5"><font color=red>%s is invalid!</font><b>' %(line_text))
        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
    
    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Welcome_Form", "Welcome_Form"))
        
class Welcome_Window(QWidget, Welcome_Form):
    def __init__(self, parent=None):
        super(Welcome_Window, self).__init__(parent)
        self.setupUi(self)
        self.QuestionButton = ToolButton(FIF.HELP,self)
        self.QuestionButton.setGeometry(QtCore.QRect(640, 462, 30, 30))
        self.QuestionButton.setToolTip('这个没用')
        ft=self.QuestionButton.font()
        self.QuestionButton.hide()
        ft.setPointSize(11)
        
        self.sound=QSound('res/VOI/Intro.wav')
        self.sound.setLoops(1)

        self.timer1=QTimer(self)
        self.timer1.timeout.connect(self.line1)
        self.timer2=QTimer(self)
        self.timer2.timeout.connect(self.line2)
        self.timer3=QTimer(self)
        self.timer3.timeout.connect(self.line3)
        self.timer4=QTimer(self)
        self.timer4.timeout.connect(self.line4)
        self.timer5=QTimer(self)
        self.timer5.timeout.connect(self.line5)
        self.timer6=QTimer(self)
        self.timer6.timeout.connect(self.line6)
        self.timer7=QTimer(self)
        self.timer7.timeout.connect(self.line7)
        self.timer8=QTimer(self)
        self.timer8.timeout.connect(self.line8)
        self.timer9=QTimer(self)
        self.timer9.timeout.connect(self.line9)
        self.timer10=QTimer(self)
        self.timer10.timeout.connect(self.line10)
        self.timer11=QTimer(self)
        self.timer11.timeout.connect(self.line11)
        self.timer12=QTimer(self)
        self.timer12.timeout.connect(self.line12)
        self.timer13=QTimer(self)
        self.timer13.timeout.connect(self.line13)
        self.timer14=QTimer(self)
        self.timer14.timeout.connect(self.line14)
        self.timer15=QTimer(self)
        self.timer15.timeout.connect(self.line15)
        self.timer16=QTimer(self)
        self.timer16.timeout.connect(self.line16)
        self.timer17=QTimer(self)
        self.timer17.timeout.connect(self.line17)
        self.timer18=QTimer(self)
        self.timer18.timeout.connect(self.line18)
        self.timer19=QTimer(self)
        self.timer19.timeout.connect(self.line19)
        self.timer20=QTimer(self)
        self.timer20.timeout.connect(self.line20)
        self.timer21=QTimer(self)
        self.timer21.timeout.connect(self.line21)
        self.timer22=QTimer(self)
        self.timer22.timeout.connect(self.line22)
        self.timer23=QTimer(self)
        self.timer23.timeout.connect(self.line23)
        self.timer24=QTimer(self)
        self.timer24.timeout.connect(self.line24)
        self.timer25=QTimer(self)
        self.timer25.timeout.connect(self.line25)
        self.timer26=QTimer(self)
        self.timer26.timeout.connect(self.line26)
        self.timer27=QTimer(self)
        self.timer27.timeout.connect(self.line27)
        self.timer28=QTimer(self)
        self.timer28.timeout.connect(self.line28)
        
        self.LOGO=QLabel(self)
        self.LOGO.setGeometry(325,125,150,150)
        self.LOGO.setScaledContents(True)
        self.LOGO.setPixmap(QPixmap(os.path.abspath('res/PIC/1.png')))
        self.Title=QLabel(self)
        self.Title.setGeometry(50,75,720,480)
        self.Title.setScaledContents(True)
        self.logoGIF=QMovie(os.path.abspath('res/GIF/LOGO-3-Black.gif'))
        self.Title.setMovie(self.logoGIF)
        self.logoGIF.stop()
        self.Qbutton=QLabel(self)
        self.Qbutton.setGeometry(100,380,200,200)
        self.Qbutton.setScaledContents(True)
        self.Qbutton.setPixmap(QPixmap(os.path.abspath('res/PIC/qbutton.png')))
        self.Qbutton.hide()
        self.tooltip=QLabel(self)
        self.tooltip.setGeometry(300,380,200,200)
        self.tooltip.setScaledContents(True)
        self.tooltip.setPixmap(QPixmap(os.path.abspath('res/PIC/tooltip.png')))
        self.tooltip.hide()
        self.feedback=QLabel(self)
        self.feedback.setGeometry(500,380,200,200)
        self.feedback.setScaledContents(True)
        self.feedback.setPixmap(QPixmap(os.path.abspath('res/PIC/feedback.png')))
        self.feedback.hide()
        
        self.menuArr=QLabel(self)
        self.menuArr.setGeometry(0,48,32,30)
        self.menuArr.setScaledContents(True)
        self.menuArr.setPixmap(QPixmap(os.path.abspath('res/PIC/arrow.png')))
        self.menuText=LineEdit(self)
        self.menuText.setGeometry(QtCore.QRect(40, 45, 100, 20))
        self.menuText.setFocusPolicy(QtCore.Qt.NoFocus)
        self.menuText.setText('打开菜单栏')
        self.menuText.setFont(ft)
        self.recArr=QLabel(self)
        self.recArr.setGeometry(0,88,32,30)
        self.recArr.setScaledContents(True)
        self.recArr.setPixmap(QPixmap(os.path.abspath('res/PIC/arrow.png')))
        self.recText=LineEdit(self)
        self.recText.setGeometry(QtCore.QRect(40, 85, 140, 20))
        self.recText.setFocusPolicy(QtCore.Qt.NoFocus)
        self.recText.setText('功能一:手势识别')
        self.recText.setFont(ft)
        self.contArr=QLabel(self)
        self.contArr.setGeometry(0,128,32,30)
        self.contArr.setScaledContents(True)
        self.contArr.setPixmap(QPixmap(os.path.abspath('res/PIC/arrow.png')))
        self.contText=LineEdit(self)
        self.contText.setGeometry(QtCore.QRect(40, 125, 140, 20))
        self.contText.setFocusPolicy(QtCore.Qt.NoFocus)
        self.contText.setText('功能二:手势控制')
        self.contText.setFont(ft)
        self.pptArr=QLabel(self)
        self.pptArr.setGeometry(0,168,32,30)
        self.pptArr.setScaledContents(True)
        self.pptArr.setPixmap(QPixmap(os.path.abspath('res/PIC/arrow.png')))
        self.pptText=LineEdit(self)
        self.pptText.setGeometry(QtCore.QRect(40, 165, 150, 20))
        self.pptText.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pptText.setText('功能三:PPT助手')
        self.pptText.setFont(ft)

        self.TutArr=QLabel(self)
        self.TutArr.setGeometry(0,263,32,30)
        self.TutArr.setScaledContents(True)
        self.TutArr.setPixmap(QPixmap(os.path.abspath('res/PIC/arrow.png')))
        self.TutText=LineEdit(self)
        self.TutText.setGeometry(QtCore.QRect(40, 260, 100, 20))
        self.TutText.setFocusPolicy(QtCore.Qt.NoFocus)
        self.TutText.setText('功能手册')
        self.TutText.setFont(ft)

        self.setArr=QLabel(self)
        self.setArr.setGeometry(0,640,32,30)
        self.setArr.setScaledContents(True)
        self.setArr.setPixmap(QPixmap(os.path.abspath('res/PIC/arrow.png')))
        self.setText=LineEdit(self)
        self.setText.setGeometry(QtCore.QRect(40, 635, 100, 20))
        self.setText.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setText.setText('程序设置')
        self.setText.setFont(ft)
        
        self.startLink=QCommandLinkButton(self)
        self.startLink.setText('开始探索HAND WIGI')
        self.startLink.setDescription('In honor of Dishonored')
        self.startLink.setGeometry(325,380,190,60)
        #self.startLink.setIconSize(40)
        self.startLink.clicked.connect(self.start)
        
        self.TutLink=QCommandLinkButton(self)
        self.TutLink.setText('转到功能手册')
        self.TutLink.setDescription('Switch to tutorial')
        self.TutLink.setGeometry(345,560,150,50)
        self.TutLink.clicked.connect(self.Change2Tutor)
        self.TutLink.hide()

        self.setQss()
        self.menuArr.hide();self.menuText.hide()
        self.recArr.hide();self.recText.hide()
        self.contArr.hide();self.contText.hide()
        self.pptArr.hide();self.pptText.hide()
        self.TutArr.hide();self.TutText.hide()
        self.setArr.hide();self.setText.hide()

    def line0(self):
        self.timer1.start(425)
    def line1(self):
        self.timer1.stop()
        self.createLines('欢迎使用HAND WIGI',2000)
        self.timer2.start(2000)
    def line2(self):
        self.timer2.stop()
        self.createLines('这是一个基于mediapipe和OpenCV实现的手势识别功能软件',5120)
        self.timer3.start(5120)
    def line3(self):
        self.timer3.stop()
        self.createLines('现在我将为您介绍本程序的主要界面情况',3940)
        self.timer4.start(3940)
    def line4(self):
        self.timer4.stop()
        self.createLines('您现在看到的是首页欢迎界面',3010)
        self.timer5.start(3010)
    def line5(self):
        self.timer5.stop()
        self.createLines('若要切换到其他界面',1970)
        self.timer6.start(1970)
    def line6(self):
        self.timer6.stop()
        self.createLines('请在左侧导航栏进行切换',2200)
        self.timer7.start(2200)
    def line7(self):
        self.timer7.stop()
        self.createLines('标题栏下方第一个是菜单按钮',2250)
        self.menuArr.show();self.menuText.show()
        self.timer8.start(2250)
    def line8(self):
        self.timer8.stop()
        self.createLines('点击它将展开导航菜单',2850)
        self.timer9.start(2850)
    def line9(self):
        self.timer9.stop()
        self.createLines('您可以在展开菜单栏看到各界面的详细名称',4040)
        self.timer10.start(4040)
    def line10(self):
        self.timer10.stop()
        self.createLines('菜单栏下方依次是程序的三个主要功能界面切换按钮',4970)
        self.timer11.start(4970)
    def line11(self):
        self.timer11.stop()
        self.createLines('第一个功能是手势识别',2130)
        self.recArr.show();self.recText.show()
        self.timer12.start(2130)
    def line12(self):
        self.timer12.stop()
        self.createLines('第二个功能是手势鼠标控制接管',2960)
        self.contArr.show();self.contText.show()
        self.timer13.start(2960)
    def line13(self):
        self.timer13.stop()
        self.createLines('第三个功能是隔空翻页助手',3000)
        self.pptArr.show();self.pptText.show()
        self.timer14.start(3000)
    def line14(self):
        self.timer14.stop()
        self.createLines('您可以在稍后前往探索各个功能',3060)
        self.timer15.start(3060)
    def line15(self):
        self.timer15.stop()
        self.createLines('在当前页面，即左侧选中的爱心页面',3860)
        self.timer16.start(3860)
    def line16(self):
        self.timer16.stop()
        self.createLines('下方的文件夹按钮可以切换到各个功能的详细文本介绍',4970)
        self.TutArr.show();self.TutText.show()
        self.timer17.start(4970)
    def line17(self):
        self.timer17.stop()
        self.createLines('您也能够在功能页面通过Qbutton随时跳转到对应功能的介绍',6090)
        self.Qbutton.show()
        self.timer18.start(6090)
    def line18(self):
        self.timer18.stop()
        self.createLines('跳转到介绍页面后',2020)
        self.timer19.start(2020)
    def line19(self):
        self.timer19.stop()
        self.createLines('您可以点击左上角的返回上一级页面按钮快速回到刚才的功能页面',5980)
        self.timer20.start(5980)
    def line20(self):
        self.timer20.stop()
        self.createLines('若在使用中对个别输入栏作用有疑问',3910)
        self.timer21.start(3910)
    def line21(self):
        self.timer21.stop()
        self.createLines('只需将鼠标悬停在其上方就会出现对应的解释语句',4180)
        self.tooltip.show()
        self.timer22.start(4180)
    def line22(self):
        self.timer22.stop()
        self.createLines('最下方还有设置界面的切换按钮',3780)
        self.setArr.show();self.setText.show()
        self.timer23.start(3780)
    def line23(self):
        self.timer23.stop()
        self.createLines('里面有一些基本的程序设置功能',2220)
        self.timer24.start(2220)
    def line24(self):
        self.timer24.stop()
        self.createLines(r'orz %%%',1950)
        self.timer25.start(1950)
    def line25(self):
        self.timer25.stop()
        self.createLines('如果在使用中遇到问题',2040)
        self.timer26.start(2040)
    def line26(self):
        self.timer26.stop()
        self.createLines('欢迎您进行反馈',1910)
        self.feedback.show()
        self.timer27.start(1910)
    def line27(self):
        self.timer27.stop()
        self.createLines('希望您能够使用顺利，谢谢!',3080)
        self.timer28.start(3080)
    def line28(self):
        self.TutLink.show()
    
    def Change2Tutor(self):
        w.switchTo(w.TutorInterface)

    def createLines(self,text: str,dur:int):
        w = InfoBar.new(
            icon=FIF.GITHUB,
            title='Narrator:',
            content=text,
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.BOTTOM,
            duration=dur,
            parent=self
        )
        w.setCustomBackgroundColor('white', '#202020')
        
    def start(self):
        cv2.waitKey(250)
        self.startLink.hide()
        #self.WelcomeText.show()
        self.sound.play()
        self.line0()

    
    def setQss(self):
        if isDarkTheme():
            self.startLink.setStyleSheet('color:white;')
            self.TutLink.setStyleSheet('color:white;')
            self.pptText.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.recText.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.setText.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.contText.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.TutText.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.menuText.setStyleSheet('''color:white;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.logoGIF=QMovie(os.path.abspath('res/GIF/LOGO 02_white.gif'))
            self.Title.setMovie(self.logoGIF)
            self.logoGIF.stop()
        else:
            self.startLink.setStyleSheet('color:black;')
            self.TutLink.setStyleSheet('color:black;')
            self.pptText.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.recText.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.setText.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.contText.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.menuText.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.TutText.setStyleSheet('''color:black;background-color: rgba(0, 0, 0, 0);border: none;border-bottom: 2px solid qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF00FF,stop: 1 #00FFFF);''')
            self.logoGIF=QMovie(os.path.abspath('res/GIF/LOGO-3-Black.gif'))
            self.Title.setMovie(self.logoGIF)
            self.logoGIF.stop()

class HAND_REC_Window(QWidget, Ui_Form):
    def __init__(self, parent=None):
        super(HAND_REC_Window, self).__init__(parent)
        self.setupUi(self)
        self.Activate=PrimaryPushButton('启动捕捉',self,FIF.SEND)
        self.Activate.move(510,460)
        self.Activate.clicked.connect(self.ActivateCapture)
    def ActivateCapture(self):
        if not mainThread.cap_inited:
            w.createErrorInfoBar()
            return
        global paused
        paused=1-paused
        if paused==0:
            self.Activate.setIcon(FIF.SEND_FILL)
            self.Activate.setText('暂停捕捉')
            self.switchbar.hide()
            self.progressBar.show()
        else:
            self.Activate.setIcon(FIF.SEND)
            self.Activate.setText('启动捕捉')
            self.switchbar.show()
            self.progressBar.hide()
    def ResetButton(self):
        global paused
        if paused==0:
            self.Activate.setIcon(FIF.SEND_FILL)
            self.Activate.setText('暂停捕捉')
        else:
            self.Activate.setIcon(FIF.SEND)
            self.Activate.setText('启动捕捉')
        
class HAND_CONTROL_Window(QWidget, Ui_Form2):
    def __init__(self, parent=None):
        super(HAND_CONTROL_Window, self).__init__(parent)
        self.setupUi(self)
        self.Activate=PrimaryPushButton('启动捕捉',self,FIF.SEND)
        self.Activate.move(510,460)
        self.Activate.clicked.connect(self.ActivateCapture)
    def ActivateCapture(self):
        if not mainThread.cap_inited:
            w.createErrorInfoBar()
            return
        global paused
        paused=1-paused
        if paused==0:
            self.Activate.setIcon(FIF.SEND_FILL)
            self.Activate.setText('暂停捕捉')
            self.switchbar.hide()
            self.progressBar.show()
        else:
            self.Activate.setIcon(FIF.SEND)
            self.Activate.setText('启动捕捉')
            self.switchbar.show()
            self.progressBar.hide()
    def ResetButton(self):
        global paused
        if paused==0:
            self.Activate.setIcon(FIF.SEND_FILL)
            self.Activate.setText('暂停捕捉')
        else:
            self.Activate.setIcon(FIF.SEND)
            self.Activate.setText('启动捕捉')
        
class PPT_ASSIS_Window(QWidget, Ui_Form3):
    def __init__(self, parent=None):
        super(PPT_ASSIS_Window, self).__init__(parent)
        self.setupUi(self)
        self.Activate=PrimaryPushButton('启动捕捉',self,FIF.SEND)
        self.Activate.move(510,460)
        self.Activate.clicked.connect(self.ActivateCapture)
    def ActivateCapture(self):
        if not mainThread.cap_inited:
            w.createErrorInfoBar()
            return
        global paused
        paused=1-paused
        if paused==0:
            self.Activate.setIcon(FIF.SEND_FILL)
            self.Activate.setText('暂停捕捉')
            self.switchbar.hide()
            self.progressBar.show()
        else:
            self.Activate.setIcon(FIF.SEND)
            self.Activate.setText('启动捕捉')
            self.switchbar.show()
            self.progressBar.hide()
    def ResetButton(self):
        global paused
        if paused==0:
            self.Activate.setIcon(FIF.SEND_FILL)
            self.Activate.setText('暂停捕捉')
        else:
            self.Activate.setIcon(FIF.SEND)
            self.Activate.setText('启动捕捉')
        
class TutorForm(object):#总手册窗口基类
    '''
    总手册窗口基类
    '''
    def setupUi(self, Form):
        Form.setObjectName("TutorForm")
        Form.resize(870, 670)
        
        self.DisplayWindow = QtWidgets.QLabel(Form)
        self.DisplayWindow.setGeometry(QtCore.QRect(150, 150, 512, 288))
        self.DisplayWindow.setObjectName("DisplayWindow")
        self.DisplayWindow.setScaledContents(True)
        self.retranslateUi(Form)
        self.logoGIF=QMovie(os.path.abspath('res/GIF/manual1.gif'))
        self.DisplayWindow.setMovie(self.logoGIF)
        self.logoGIF.stop()
        #self.logoGIF.start()
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("TutorForm", "TutorForm"))
        self.DisplayWindow.setText(_translate("TutorForm", "DisplayWindow"))

class TutorWindow(QWidget, TutorForm):
    def __init__(self, parent=None):
        super(TutorWindow, self).__init__(parent)
        self.setupUi(self)
        self.Link1=QCommandLinkButton(self)
        self.Link1.setText('手势识别手册')
        self.Link1.setDescription('Manual for Recog')
        self.Link1.setGeometry(155,450,190,60)
        self.Link1.clicked.connect(self.change1)
        self.Link2=QCommandLinkButton(self)
        self.Link2.setText('手势控制手册')
        self.Link2.setDescription('Manual for control')
        self.Link2.setGeometry(355,450,190,60)
        self.Link2.clicked.connect(self.change2)
        self.Link3=QCommandLinkButton(self)
        self.Link3.setText('PPT助手手册')
        self.Link3.setDescription('Manual for PPTassist')
        self.Link3.setGeometry(555,450,190,60)
        self.Link3.clicked.connect(self.change3)

    def setqss(self):
        if isDarkTheme():
            self.Link1.setStyleSheet('color:white;')
            self.Link2.setStyleSheet('color:white;')
            self.Link3.setStyleSheet('color:white;')
            self.logoGIF=QMovie(os.path.abspath('res/GIF/manual2.gif'))
            self.DisplayWindow.setMovie(self.logoGIF)
            self.logoGIF.stop()
        else:
            self.Link1.setStyleSheet('color:black;')
            self.Link2.setStyleSheet('color:black;')
            self.Link3.setStyleSheet('color:black;')
            self.logoGIF=QMovie(os.path.abspath('res/GIF/manual1.gif'))
            self.DisplayWindow.setMovie(self.logoGIF)
            self.logoGIF.stop()

    def change1(self):
        w.switchTo(w.TutorInterface_1)
    def change2(self):
        w.switchTo(w.TutorInterface_2)
    def change3(self):
        w.switchTo(w.TutorInterface_3)

class TutorForm1(object):#手势识别手册窗口基类
    '''
    手势识别手册窗口基类
    '''
    def setupUi(self, Form):
        Form.setObjectName("TutorForm1")
        Form.resize(870, 670)
        
        self.DisplayWindow = QtWidgets.QLabel(Form)
        self.DisplayWindow.setGeometry(QtCore.QRect(10, 20, 850, 650))
        self.DisplayWindow.setObjectName("DisplayWindow")
        self.DisplayWindow.setScaledContents(True)
        self.retranslateUi(Form)
        self.DisplayWindow.setPixmap(QPixmap(os.path.abspath('res/PIC/Tut-1.png')))
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("TutorForm1", "TutorForm1"))
        self.DisplayWindow.setText(_translate("TutorForm1", "DisplayWindow"))

class Tutor1Window(QWidget,TutorForm1):
    def __init__(self, parent=None):
        super(Tutor1Window, self).__init__(parent)
        self.setupUi(self)

class TutorForm2(object):#手势控制手册窗口基类
    '''
    手势控制手册窗口基类
    '''
    def setupUi(self, Form):
        Form.setObjectName("TutorForm2")
        Form.resize(870, 670)
        
        self.DisplayWindow = QtWidgets.QLabel(Form)
        self.DisplayWindow.setGeometry(QtCore.QRect(10, 20, 850, 650))
        self.DisplayWindow.setObjectName("DisplayWindow")
        self.DisplayWindow.setScaledContents(True)
        self.retranslateUi(Form)
        self.DisplayWindow.setPixmap(QPixmap(os.path.abspath('res/PIC/Tut-2.png')))
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("TutorForm2", "TutorForm2"))
        self.DisplayWindow.setText(_translate("TutorForm2", "DisplayWindow"))

class Tutor2Window(QWidget,TutorForm2):
    def __init__(self, parent=None):
        super(Tutor2Window, self).__init__(parent)
        self.setupUi(self)

class TutorForm3(object):#PPT助手手册窗口基类
    '''
    PPT助手手册窗口基类
    '''
    def setupUi(self, Form):
        Form.setObjectName("TutorForm3")
        Form.resize(870, 670)
        
        self.DisplayWindow = QtWidgets.QLabel(Form)
        self.DisplayWindow.setGeometry(QtCore.QRect(10, 20, 850, 650))
        self.DisplayWindow.setObjectName("DisplayWindow")
        self.DisplayWindow.setScaledContents(True)
        self.retranslateUi(Form)
        self.DisplayWindow.setPixmap(QPixmap(os.path.abspath('res/PIC/Tut-3.png')))
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("TutorForm3", "TutorForm3"))
        self.DisplayWindow.setText(_translate("TutorForm3", "DisplayWindow"))

class Tutor3Window(QWidget,TutorForm3):
    def __init__(self, parent=None):
        super(Tutor3Window, self).__init__(parent)
        self.setupUi(self)

def vector2angle(v1,v2):#二维向量转角度
    '''
        二维向量转角度
    '''
    v1_x=v1[0]
    v1_y=v1[1]
    v2_x=v2[0]
    v2_y=v2[1]
    try:
        angle_= math.degrees(math.acos((v1_x*v2_x+v1_y*v2_y)/(((v1_x**2+v1_y**2)**0.5)*((v2_x**2+v2_y**2)**0.5))))
    except:
        angle_ =65535.
    if angle_ > 180.:
        angle_ = 65535.
    return angle_

def hand_angle(hand_points):#关键点坐标转各手势弯曲角度
    '''
        关键点坐标转各手势弯曲角度
    '''
    angle_list = []
    #大拇指
    angle_ = vector2angle(
        ((int(hand_points[0][0])- int(hand_points[2][0])),(int(hand_points[0][1])-int(hand_points[2][1]))),
        ((int(hand_points[3][0])- int(hand_points[4][0])),(int(hand_points[3][1])- int(hand_points[4][1])))
        )
    angle_list.append(angle_)
    #食指
    angle_ = vector2angle(
        ((int(hand_points[0][0])-int(hand_points[6][0])),(int(hand_points[0][1])- int(hand_points[6][1]))),
        ((int(hand_points[7][0])- int(hand_points[8][0])),(int(hand_points[7][1])- int(hand_points[8][1])))
        )
    angle_list.append(angle_)
    #中指
    angle_ = vector2angle(
        ((int(hand_points[0][0])- int(hand_points[10][0])),(int(hand_points[0][1])- int(hand_points[10][1]))),
        ((int(hand_points[11][0])- int(hand_points[12][0])),(int(hand_points[11][1])- int(hand_points[12][1])))
        )
    angle_list.append(angle_)
    #无名指
    angle_ = vector2angle(
        ((int(hand_points[0][0])- int(hand_points[14][0])),(int(hand_points[0][1])- int(hand_points[14][1]))),
        ((int(hand_points[15][0])- int(hand_points[16][0])),(int(hand_points[15][1])- int(hand_points[16][1])))
        )
    angle_list.append(angle_)
    #小拇指
    angle_ = vector2angle(
        ((int(hand_points[0][0])- int(hand_points[18][0])),(int(hand_points[0][1])- int(hand_points[18][1]))),
        ((int(hand_points[19][0])- int(hand_points[20][0])),(int(hand_points[19][1])- int(hand_points[20][1])))
        )
    angle_list.append(angle_)
    return angle_list

thr_angle = 65.  #手指闭合则大于这个值（大拇指除外）
thr_angle_thumb = 51.  #大拇指闭合则大于这个值
thr_angle_s = 49.  #手指张开则小于这个值

def gesture_recog(angle_list):#通过判断各个手指弯曲状况来识别手势
    '''
        通过判断各个手指弯曲状况来识别手势
    '''
    global thr_angle,thr_angle_thumb,thr_angle_s
    
    gesture_str = "Unknown"
    if 65535. not in angle_list:
        if (angle_list[0]>thr_angle_thumb) and (angle_list[1]>thr_angle) and (angle_list[2]>thr_angle) and (angle_list[3]>thr_angle) and (angle_list[4]>thr_angle):
            gesture_str = "Number 0"
        elif (angle_list[0]>thr_angle_thumb)  and (angle_list[1]<thr_angle_s) and (angle_list[2]>thr_angle) and (angle_list[3]>thr_angle) and (angle_list[4]>thr_angle):
            gesture_str = "Number 1"
        elif (angle_list[0]>thr_angle_thumb)  and (angle_list[1]<thr_angle_s) and (angle_list[2]<thr_angle_s) and (angle_list[3]>thr_angle) and (angle_list[4]>thr_angle):
            gesture_str = "Number 2"
        elif (angle_list[0]>thr_angle_thumb)  and (angle_list[1]<thr_angle_s) and (angle_list[2]<thr_angle_s) and (angle_list[3]<thr_angle_s) and (angle_list[4]>thr_angle):
            gesture_str = "Number 3"
        elif (angle_list[0]>thr_angle_thumb) and (angle_list[1]<thr_angle_s) and (angle_list[2]<thr_angle_s) and (angle_list[3]<thr_angle_s) and (angle_list[4]<thr_angle_s):
            gesture_str = "Number 4"
        elif (angle_list[0]<thr_angle_s) and (angle_list[1]<thr_angle_s) and (angle_list[2]<thr_angle_s) and (angle_list[3]<thr_angle_s) and (angle_list[4]<thr_angle_s):
            gesture_str = "Number 5"
        elif (angle_list[0]<thr_angle_s)  and (angle_list[1]>thr_angle) and (angle_list[2]>thr_angle) and (angle_list[3]>thr_angle) and (angle_list[4]<thr_angle_s):
            gesture_str = "Number 6"
        elif (angle_list[0]<thr_angle_s)  and (angle_list[1]<thr_angle_s) and (angle_list[2]>thr_angle) and (angle_list[3]>thr_angle) and (angle_list[4]>thr_angle):
            gesture_str = "Number 8"
        elif (angle_list[0]>thr_angle_thumb) and (angle_list[1]>thr_angle) and (angle_list[2]>thr_angle) and (angle_list[3]>thr_angle) and (angle_list[4]<thr_angle_s):
            gesture_str = "Despise"
        elif (angle_list[0]<thr_angle_s)  and (angle_list[1]>thr_angle) and (angle_list[2]>thr_angle) and (angle_list[3]>thr_angle) and (angle_list[4]>thr_angle):
            gesture_str = "Thumb Up"
        elif (angle_list[0]>thr_angle_thumb) and (angle_list[1]>thr_angle) and (angle_list[2]<thr_angle_s) and (angle_list[3]>thr_angle) and (angle_list[4]>thr_angle):
            gesture_str = "F*ck"
        elif (angle_list[0]>thr_angle_thumb) and (angle_list[1]>thr_angle) and (angle_list[2]<thr_angle_s) and (angle_list[3]<thr_angle_s) and (angle_list[4]<thr_angle_s):
            gesture_str = "Okaydokay"
        elif (angle_list[0]<thr_angle_s)  and (angle_list[1]<thr_angle_s) and (angle_list[2]>thr_angle) and (angle_list[3]>thr_angle) and (angle_list[4]<thr_angle_s):
            gesture_str = "SpiderMan"
        elif (angle_list[0]>thr_angle_thumb)  and (angle_list[1]<thr_angle_s) and (angle_list[2]>thr_angle) and (angle_list[3]>thr_angle) and (angle_list[4]<thr_angle_s):
            gesture_str = "Rock&Roll"
        
    return gesture_str

def four_finger_turned(angle_list):#检测拇指外四指弯曲
    '''
    检测拇指外四指弯曲
    '''
    if 65535. not in angle_list:
        if (angle_list[1]>40) and (angle_list[2]>40) and (angle_list[3]>40) and (angle_list[4]>40):return True
        else:return False
    else:return False

def control_paused(angle_list):#检测严格的手掌张开
    '''
    检测严格的手掌张开
    '''
    if (angle_list[0]<=25) and (angle_list[1]<=25) and (angle_list[2]<=25) and (angle_list[3]<=25) and (angle_list[4]<=25):return True
    return False

class WorkThread(QThread):#手势识别线程
    def __init__(self):
        super(WorkThread,self).__init__()
        self.cap_inited=False
        self.controlx=0;self.controly=0
        global B,G,R
        self.stable_press_cnt=0
        self.press_cooldown=0
        self.moving=0
    def run(self):
        global cTime;global pTime;global capturing;global status;global paused
        cap=cv2.VideoCapture(0)
        cap.set(3,640)
        cap.set(4,360)
        self.w=640;self.h=360
        self.window_w,self.window_h=wigi.size()
        self.img=None
        self.fist_status=False
        self.lastx=0;self.lasty=0
        self.upsum=0;self.downsum=0
        self.cooldown=0;self.period=-1
        self.firstx=0;self.firsty=0
        self.Countup=0;self.Countdown=0
        self.error_reported=False
        while capturing==1:
            #print(1)
            if self.cap_inited and paused:
                cv2.waitKey(30)
                continue
            #print(2)
            success,self.img=cap.read()
            if not success:
                if not self.error_reported:
                    w.createErrorInfoBar2()
                    self.error_reported=True
                continue
            #print(3)
            if(self.cap_inited==False):
                self.cap_inited=True
                w.stateTooltip.setContent('初始化完成😆!')
                w.stateTooltip.setState(True)
                w.stateTooltip=None
                QApplication.processEvents()
                continue
                #e.loadingGIF.stop()#不由自己stop会有warning
                #e.LoadingWindow.hide()
            self.img=cv2.flip(self.img,1)
            QApplication.processEvents()
            #print(4)
            if status==1:
                self.hand_recog(self.img)
            elif status==2:
                self.hand_control(self.img)
            elif status==3:
                self.PPT_control(self.img)
            QApplication.processEvents()
            cv2.waitKey(10)
            #print(5)
            
    def hand_recog(self,img):
        global cTime;global pTime
        #print(11)
        imgRGB=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        #print(12)
        results=hands1.process(imgRGB)
        #print(13)
        if results.multi_handedness:
            for hand_label in results.multi_handedness:
                hand_direction=str(hand_label).split('"')[1]
                #print(hand_direction)
                cv2.putText(img,f'{str(hand_direction)} Hand',(410,40),0,1.3,(B,G,R),2)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                if PaintKeypoints:
                    mpDraw.draw_landmarks(img, hand_landmarks, mpHands.HAND_CONNECTIONS)
                keypoints = []
                z=0.0
                for i in range(21):
                    x = hand_landmarks.landmark[i].x*img.shape[1]
                    y = hand_landmarks.landmark[i].y*img.shape[0]
                    keypoints.append((x,y))
                if keypoints:
                    angle_list = hand_angle(keypoints)
                    gesture = gesture_recog(angle_list)
                    #print(gesture_str)
                    #print(angle_list[0])
                    if gesture=="Thumb Up":
                        (x_thumb,y_thumb)=keypoints[4]
                        (x_wrist,y_wrist)=keypoints[0]
                        if y_thumb>y_wrist:gesture="Thumb Down"
                    if gesture=="Unknown" and (angle_list[2]<thr_angle_s) and (angle_list[3]<thr_angle_s) and (angle_list[4]<thr_angle_s):
                        landmarks=hand_landmarks.landmark
                        x_thump_tip=landmarks[mpHands.HandLandmark.THUMB_TIP].x;y_thump_tip=landmarks[mpHands.HandLandmark.THUMB_TIP].y
                        x_index_tip=landmarks[mpHands.HandLandmark.INDEX_FINGER_TIP].x;y_index_tip=landmarks[mpHands.HandLandmark.INDEX_FINGER_TIP].y
                        z=fabs(float((landmarks[mpHands.HandLandmark.THUMB_TIP].z+landmarks[mpHands.HandLandmark.INDEX_FINGER_TIP].z)/2.0))
                        s=sqrt(float((x_index_tip-x_thump_tip)*(x_index_tip-x_thump_tip)+(y_index_tip-y_thump_tip)*(y_index_tip-y_thump_tip)))
                        ratiofinger=s/z
                        if ratiofinger<pressLevel:
                            gesture='Okaydokay'
                    if gesture=="Thumb Down":
                        cv2.putText(img,gesture,(380,70),0,1.3,(B,G,R),2)
                    else:
                        cv2.putText(img,gesture,(410,70),0,1.3,(B,G,R),2)
                    if PaintPara:
                        cv2.putText(img,f'Finger Angles:{int(angle_list[0])},{int(angle_list[1])},{int(angle_list[2])},{int(angle_list[3])},{int(angle_list[4])}',(20,345),0,1.1,(B,G,R),2)
                    
        cTime=time.time()
        fps=1/(cTime-pTime)
        pTime=cTime
        if PaintFPS:
            cv2.putText(img,f'FPS:{int(fps)}',(10,30),cv2.FONT_HERSHEY_PLAIN,2,(B,G,R),2)
        imgRGB=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        qimg=QImage(imgRGB.data,imgRGB.shape[1],imgRGB.shape[0],QImage.Format_RGB888)
        if paused!=1:
            w.RecInterface.DisplayWindow.setPixmap(QPixmap.fromImage(qimg))
     
    def hand_control(self,img):
        global cTime;global pTime;global sensity;global mouseControl;global pressLevel;global windowH;global windowW;global FistLevel
        imgRGB=cv2.cvtColor(self.img,cv2.COLOR_BGR2RGB)
        #results=hands.process(imgRGB)
        results=hands1.process(imgRGB)
        if results.multi_hand_landmarks:
            for result_landmarks in results.multi_hand_landmarks:
                landmarks=result_landmarks.landmark
                x_thump_tip=landmarks[mpHands.HandLandmark.THUMB_TIP].x;y_thump_tip=landmarks[mpHands.HandLandmark.THUMB_TIP].y
                x_index_tip=landmarks[mpHands.HandLandmark.INDEX_FINGER_TIP].x;y_index_tip=landmarks[mpHands.HandLandmark.INDEX_FINGER_TIP].y
                z=fabs(float((landmarks[mpHands.HandLandmark.THUMB_TIP].z+landmarks[mpHands.HandLandmark.INDEX_FINGER_TIP].z)/2.0))
                s=sqrt(float((x_index_tip-x_thump_tip)*(x_index_tip-x_thump_tip)+(y_index_tip-y_thump_tip)*(y_index_tip-y_thump_tip)))
                ratiofinger=s/z
                ratiofinger=round(ratiofinger,3)
                Fisted=False
                #判断握拳暂停移动
                keypoints = []
                for i in range(21):
                    x = landmarks[i].x*img.shape[1]
                    y = landmarks[i].y*img.shape[0]
                    keypoints.append((x,y))
                if keypoints:
                    z=fabs(float(landmarks[0].z))
                    points_array = np.array(keypoints, dtype=np.int32)
                    hull1=cv2.convexHull(points_array)#完整手部凸包
                    angle_list = hand_angle(keypoints)
                    gesture = gesture_recog(angle_list)
                    if control_paused(angle_list):#严格手掌张开时暂停
                        Fisted=True
                        cv2.polylines(img, [hull1], True, (0, 255, 0), 2)
                        cv2.putText(img,"Suspended",(420,40),0,1.3,(B,G,R),2)
                if not Fisted:
                    cx=int(x_thump_tip*self.w);cy=int(y_thump_tip*self.h)
                    cv2.circle(img,(cx,cy),4,(0,0,255),cv2.FILLED)
                    cx=int(x_index_tip*self.w);cy=int(y_index_tip*self.h)
                    cv2.circle(img,(cx,cy),4,(0,0,255),cv2.FILLED)
                    cv2.putText(img,f"Ratio={float(ratiofinger)}",(410,80),0,1.3,(B,G,R),2)
                    if ratiofinger<pressLevel:
                        if self.press_cooldown==0:
                            self.stable_press_cnt+=1
                        if mouseControl:
                            #wigi.click()
                            if self.stable_press_cnt==1:
                                wigi.mouseDown()
                            elif self.stable_press_cnt>=30 and not self.moving:
                                wigi.mouseUp()
                                wigi.rightClick()
                                self.stable_press_cnt=0
                                self.press_cooldown=40
                            
                        #print("pressed")
                        cv2.putText(img,"Pressed",(450,40),0,1.3,(B,G,R),2)
                    else:
                        if mouseControl and self.stable_press_cnt!=0:
                            wigi.mouseUp()
                        self.stable_press_cnt=0
                        self.moving=0
                        cv2.putText(img,"Not Pressed",(390,40),0,1.3,(B,G,R),2)
                            
                    x_wrist=(landmarks[mpHands.HandLandmark.WRIST].x+landmarks[mpHands.HandLandmark.MIDDLE_FINGER_MCP].x)/2;y_wrist=(landmarks[mpHands.HandLandmark.WRIST].y+landmarks[mpHands.HandLandmark.MIDDLE_FINGER_MCP].y)/2
                    cx=int(x_wrist*self.w);cy=int(y_wrist*self.h)
                    cv2.circle(img,(cx,cy),7,(255,255,0),cv2.FILLED)                #cx-controlx                               cy-controly
                    if mouseControl and self.controlx!=0 and self.controly!=0 and (abs(x_wrist*self.w-self.controlx)>1 or abs(y_wrist*self.h-self.controly)>1):
                        if self.stable_press_cnt>=2:
                            self.moving=1
                        targetx,targety=wigi.position()
                        targetx+=int((cx-self.controlx)*(W/windowW)*sensity)
                        targety+=int((cy-self.controly)*(H/windowH)*sensity)
                        #targetx,targety=int(x_wrist*self.window_w*sensity),int(y_wrist*self.window_h*sensity)
                        targetx=min(targetx,windowW-10);targetx=max(targetx,10)
                        targety=min(targety,windowH-10);targety=max(targety,10)
                        #print(targetx,targety)
                        wigi.moveTo(targetx,targety,duration=0.0,_pause=False) 
                    self.controlx,self.controly=x_wrist*self.w,y_wrist*self.h
                else:
                    if mouseControl and self.stable_press_cnt!=0:
                        wigi.mouseUp()
                    self.controlx,self.controly=0,0
                    self.stable_press_cnt=0
                    self.moving=0
                    self.cooldown=8
        if self.press_cooldown!=0:
            self.press_cooldown-=1
            
        cTime=time.time()
        fps=1/(cTime-pTime)
        pTime=cTime
        cv2.putText(img,f'FPS:{int(fps)}',(10,30),cv2.FONT_HERSHEY_PLAIN,2,(B,G,R),2)
        imgRGB=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        qimg=QImage(imgRGB.data,imgRGB.shape[1],imgRGB.shape[0],QImage.Format_RGB888)
        if paused!=1:
            w.ControlInterface.DisplayWindow.setPixmap(QPixmap.fromImage(qimg))
        
    def PPT_control(self,img):
        global cTime;global pTime;global FistLevel;global ScrollLevel;global CooldownTime;global PaintHux
        imgRGB=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        results=hands1.process(imgRGB)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                #判定握拳
                keypoints = []
                other_points=[]
                pnt=None;pnt2=None;pnt3=None#拇指从上往下三个关键点
                for i in range(21):
                    x = hand_landmarks.landmark[i].x*img.shape[1]
                    y = hand_landmarks.landmark[i].y*img.shape[0]
                    keypoints.append((x,y))
                    if i!=4 and i!=3:
                        other_points.append((x,y))
                    if i==4:pnt=(int(x),int(y))
                    elif i==3:pnt2=(int(x),int(y))
                    elif i==2:pnt3=(int(x),int(y))
                if keypoints:
                    z=fabs(float(hand_landmarks.landmark[0].z))
                    points_array = np.array(keypoints, dtype=np.int32)
                    other_array=np.array(other_points, dtype=np.int32)
                    hull1=cv2.convexHull(points_array)#完整手部凸包
                    hull2=cv2.convexHull(other_array)#删除拇指的手部凸包
                    if PaintHux:
                        cv2.polylines(img, [hull2], True, (B,G,R), 2)#凸包
                    area = cv2.contourArea(hull1)#凸包面积
                    distance = -cv2.pointPolygonTest(hull2, pnt, True)#计算点到多边形(此处就是凸包)距离 此处取反了
                    (x1,y1)=pnt2;(x2,y2)=pnt3
                    lenth=int(math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)))#拇指第二关节长度
                    ratio3=distance/lenth#拇指接近掌心程度 负数表示直接在凸包里面了
                    #print(ratio3)
                    (x, y), radius = cv2.minEnclosingCircle(hull1)
                    center = (int(x), int(y))
                    radius = int(radius)
                    if PaintHux:
                        cv2.line(img,pnt,pnt2,(B,G,R),2)
                        cv2.line(img,pnt2,pnt3,(B,G,R),2)
                        cv2.circle(img, center, radius, (B,G,R), 2)
                    s=3.141592*radius*radius
                    ratio=s/area#凸包占最小圆覆盖比例 
                    #print(ratio)
                    angle_list = hand_angle(keypoints)
                    gesture = gesture_recog(angle_list)
                    landmarks=hand_landmarks.landmark
                    z=fabs(float(landmarks[mpHands.HandLandmark.THUMB_TIP].z))
                    x_thump_tip=landmarks[mpHands.HandLandmark.THUMB_TIP].x;y_thump_tip=landmarks[mpHands.HandLandmark.THUMB_TIP].y
                    x_index_pip=landmarks[mpHands.HandLandmark.INDEX_FINGER_PIP].x;y_index_pip=landmarks[mpHands.HandLandmark.INDEX_FINGER_PIP].y
                    sw=sqrt(float((x_thump_tip-x_index_pip)*(x_thump_tip-x_index_pip)+(y_thump_tip-y_index_pip)*(y_thump_tip-y_index_pip)))
                    ratio2=sw/z
                    #print(ratio,end=' ');print(ratio3)
                    if gesture=='0' or (four_finger_turned(angle_list) and ratio<2.25 and (ratio2<FistLevel or ratio3<FistLevel*0.65)):#握拳的融合判定
                        cv2.putText(img,"Fisted",(460,40),0,1.3,(B,G,R),2)
                        cx,cy=landmarks[mpHands.HandLandmark.WRIST].x*img.shape[1],landmarks[mpHands.HandLandmark.WRIST].y*img.shape[0]
                        #print(cx,end=' ')
                        #print(cy)
                        if self.fist_status:
                            deltax=cx-self.lastx
                            deltay=cy-self.lasty
                            if self.cooldown==0:
                                if deltay>1.3:
                                    self.downsum+=1
                                elif deltay<-1.3:
                                    self.upsum+=1
                            
                        self.lastx,self.lasty=cx,cy
                        self.fist_status=True
                        if self.period==-1:
                            self.period=0
                            self.firstx,self.firsty=cx,cy
                    else:
                        #未握拳
                        cv2.putText(img,"Not Fisted",(410,40),0,1.3,(B,G,R),2)
                        self.fist_status=False
                        self.lastx=self.lasty=self.downsum=self.upsum=0
                        self.period=-1
        else:
            #手势=NONE
            self.fist_status=False
            self.lastx=self.lasty=self.downsum=self.upsum=self.cooldown=0
            self.period=-1
        if self.period!=-1:
            self.period+=1
        if self.cooldown!=0:
            #print('cooling down')
            cv2.putText(img,'Cooling Down',(410,160),0,1.0,(B,G,R),2)
        if self.cooldown==0:
            if self.period==2*(20-ScrollLevel)+1 or self.upsum>=20-ScrollLevel or self.downsum>=20-ScrollLevel:
                if self.upsum>=20-ScrollLevel:
                    self.Countup+=1
                    if PPTcontrol:
                        wigi.press('pagedown')
                    self.cooldown=CooldownTime
                if self.downsum>=20-ScrollLevel:
                    self.Countdown+=1
                    if PPTcontrol:
                        wigi.press('pageup')
                    self.cooldown=CooldownTime
                if self.period==2*(20-ScrollLevel)+1:
                    pass
                    #print('timeup')
                #if self.cooldown==0:
                #    self.cooldown=1
                self.lastx=self.lasty=self.downsum=self.upsum=0
                self.period=-1
                
        else:
            self.cooldown-=1
        cTime=time.time()
        fps=1/(cTime-pTime)
        pTime=cTime
        cv2.putText(img,f'FPS:{int(fps)}',(10,30),cv2.FONT_HERSHEY_PLAIN,2,(B,G,R),2)
        cv2.putText(img,f'Pageups:{int(self.Countup)}',(415,80),0,1.0,(B,G,R),2)
        cv2.putText(img,f'Pagedowns:{int(self.Countdown)}',(415,120),0,1.0,(B,G,R),2)
        imgRGB=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        qimg=QImage(imgRGB.data,imgRGB.shape[1],imgRGB.shape[0],QImage.Format_RGB888)
        if paused!=1:
            w.PPTInterface.DisplayWindow.setPixmap(QPixmap.fromImage(qimg))

class Window(FramelessWindow):#主窗口

    def __init__(self):
        super().__init__()
        self.setTitleBar(CustomTitleBar(self))
        self.setResizeEnabled(False)

        self.hBoxLayout = QHBoxLayout(self)
        self.navigationInterface = NavigationInterface(
            self, showMenuButton=True, showReturnButton=True)
        self.stackWidget = QStackedWidget(self)

        # create sub interface
        
        self.RecInterface = HAND_REC_Window()
        #self.RecInterface.DisplayWindow.setPixmap(QPixmap(os.path.abspath('1.jpeg')))
        self.ControlInterface = HAND_CONTROL_Window()
        self.PPTInterface = PPT_ASSIS_Window()
        self.WelcomeInterface = Welcome_Window()
        self.settingInterface = Setting_Window()
        self.TutorInterface = TutorWindow()
        self.TutorInterface_1= Tutor1Window()
        self.TutorInterface_2= Tutor2Window()
        self.TutorInterface_3= Tutor3Window()

        # initialize layout
        self.initLayout()

        # add items to navigation interface
        self.initNavigation()

        self.initWindow()
        
        self.stateTooltip = StateToolTip('正在初始化模型与相机', '      预计时间<20s,请耐心等待', self)
        self.stateTooltip.move(650, 50)

    def initLayout(self):
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addWidget(self.stackWidget)
        self.hBoxLayout.setStretchFactor(self.stackWidget, 1)

        self.titleBar.raise_()
        self.navigationInterface.displayModeChanged.connect(self.titleBar.raise_)

    def initNavigation(self):
        self.addSubInterface(self.RecInterface, FIF.CAMERA, '手势识别/HAND_REC')
        self.addSubInterface(self.ControlInterface, FIF.VIEW, '手势控制/HAND_CONTROL')
        self.addSubInterface(self.PPTInterface, FIF.SCROLL, 'PPT助手/PPT_ASSIS')

        self.navigationInterface.addSeparator()
        self.addSubInterface(self.WelcomeInterface, FIF.HEART, 'Welcome Page', NavigationItemPosition.SCROLL)
        self.navigationInterface.addSeparator(NavigationItemPosition.SCROLL)

        self.addSubInterface(self.TutorInterface,FIF.FOLDER,'功能手册/Tutorial',NavigationItemPosition.SCROLL)
        self.addSubInterface(self.TutorInterface_1,FIF.CAMERA,'@手势识别/HAND_REC',parent=self.TutorInterface)
        self.addSubInterface(self.TutorInterface_2,FIF.VIEW,'@手势控制/HAND_CONTROL',parent=self.TutorInterface)
        self.addSubInterface(self.TutorInterface_3,FIF.SCROLL,'@PPT助手/PPT_ASSIS',parent=self.TutorInterface)
        # add custom widget to bottom
        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=AvatarWidget(),
            onClick=self.showMessageBox,
            position=NavigationItemPosition.BOTTOM
        )

        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置/Settings', NavigationItemPosition.BOTTOM)

        #!IMPORTANT: don't forget to set the default route key
        #self.navigationInterface.setDefaultRouteKey(self.RecInterface.objectName())
        qrouter.setDefaultRouteKey(self.stackWidget,self.WelcomeInterface.objectName())
        # set the maximum width
        # self.navigationInterface.setExpandWidth(300)

        self.stackWidget.currentChanged.connect(self.onCurrentInterfaceChanged)
        self.stackWidget.setCurrentIndex(3)

    def initWindow(self):
        self.resize(W, H)
        self.setWindowIcon(QIcon(os.path.abspath('res/PIC/2.png')))
        self.setWindowTitle('HAND WIGI')
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

        self.setQss()

    def addSubInterface(self, interface, icon, text: str, position=NavigationItemPosition.TOP, parent=None):
        """ add sub interface """
        self.stackWidget.addWidget(interface)
        self.navigationInterface.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            position=position,
            tooltip=text,
            parentRouteKey=parent.objectName() if parent else None
        )
    
    def setQss(self):
        color = 'dark' if isDarkTheme() else 'light'
        with open(f'resource/{color}/demo.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())
        #self.settingInterface.icon1.setStyleSheet("border:none;")

    def createInterfaceInfoBar(self):
        # convenient class mothod
        ico=None;txt=None
        if status==1:
            ico=FIF.CAMERA
            txt='手势识别'
        elif status==2:
            ico=FIF.VIEW
            txt='手势控制'
        else:
            ico=FIF.SCROLL
            txt='PPT助手'
        w = InfoBar.new(
            icon=FIF.ACCEPT if ico==None else ico,
            title='Func',
            content=txt,
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP,
            duration=1500,
            parent=self
        )
        w.setCustomBackgroundColor('#00ffff', '#007575')

    def switchTo(self, widget):
        global status;global paused
        last_status=status
        self.stackWidget.setCurrentWidget(widget)
        status=self.stackWidget.currentIndex()+1
        #print(status)
        if status!=last_status:
            paused=1
            mainThread.controlx=mainThread.controly=0
            if status>=1 and status<=3:
                self.createInterfaceInfoBar()
            self.RecInterface.ResetButton()
            self.ControlInterface.ResetButton()
            self.PPTInterface.ResetButton()
            if status==1:
                self.RecInterface.SwitchBar()
            elif status==2:
                self.ControlInterface.SwitchBar()
            elif status==3:
                self.PPTInterface.SwitchBar()
            elif status==4:
                self.WelcomeInterface.logoGIF.start()
            elif status==5:
                self.TutorInterface.logoGIF.start()
                
            if last_status==1:
                self.RecInterface.switchbar.setValue(0)
                self.RecInterface.progressBar.hide()
                self.RecInterface.RefreshWindow()
            elif last_status==2:
                self.ControlInterface.switchbar.setValue(0)
                self.ControlInterface.progressBar.hide()
                self.ControlInterface.RefreshWindow()
            elif last_status==3:
                self.PPTInterface.switchbar.setValue(0)
                self.PPTInterface.progressBar.hide()
                self.PPTInterface.RefreshWindow()
            elif last_status==4:
                self.WelcomeInterface.logoGIF.stop()
            elif last_status==5:
                self.TutorInterface.logoGIF.stop()
        
    def onCurrentInterfaceChanged(self, index):
        widget = self.stackWidget.widget(index)
        self.navigationInterface.setCurrentItem(widget.objectName())
        qrouter.push(self.stackWidget,widget.objectName())

    def ResetPara(self):
        self.RecInterface.ResetPara()
        self.ControlInterface.ResetPara()
        self.PPTInterface.ResetPara()

    def createErrorInfoBar(self):
        InfoBar.error(
            title='启动错误',
            content="模型与相机尚未初始化完成!\n若您已经等待很久还未能启动,请联系开发者反馈",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,    # won't disappear automatically
            parent=self
        )
        
    def createErrorInfoBar2(self):
        InfoBar.error(
            title='初始化异常',
            content="无法初始化模型与相机!\n请检查默认相机设置是否正常.仍存在问题请联系开发者解决",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,    # won't disappear automatically
            parent=self
        )

    def showMessageBox(self):
        w = MessageBox(
            'WoW!!!😅',
            '你发现了开发者的头像,但是他并不打算让你也换🤗',
            self
        )
        w.exec()

    def showMaxnotice(self):
        w = MessageBox(
            'Developer Notice:',
            '因为固定了图像处理大小以保证运行帧率和显示效果\n程序大小已经被锁定(同时也懒得做大窗口的排版)',
            self
        )
        w.exec()

    def resizeEvent(self, e):
        self.titleBar.move(46, 0)
        self.titleBar.resize(self.width()-46, self.titleBar.height())

capturing=1;status=4;paused=1

if __name__ == '__main__':
    log_dir = os.path.join(os.getcwd(), 'log')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    cgitb.enable(format='text', logdir=log_dir)#自动存档崩溃报错信息
    
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)#高分辨率适配

    app = QApplication(sys.argv)
    welcome=WelcomeWindow()
    w = Window()
    w.hide()
    #w.show()
    mainThread=WorkThread()
    mainThread.start()
    app.exec_()
