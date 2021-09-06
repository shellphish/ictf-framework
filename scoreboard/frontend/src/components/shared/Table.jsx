import React, { Component } from 'react';
import classNames from 'classnames';
import _ from 'underscore';
import PropTypes from 'prop-types'

/*
   Props format:

   headers: [
     {id: 'team_name', label: 'Team', sort_attr: '...', altSortAttr: 'team_id', className="column-class"},
     {id: 'points', label: 'Total points'}
   ]
   rows: [{team_name: 'Shellphish', points: 100}, {...}]
   defaultSortAttr: 'team_name'
   defaultSortDirection: 'asc'
   className: "table-css-class"
 */
export default class Table extends Component {
  static propTypes = {
    headers: PropTypes.array.isRequired,
    rows: PropTypes.array.isRequired,
    defaultSortAttr: PropTypes.string.isRequired,
    defaultSortDirection: PropTypes.string,
    className: PropTypes.string
  }

  state = {
    sortAttr: this.props.defaultSortAttr,
    sortDesc: this.props.defaultSortDirection === 'asc' ? false : true
  }

  sortRows() {
    let sortHeader = _.find(this.props.headers, h => { return h.id === this.state.sortAttr; });
    let sortAttr = undefined;
    if (sortHeader) {
      sortAttr = sortHeader.altSortAttr ? sortHeader.altSortAttr : sortHeader.id;
    }
    let sortedRows = _.chain(this.props.rows).sortBy(sortAttr);
    if (this.state.sortDesc) {
      sortedRows = sortedRows.reverse().value();
    }
    else {
      sortedRows = sortedRows.value();
    }
    return sortedRows;
  }

  handleSortColumn(attr, e) {
    e.preventDefault();
    if (this.state.sortAttr === attr) {
      this.setState({sortDesc: !this.state.sortDesc});
    }
    else {
      this.setState({sortDesc: true});
    }
    this.setState({sortAttr: attr});
  }

  render() {
    return (
      <table className={ classNames('table', this.props.className) }>
        <thead>
          <tr>
            { this.renderHeaders() }
          </tr>
        </thead>
        <tbody>
          { this.renderRows() }
        </tbody>
      </table>
    );
  }

  renderHeaders() {
    return this.props.headers.map(h => {
      return (
        <th key={ `th-${h.id}` } className={ h.className }>
          <a 
             href="#sort"
             className={ classNames({'is-sorted': this.state.sortAttr === h.id, 'is-desc': this.state.sortDesc}) }
             onClick={ this.handleSortColumn.bind(this, h.id) }
            >
            { h.label }
            
          </a>
        </th>
      );
    });
  }

  renderRows() {
    return this.sortRows().map((row, i) => {
      let cells = _.map(this.props.headers).map(header => {
        let id = header.id;
        return (
          <td key={ `td-${i}-${id}` }
              data-title={ header.label }
              className={ header.className }>
            { row[id] }
          </td>
        );
      });
      return (
        <tr key={ `tr-${i}` }>
          { cells }
        </tr>
      );
    });
  }
}
