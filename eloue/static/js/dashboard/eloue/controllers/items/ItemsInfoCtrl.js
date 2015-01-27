define([
    "eloue/app",
    "../../../../common/eloue/values",
    "../../../../common/eloue/services/AddressesService",
    "../../../../common/eloue/services/CategoriesService",
    "../../../../common/eloue/services/PicturesService",
    "../../../../common/eloue/services/ProductsService"
], function (EloueDashboardApp) {
    "use strict";
    /**
     * Controller for the items photos and info page.
     */
    EloueDashboardApp.controller("ItemsInfoCtrl", [
        "$q",
        "$scope",
        "$stateParams",
        "Endpoints",
        "PrivateLife",
        "Fuel",
        "Transmission",
        "Mileage",
        "AddressesService",
        "CategoriesService",
        "PicturesService",
        "ProductsService",
        function ($q, $scope, $stateParams, Endpoints, PrivateLife, Fuel, Transmission, Mileage, AddressesService, CategoriesService, PicturesService, ProductsService) {

            $scope.rootCategories = {};
            $scope.nodeCategories = {};
            $scope.leafCategories = {};
            $scope.rootCategory = {};
            $scope.nodeCategory = {};
            $scope.loadingPicture = 0;
            $scope.productsBaseUrl = Endpoints.api_url + "products/";
            $scope.categoriesBaseUrl = Endpoints.api_url + "categories/";
            $scope.isAuto = false;
            $scope.isRealEstate = false;
            $scope.privateLifeOptions = PrivateLife;
            $scope.seatNumberOptions = [
                {id: 2, name: "2"},
                {id: 3, name: "3"},
                {id: 4, name: "4"},
                {id: 5, name: "5"},
                {id: 6, name: "6"},
                {id: 7, name: "7"},
                {id: 8, name: "8"},
                {id: 9, name: "9"},
                {id: 10, name: "10"}
            ];
            $scope.doorNumberOptions = [
                {id: 2, name: "2"},
                {id: 3, name: "3"},
                {id: 4, name: "4"},
                {id: 5, name: "5"},
                {id: 6, name: "6"}
            ];
            $scope.fuelOptions = Fuel;
            $scope.transmissionOptions = Transmission;
            $scope.mileageOptions = Mileage;
            $scope.consumptionOptions = [
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
                {id: 19, name: "19"}
            ];
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

            $scope.handleResponseErrors = function (error, object, action) {
                $scope.submitInProgress = false;
                $scope.showNotification(object, action, false);
            };

            ProductsService.getProductDetails($stateParams.id).then(
                function (product) {
                    $scope.applyProductDetails(product);
                }
            );

            $scope.applyProductDetails = function (product) {
                $scope.markListItemAsSelected("item-", $stateParams.id);
                $scope.markListItemAsSelected("item-tab-", "info");
                // Backend may send this fiels as string. It's wrong. The value
                // must be a number value.
                if (product && product.costs_per_km) {
                    product.costs_per_km = parseFloat(product.costs_per_km);
                }
                $scope.product = product;
                var initialCategoryId = product.category.id;
                CategoriesService.getParentCategory(product.category).then(function (nodeCategory) {
                    if (!nodeCategory.parent) {
                        $scope.nodeCategory = initialCategoryId;
                        $scope.rootCategory = nodeCategory.id;
                        $scope.updateNodeCategories();
                        $scope.updateFieldSet(nodeCategory);
                    } else {
                        $scope.nodeCategory = nodeCategory.id;
                        $scope.updateLeafCategories();
                        CategoriesService.getParentCategory(nodeCategory).then(function (rootCategory) {
                            $scope.rootCategory = rootCategory.id;
                            $scope.updateNodeCategories();
                            $scope.updateFieldSet(rootCategory);
                        });
                    }
                });
                $scope.product.category = $scope.categoriesBaseUrl + $scope.product.category.id + "/";
                $scope.product.addressDetails = $scope.product.address;
                $scope.product.phoneDetails = $scope.product.phone;
                // Initiate custom scrollbars
                $scope.initCustomScrollbars();
            };

            CategoriesService.getRootCategories().then(function (categories) {
                $scope.rootCategories = categories;
            });

            $scope.onPictureAdded = function () {
                $scope.$apply(function () {
                    $scope.loadingPicture += 1;
                });
                PicturesService.savePicture($("#add-picture"), function (data) {
                    $scope.$apply(function () {
                        $scope.loadingPicture -= 1;
                        $scope.product.pictures.push(data);
                    });
                    $scope.showNotification("picture", "upload", true);
                }, function () {
                    $scope.$apply(function () {
                        $scope.loadingPicture -= 1;
                    });
                    $scope.showNotification("picture", "upload", false);
                });
            };

            $scope.updateProduct = function () {
                $scope.submitInProgress = true;
                $scope.product.address = Endpoints.api_url + "addresses/" + $scope.product.addressDetails.id + "/";
                if ($scope.product.phone && $scope.product.phone.id) {
                    $scope.product.phone = Endpoints.api_url + "phones/" + $scope.product.phone.id + "/";
                } else {
                    $scope.product.phone = null;
                }
                if ($scope.isAuto || $scope.isRealEstate) {
                    $scope.product.category = $scope.categoriesBaseUrl + $scope.nodeCategory + "/";
                }
                var promises = [];
                promises.push(AddressesService.update($scope.product.addressDetails));
                promises.push(ProductsService.updateProduct($scope.product));
                $q.all(promises).then(function () {
                    $("#item-title-link-" + $scope.product.id).text($scope.product.summary);
                    $scope.submitInProgress = false;
                    $scope.showNotification("item_info", "save", true);
                }, function (error) {
                    $scope.handleResponseErrors(error, "item_info", "save");
                });
            };

            $scope.updateNodeCategories = function () {
                CategoriesService.getChildCategories($scope.rootCategory).then(function (categories) {
                    $scope.nodeCategories = categories;
                });
                CategoriesService.getCategory($scope.rootCategory).then(function (rootCategory) {
                    $scope.updateFieldSet(rootCategory);
                });
            };

            $scope.updateLeafCategories = function () {
                CategoriesService.getChildCategories($scope.nodeCategory).then(function (categories) {
                    $scope.leafCategories = categories;
                });
            };

            $scope.updateFieldSet = function (rootCategory) {
                $scope.isAuto = false;
                $scope.isRealEstate = false;
                if (rootCategory.name === "Automobile") {
                    $scope.isAuto = true;
                } else if (rootCategory.name === "Location saisonnière") {
                    $scope.isRealEstate = true;
                }
            };

            $scope.getTimes = function (n) {
                return new Array(n);
            };

            $scope.showRemoveConfirm = function (pictureId) {
                $scope.selectedPictureId = pictureId;
                $("#confirm").modal();
            };

            $scope.deletePicture = function () {
                $scope.submitInProgress = true;
                PicturesService.deletePicture($scope.selectedPictureId).then(function () {
                    ProductsService.getProductDetails($stateParams.id).then(function (product) {
                        $scope.submitInProgress = false;
                        $scope.product.pictures = product.pictures;
                    });
                }, function (error) {
                    $scope.handleResponseErrors(error, "picture", "delete");
                });
            };
        }
    ]);
});
