(function (angular) {

    function ConfigApp(ConfProvider, location, urlRoute, growlProvider, translateProvider, FacebookProvider, GooglePlusProvider,loadingBar) {
        urlRoute.when('/', '/home/');
        location.html5Mode({
            enabled: true,
            requireBase: false
        });
        location.hashPrefix('!');

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

        FacebookProvider.init(ConfProvider.getItem('FACEBOOK_KEY'));
        GooglePlusProvider.init();
        GooglePlusProvider.setClientId(ConfProvider.getItem('GOOGLE_KEY'));
        GooglePlusProvider.setScopes(ConfProvider.getItem('GOOGLE_SCOPES'));


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

    var filterNl2Br = function (sce) {
        return function (msg, is_xhtml) {
            if (msg === undefined) {
                return;
            }
            var xhtml = is_xhtml || true;
            var breakTag = (xhtml) ? '<br />' : '<br>';
            var data = (msg + '').replace(/([^>\r\n]?)(\r\n|\n\r|\r|\n)/g, '$1' + breakTag + '$2');
            return sce.trustAsHtml(data);
        };
    };

    var AppController = function (scope, rootScope, state, stateParams, UserService, TicketService, SocketIO, translate, StorageService) {
        var vm = this;
        rootScope.$on('$stateChangeStart', function (event, toState) {

            if (angular.isDefined(toState.data.pageTitle)) {

                scope.pageTitle = toState.data.pageTitle + ' | Coati';
            }
            scope.actual_path = toState.name;
            rootScope.state = toState;

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

    var RunApp = function (wnd, rootScope, state, stateParams, objects, UserService, StorageService, editableOptions, editableThemes) {

        editableThemes.bs3.inputClass = 'input-sm';
        editableThemes.bs3.buttonsClass = 'btn-sm';
        editableOptions.theme = 'bs3';

        var user = null;
        try {

            user = JSON.parse(StorageService.get('user'));
            if (objects.isObject(user)) {

                rootScope.user = user;

            } else {
                if (wnd.location.href.indexOf('login') < 0 &&
                    wnd.location.href.indexOf('register') < 0 &&
                    wnd.location.href.indexOf('logout') < 0 &&
                    wnd.location.href.indexOf('activate') < 0) {
                    stateParams.next = wnd.location.href;
                    state.go('login', stateParams, {reload: true});
                }
            }

        } catch (err) {
            state.go('login', stateParams, {reload: true});
        }

        rootScope.$on('$stateChangeSuccess', function () {
            if (!rootScope.state.data.anonymous) {
                if (!UserService.is_logged()) {
                    state.go('login', stateParams, {reload: true});
                }
            }
        });

    };

    // Injections
    filterTrustedHTML.$inject = ['$sce'];
    filterNl2Br.$inject = ['$sce'];
    RunApp.$inject = ['$window', '$rootScope', '$state', '$stateParams', '$objects', 'UserService', 'StorageService', 'editableOptions', 'editableThemes'];
    ConfigApp.$inject = ['ConfProvider', '$locationProvider', '$urlRouterProvider', 'growlProvider', '$translateProvider', 'FacebookProvider', 'GooglePlusProvider', 'cfpLoadingBarProvider'];
    AppController.$inject = ['$scope', '$rootScope', '$state', '$stateParams', 'UserService', 'TicketService', 'SocketIO', '$translate', 'StorageService'];

    angular.module('Coati', [
        'templates-app',
        'templates-common',
        'angular-loading-bar',
        'angular.filter',
        'pascalprecht.translate',
        'ui.router',
        'ui.bootstrap',
        'facebook',
        'googleplus',
        'Coati.SocketIO',
        'Coati.Config',
        'Coati.Directives',
        'Coati.Services.User',
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


