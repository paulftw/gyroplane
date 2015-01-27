
(function(context) {
    var MAX_FILE_SIZE = 1024 * 1024;

    var SERVER_NAME = context.SERVER_NAME;

    var LOADED_SRC = context.files;
    var LOADED_DOMAINS = context.domains || [];
    var LOADED_FIDDLE_ID = context.fiddle_id;

    var module = angular.module('gyro', ['ui.ace', 'ui.bootstrap', 'angularFileUpload']);

    module.controller('Fiddler', function($scope, $http, $sce, $document, $focus, $uploadSignal, FileUploader) {
        mixpanel.track("Page loaded");
        $scope.reset_state = function() {

            $scope.domains = LOADED_DOMAINS;
            $scope.files = LOADED_SRC;
            $scope.deleted_files = {};

            $scope.fiddle_id = LOADED_FIDDLE_ID;
            $scope.url_suffix = '/';
            $scope.active_file = 'main.py';
        };
        $scope.reset_state();

        $scope.save = function() {
            mixpanel.track("Saved app");
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
            if ($scope.files[filename].is_binary) {
                alert('Cannot edit a binary file, sorry.');
                return;
            }
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
            mixpanel.track("Deleted a file");
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
                if ($scope.files[new_name]) {
                    alert('A file with this name already exists');
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

        $scope.uploader = new FileUploader();
        $scope.open_upload = function(event) {
            $uploadSignal('button');
        };

        $scope.uploader.onAfterAddingFile = function(fileItem) {
            if (fileItem.file.size > MAX_FILE_SIZE) {
                alert('File is too big: ' + fileItem.file.name);
                fileItem.remove();
                return;
            }
            var reader = new FileReader();

            // If we use onloadend, we need to check the readyState.
            reader.onloadend = function(evt) {
                $scope.$apply(function() {
                    fileItem.remove();
                    if (evt.target.readyState != FileReader.DONE) {
                        return;
                    }
                    $scope.files[fileItem.file.name] = {
                        is_binary: true,
                        data: btoa(evt.target.result),
                    };
                });
            };

            reader.readAsBinaryString(fileItem._file);
        };

        $scope.add_new_domain = function() {
            var new_domain = 'example-' + $scope.fiddle_id + '.com';
            $scope.domains.push(new_domain);
            $scope.edit_domain(new_domain);
        };

        $scope.edit_domain = function(domain) {
            $scope.editing_domain = $scope.editing_domain || {};
            $scope.editing_domain.from = domain;
            $scope.editing_domain.index = domain;
            $scope.editing_domain.to = domain;
            $focus('renaming_domain');
        };

        $scope.domain_keydown = function(event) {
            if (!$scope.editing_domain || !$scope.editing_domain.from) {
                return;
            }
            if (event.keyCode == 13) {
                var new_name = $scope.editing_domain.to;
                var old_name = $scope.editing_domain.from;
                if (new_name == old_name) {
                    $scope.editing_domain = {};
                    return;
                }
                if ($scope.domains.indexOf(new_name) > -1) {
                    alert('This domain already exists');
                    $scope.editing_domain = {};
                    return;
                }
                $scope.domains[$scope.domains.indexOf(old_name)] = new_name;
                $scope.editing_domain = {};
                $scope.save_domains();
                return;
            }
            if (event.keyCode == 27) {
                $scope.editing_domain = {};
            }
        };


        $scope.save_domains = function() {
            $http.post('/save_domains', {
                    domains: $scope.domains,
                    fiddle_id: $scope.fiddle_id
            }).success(function(data, status, headers, config) {
                console.log('domains saved');
            }).error(function() {
                console.log('error', arguments);
            });
        };


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
        $timeout(function () {
          $rootScope.$broadcast('focusOn', name);
        });
      }
    });

    module.directive('uploadSignal', function() {
       return function(scope, elem, attr) {
          scope.$on('uploadSignal', function(e, name) {
            if(name === attr.uploadSignal) {
              console.log('Got signal', elem, attr);
              elem[0].click();
            }
          });
       };
    });

    module.factory('$uploadSignal', function ($rootScope) {
        return function(name) {
            $rootScope.$broadcast('uploadSignal', name);
        }
    });

}(window.Gyroplane_Context));
