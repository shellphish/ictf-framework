import api from "./api";
import useSWR from "swr";
import _ from 'underscore';
import { useState } from "react";

const api_fetcher = (url, n_ticks=1,) => {
  return api.get(url, {n_ticks: n_ticks}).then(r => r.body)
}

const STATE_POLLING_INTERVAL = 10 * 1000;
export function useGameState (n_ticks=1, swr_config={}) 
{
  var config = {refreshInterval: STATE_POLLING_INTERVAL, dedupingInterval: STATE_POLLING_INTERVAL, ...swr_config};
  
  const { data, error } = useSWR(
    [`/game/state`, n_ticks], 
    api_fetcher,
    config
  )
  console.log(data, error);

  return {
    gamestate: (error || !data) ? undefined : data,
    isLoading: !!(!error && !data),
    isError: error
  }
}
export function useLatestGameState() {
  const {gs, loading, error} = useGameState();
  let latest_dynamic = gs && gs.dynamic && gs.dynamic[0];
  return {latest_dynamic, static: gs.static, loading, error}

}
function sortScores(scores, sortAttribute) {
  let sortedScores = _.chain(scores).values().sortBy(sortAttribute).reverse().value();
  return sortedScores;
}
export function useTicksScores(n_ticks=1) {
  let [ticks, setTicks] = useState([]);
  const {gamestate, loading, error} = useGameState(n_ticks=1);
  var lastScores = [];
  var lastScoresSorted = [];
  if (!gamestate || gamestate.dynamic.length < 1)
  {
    return {ticks: undefined, lastScores, lastScoresSorted, loading, error}
  }
  let lastTick = ticks[ticks.length-1];
  if (!lastTick || lastTick.tick.tick_id !== gamestate.dynamic[0].tick.tick_id) {
    let lastScores = _.values(gamestate.dynamic[0].scores);
    let attackMax = Math.max(_.chain(lastScores).pluck('attack_points').max().value(), 1);
    let serviceMax = Math.max(_.chain(lastScores).pluck('service_points').max().value(), 1);
    let slaMax = _.chain(lastScores).pluck('sla').max().value();
    lastScores = lastScores.for(s => {
      s.attack_score = s.attack_points / attackMax * 100;
      s.service_score = s.service_points / serviceMax * 100;
      s.sla_score = s.sla / (slaMax === 0 ? 1 : slaMax) * 100;
      s.team_name = gamestate.static.teams[s.team_id] && gamestate.static.teams[s.team_id].name;
      return s;
    });
    lastScoresSorted = sortScores(lastScores, 'total_points');
    setTicks(ticks.concat(gamestate.dynamic));
  }
  return {ticks, lastScores, lastScoresSorted, loading, error}
}
// const loadData = () =>
// api.get('/game/state')
// .then(res => res.json()
//     console.log(res.body);
//     setDynamicData(res.body.dynamic);
//     setStaticData(res.body.static);
//     setServices(res.body.static.services);
//     setTeams(res.body.static.teams);
// })
// .catch((e) => {
//     console.log("Error getting game state: " + e)
// });