import datetime
import functools

from flask import request, abort

from . import app, mysql


def requires_auth(func):
    """Decorator to wrap API calls that need authentication.

    :param function func: Function wrapped to check for API secret before
                             continuing.
    """
    @functools.wraps(func)
    def wrapper(**kwds):     # pylint: disable=missing-docstring
        if request.args.get("secret") != app.config["API_SECRET"]:
            abort(401)
        else:
            return func(**kwds)
    return wrapper


def get_current_tick(cursor):
    """Gets the current tick of the game.

    :param cursor: Cursor that points to the MySQL database.

    :return: Tuple of the tick number, created on, seconds left and time to change in that order.
    """
    cursor.execute("""SELECT id, time_to_change, created_on
                      FROM ticks ORDER BY created_on DESC LIMIT 1""")
    result = cursor.fetchone()

    if result:
        current_tick = result["id"]
        current_time = datetime.datetime.now()
        created_on = result["created_on"]

        time_to_change = result["time_to_change"]
        seconds_left = (time_to_change - current_time).total_seconds()
        seconds_left = max(0, seconds_left)
    # This is to make sure that everything works even when the game is
    # not running
    else:
        current_tick, seconds_left = 0, 1337
        created_on = datetime.datetime.fromordinal(1337)
        time_to_change = datetime.datetime.now() + datetime.timedelta(seconds=seconds_left)

    return current_tick, created_on, seconds_left, time_to_change

