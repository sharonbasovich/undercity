from time import sleep
import random
import threading
import json
import time
from flask import Flask, render_template, redirect, url_for, request
from flask_socketio import SocketIO, emit

from gpiozero import AngularServo, Button
from gpiozero.pins.pigpio import PiGPIOFactory

app = Flask(__name__)
socketio = SocketIO(app)

factory = PiGPIOFactory()

# arm
sArm = AngularServo(14, min_angle=0, max_angle=180, min_pulse_width=0.0005, max_pulse_width=0.0025, pin_factory=factory)

# table
sTable = AngularServo(15, min_angle=0, max_angle=180, min_pulse_width=0.0005, max_pulse_width=0.0025, pin_factory=factory)

itemIndexObject = 0

getting = 0

# initial arm angle
sArm.angle = 98

def slow_move(servo, start, end, step=1, delay=0.02):
    """Move servo from start to end in small steps."""
    if start < end:
        angle_range = range(int(start), int(end)+1, step)
    else:
        angle_range = range(int(start), int(end)-1, -step)
    
    for angle in angle_range:
        servo.angle = angle
        time.sleep(delay)

@app.route("/")
def hello():
    return render_template('index.html')

@app.route('/redirect-to-catalog', methods=['POST'])
def redirect_to_catalog():
    return redirect(url_for('catalog'))

# loading items from json for catalog
def load_items():
    with open('items.json') as f:
        return json.load(f)

# loading codes for ordering
def load_codes():
    with open('codes.json') as f:
        return json.load(f)

@app.route('/catalog/')
def catalog():
    items = load_items()
    return render_template('catalog.html', items = items)

@app.route('/redirect-to-code')
def redirect_to_code():
    global itemIndexObject
    index = request.args.get('item')
    itemIndexObject = int(index)
    return redirect(url_for('code', item=index))

@app.route('/code/')
def code():
    global itemIndexObject 

    item = request.args.get('item')
    items = load_items()
    name = items[int(item)]['name']
    itemIndexObject = int(item)
    print(f"saving obj as {itemIndexObject} from {item}")
    return render_template('code.html', item = name)

@app.route('/redirect-to-result', methods=['POST'])
def redirect_to_result():
    raw = request.form.get('code')

    if len(raw) < 1:
        return redirect(url_for('wrong'))

    code = int(request.form.get('code'))
    codes = load_codes()

    if code in codes:
        return redirect(url_for('result'))
    else:
        return redirect(url_for('wrong'))

def serve_threaded():
    print(f"angle is currentlyyy {sTable.angle}")

    angle = getting["angle"]
    inverted = getting["inverted"]

    slow_move(sTable, sTable.angle or 0, angle)

    time.sleep(3)

    sArm.angle = 98

    if inverted:
        sArm.angle = 180
    else:
        sArm.angle = 0
    
    time.sleep(3)

    sArm.angle = 98

@app.route('/result/')
def result():
    global getting

    # you wanted a #, you get a #!
    # code = request.args.get('code')
    print(f"ok please be right!!!!!!!!!! {itemIndexObject}")
    items = load_items()
    name = items[int(itemIndexObject)]['name']

    in_stock_items = [item for item in items if item.get("in_stock")]

    getting = random.choice(in_stock_items)

    threading.Thread(target=serve_threaded).start()

    return render_template('result.html', wanted = name, getting = getting)

@app.route('/wrong/')
def wrong():
    return render_template('wrong.html')

# testing all, use w/o cans!!!!!!!!!
def sweep(servo):
    for angle in range(0, 181, 10):
        servo.angle = angle
        sleep(0.1)
    for angle in range(180, -1, -10):
        servo.angle = angle
        sleep(0.1)

@app.route("/testing/")
def testing():
    sweep(sArm)
    sweep(sTable)
    return "<p>running test!!!</p>"

# down pos on arm
@app.route("/testing1/")
def testing1():
    print(f"angle is currentlyyy {sArm.angle}")
    sArm.angle = 98
    
    return "<p>running test!!!</p>"

# pos for table
def testing2_threaded():
    print(f"angle is currentlyyy {sTable.angle}")
    
    time.sleep(5)
    slow_move(sTable, sTable.angle or 0, 35)
    print(f"angle is currentlyyy {sTable.angle}")
    time.sleep(5)
    slow_move(sTable, sTable.angle or 35, 85)
    print(f"angle is currentlyyy {sTable.angle}")
    time.sleep(5)
    slow_move(sTable, sTable.angle or 85, 134)
    print(f"angle is currentlyyy {sTable.angle}")
    time.sleep(5)
    slow_move(sTable, sTable.angle or 134, 180)
    print(f"angle is currentlyyy {sTable.angle}")

@app.route("/testing2/")
def testing2():
    threading.Thread(target=testing2_threaded).start()
    return "<p>running test!!!</p>"

# arcade button on GPIO 18
arcade_button = Button(18, pull_up=False, bounce_time=0.2)

def on_button_pressed():
    global itemIndexObject
    print(f"[GPIO] Button pressed, emitting socket redirect for item {itemIndexObject}")
    socketio.emit('redirect_to_code', {'item': itemIndexObject})

arcade_button.when_pressed = on_button_pressed

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
