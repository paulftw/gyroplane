
(function() {
    var SERVER_NAME = window.Gyroplane_Context.SERVER_NAME;

    var LOADED_SRC = window.Gyroplane_Context.files;
    var LOADED_FIDDLE_ID = window.Gyroplane_Context.fiddle_id;

    var DEFAULT_CODE = "@app.route('/')\n\
def homepage():\n\
    return mainpage_tpl\n\
\n\
\n\
view_count = 0\n\
\n\
@app.route('/counter')\n\
def counter():\n\
    global view_count\n\
    view_count = view_count + 1\n\
    return counter_tpl % view_count\n\
\n\
\n\
mainpage_tpl = \"\"\"\n\
    <h1>Hello World!</h1>\n\
    <p>\n\
        Try <a href=/counter>counter</a>\n\
    </p>\n\
\"\"\"\n\
\n\
counter_tpl = \"\"\"\n\
    <p>This page has been visited %s time(s)</p>\n\
    <a href=/counter>Refresh</a>\n\
\"\"\"\n\
";

    var module = angular.module('gyro', ['ui.ace']);

    module.controller('Fiddler', function($scope, $http, $sce, $document) {

        $scope.reset_state = function() {

            $scope.files = LOADED_SRC || {
                'main.py': DEFAULT_CODE
            };

            $scope.fiddle_id = LOADED_FIDDLE_ID;
            $scope.url_suffix = '/';
        };
        $scope.reset_state();

        $scope.save = function() {
            $http.post('/save', {files: $scope.files})
                .success(function(data, status, headers, config) {
                    if ($scope.fiddle_id != data.fiddle_id) {
                        $scope.fiddle_id = data.fiddle_id;
                        $scope.open_fiddle_root();
                        window.location = '/v0/' + $scope.fiddle_id;
                    }
                    $scope.refresh_iframe();
                })
                .error(function() {
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
        }

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

}());
