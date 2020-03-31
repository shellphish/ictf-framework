import mixin from 'universal-mixin';

export default mixin({
  componentWillMount() {
    this.intervals = [];
  },

  setInterval() {
    this.intervals.push(setInterval.apply(null, arguments));
  },

  componentWillUnmount: function() {
    this.intervals.forEach(clearInterval);
  }
});
