/**
 * This file/module contains all configuration for the build process.
 */
module.exports = {
    /**
     * The `build_dir` folder is where our projects are compiled during
     * development and the `compile_dir` folder is where our app resides once it's
     * completely built.
     */
    build_dir: 'build',
    compile_dir: 'bin',
    static_dir: 'static',

    /**
     * This is a collection of file patterns that refer to our app code (the
     * stuff in `src/`). These file paths are used in the configuration of
     * build tasks. `js` is all project javascript, less tests. `ctpl` contains
     * our reusable components' (`src/common`) template HTML files, while
     * `atpl` contains the same, but for our app's code. `html` is just our
     * main HTML file, `less` is our main stylesheet, and `unit` contains our
     * app's unit tests.
     */
    app_files: {
        js: [ 'src/**/*.js', '!src/**/*.spec.js', '!src/assets/**/*.js',
            '!src/**/*.map.js'],
        jsunit: [ 'src/**/*.spec.js' ],

        lint: ['src/**/*.js', '!src/**/utils/*.js', '!src/assets/**/*.js',
            '!src/**/*.map.js'],

        coffee: [ 'src/**/*.coffee', '!src/**/*.spec.coffee' ],
        coffeeunit: [ 'src/**/*.spec.coffee' ],

        atpl: [ 'src/app/**/*.tpl.html' ],
        ctpl: [ 'src/common/**/*.tpl.html', 'src/common/**/*.html' ],

        html: [ 'src/index.html' ],

        css: [
            'src/css/font-awesome.min.css',
            'src/css/bootstrap.min.css',
            'src/css/bootstrap-theme.min.css',
            'src/css/bootstrap-social.css',
            'src/css/navbar-fixed-top.css',
            'src/css/table-responsive.css',
            'src/css/tasks.css',
            'src/css/bootstrap-reset.css',
            'src/css/style.css',
            'src/css/style-responsive.css',
            'src/css/angular-growl.min.css',
            'src/css/datepicker.css',
            'src/css/custom.css'
        ]
    },

    /**
     * This is a collection of files used during testing only.
     */
    test_files: {
        js: [
            'vendor/angular-mocks/angular-mocks.js'
        ]
    },

    /**
     * This is the same as `app_files`, except it contains patterns that
     * reference vendor code (`vendor/`) that we need to place into the build
     * process somewhere. While the `app_files` property ensures all
     * standardized files are collected for compilation, it is the user's job
     * to ensure non-standardized (i.e. vendor-related) files are handled
     * appropriately in `vendor_files.js`.
     *
     * The `vendor_files.js` property holds files to be automatically
     * concatenated and minified with our project source files.
     *
     * The `vendor_files.css` property holds any CSS files to be automatically
     * included in our app.
     *
     * The `vendor_files.assets` property holds any assets to be copied along
     * with our app's assets. This structure is flattened, so it is not
     * recommended that you use wildcards.
     */
    vendor_files: {
        js: [
            'vendor/jquery/dist/jquery.min.js',
            'vendor/jquery-ui/ui/minified/jquery-ui.min.js',
            'vendor/angular/angular.min.js',
            'vendor/lodash/lodash.min.js',
            'vendor/angular-ui-router/release/angular-ui-router.js',
            'vendor/angular-ui-utils/modules/route/route.js',
            'vendor/angular-bootstrap/ui-bootstrap.min.js',
            'vendor/angular-bootstrap/ui-bootstrap-tpls.min.js',
            'vendor/angular-cookies/angular-cookies.min.js',
            'vendor/bootstrap/dist/js/bootstrap.min.js',
            'vendor/html5shiv/dist/html5shiv.min.js',
            'vendor/ng-tags-input/ng-tags-input.js',
            'vendor/ng-file-upload/angular-file-upload.min.js',
            'vendor/ng-file-upload/angular-file-upload-shim.min.js',
            'vendor/angular-ui-sortable/sortable.min.js',
            'vendor/angular-xeditable/dist/js/xeditable.min.js',
            'vendor/angular-translate/angular-translate.js',
            'vendor/angular-translate-loader-static-files/angular-translate-loader-static-files.min.js',
            'vendor/chartjs/Chart.min.js',
            'vendor/angular-loading-bar/build/loading-bar.min.js',
            'vendor/angular-bootstrap-colorpicker/js/bootstrap-colorpicker-module.min.js',
            'vendor/angular-filter/dist/angular-filter.min.js',
            'vendor/angular-facebook/lib/angular-facebook.js'

        ],
        maps: [
            'vendor/angular/angular.min.js.map',
            'vendor/jquery/dist/jquery.min.map'
        ],
        css: [
            'vendor/angular/angular-csp.css',
            'vendor/angular-notifications/notification.min.css',
            'vendor/ng-tags-input/ng-tags-input.min.css',
            'vendor/angular-xeditable/dist/css/xeditable.css',
            'vendor/angular-loading-bar/build/loading-bar.min.css',
            'vendor/angular-bootstrap-colorpicker/css/colorpicker.min.css'
        ],
        assets: [],
        fonts: [
            'vendor/bootstrap/dist/fonts/*'
        ]
    }
};
