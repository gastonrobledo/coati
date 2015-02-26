(function (angular) {

    function ConfigApp(interpolate, location, urlRoute, growlProvider, translateProvider, loadingBar) {
        urlRoute.when('/', '/home/');
        location.html5Mode({
            enabled: true,
            requireBase: false
        });
        location.hashPrefix('!');
        interpolate.startSymbol('<[');
        interpolate.endSymbol(']>');
        growlProvider.globalTimeToLive(5000);
        growlProvider.onlyUniqueMessages(true);
        translateProvider.useStaticFilesLoader({
            prefix: '/static/assets/lang/',
            suffix: '.json'
        });
        translateProvider.preferredLanguage('en')
            .fallbackLanguage('en')
            .useStorage('StorageService');
        loadingBar.includeSpinner = false;
        loadingBar.latencyThreshold = 500;

    }


    // Filters
    var sumValue = function () {
        return function (items, field) {
            var total = 0, i = 0;
            if (items !== undefined) {
                for (i = 0; i < items.length; i++) {
                    total += items[i][field] || 0;
                }
            }
            return total;
        };
    };

    var filterGetByProperty = function () {
        return function (propertyName, propertyValue, collection) {
            for (var i = 0; i < collection.length; i++) {
                var v = collection[i];
                if (v[propertyName] === propertyValue) {
                    return v;
                }
            }
            return null;
        };
    };

    var filterGetIndexByProperty = function () {
        return function (propertyName, propertyValue, collection) {
            for (var i = 0; i < collection.length; i++) {
                var v = collection[i];
                if (v[propertyName] === propertyValue) {
                    return i;
                }
            }
            return null;
        };
    };

    var filterTicketTypes = function () {
        return function (types, type) {
            var value = null;
            for (var i = 0; i < types.length; i++) {
                var v = types[i];
                if (v.value === type) {
                    value = v.name;
                    break;
                }
            }
            return value;
        };
    };

    var filterTrustedHTML = function (sce) {
        return function (text) {
            return sce.trustAsHtml(text);
        };
    };

    var filterNl2Br =  function(sce) {
        return function (msg, is_xhtml) {
            if(msg === undefined){
                return;
            }
            var xhtml = is_xhtml || true;
            var breakTag = (xhtml) ? '<br />' : '<br>';
            var data = (msg + '').replace(/([^>\r\n]?)(\r\n|\n\r|\r|\n)/g, '$1' + breakTag + '$2');
            return sce.trustAsHtml(data);
        };
    };

    var AppController = function (scope, rootScope, state, stateParams, tokens, TicketService, SocketIO, translate, StorageService) {
        var vm = this;
        rootScope.$on('$stateChangeStart', function (event, toState) {

            if (angular.isDefined(toState.data.pageTitle)) {
                
                scope.pageTitle = toState.data.pageTitle + ' | Coati';
            }
            scope.actual_path = toState.name;
            rootScope.state_name = toState.name;
        });

        rootScope.$on('$stateChangeSuccess', function (event) {
            if (rootScope.state_name !== 'login' &&
                rootScope.state_name !== 'login_auth' &&
                rootScope.state_name !== 'login_register') {
                if (tokens.get_token() == null) {
                    event.preventDefault();
                    state.go('login', stateParams, {reload: true, notify: false});
                }
            }
        });

        vm.searchTickets = function (query) {
            vm.loading_results = true;
            return TicketService.search(query).then(function (rta) {
                vm.loading_results = false;
                return rta.map(function (item) {
                    var result = {
                        label: item.project.prefix + '-' + item.number + ': ' + item.title,
                        description: item.description,
                        data: item
                    };
                    return result;
                });
            });
        };


        vm.on_select_result = function (item, model) {
            return model.label;
        };

        vm.selectedLanguage = StorageService.get('NG_TRANSLATE_LANG_KEY');

        vm.switchLanguage = function (lang) {
            vm.selectedLanguage = lang;
            translate.use(lang);
        };
        //Init Socket interaction
        SocketIO.init();
    };

    var RunApp = function (rootScope, state, stateParams, objects, StorageService, editableOptions, editableThemes) {

        editableThemes.bs3.inputClass = 'input-sm';
        editableThemes.bs3.buttonsClass = 'btn-sm';
        editableOptions.theme = 'bs3';

        var user = null;
        try {
            user = JSON.parse(StorageService.get('user'));
            if (objects.isObject(user)) {
                rootScope.user = user;
            } else {
                if (window.location.href.indexOf('login') < 0) {
                    stateParams.next = window.location.href;
                    state.go('login', stateParams);
                }
            }
        } catch (err) {

        }

    };

    // Injections
    filterTrustedHTML.$inject = ['$sce'];
    filterNl2Br.$inject = ['$sce'];
    RunApp.$inject = ['$rootScope', '$state', '$stateParams', '$objects', 'StorageService', 'editableOptions', 'editableThemes'];
    ConfigApp.$inject = ['$interpolateProvider', '$locationProvider', '$urlRouterProvider', 'growlProvider', '$translateProvider', 'cfpLoadingBarProvider'];
    AppController.$inject = ['$scope', '$rootScope', '$state', '$stateParams', 'tokens', 'TicketService', 'SocketIO', '$translate', 'StorageService'];

    angular.module('Coati', [
        'templates-app',
        'templates-common',
        'angular-loading-bar',
        'pascalprecht.translate',
        'ui.router',
        'ui.bootstrap',
        'Coati.SocketIO',
        'Coati.Config',
        'Coati.Directives',
        'Coati.Services.Storage',
        'Coati.Services.Ticket',
        'Coati.Errors',
        'Coati.Home',
        'Coati.Login',
        'Coati.User',
        'Coati.Project',
        'Coati.Ticket',
        'Coati.Sprint'
    ])
        .config(ConfigApp)
        .run(RunApp)
        .filter('getByProperty', filterGetByProperty)
        .filter('getIndexByProperty', filterGetIndexByProperty)
        .filter('sumValue', sumValue)
        .filter('ticketTypes', filterTicketTypes)
        .filter('trustedHtml', filterTrustedHTML)
        .filter('nl2br', filterNl2Br)
        .controller('AppCtrl', AppController);


}(angular));

