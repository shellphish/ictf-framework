import React, { Component } from 'react';
import _ from 'underscore';

import Table from './shared/Table';

export default class Services extends Component {
  static propTypes = {
    services: React.PropTypes.object.isRequired
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
    return _.map(this.props.services, service => {
      if (service.state == 'enabled') {
        return service;
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
