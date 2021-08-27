let round = function(number, precision = 2) {
  let multiplier = Math.pow(10, precision);
  return Math.round(number * multiplier) / multiplier;
};

export default round;
