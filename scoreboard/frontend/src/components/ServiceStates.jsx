import React, { Component } from 'react';
import _ from 'underscore';
import cx from 'classnames';

export default class ServiceStates extends Component {
  state = {
    serviceStates: {},
    services: {}
  }

  componentWillMount() {
    this.parseDataAndSetState(this.props);
  }

  componentWillReceiveProps(nextProps) {
    this.parseDataAndSetState(nextProps);
  }

  parseDataAndSetState(props) {
    let lastData = props.dynamicdata[0];
    if (lastData === undefined) { return; }
    this.setState({
      serviceStates: lastData.service_states,
      services: props.services
    });
  }

  render() {
    return (
      <div>
        <h3 className="title">Service Status</h3>
        { this.renderLegend() }
        <table className="table condensed state-table">
          <thead>
            <tr>
              { this.renderTableHeader() }
            </tr>
          </thead>
          <tbody>
            { this.renderTableRows() }
          </tbody>
        </table>
      </div>
    );
  }

  renderLegend() {
    return (
      <ul className="state-legend">
        <li>
          <span className="state-tag is-up"></span>
          Service is up
        </li>
        <li>
          <span className="state-tag is-down"></span>
          Service is down
        </li>
        <li>
          <span className="state-tag is-untested"></span>
          Service is untested
        </li>
      </ul>
    );
  }

  renderTableHeader() {
    let services = _.chain(this.state.serviceStates)
     .values()
     .first()  /*  get only the first item to build the header */
     .map((service, id) => {
       let filteredStatuses = _.chain(this.state.serviceStates).map(s => {
         return s[id]['service_state'];
       }).reject(s => {
         return s === 'untested';
       }).value();
       let isServiceDown = (filteredStatuses.length > 0) && _.every(filteredStatuses, s => {
         return s === 'down';
       });

       let classes = cx('state-table__th--rotate', {'is-down': isServiceDown});
       return (
         <th key={id} className={ classes }>
           <div><span>{ `${service.service_name} : ${this.state.services[id] && this.state.services[id].port}` }</span></div>
         </th>
       );
     }).value();
    return [
      <th key="team" className="align--bottom state-table__th--big">Team</th>
    ].concat(services);
  }

  renderTableRows() {
    return _.map(this.state.serviceStates, (services, teamId) => {
      let team = this.props.teams.find(t => t.id === teamId);
      if (!team || !team.validated) {
        return;
      }
      let states = _.map(services, (s, sId) => {
        return (
          <td key={ `${teamId}-${sId}` } className="align--center" data-title={ s.service_name }>
            { this.renderStateTag(s.service_state, s.service_name, team.name) }
          </td>
        );
      });
      states.unshift(
          <td key={ `${teamId}-name` } className="truncate">{ `${team.name.substring(0, 40)}`}</td>
      );
      return (
        <tr key={ `t-${teamId}` }>
          { states }
        </tr>
      );
    });
  }

  renderStateTag(state, serviceName, teamName) {
    return (
      <span className={ `state-tag is-${state.toLowerCase()}` }
            title={ `${teamName} - ${serviceName}` } />
    );
  }
}
