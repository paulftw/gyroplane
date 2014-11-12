
(function() {
    var SERVER_NAME = window.Gyroplane_Context.SERVER_NAME;

    var LOADED_SRC = window.Gyroplane_Context.files;
    var LOADED_FIDDLE_ID = window.Gyroplane_Context.fiddle_id;

    var module = angular.module('gyro', ['ui.ace', 'ui.bootstrap']);

    module.controller('Fiddler', function($scope, $http, $sce, $document, $focus) {

        $scope.reset_state = function() {

            $scope.files = LOADED_SRC;
            $scope.deleted_files = {};

            $scope.fiddle_id = LOADED_FIDDLE_ID;
            $scope.url_suffix = '/';
            $scope.active_file = 'main.py';
        };
        $scope.reset_state();

        $scope.save = function() {
            $scope.save_in_progress = true;
            $http.post('/save', {
                    files: $scope.files,
                    deleted_files: $scope.deleted_files,
                    fiddle_id: $scope.fiddle_id
            }).success(function(data, status, headers, config) {
                $scope.save_in_progress = false;
                if ($scope.fiddle_id != data.fiddle_id) {
                    $scope.fiddle_id = data.fiddle_id;
                    $scope.open_fiddle_root();
                    window.location = '/v0/' + $scope.fiddle_id;
                }
                $scope.refresh_iframe();
            }).error(function() {
                $scope.save_in_progress = false;
                console.log('error', arguments);
            });
        };

        $scope.url_prefix = function() {
            return 'http://' + $scope.fiddle_id + '.' + SERVER_NAME + '';
        };

        $scope.refresh_iframe = function() {
            var url = $scope.url_prefix() + $scope.url_suffix;
            var url_changed = url != $scope.iframe_url;
            $scope.iframe_url = $sce.trustAsResourceUrl(url);

            if (!url_changed) {
                var iFrame = $document.find("iframe");
                iFrame.attr("src",iFrame.attr("src"));
            }
        };
        if ($scope.fiddle_id) {
            $scope.refresh_iframe();
        }


        $scope.open_fiddle_root = function() {
            $scope.url_suffix = '/';
            //$location.path($scope.fiddle_id);
        };

        $scope.edit_file = function(filename, $event) {
            $scope.active_file = filename;
        };

        $scope.new_file = function() {
            var filename = "new_file.000";
            var index = 1;
            while ($scope.files.hasOwnProperty(filename)) {
                filename = (index++) + "";
                while (filename.length < 3) {
                    filename = "0" + filename;
                }
                filename = "new_file." + filename;
            }
            $scope.files[filename] = '<type something awesome>';
            $scope.active_file = filename;
            $scope.rename_file(filename);
        };

        $scope.delete_file = function(name) {
            if (name=='main.py') {
                return;
            }
            $scope.deleted_files[name] = 1;
            delete $scope.files[name];
            $scope.active_file = 'main.py';
        };

        $scope.rename_file = function(name) {
            $scope.renaming = $scope.renaming || {};
            $scope.renaming.file = name;
            $scope.renaming.to = name;
            $focus('renaming_input');
        };

        $scope.renaming_keydown = function(event) {
            if (!$scope.renaming || !$scope.renaming.file) {
                return;
            }
            if (event.keyCode == 13) {
                var new_name = $scope.renaming.to;
                var old_name = $scope.renaming.file;
                if (new_name == old_name) {
                    $scope.renaming= {};
                    return;
                }
                $scope.files[new_name] = $scope.files[old_name];
                $scope.delete_file(old_name);
                $scope.active_file = new_name;
                return;
            }
            if (event.keyCode == 27) {
                $scope.renaming= {};
            }
        };

//        $scope.$watch(function() {
//            return $location.path();
//        }, function(newVal) {
//            var fiddle_id = newVal;
//            if (fiddle_id[0] == '/') {
//                fiddle_id = fiddle_id.substring(1);
//            }
//
//            if (fiddle_id == '') {
//                if ($scope.fiddle_id == null) {
//                    return;
//                } else {
//                    $scope.reset_state();
//                    return;
//                }
//            }
//
//            $scope.fiddle_id = fiddle_id;
//            $http.get('/get_code', { params: {fiddle_id: fiddle_id } })
//                .success(function(response, status) {
//                    $scope.files = response;
//                    //alert('loaded some');
//                });
//            $scope.refresh_iframe();
//        });
    });


    module.directive('focusOn', function() {
       return function(scope, elem, attr) {
          scope.$on('focusOn', function(e, name) {
            if(name === attr.focusOn) {
              elem[0].focus();
              elem[0].select();
            }
          });
       };
    });

    module.factory('$focus', function ($rootScope, $timeout) {
      return function(name) {
        $timeout(function (){
          $rootScope.$broadcast('focusOn', name);
        });
      }
    });

}());
