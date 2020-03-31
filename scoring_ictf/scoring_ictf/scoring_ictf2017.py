from . import ScoringInterface

POINTS_PER_SERVICE_PER_TICK = 50.0

def extract_interesting_data(all_teams, all_services, service_status_report, attack_report):
    # print('ATTACK_REPORT: {}'.format(attack_report))
    up_teams = {}
    exploited_by = {}
    for sid in all_services:
        up_teams[sid] = set()
        exploited_by[sid] = {}
        for tid in all_teams:
            exploited_by[sid][tid] = set(attack_report.get(sid, {}).get(tid, {}).keys())
            if service_status_report[tid][sid] == 'up':
                up_teams[sid].add(tid)

    return up_teams, exploited_by

def get_per_service_team_points(all_teams, all_services, service_status_report, attack_report):
    up_teams, exploited_by = extract_interesting_data(all_teams, all_services, service_status_report, attack_report)
    # print("exploited_by: {}".format(exploited_by))
    team_service_points = {tid: {sid: 0.0 for sid in all_services} for tid in all_teams}
    for sid in all_services:
        cur_up = up_teams[sid]
        cur_expl_by = exploited_by[sid]
        for tid in all_teams:

            # if you're down your points go to the teams that are still up
            if tid not in cur_up:
                for other in cur_up:
                    team_service_points[other][sid] += (POINTS_PER_SERVICE_PER_TICK / len(cur_up))

            # otherwise, if you're exploited your points go to the exploiting teams
            elif len(cur_expl_by[tid]) > 0:
                for other in cur_expl_by[tid]:
                    team_service_points[other][sid] += (POINTS_PER_SERVICE_PER_TICK / len(cur_expl_by[tid]))

            # otherwise, you keep your points
            else:
                team_service_points[tid][sid] += POINTS_PER_SERVICE_PER_TICK

    return team_service_points


def get_tick_team_points(*args):
    team_service_points = get_per_service_team_points(*args)
    return {tid: sum(service_points.values()) for tid, service_points in team_service_points.items()}


class Scoring_ICTF2017(ScoringInterface):
    def _default_value(self):
        return 0.0, 0.0

    def _calculate_single_tick_score(self, tick):
        all_team_ids = self.gsi.team_id_to_name_map.keys()
        all_service_ids = self.gsi.service_id_to_name_map.keys()
        scored_events = self.gsi.scored_events_for_tick(tick)

        service_status_report = scored_events['service_status_report']
        attack_report = scored_events['attack_report']

        tick_team_points = get_tick_team_points(all_team_ids, all_service_ids, service_status_report, attack_report)
        return tick_team_points

    def _add_scores(self, prev, current):
        v = {}
        for tid in current.keys():
            prev_total, prev_attack = prev[tid]
            v[tid] = (prev_total + current[tid], current[tid])
        return v

    def wrap_into_output_format(self, tick, scores):
        output = {}
        for tid, (total_score, last_round_score) in scores.items():
            output[tid] = dict(team_id=tid,
                               attack_points=last_round_score,
                               total_points=total_score,
                               num_valid_ticks=tick,
                               service_points=0.0,
                               sla=1.0)
        return output
