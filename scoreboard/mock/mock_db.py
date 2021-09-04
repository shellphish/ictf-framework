import time

from flask import Flask

app = Flask(__name__)

game_start = int(time.time())
MINUTE = 60
TICK_LEN = 2 * MINUTE

TEAMS = {
    0: dict(name='Shellphish', logo='', academic_team=True, country='usa', url='http://shellphish.net'),
    1: dict(name='Sashimi', logo='', academic_team=False, country='usa', url='http://shellphish.net')
}

SERVICES={
    0: dict(service_name='a', port=31337, description='Service A', flag_id_description='AAA', authors='Lukas', state='enabled'),
    1: dict(service_name='b', port=31338, description='Service B', flag_id_description='BBB', authors='LukasB', state='enabled')
}
@app.route("/api/game/state")
def game_state():
    return {
        'static': {
            'teams': TEAMS,
            'services': SERVICES,
        },
        'dynamic': []
    }

@app.route("/api/tick")
def tick():
    tick_end = int(time.time())
    tick_end = (tick_end + TICK_LEN)
    tick_end -= tick_end % TICK_LEN
    res = {
        'tick_id': int(time.time() - game_start) // TICK_LEN,
        'ends_on': tick_end
        }
    return res
