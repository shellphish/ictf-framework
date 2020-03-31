import json

from . import app, mysql
from .utils import requires_auth
from .db_helpers import get_scored_events, get_full_service_status_report, get_attack_report


@app.route("/scored_events/<int:tick>")
@requires_auth
def endpoint_scored_events(tick):
    scored_events = get_scored_events(tick)
    return json.dumps(scored_events)


@app.route("/scored_events/service_status_report/<int:tick>")
@requires_auth
def endpoint_service_status_report(tick):
    cursor = mysql.cursor()

    report = get_full_service_status_report(cursor, tick)
    return json.dumps(report)


@app.route("/scored_events/attack_report/<int:tick>")
@requires_auth
def endpoint_attack_report(tick):
    cursor = mysql.cursor()

    report = get_attack_report(cursor, tick)
    return json.dumps(report)
