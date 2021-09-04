import React, { Component } from 'react';
import PropTypes from 'prop-types';

import Flag from './shared/Flag';
import Table from './shared/Table';

export default class Teams extends Component {
  static propTypes = {
    teams: PropTypes.object.isRequired
  }

  static defaultProps = {
    teams: {}
  }

  tableHeaders() {
    return [
      {id: 'logo', label: '', className: 'width--64-on-desk'},
      {id: 'name', label: 'Name', className: 'truncate'},
      {id: 'academic_team', label: 'Academic', className: 'width--128-on-desk'},
      {id: 'country', label: 'Country', className: 'width--128-on-desk'},
      {id: 'url', label: 'Website', className: 'truncate'}
    ];
  }

  tableRows() {
    return Object.values(this.props.teams).map(team => {
      return {
        logo: this.renderLogo(team.logo),
        name: team.name,
        academic_team: (team.academic_team ? 'Yes' : 'No'),
        country: <Flag country={ team.country }/>,
        url: <a href={ team.url } target="_blank" rel="noreferrer">{ team.url }</a>
      };
    });
  }

  render() {
    return (
      <div>
        <h3 className="title">Teams</h3>

        <div className="space--bottom-1">{this.props.teams.length} teams</div>

        <Table headers={ this.tableHeaders() }
               rows={ this.tableRows() }
               defaultSortAttr="name"
               defaultSortDirection="asc"/>
      </div>
    );
  }

  renderLogo(base64str) {
    if (base64str && base64str !== 'None' && base64str !== '') {
      return <img src={ `data:image;base64,${base64str}` }
                  alt="Logo" width="32"/>;
    }
    else {
      return '';
    }
  }
}
