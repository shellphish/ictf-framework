import logging
from datetime import datetime

import coloredlogs

from .game_state_interface import GameStateInterface
from .simple_lru_cache import LRUCache


class ScoringInterface(object):
    LOG_FMT = '%(levelname)s - %(asctime)s (%(name)s): %(msg)s'

    def __init__(self, game_state_interface, cache_count=30, log_level=logging.DEBUG):  # this is cheaper to store
        '''
        :type self.gsi: GameStateInterface

        :param game_state_interface: GameStateInterface
        :type game_state_interface: GameStateInterface
        :param cache_count: How many score ticks to cache
        :type cache_count: int
        '''
        self.gsi = game_state_interface

        self.single_tick_score_cache = LRUCache(cache_count)
        self._total_scores = {}

        log = logging.getLogger('gamebot_scoring')
        log.setLevel(log_level)
        log_formatter = coloredlogs.ColoredFormatter(ScoringInterface.LOG_FMT)
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(log_formatter)
        log.addHandler(log_handler)

        self.log = log

    def clear_stored_scores(self):
        self.log.debug("Clearing calculated scores, recomputation will take a while.")
        self._total_scores = {}

    def _calculate_single_tick_score(self, tick):
        raise NotImplementedError

    def _add_scores(self, prev, current):
        raise NotImplementedError

    def _default_value(self):
        raise NotImplementedError

    def wrap_into_output_format(self, tick, scores):
        raise NotImplementedError

    def calculate_single_tick_score(self, tick):
        if tick in self.single_tick_score_cache:
            return self.single_tick_score_cache[tick]
        score = self._calculate_single_tick_score(tick)
        self.single_tick_score_cache[tick] = score
        return score

    def _get_scores_for_tick(self, tick):
        assert tick >= 0

        if tick == 0:
            self.log.debug("Tick 0 requested, providing default value!")
            # this is treated as immutable, so one instance is fine :)
            default = self._default_value()
            self._total_scores[0] = {tid: default for tid in self.gsi.team_id_to_name_map.keys()}

        if tick not in self._total_scores:
            t1 = datetime.now()
            # self.log.debug("Requesting previous scores upto tick {} at {}...".format(tick, tick-1, t1))
            previous_scores = self._get_scores_for_tick(tick-1)
            # t2 = datetime.now()
            # self.log.debug("Computed scores upto tick {}, took {}".format(tick-1, t2-t1))
            current_scores = self.calculate_single_tick_score(tick)
            # t3 = datetime.now()
            # self.log.debug('Computed scores upto tick {}, took {}'.format(tick, t3-t2))
            new_scores = self._add_scores(previous_scores, current_scores)
            t4 = datetime.now()
            self.log.debug('TOTAL TIME for scores for tick {}: {}, finished at {}'.format(tick, t4-t1, t4))
            self._total_scores[tick] = new_scores

        return self._total_scores[tick]

    def get_scores_for_tick(self, tick):
        return self.wrap_into_output_format(tick, self._get_scores_for_tick(tick))
