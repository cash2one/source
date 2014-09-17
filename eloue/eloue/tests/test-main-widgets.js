var tests = [];
for (var file in window.__karma__.files) {
  if (window.__karma__.files.hasOwnProperty(file)) {
    if (/.spec\.js$/.test(file)) {
      tests.push(file);
    }
  }
}

requirejs.config({
    // Karma serves files from '/base'
    baseUrl: '/base/static/js/widgets',

    paths: {
        "bootstrap": "../../bower_components/bootstrap/dist/js/bootstrap.min",
        "jQuery": "../../bower_components/jquery/dist/jquery.min",
        "angular": "../../bower_components/angular/angular.min",
        "angular-resource": "../../bower_components/angular-resource/angular-resource.min",
        "angular-route": "../../bower_components/angular-route/angular-route.min",
        "angular-cookies": "../../bower_components/angular-cookies/angular-cookies.min",
        "angular-sanitize": "../../bower_components/angular-sanitize/angular-sanitize.min",
        "angular-mocks": "../../bower_components/angular-mocks/angular-mocks",
        "moment": "../../bower_components/moment/min/moment.min",
        "angular-moment": "../../bower_components/angular-moment/angular-moment.min",
        "bootstrap-datepicker": "../../bower_components/bootstrap-datepicker/js/bootstrap-datepicker",
        "datejs": "../../bower_components/datejs/build/production/date.min",
        "custom-scrollbar": "../../bower_components/malihu-custom-scrollbar-plugin/jquery.mCustomScrollbar",
        "jquery-mousewheel": "../../bower_components/jquery-mousewheel/jquery.mousewheel",
        "toastr": "../../bower_components/toastr/toastr.min",
        "formmapper": "../formmapper"
    },

    shim: {
        "angular": {"exports": "angular"},
        "angular-route": ["angular"],
        "angular-cookies": ["angular"],
        "angular-sanitize": ["angular"],
        "angular-resource": ["angular"],
        "angular-mocks": {
            deps: ["angular"],
            "exports": "angular.mock"
        },
        "jQuery": {exports: "jQuery"},
        "bootstrap": ["jQuery"],
        "moment": ["jQuery"],
        "bootstrap-datepicker": ["jQuery"],
        "formmapper": ["jQuery"],
        "jquery-mousewheel": ["jQuery"],
        "custom-scrollbar": ["jQuery", "jquery-mousewheel"],
        "toastr": ["jQuery"]
    },

    // ask Require.js to load these files (all our tests)
    deps: tests,

    // start test run, once Require.js is done
    callback: window.__karma__.start
});
