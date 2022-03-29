import PySimpleGUIWeb as sg
from adafruit_motorkit import MotorKit
from time import sleep

kit = MotorKit()

def move(throttle):
    print("Moving at throttle",throttle)
    kit.motor1.throttle = throttle
    kit.motor2.throttle = throttle
    kit.motor3.throttle = throttle
    kit.motor4.throttle = throttle

def stop():
    print("stopping")
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0
    kit.motor3.throttle = 0
    kit.motor4.throttle = 0

def turn(throttle):
    print("Moving at throttle",throttle)
    kit.motor1.throttle = throttle
    kit.motor2.throttle = throttle
    kit.motor3.throttle = throttle
    kit.motor4.throttle = throttle

#PySimpleGUIWEB Code
################################################
## Theme Settings:
################################################
#these lines set global themes for our windows with PySimpleGUI. See all options here: https://pysimplegui.readthedocs.io/en/latest/call%20reference/#themes
sg.theme('DarkBlack') # (darkbrown4) this is one of the best themes, but we need some adjustments to make it... not tacky:

def startWindow():
    throttle = 0.4

    layout = [  [sg.Text('Speed (0.0-1.0):'),sg.Input(default_text  = '0.4',size=(10, 1), justification='center', key='throttle'),sg.Button('Submit')],
                [sg.Button('Forward')],
                [sg.Button('Backward')],
                [sg.Button('Exit'),sg.Button('Stop Car')]  ]

    window = sg.Window('Pi Car Controls', layout, web_port=6080, web_start_browser=False,element_justification='c')

    while True:             # Event Loop
        event, values = window.read()
        print(event, values)
        if event in (None, 'Exit'):
            break
        if event == 'Forward':
            move(throttle)
        if event == 'Backward':
            move(throttle*-1)
        if event == 'Stop Car':
            stop()
        if event == 'Submit':
            if values['throttle'].isnumeric() and (float(0.0) <= float(values['throttle']) <= float(1.0)):
                throttle = float(values['throttle'])
            else:
                print("ERROR: INVALID THROTTLE INPUT")
    window.close()



startWindow()