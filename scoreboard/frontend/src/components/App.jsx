import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import ReactCSSTransitionGroup from 'react-addons-css-transition-group';
import _ from 'underscore';

import SetIntervalMixin from '../mixins/SetIntervalMixin';
import api from '../sources/api';
/* import AcademicSwitch from './AcademicSwitch'; */
import Countdown from './shared/Countdown';

const POLLING_INTERVAL = 10 * 1000;

class App extends Component {
  state = {
    title: '',
    staticdata: {},
    dynamicData: [],
    teams: [],
    services: []
  }

  filterAcademicTeams(teams, academiconly) {
    return _.values(teams).filter(t => !t.academiconly || t.academic_team === 1)
  }

  loadData() {
    api.get('/game/state').then(res => {
      this.setState({
        staticData: res.body.static,
        dynamicData: res.body.dynamic,
        services: res.body.static.services,
        teams: this.filterAcademicTeams(
          res.body.static.teams,
          this.props.location.query.academiconly
        )
      });
    });
  }

  componentDidMount() {
    this.loadData();
    this.setInterval(() => this.loadData(), POLLING_INTERVAL);
    this.setState({title: document.title});
  }

  componentWillReceiveProps(nextProps) {
    this.setState({
      teams: this.filterAcademicTeams(
        this.state.staticData.teams,
        nextProps.location.query.academiconly
      )
    });
  }

  render() {
    const pathname = this.props.location.pathname;
    return (
      <div className="wrap space--both-2">

        <header className="main-header">
          <Link className="logo" to="/">
            <span className="logo__name">{ this.state.title }</span>
          </Link>
          {/* <AcademicSwitch location={ this.props.location } /> */}
          <Countdown/>
          <nav className="navigation">
            <Link to="/scores" query={ this.props.location.query } activeClassName="is-active">Scoreboard</Link>
            <Link to="/services" query={ this.props.location.query } activeClassName="is-active">Service List</Link>
            <Link to="/service-states" query={ this.props.location.query } activeClassName="is-active">Service Status</Link>
            <Link to="/service-exploits" query={ this.props.location.query } activeClassName="is-active">Service Exploits</Link>
            <Link to="/teams" query={ this.props.location.query } activeClassName="is-active">Teams</Link>
          </nav>
        </header>

        <div className="main-content">
          <ReactCSSTransitionGroup transitionName="moveUp"
                                      transitionEnterTimeout={300}
                                      transitionLeaveTimeout={300}>
            {
              React.cloneElement(
                this.props.children || <div />,
                {
                  dynamicData: this.state.dynamicData,
                  teams: this.state.teams,
                  services: this.state.services,
                  key: pathname
                }
              )
            }
          </ReactCSSTransitionGroup>
        </div>

      </div>
    );
  }
}
App = SetIntervalMixin(App);
export default App;