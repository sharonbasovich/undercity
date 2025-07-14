from time import sleep
import random
import threading
import json
from flask import Flask, render_template, redirect, url_for, request # type: ignore

from gpiozero import AngularServo # type: ignore
from gpiozero.pins.pigpio import PiGPIOFactory # type: ignore

app = Flask(__name__)

factory = PiGPIOFactory()

servo1 = AngularServo(14, min_angle=0, max_angle=180, min_pulse_width=0.0005, max_pulse_width=0.0025, pin_factory=factory)
servo2 = AngularServo(15, min_angle=0, max_angle=180, min_pulse_width=0.0005, max_pulse_width=0.0025, pin_factory=factory)

itemIndexObject = 0
                                                                                                  
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
    index = request.args.get('item')
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

@app.route('/result/')
def result():
    # you wanted a #, you get a #!
    # code = request.args.get('code')
    print(f"ok please be right!!!!!!!!!! {itemIndexObject}")
    items = load_items()
    name = items[int(itemIndexObject)]['name']

    in_stock_items = [item for item in items if item.get("in_stock")]

    getting = random.choice(in_stock_items)

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
    sweep(servo1)
    sweep(servo2)
    return "<p>running test!!!</p>"

# down pos on arm
@app.route("/testing1/")
def testing1():
    return "<p>running test!!!</p>"

if __name__ == "__main__":
    app.run()