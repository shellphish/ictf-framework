'use strict';

var ctfControllers = angular.module('ctfControllers', []);

ctfControllers.controller('ServicesCtrl', ['$scope', '$http',
  function ($scope, $http) {
      $http.get('/services').success(function(data) {
          $scope.services = data;
      });
      $http.get('/services_status').success(function(data) {
          $scope.services_status = data;
      });
  }]);

ctfControllers.controller('FlagCtrl', ['$scope', '$http',
  function ($scope, $http) {
      $scope.flag = '';
      $scope.result = '';

      $scope.submit = function() {
          if ($scope.flag) {
            $http.post('/flag', {'flag': $scope.flag}).success(function(data) {
                $scope.result = data;
            })
          }
      }
  }]);

ctfControllers.controller('ScoreboardCtrl', ['$scope', '$http',
  function ($scope, $http) {
      $http.get('/scores').success(function(data) {
          $scope.scores = Object.keys(data).map(function(key) {
              return {"team_name" : key, "score" : data[key] }
            });
      });
  }]);

ctfControllers.controller('ToggleCtrl', ['$scope',
  function ($scope) {
      $scope.visible = false;

      $scope.toggle = function() {
          $scope.visible = !$scope.visible;
      };
  }]);

ctfControllers.controller('ConfigCtrl', ['$scope', '$http',
  function ($scope, $http) {
      $http.get('/config').success(function(data) {
          $scope.config = data;
      });
  }]);
