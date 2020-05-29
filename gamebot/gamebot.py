#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The gamebot is an internal component of the database backend and is
responsible for progressing the game (each "round" of the game is known as a
tick). Each tick the gamebot decides which scripts to run against which team
and randomizes the order. This information is persisted directly into the
database, then the gamebot sleeps until the next tick.
"""

from __future__ import print_function

__authors__ = "Adam Doupé, Kevin Borgolte, Aravind Machiry"
__version__ = "0.1.1"

from datetime import datetime, timedelta
from dbapi import DBApi
from scripts_facade import ScriptsFacade

import coloredlogs
import logging
import logstash
import random
import sys
import time


LOGSTASH_PORT = 1717
LOGSTASH_IP = "localhost"

def _get_ticks_configuration(db_api):
    tick_time_in_sec, configured_benign, configured_exploit, num_get_flags = db_api.get_tick_config()

    at_least_one = max(1, configured_benign - 1)
    one_more_than_available = configured_benign + 1
    num_benign = random.randint(at_least_one, one_more_than_available)

    # if number of exploits is zero. We do not schedule them.
    if configured_exploit > 0:
        at_least_one = max(1, configured_exploit - 1)
        one_more_than_available = configured_exploit + 1
        num_exploit = random.randint(at_least_one, one_more_than_available)
    else:
        num_exploit = 0

    tick_time_in_sec = random.uniform(tick_time_in_sec - 30,
                                      tick_time_in_sec + 30)

    return tick_time_in_sec, num_benign, num_exploit, num_get_flags

MAIN_LOG_LEVEL = logging.DEBUG
LOG_FMT = '%(levelname)s - %(asctime)s (%(name)s): %(msg)s'


def main():     # pylint:disable=missing-docstring,too-many-locals

    log = logging.getLogger('gamebot_main')
    log.setLevel(MAIN_LOG_LEVEL)
    log_formatter = coloredlogs.ColoredFormatter(LOG_FMT)
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(log_formatter)
    log.addHandler(log_handler)
    log.addHandler(logstash.TCPLogstashHandler(LOGSTASH_IP, LOGSTASH_PORT, version=1))

    log.info("Starting GameBot")
    db_api = DBApi()

    # Check DB connection.
    while True:
        if db_api.check_connection():
            log.info("Connection to DB Verified.")
            break
        else:
            log.fatal("Looks like DB is Down. Unable to verify db connection.")
            time.sleep(5)

    scripts_interface = ScriptsFacade(db_api)
    log.info("Initialization Complete")
    log.info("Check to see if there's a game running")

    while True:
        current_game_id = db_api.get_game_state()
        if current_game_id is None:
            log.info("Game is paused or hasn't started yet, retrying...")
            time.sleep(10)
            continue

        current_tick, seconds_left = db_api.get_current_tick_info()

        if current_tick != 0:
            log.info(
                "We must be picking up from the last run. "
                "Sleep for {} seconds until the next tick.".format(seconds_left)
            )
            time.sleep(seconds_left)

        log.warning("Starting Main Loop")
        tick_id = current_tick

        while True:
            log.info("Starting Iteration")

            current_game_id = db_api.get_game_state()
            if current_game_id is None:
                log.info("Game is paused, breaking out of main loop")
                break

            # Create a new tick and decide what scripts to run against each team
            sleep_time, num_benign, num_exploit, num_get_flags = _get_ticks_configuration(db_api)

            # Update script to be run, we should update these first as scriptbot
            # waits for tick to pick up the scripts.
            # First, update scripts and then update tick so that
            # when the tick is updated,
            # scriptbot can get all the scripts in a single shot.
            if scripts_interface.update_scripts_to_run(tick_id + 1, num_benign, num_exploit, num_get_flags):
                log.info("Successfully updated scripts to run for:" + str(tick_id + 1))
            else:
                log.error("Failed to update scripts to run for:" + str(tick_id + 1))

            # Change the tick
            current = datetime.now()
            time_to_change = current + timedelta(seconds=sleep_time)

            tick_id = db_api.update_tick_info(time_to_change.isoformat(), current.isoformat())

            log.info("Current Tick {}".format(tick_id))
            log.info("Tick Configuration, Sleep Time:" + str(sleep_time) + ", num_benign:" + str(num_benign) +
                     ", num_exploit:" + str(num_exploit) + ", num_get_flags:" + str(num_get_flags))

            # compute scores for the previous tick (the last completed tick)
            if tick_id > 1:
                # update the state of services for previous tick
                old_time = datetime.now()
                log.info("Updating state of services across all teams.")
                scripts_interface.update_state_of_services(tick_id - 1)
                log.info("Updated state of services across all teams in:" + str(datetime.now() - old_time))
            else:
                log.info("Ignoring Scoring, as this is first tick.")

            # Sleep for the amount of time until the next tick
            time_diff_to_sleep = time_to_change - datetime.now()
            if time_diff_to_sleep.total_seconds() < 0:
                log.warning("Not sleeping at all. I was {} seconds too slow".format(time_diff_to_sleep))
            else:
                seconds_to_sleep = (time_diff_to_sleep.seconds +
                                    (time_diff_to_sleep.microseconds / 1E6))
                log.info("Sleeping for:" + str(seconds_to_sleep))
                time.sleep(seconds_to_sleep)
                log.info("Awake")


if __name__ == "__main__":
    sys.exit(main())
