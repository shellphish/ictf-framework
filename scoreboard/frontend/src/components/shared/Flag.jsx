import React, { Component } from 'react';
import PropTypes from 'prop-types';

export default class Flag extends Component {
  static propTypes = {
    country: PropTypes.string.isRequired,
    size: PropTypes.string
  }

  static defaultProps = {
    size: "32"
  }

  render() {
    return (
      <img src={ process.env.PUBLIC_URL + `/flags/${this.props.country.toUpperCase()}.png` } alt={`flag of ${this.props.country.toUpperCase()}`} width={ this.props.size }/>
    );
  }
}
