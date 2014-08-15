'use strict';

var ctfApp = angular.module('ctfApp', [
    'ngRoute',
    'ctfControllers'
]);

// routing
ctfApp.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/services', {
        templateUrl: 'partials/services.html',
        controller: 'ServicesCtrl'
      }).
      when('/submit_flag', {
        templateUrl: 'partials/submit_flag.html',
        controller: 'FlagCtrl'
      }).
      when('/scoreboard', {
        templateUrl: 'partials/scoreboard.html',
        controller: 'ScoreboardCtrl'
      }).
      when('/welcome', {
        templateUrl: 'partials/welcome.html',
        controller: 'ConfigCtrl'
      }).
      otherwise({
        redirectTo: '/welcome'
      });
  }]);

