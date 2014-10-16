"use strict";

define(["angular", "toastr", "eloue/app"], function (angular, toastr) {

    /**
     * Controller for the booking detail page.
     */
    angular.module("EloueDashboardApp").controller("BookingDetailCtrl", [
        "$scope",
        "$stateParams",
        "$window",
        "Endpoints",
        "BookingsLoadService",
        "CommentsLoadService",
        "PhoneNumbersService",
        "UsersService",
        "UtilsService",
        function ($scope, $stateParams, $window, Endpoints, BookingsLoadService, CommentsLoadService, PhoneNumbersService, UsersService, UtilsService) {

            // Initial comment data
            $scope.comment = {rate: 0};
            $scope.showIncidentForm = false;

            // On rating star click
            $(".star i").click(function () {
                var self = $(this);
                $scope.$apply(function () {
                    $scope.comment.rate = self.attr("rate");
                });
            });

            // Load booking details
            BookingsLoadService.getBookingDetails($stateParams.uuid).then(function (bookingDetails) {
                $scope.bookingDetails = bookingDetails;
                $scope.showIncidentForm = $scope.bookingDetails.state == 'incident';
                $scope.currentUserPromise.then(function (currentUser) {
                    $scope.currentUserUrl = Endpoints.api_url + "users/" + currentUser.id + "/";
                    $scope.contractLink = Endpoints.api_url + "bookings/" + $stateParams.uuid + "/contract/";
                    $scope.isOwner = bookingDetails.owner.indexOf($scope.currentUserUrl) != -1;
                    $scope.isBorrower = bookingDetails.borrower.indexOf($scope.currentUserUrl) != -1;
                });

                UsersService.get(UtilsService.getIdFromUrl(bookingDetails.borrower)).$promise.then(function (result) {
                    $scope.borrowerName = result.username;
                    $scope.borrowerSlug = result.slug;
                });

                UsersService.get(UtilsService.getIdFromUrl(bookingDetails.owner)).$promise.then(function (result) {
                    $scope.ownerName = result.username;
                    $scope.ownerSlug = result.slug;
                });

                if ($scope.bookingDetails.product.phone) {
                    if ($scope.showRealPhoneNumber($scope.bookingDetails.state)) {
                        $scope.phoneNumber = !!$scope.bookingDetails.product.phone.number.numero ? $scope.bookingDetails.product.phone.number.numero : $scope.bookingDetails.product.phone.number;
                    } else {
                        PhoneNumbersService.getPremiumRateNumber($scope.bookingDetails.product.phone.id).$promise.then(function (result) {
                            if (!result.error || result.error == "0") {
                                $scope.phoneNumber = result.numero;
                            }
                        });
                    }
                }

                $scope.markListItemAsSelected("booking-", $stateParams.uuid);
                // Initiate custom scrollbars
                $scope.initCustomScrollbars();
                // Load comments
                CommentsLoadService.getCommentList($stateParams.uuid).then(function (commentList) {
                    $scope.commentList = commentList;
                    $scope.showCommentForm = $scope.commentList.length == 0 && $scope.bookingDetails.state == "ended";
                });
            });

            /**
             * Show real number of the owner if the booking have the pending status and after.
             * @param status booking status
             * @returns show be real number shown
             */
            $scope.showRealPhoneNumber = function (status) {
                return $.inArray(status, ["pending", "ongoing", "ended", "incident", "refunded", "closed"]) != -1;
            };


            $scope.acceptBooking = function () {
                BookingsLoadService.acceptBooking($stateParams.uuid).$promise.then(function (result) {
                    toastr.options.positionClass = "toast-top-full-width";
                    toastr.success(result.detail, "");
                    $window.location.reload();
                })
            };

            $scope.rejectBooking = function () {
                BookingsLoadService.rejectBooking($stateParams.uuid).$promise.then(function (result) {
                    toastr.options.positionClass = "toast-top-full-width";
                    toastr.success(result.detail, "");
                    $window.location.reload();
                })
            };

            $scope.cancelBooking = function () {
                BookingsLoadService.cancelBooking($stateParams.uuid).$promise.then(function (result) {
                    toastr.options.positionClass = "toast-top-full-width";
                    toastr.success(result.detail, "");
                    $window.location.reload();
                })
            };

            $scope.declareIncident = function () {
                $scope.showIncidentForm = true;
            };

            // Method to post new comment
            $scope.postComment = function () {
                CommentsLoadService.postComment($stateParams.uuid, $scope.comment.text, $scope.comment.rate).$promise
                    .then(function () {
                        toastr.options.positionClass = "toast-top-full-width";
                        toastr.success("Posted comment", "");
                        $scope.showCommentForm = false;
                    });
            };

            // Method to post new incident
            $scope.postIncident = function () {
                BookingsLoadService.postIncident($stateParams.uuid, $scope.incident.description).$promise
                    .then(function (result) {
                        toastr.options.positionClass = "toast-top-full-width";
                        toastr.success(result.detail, "");
                        $scope.showIncidentForm = false;
                        $window.location.reload();
                    });
            };
        }
    ]);
});