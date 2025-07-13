from flask import Flask, render_template, redirect, url_for, request # type: ignore

import json

app = Flask(__name__)

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

@app.route('/code/')
def code():
    return render_template('code.html')

@app.route('/result/')
def result():
    return render_template('result.html')

if __name__ == "__main__":
    app.run()