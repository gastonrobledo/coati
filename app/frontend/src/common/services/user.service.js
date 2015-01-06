(function(angular){

    var UserService = function(req, tokens){
        return {
            'search': function (q) {
                return req.$do('/users/search/' + q, req.METHODS.GET);
            },
            'update': function(pk, data){
                return req.$do('/user/' + pk, req.METHODS.UPDATE, data);
            },
            'register': function(data){
              return req.$do('/user/register', req.METHODS.POST, data);
            },
            'get': function(pk){
                return req.$do('/user/' + pk, req.METHODS.GET);
            },
            'me': function(){
                return req.$do('/user/me', req.METHODS.GET);
            },
            'activateUser': function(code){
                return req.$do('/user/activate/' + code, req.METHODS.GET);
            },
            'is_logged': function(){
                var token = tokens.get_token();
                return token ? true : false;
            }
        };
    };

    UserService.$inject = ['$requests', 'tokens'];

    angular.module('Coati.Services.User', ['Coati.Helpers'])
        .factory('UserService', UserService);

}(angular));