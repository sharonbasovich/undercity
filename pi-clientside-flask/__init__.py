from flask import Flask, render_template, redirect, url_for, request # type: ignore

import json
import RPi.GPIO as GPIO # type: ignore
import time

### important gpio pins
# table stepper moter
tDIR = 23
tSTEP = 24
# hand stepper motor
hDIR = 14
hSTEP = 15

GPIO.setmode(GPIO.BCM)
GPIO.setup(tDIR, GPIO.OUT)
GPIO.setup(tSTEP, GPIO.OUT)

GPIO.setup(hDIR, GPIO.OUT)
GPIO.setup(hSTEP, GPIO.OUT)

app = Flask(__name__)

itemIndex = 0

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

@app.route('/catalog/')
def catalog():
    items = load_items()
    return render_template('catalog.html', items = items)

@app.route('/redirect-to-code')
def redirect_to_code():
    index = request.args.get('item')
    # item = load_items()[index]
    return redirect(url_for('code', item=index))

@app.route('/code/')
def code():
    item = request.args.get('item')
    items = load_items()
    name = items[int(item)]['name']
    return render_template('code.html', item = name)

@app.route('/redirect-to-result', methods=['POST'])
def redirect_to_result():
    code = request.form.get('code')
    return redirect(url_for('result', code=code))

@app.route('/result/')
def result():
    code = request.args.get('code')
    return render_template('result.html', code = code)

@app.route("/testing")
def testing():

    GPIO.output(hDIR, GPIO.HIGH)

    for _ in range(200):  # One full revolution for 1.8° step motor
        GPIO.output(hSTEP, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(hSTEP, GPIO.LOW)
        time.sleep(0.001)

    # GPIO.cleanup()

    return "<p>running test!!!</p>"

if __name__ == "__main__":
    app.run()