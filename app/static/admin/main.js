
(function() {
    var module = angular.module('gyro', ['ui.ace']);

    module.controller('Fiddler', function($scope, $http, $sce, $location) {

        $scope.files = {
            'main.py':
"@app.route('/')\n\
def homepage():\n\
    return '<h1>Hello World!</h1><p>Try <a href=/counter>counter</a></p>'\n\
\n\
\n\
view_count = 0\n\
\n\
@app.route('/counter')\n\
def counter():\n\
    global view_count\n\
    view_count = view_count + 1\n\
    return 'This page has been visited %s time(s)<br/><a href=/counter>Refresh</a>' % view_count\n\
\n\
"
        };// end of files.

        $scope.fiddle_id = null;
        $scope.url_suffix = '/';
        $scope.save = function() {
            $http.post('/save', {main_py: $scope.files['main.py']})
                .success(function(data, status, headers, config) {
                    if ($scope.fiddle_id != data.fiddle_id) {
                        $scope.fiddle_id = data.fiddle_id;
                        $scope.open_fiddle_root();
                    }
                    $scope.refresh_iframe();
                })
                .error(function() {
                    console.log('error', arguments);
                });
        };

        $scope.url_prefix = function() {
            return 'http://' + $scope.fiddle_id + '.lvh.me:8080/';
        };

        $scope.refresh_iframe = function() {
            $scope.iframe_url = $sce.trustAsResourceUrl($scope.url_prefix() + $scope.url_suffix);
        };

        $scope.open_fiddle_root = function() {
            $scope.url_suffix = '/';
            $location.path($scope.fiddle_id);
        }

        $scope.$watch(function() {
            return $location.path();
        }, function(newVal) {
            var fiddle_id = newVal;
            if (fiddle_id[0] == '/') {
                fiddle_id = fiddle_id.substring(1);
            }
            $scope.fiddle_id = fiddle_id;
            $http.get('/get_code', { params: {fiddle_id: fiddle_id } })
                .success(function(response, status) {
                    $scope.files = response;
                    //alert('loaded some');
                });
        });
    });

}());
