import React, { Component } from 'react';

export default class Flag extends Component {
  static propTypes = {
    country: React.PropTypes.string.isRequired,
    size: React.PropTypes.string
  }

  static defaultProps = {
    size: "32"
  }

  render() {
    return (
      <img src={ `/flags/${this.props.country.toUpperCase()}.png` } width={ this.props.size }/>
    );
  }
}
