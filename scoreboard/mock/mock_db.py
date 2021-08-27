import flask

from flask import Flask

app = Flask(__name__)

@app.route("/api/game/state")
def game_state():
    return []

@app.route("/api/tick")
def tick():
    return 10
