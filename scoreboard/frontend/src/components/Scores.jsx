import React, { Component } from 'react';
import { findDOMNode } from 'react-dom';
import c3 from 'c3';
import _ from 'underscore';

import api from '../sources/api';
import SetIntervalMixin from '../mixins/SetIntervalMixin';
import round from '../utils/round';
import Table from './shared/Table';
import Flag from './shared/Flag';

const POLLING_INTERVAL = 10 * 1000;

class Scores extends Component {
  state = {
    lastScores: [],
    lastScoresSorted: [],
    teamsShown: 'top'
  }

  constructor() {
    /* don't use state for scores, c3 is rendered outside React */
    super();
    this.ticks = [];
    this.chart_ref = React.createRef();
  }

  /* FIXME: double fetch, check App component */
  loadTicks(ticksCount) {
    api.get('/game/state', {n_ticks: ticksCount}).then(res => {
      let lastTick = this.ticks[this.ticks.length-1];
      if (res.body.dynamic.length > 0 && (!lastTick || lastTick.tick.tick_id !== res.body.dynamic[0].tick.tick_id)) {
        let lastScores = _.values(res.body.dynamic[0].scores);
        let attackMax = Math.max(_.chain(lastScores).pluck('attack_points').max().value(), 1);
        let serviceMax = Math.max(_.chain(lastScores).pluck('service_points').max().value(), 1);
        let slaMax = _.chain(lastScores).pluck('sla').max().value();
        lastScores = lastScores.map(s => {
          s.attack_score = s.attack_points / attackMax * 100;
          s.service_score = s.service_points / serviceMax * 100;
          s.sla_score = s.sla / (slaMax === 0 ? 1 : slaMax) * 100;
          s.team_name = res.body.static.teams[s.team_id] && res.body.static.teams[s.team_id].name;
          return s;
        });
        this.ticks = this.ticks.concat(res.body.dynamic);
        this.setState({
          lastScores: lastScores,
          lastScoresSorted: this.sortScores(lastScores, 'total_points')
        });
      }
    });
  }

  sortScores(scores, sortAttribute) {
    let sortedScores = _.chain(scores).values().sortBy(sortAttribute).reverse().value();
    return sortedScores;
  }

  componentDidMount() {
    this.loadTicks(20);
    this.chart = c3.generate({
      bindto: findDOMNode(this.chart),
      legend: {
        show: true
      },
      data: {
        x: 'x',
        rows: [['x']]

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
    });
    this.setInterval(() => this.loadTicks(1), POLLING_INTERVAL);
  }

  componentDidUpdate() {
    let teamsNames = _.pluck(_.first(this.state.lastScoresSorted, 10), 'team_name');
    let teamsIds = _.pluck(_.first(this.state.lastScoresSorted, 10), 'team_id');
    let scores = this.ticks.map(tick => {
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
    this.chart.load({
      rows: scores
    });
    this.chartShowTeams();
  }

  chartShowTeams() {
    if (this.state.teamsShown === 'all') {
      this.chart.show && this.chart.show();
    }
    else if (this.state.teamsShown === 'none') {
      this.chart.hide && this.chart.hide() && this.chart.hide();
    } else if (this.state.teamsShown === 'top') {
      this.chartShowTop();
    }
  }

  chartShowTop() {
    this.chart.hide();
    let firstScores = _.first(this.state.lastScoresSorted, 10);
    let teamNames = firstScores.map(k => {
      let team = _.find(this.props.teams, f => {
        if (f.id === k.team_id) {
          return true;
        }
      });
      return team && team.name;
    });
    this.chart.show(teamNames);
  }

  handleChartToggle(type, e) {
    e.preventDefault();
    this.setState({teamsShown: type});
  }

  tableHeaders() {
    return [
      {id: 'team_rank', label: 'Rank', className: 'width--128-on-desk'},
      {id: 'team_name', label: 'Team', altSortAttr: 'team_name_sort'},
      {id: 'attack_points', label: 'Last Round Points'},
      {id: 'total_points', label: 'Total Score'}
    ];
  }

  tableRows() {
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

  render() {
    return (
      <div>
        <h3 className="title">Scoreboard</h3>
        <div className="chart" ref={this.chart_ref}/>
        <nav className="chart-controls">
          {/* <a href="#" onClick={ this.handleChartToggle.bind(this, 'all') }>Show all</a>
              <span> - </span>
              <a href="#" onClick={ this.handleChartToggle.bind(this, 'none') }>Hide all</a>
              <span> - </span> */}
          <a href='#top10' onClick={ this.handleChartToggle.bind(this, 'top') }>
            Top 10
          </a>
        </nav>

        <Table headers={ this.tableHeaders() }
               rows={ this.tableRows() }
               defaultSortAttr={ 'team_rank' }
               defaultSortDirection={ 'asc' }
               className={ 'space--top-1' }/>
      </div>
    );
  }
}
Scores = SetIntervalMixin(Scores);
export default Scores;