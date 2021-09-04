import React, { useState, useEffect, useRef } from 'react';
import { findDOMNode } from 'react-dom';
import c3 from 'c3';
import _ from 'underscore';

import api from '../sources/api';
import SetIntervalMixin from '../mixins/SetIntervalMixin';
import round from '../utils/round';
import Table from './shared/Table';
import Flag from './shared/Flag';
import { useGameState, useTicksScores } from '../sources/api_hooks';

const Scores = (props) => {
  const [teamsShown, setTeamsShown] = useState('top');
  const [chart, setChart] = useState(undefined);
  const chart_ref = useRef(null);
  const {ticks, lastScores, lastScoresSorted, loading, error} = useTicksScores();
  const {gamestate, state_loading, state_error} = useGameState();

  let teamsNames = _.pluck(_.first(lastScoresSorted, 10), 'team_name');
  let teamsIds = _.pluck(_.first(lastScoresSorted, 10), 'team_id');
  let _scores = (ticks || []).map(tick => {
    var pickedScores = [];
    for (var idx in teamsIds) {
      pickedScores.push(tick.scores[teamsIds[idx]]);
    }
    let points = _.pluck(pickedScores, 'total_points');
    return [tick.tick.tick_id].concat(points);
  });
  _scores.unshift(
    ['x'].concat(teamsNames)
  );

  useEffect(() => {
    setChart(c3.generate({
      // bindto: findDOMNode(chart),
      bindto: '#chart',
      // bindto: chart_ref,
      legend: {
        show: true
      },
      data: {
        x: 'x',
        rows: _scores
      },
      tooltip: {
        show: false
      },
      axis: {
        y: {
          show: false
        },
        x: {
          type: 'line'
        }
      }
    }))
  }, [chart, _scores])

  useEffect(
    () => {
      function chartShowTeams() {
        if (teamsShown === 'all') {
          chart && chart.show && chart.show();
        }
        else if (teamsShown === 'none') {
          chart && chart.hide && chart.hide() && chart.hide();
        } else if (teamsShown === 'top') {
          chartShowTop();
        }
      }
    
      function chartShowTop() {
        chart && chart.hide();
        let firstScores = _.first(lastScoresSorted, 10);
        let teamNames = firstScores.map(k => {
          let team = _.find(gamestate.static.teams, f => {
            if (f.id === k.team_id) {
              return true;
            }
          });
          return team && team.name;
        });
        chart && chart.show(teamNames);
      }

      chartShowTeams();
    },
    [chart, ticks, lastScoresSorted, lastScores, teamsShown, gamestate.static.teams]
  )



  // function handleChartToggle(type, e) {
  //   e.preventDefault();
  //   setTeamsShown(type);
  // }

  function tableHeaders() {
    return [
      {id: 'team_rank', label: 'Rank', className: 'width--128-on-desk'},
      {id: 'team_name', label: 'Team', altSortAttr: 'team_name_sort'},
      {id: 'attack_points', label: 'Last Round Points'},
      {id: 'total_points', label: 'Total Score'}
    ];
  }

  function tableRows() {
    return lastScoresSorted.filter(score => {
      return gamestate.static.teams.find(t => t.id === score.team_id);
    }).map((s, i) => {
      let team = gamestate.static.teams.find(t => t.id === s.team_id);
      let teamNameTag = <span><Flag country={ team.country } size="16"/> { team.name }</span>;
      return {
        team_rank: i + 1,
        team_name_sort: team.name.toLowerCase(),
        team_name: teamNameTag,
        attack_points: round(s.attack_points),
        total_points: round(s.total_points)
      };
    });
  }

  return (
    <div>
      <h3 className="title">Scoreboard</h3>
      <div className="chart" ref={chart_ref}/>
      <nav className="chart-controls">
        {/* <a href="#" onClick={ this.handleChartToggle.bind(this, 'all') }>Show all</a>
            <span> - </span>
            <a href="#" onClick={ this.handleChartToggle.bind(this, 'none') }>Hide all</a>
            <span> - </span> */}
        {/* <button onClick={ handleChartToggle.bind('top') }>Top 10</button> */}
      </nav>

      <Table headers={ tableHeaders() }
              rows={ tableRows() }
              defaultSortAttr={ 'team_rank' }
              defaultSortDirection={ 'asc' }
              className={ 'space--top-1' }/>
    </div>
  );
}
export default Scores;