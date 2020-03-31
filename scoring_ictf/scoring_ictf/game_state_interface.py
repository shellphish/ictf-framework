class GameStateInterface(object):
    def __init__(self):
        self._team_ids_to_names = None
        self._service_ids_to_names = None

    def _team_id_to_name_map(self):
        raise NotImplementedError

    def _service_id_to_name_map(self):
        raise NotImplementedError

    def _scored_events_for_tick(self, tick):
        raise NotImplementedError

    @property
    def team_id_to_name_map(self):
        if self._team_ids_to_names is None:
            self._team_ids_to_names = self._team_id_to_name_map()
        return self._team_ids_to_names

    @property
    def service_id_to_name_map(self):
        if self._service_ids_to_names is None:
            self._service_ids_to_names = self._service_id_to_name_map()
        return self._service_ids_to_names

    def scored_events_for_tick(self, tick):
        # TODO: maybe cache here? or do we cache in the database side?
        return self._scored_events_for_tick(tick)
