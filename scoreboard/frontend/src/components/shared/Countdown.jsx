import React, { Component } from 'react';
import api from '../../sources/api';
import dayjs from '../../sources/dayjs-local';

import SetIntervalMixin from '../../mixins/SetIntervalMixin';
import {pad} from '../../utils/pad';

class Countdown extends Component {

  getNewDeadline() {
    api.get('/tick').then(res => {
      let end = dayjs.utc(res.body.ends_on);
      let now = dayjs.utc();
      let newDeadline = Math.max(end.diff(now, 's'), 0);
      this.setState({
        deadline: newDeadline,
        tickId: res.body.tick_id
      });
    })
  }

  constructor(props) {
    super(props);
    // game ends
    //alert(dayjs);
    var endGame = dayjs('2021-10-15 19:00')
      .tz('America/Los_Angeles', true);
    //alert("endGame (parsed): " + endGame);
    endGame = dayjs.utc(endGame);
    // alert("endGame (utc): " + endGame);
      
    let now = dayjs.utc();
    let newGameDeadline = Math.max(endGame.diff(now, 's'), 0);
    this.state = {
      deadline: 0,
      gameDeadline: newGameDeadline,
      tickId: 0
    }
  }

  componentDidMount() {
    this.getNewDeadline();
    this.setInterval(() => this.updateCountdown(), 1000);
  }

  updateCountdown() {
    let deadline = this.state.deadline;
    let newGameDeadline = this.state.gameDeadline;

    if (newGameDeadline > 0) {
      newGameDeadline = newGameDeadline - 1;
      if (newGameDeadline === 0) return;
    }

    if (deadline <= 0) {
      this.getNewDeadline();
      this.setState({gameDeadline: newGameDeadline});
    }
    else {
      deadline = deadline - 1;
      this.setState({deadline: deadline, gameDeadline: newGameDeadline});
    }

  }

  render() {
    let minutes = Math.floor(this.state.deadline / 60);
    let seconds = this.state.deadline % 60;

    let gameHours = Math.floor(this.state.gameDeadline / 3600)
    let gameMinutes = Math.floor((this.state.gameDeadline - (gameHours * 3600))/ 60);
    let gameSeconds = this.state.gameDeadline - (gameHours * 3600) - (gameMinutes * 60);

    return (
      <div className="countdown">

      <div className="space--bottom-1">
        <span className="countdown__label">Game ends in</span>
        <span className="countdown__time--small">
          <span id="gameHours">{ pad(gameHours, 2) }</span>
          :
          <span id="gameMinutes">{ pad(gameMinutes, 2) }</span>
          :
          <span id="gameSeconds">{ pad(gameSeconds, 2) }</span>
        </span>
      </div>

        <div className="space--bottom-1">
          <span className="countdown__label">current tick</span>
          <span className="countdown__time">
            { this.state.tickId }
          </span>
        </div>

        <div>
          <span className="countdown__label">next in about</span>
          <span className="countdown__time">
            <span id="minutes">{ pad(minutes, 2) }</span>
            :
            <span id="seconds">{ pad(seconds, 2) }</span>
          </span>
        </div>
      </div>
    );
  }
}
Countdown = SetIntervalMixin(Countdown);
export default Countdown;
