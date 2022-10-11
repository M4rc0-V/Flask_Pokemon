from flask import Flask, render_template

app = Flask(__name__)

@app.route('/', methods=['GET'])
def homepage():
    return render_template('index.html')

@app.route('/pokemon', methods=['GET'])
def pokemon():
    return render_template('pokemon.html')


