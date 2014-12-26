define([
    "eloue/app",
    "../../../../../bower_components/toastr/toastr",
    "../../../../common/eloue/values",
    "../../../../common/eloue/services/ProductsService",
    "../../../../common/eloue/services/UsersService",
    "../../../../common/eloue/services/AddressesService",
    "../../../../common/eloue/services/AuthService",
    "../../../../common/eloue/services/CategoriesService",
    "../../../../common/eloue/services/PricesService",
    "../../../../common/eloue/services/UtilsService",
    "../../../../common/eloue/services/ToDashboardRedirectService",
    "../../../../common/eloue/services/ServerValidationService",
    "../../../../common/eloue/services/ScriptTagService"
], function (EloueWidgetsApp, toastr) {
    "use strict";

    EloueWidgetsApp.controller("PublishAdCtrl", [
        "$scope",
        "$window",
        "$location",
        "Endpoints",
        "Unit",
        "Currency",
        "ProductsService",
        "UsersService",
        "AddressesService",
        "AuthService",
        "CategoriesService",
        "PricesService",
        "UtilsService",
        "ToDashboardRedirectService",
        "ServerValidationService",
        "ScriptTagService",
        function ($scope, $window, $location, Endpoints, Unit, Currency, ProductsService, UsersService, AddressesService, AuthService, CategoriesService, PricesService, UtilsService, ToDashboardRedirectService, ServerValidationService, ScriptTagService) {

            $scope.submitInProgress = false;
            $scope.publishAdError = null;
            $scope.rootCategories = [];
            $scope.nodeCategories = [];
            $scope.leafCategories = [];
            $scope.capacityOptions = [
                {id: 1, name: "1"},
                {id: 2, name: "2"},
                {id: 3, name: "3"},
                {id: 4, name: "4"},
                {id: 5, name: "5"},
                {id: 6, name: "6"},
                {id: 7, name: "7"},
                {id: 8, name: "8"},
                {id: 9, name: "9"},
                {id: 10, name: "10"},
                {id: 11, name: "11"},
                {id: 12, name: "12"},
                {id: 13, name: "13"},
                {id: 14, name: "14"},
                {id: 15, name: "15"},
                {id: 16, name: "16"},
                {id: 17, name: "17"},
                {id: 18, name: "18"},
                {id: 19, name: "19+"}
            ];
            $scope.productsBaseUrl = Endpoints.api_url + "products/";
            $scope.categoriesBaseUrl = Endpoints.api_url + "categories/";
            $scope.product = {};
            $scope.isAuto = false;
            $scope.isRealEstate = false;
            $scope.price = {
                id: null,
                amount: null,
                unit: Unit.DAY.id
            };

            $scope.errors = {
                summary: "",
                brand: "",
                model: "",
                category: "",
                street: "",
                zipcode: "",
                amount: "",
                deposit_amount: "",
                km_included: "",
                costs_per_km: "",
                first_registration_date: "",
                licence_plate: "",
                tax_horsepower: ""
            };

            /**
             * Show response errors on publish ad form under appropriate field.
             * @param error JSON object with error details
             */
            $scope.handleResponseErrors = function (error) {
                $scope.submitInProgress = false;
            };

            // Read authorization token
            $scope.currentUserToken = AuthService.getUserToken();

            if (!!$scope.currentUserToken) {
                // Get current user
                $scope.currentUserPromise = UsersService.getMe().$promise;
                $scope.currentUserPromise.then(function (currentUser) {
                    // Save current user in the scope
                    $scope.currentUser = currentUser;
                    if (!currentUser.default_address) {
                        $scope.noAddress = true;
                    }
                });
            }

            $scope.setCategoryByLvl = function (categoryId, level) {
                switch (level) {
                    case 1:
                        $scope.nodeCategory = categoryId;
                        $scope.updateLeafCategories();
                        break;
                    case 2:
                        $scope.product.category = categoryId;
                        break;
                    default:
                        $scope.rootCategory = categoryId;
                        $scope.updateNodeCategories();
                }
            };

            /**
             * Load necessary data on modal window open event based on modal name.
             */
            $scope.$on("openModal", function (event, args) {
                $scope.openModal(args.name, args.params.category);
            });

            $scope.openModal = function (name, categoryId) {
                var currentUserToken = AuthService.getUserToken(), modalContainer;
                if (!currentUserToken && name !== "login") {
                    AuthService.saveAttemptUrl(name, {category: categoryId});
                    name = "login";
                } else {
                    //var rootCategoryId = params.category;
                    $scope.product = {};
                    $scope.price = {
                        id: null,
                        amount: null,
                        unit: Unit.DAY.id
                    };
                    $scope.publishAdError = null;
                    // load categories for comboboxes
                    CategoriesService.getRootCategories().then(function (categories) {
                        if ($scope.currentUser && !$scope.currentUser.default_address) {
                            $scope.noAddress = true;
                        }
                        $scope.rootCategories = categories;

                        if (!!categoryId && categoryId !== "") {
                            CategoriesService.getAncestors(categoryId).then($scope.processCategoryAncestors);
                        } else if ($scope.rootCategory) {
                            $scope.updateNodeCategories();
                        }
                    });
                }
                if (name) {
                    $(".modal").modal("hide");
                    modalContainer = $("#" + name + "Modal");
                    modalContainer.modal("show");
                }
            };

            $scope.processCategoryAncestors = function (categories) {
                var level = 0;
                angular.forEach(categories, function (value) {
                    $scope.setCategoryByLvl(value.id, level);
                    level += 1;
                });
                $scope.setCategoryByLvl(categoryId, level);
            };

            /**
             * Restore path when closing modal window.
             */
            $scope.$on("closeModal", function (event, args) {
                var currentPath = $location.path(), newPath = currentPath.slice(0, currentPath.indexOf(args.name));
                $location.path(newPath);
                $scope.$apply();
            });

            /**
             * Update options for node category combobox
             */
            $scope.updateNodeCategories = function () {
                $scope.nodeCategory = undefined;
                CategoriesService.getChildCategories($scope.rootCategory).then(function (categories) {
                    $scope.nodeCategories = categories;
                });
                CategoriesService.getCategory($scope.rootCategory).$promise.then(function (rootCategory) {
                    $scope.updateFieldSet(rootCategory);
                });
            };

            /**
             * Update options for leaf category combobox
             */
            $scope.updateLeafCategories = function () {
                $scope.product.category = undefined;
                CategoriesService.getChildCategories($scope.nodeCategory).then(function (categories) {
                    $scope.leafCategories = categories;
                });
            };


            $scope.isCategorySelectorsValid = function () {
                return !!$scope.rootCategories && !!$scope.rootCategory &&
                    ((!!$scope.nodeCategories && $scope.nodeCategories.length > 0 && !!$scope.nodeCategory) ||
                    (!$scope.nodeCategories || $scope.nodeCategories.length === 0)) &&
                    ((!!$scope.leafCategories && $scope.leafCategories.length > 0 && !!$scope.product.category) ||
                    (!$scope.leafCategories || $scope.leafCategories.length === 0));
            };

            /**
             * Publish product ad.
             */
            $scope.publishAd = function () {
                //if user has no default address, firstly save his address
                if ($scope.noAddress) {
                    $scope.submitInProgress = true;
                    $scope.currentUser.default_address.country = "FR";
                    AddressesService.saveAddress($scope.currentUser.default_address).$promise.then(
                        $scope.applyUserAddress,
                        $scope.handleResponseErrors
                    );
                } else {
                    $scope.saveProduct();
                }
            };

            $scope.applyUserAddress = function (result) {
                $scope.currentUser.default_address = result;
                UsersService.updateUser({default_address: Endpoints.api_url + "addresses/" + result.id + "/"});
                $scope.saveProduct();
            };

            /**
             * Save product and price info.
             */
            $scope.saveProduct = function () {
                $scope.submitInProgress = true;
                $scope.product.description = "";
                $scope.product.address = Endpoints.api_url + "addresses/" + $scope.currentUser.default_address.id + "/";
                if ($scope.price.amount > 0) {
                    if (!$scope.leafCategories || $scope.leafCategories.length === 0) {
                        if (!!$scope.nodeCategories && $scope.nodeCategories.length > 0) {
                            $scope.product.category = $scope.categoriesBaseUrl + $scope.nodeCategory + "/";
                        } else {
                            $scope.product.category = $scope.categoriesBaseUrl + $scope.rootCategory + "/";
                        }
                    }
                    if ($scope.isAuto || $scope.isRealEstate) {
                        $scope.product.category = $scope.categoriesBaseUrl + $scope.nodeCategory + "/";
                    }
                    if ($scope.isAuto) {
                        $scope.product.summary = $scope.product.brand + " " + $scope.product.model;
                        $scope.product.first_registration_date = Date.parse($scope.product.first_registration_date).toString("yyyy-MM-dd");
                    }


                    ProductsService.saveProduct($scope.product).$promise.then(
                        function (product) {
                            $scope.price.currency = Currency.EUR.name;
                            $scope.price.product = $scope.productsBaseUrl + product.id + "/";
                            PricesService.savePrice($scope.price).$promise.then(
                                function () {
                                    CategoriesService.getCategory(UtilsService.getIdFromUrl($scope.product.category)).$promise.then(function (productCategory) {
                                        $scope.trackPublishAdEvent(product, productCategory);
                                    });
                                },
                                $scope.handleResponseErrors
                            );

                        },
                        $scope.handleResponseErrors
                    );
                } else {
                    //$scope.publishAdError = "All prices should be positive numbers!";
                    ServerValidationService.removeErrors();
                    ServerValidationService.addError("amount", "Value can't be negative");

                    $scope.submitInProgress = false;
                }
            };

            $scope.trackPublishAdEvent = function (product, productCategory) {
                if ($scope.isAuto) {
                    ScriptTagService.trackEvent("Dépôt annonce", "Voiture", productCategory.name);
                    $scope.finishProductSaveAndRedirect(product);
                } else if ($scope.isRealEstate) {
                    ScriptTagService.trackEvent("Dépôt annonce", "Logement", productCategory.name);
                    $scope.finishProductSaveAndRedirect(product);
                } else {
                    CategoriesService.getAncestors(UtilsService.getIdFromUrl($scope.product.category)).then(
                        $scope.trackPublishSimpleAdEvent
                    );
                }
            };

            $scope.trackPublishSimpleAdEvent = function (ancestors) {
                var categoriesStr = "";
                angular.forEach(ancestors, function (value) {
                    categoriesStr = categoriesStr + value.name + " - ";
                });
                categoriesStr = categoriesStr + productCategory.name;
                ScriptTagService.trackEvent("Dépôt annonce", "Objet", categoriesStr);
                $scope.finishProductSaveAndRedirect(product);
            };

            /**
             * Add analytics tags on the page and redirect to dashboard item info page.
             * @param product product
             */
            $scope.finishProductSaveAndRedirect = function (product) {
                ScriptTagService.trackPageView();
                ScriptTagService.loadPdltrackingScript($scope.currentUser.id);
                ScriptTagService.loadAdWordsTags("EO41CNPrpQMQjaaF6gM");
                toastr.options.positionClass = "toast-top-full-width";
                toastr.success("Annonce publiée", "");
                $(".modal").modal("hide");
                //$window.location.href = "/dashboard/#/items/" + product.id + "/info";
                $scope.submitInProgress = false;
                ToDashboardRedirectService.showPopupAndRedirect("/dashboard/#/items/" + product.id + "/info");
            };

            /**
             * Update publish ad form according to selected root category.
             * @param rootCategory product root category
             */
            $scope.updateFieldSet = function (rootCategory) {
                $scope.isAuto = false;
                $scope.isRealEstate = false;
                if (rootCategory.name === "Automobile") {
                    $scope.isAuto = true;
                } else if (rootCategory.name === "Location saisonnière") {
                    $scope.isRealEstate = true;
                }
            };

            /**
             * Search for node and leaf categories suggestions based on entered product title.
             */
            $scope.searchCategory = function () {
                if (!$scope.isAuto && !$scope.isRealEstate && $scope.rootCategory && $scope.product.summary && ($scope.product.summary.length > 1)) {
                    CategoriesService.searchByProductTitle($scope.product.summary, $scope.rootCategory).then(
                        $scope.applySuggestedCategories
                    );
                }
            };

            $scope.applySuggestedCategories = function (categories) {
                if (categories && categories.length > 0) {
                    var nodeCategoryList = [], leafCategoryList = [];
                    angular.forEach(categories, function (value) {
                        nodeCategoryList.push({id: value[1].id, name: value[1].name});
                        leafCategoryList.push({id: value[2].id, name: value[2].name});
                    });
                    $scope.nodeCategories = nodeCategoryList;
                    $scope.leafCategories = leafCategoryList;
                }
            };
        }]);
});
