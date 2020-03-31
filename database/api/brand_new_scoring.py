import json

# the new fixed endpoint
from . import app, mysql
from .scores import _scores_get
from .utils import requires_auth, get_current_tick
from .db_helpers import get_team_map, enabled_service_map, get_scored_events

from scoring_ictf import Scoring_ICTF2017, GameStateInterface

class DatabaseGameStateInterface(GameStateInterface):
    def _team_id_to_name_map(self):
        return get_team_map()

    def _service_id_to_name_map(self):
        return enabled_service_map()

    def _scored_events_for_tick(self, tick):
        return get_scored_events(tick)


game_state_interface = DatabaseGameStateInterface()
scoring = Scoring_ICTF2017(game_state_interface)


@app.route("/scores")
@app.route("/scores/tick/<int:tick_id>")
@requires_auth
def scores_get(tick_id=None):
    """The ``/scores`` endpoint requires authentication and takes an
    optional ``tick_id`` argument. It fetches the services' states for all
    teams for the current tick if no ``tick_id`` is provided, or for the
    specified ``tick_id`` otherwise.

    It can be reached at ``/scores?secret=<API_SECRET>``.

    It can also be reached at
    ``/scores/tick/<tick_id>?secret=<API_SECRET>``.

    The JSON response looks like::

        {
        team_id: {
                  "team_id: team_id,
                  "service_points": service_points,
                  "attack_points": attack_points,
                  "sla": sla,
                  "total_points", total_points,
                  "num_valid_ticks": num_valid_ticks
                 }
        }

    :param int tick_id: optional tick_id
    :return: a JSON dictionary that maps teams to scores.
    """

    scores_old = _scores_get(tick_id=tick_id)

    if tick_id is None:
        tick_id, _, _, _ = get_current_tick(cursor=mysql.cursor())
    scores_new = scoring.get_scores_for_tick(tick_id - 1)

    if scores_new != scores_old:
        print("OLD: {}" + str(scores_old))
        print("NEW: {}" + str(scores_new))

    return json.dumps({"scores": scores_new})