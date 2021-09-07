# pylint: disable=unused-argument

from functools import wraps
from flask import Flask, Response, request
from flask_cors import CORS
import redis
import ujson as json
import sys

app = Flask(__name__, static_folder='_static')
CORS(app, origins=['http://127.0.0.1:5000'])

# Helpers
def cache(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        response = f(*args, **kwargs)
        response.headers['Cache-Control'] = 'public, max-age=10'
        return response
    return wrapped

def jsonize(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        data = f(*args, **kwargs)
        if isinstance(data, Response):
            response = data
        else:
            response = Response(json.dumps(data), mimetype='application/json')
        return response
    return wrapped

# Retrieves the static info of the game.
def get_game_info():
    static_data = db_list.get('static').decode()
    static_data = json.loads(static_data)
    return static_data

# Retrieves the stats of the game
def get_game_stats(n_ticks=1):
    if n_ticks < 0:
       n_ticks = 0

    output_json = '['
    n_ticks = min(n_ticks, config['max_requested_ticks'], db_list.llen(config['redis_db_id']))
    for i in range(n_ticks):
        last_data = db_list.lindex(str(config['redis_db_id']), i).decode()
        output_json += last_data + ','

    output_json = output_json.rstrip(',') + ']'
    return output_json

@app.route('/api/tick')
def get_tick():
    tick_data_json = db_list.get('tick').decode()
    return Response(tick_data_json, mimetype='application/json')

@app.route('/api/<path:endpoint>')
@cache
def get_all(endpoint):
    n_ticks = int(request.args.get('n_ticks') or '1')

    last_data_str = get_game_stats(n_ticks)
    static_data_str = db_list.get('static').decode()
    if static_data_str is None or last_data_str is None:
        raise ValueError(f"Can't jsonize: {static_data_str=} {last_data_str=}")
    encoded = '{"static": ' + static_data_str + ', "dynamic": ' + last_data_str + '}'
    return Response(encoded, mimetype='application/json')

@app.route('/')
@app.route('/<path:path>')
def static_proxy(path='index.html'):
    return app.send_static_file(path)


# Config
def init_connections(config_file="config.json"):
    global db_list
    global config

    with open(config_file) as data_file:
        config = json.load(data_file)

    redis_params = {
        "host": config['redis_host'],
        "port": config['redis_port'],
        "db": config['redis_db_id']
    }
    db_list = redis.StrictRedis(**redis_params)

init_connections()

if __name__ == '__main__':
    print("[*] Starting")
    app.run(use_reloader=False, port=8080, host='0.0.0.0', debug=True, processes=24)
