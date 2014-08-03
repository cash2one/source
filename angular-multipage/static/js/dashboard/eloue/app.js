"use strict";
define(["angular",
        "angular-cookies",
        "angular-resource",
        "angular-route",
        "angular-ui-router",
        "../../common/eloue/commonApp"],
    function (angular) {
        // Create dashboard application
        return angular.module("EloueDashboardApp", ["EloueCommon", "ngCookies", "ngResource", "ngRoute", "ui.router"]);
    }
);
