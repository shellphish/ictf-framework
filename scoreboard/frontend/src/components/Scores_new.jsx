import React, { useState, useEffect } from 'react';
import { findDOMNode } from 'react-dom';
import c3 from 'c3';
import _ from 'underscore';

import api from '../sources/api';
import SetIntervalMixin from '../mixins/SetIntervalMixin';
import round from '../utils/round';
import Table from './shared/Table';
import Flag from './shared/Flag';
import { useGameState } from '../sources/api_hooks';

const Scores = (props) => {
  let [teamsShown, setTeamsShown] = useState('top');
  let [chart, setChart] = useState(undefined);
  const {ticks, lastScores, lastScoresSorted, loading, error} = useGameState();

  useEffect(() => {
    setChart(c3.generate({
      bindto: findDOMNode(this.refs.chart),
      legend: {
        show: true
      },
      data: {
        x: 'x',
        rows: ['x']
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
  })

  useEffect(
    () => {
      let teamsNames = _.pluck(_.first(lastScoresSorted, 10), 'team_name');
      let teamsIds = _.pluck(_.first(lastScoresSorted, 10), 'team_id');
      let scores = ticks.map(tick => {
        var pickedScores = [];
        for (var idx in teamsIds) {
          pickedScores.push(tick.scores[teamsIds[idx]]);
        }
        let points = _.pluck(pickedScores, 'total_points');
        return [tick.tick.tick_id].concat(points);
      });
      scores.unshift(
        ['x'].concat(teamsNames)
      );
      chart.load({
        rows: scores
      });
      chartShowTeams();
    },
    [chart, ticks, lastScoresSorted, lastScores, teamsShown]
  )


  function chartShowTeams() {
    if (teamsShown === 'all') {
      chart.show && chart.show();
    }
    else if (teamsShown === 'none') {
      chart.hide && chart.hide() && chart.hide();
    } else if (teamsShown === 'top') {
      chartShowTop();
    }
  }

  function chartShowTop() {
    chart.hide();
    let firstScores = _.first(lastScoresSorted, 10);
    let teamNames = firstScores.map(k => {
      let team = _.find(this.props.teams, f => {
        if (f.id === k.team_id) {
          return true;
        }
      });
      return team && team.name;
    });
    chart.show(teamNames);
  }

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
    return this.state.lastScoresSorted.filter(score => {
      return this.props.teams.find(t => t.id === score.team_id);
    }).map((s, i) => {
      let team = this.props.teams.find(t => t.id === s.team_id);
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
      <div className="chart" ref="chart"/>
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