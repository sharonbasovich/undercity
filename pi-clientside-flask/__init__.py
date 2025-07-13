from flask import Flask # type: ignore
from flask import render_template # type: ignore

app = Flask(__name__)

@app.route("/")
def hello():
    return render_template('index.html')

@app.route('/projects/')
def projects():
    return 'The project page'

@app.route('/about')
def about():
    return 'The about page'

if __name__ == "__main__":
    app.run()