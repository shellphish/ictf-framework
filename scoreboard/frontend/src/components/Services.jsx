import React, { Component } from 'react';
import _ from 'underscore';
import PropTypes from 'prop-types';

import Table from './shared/Table';

export default class Services extends Component {
  static propTypes = {
    services: PropTypes.object.isRequired
  }

  static defaultProps = {
    services: {}
  }

  tableHeaders() {
    return [
      {id: 'service_name', label: 'Name'},
      {id: 'port', label: 'Port'},
      {id: 'description', label: 'Description'},
      {id: 'flag_id_description', label: 'Flag Description'},
      {id: 'authors', label: 'Author'}
    ];
  }

  tableRows() {
    return _.filter(this.props.services, service => {
      if (service.state === 'enabled') {
        return true;
      }
    });
  }

  render() {
    return (
      <div>
        <h3 className="title">Service List</h3>

        <Table headers={ this.tableHeaders() }
               rows={ this.tableRows() }
               defaultSortAttr="port"
               defaultSortDirection="asc"/>
      </div>
    );
  }
}
