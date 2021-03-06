define(["angular-mocks", "eloue/controllers/account/AccountAddressDetailCtrl"], function () {

    describe("Controller: AccountAddressDetailCtrl", function () {

        var AccountAddressDetailCtrl,
            scope,
            state,
            stateParams,
            endpointsMock,
            addressesServiceMock,
            productsServiceMock,
            usersServiceMock,
            utilsServiceMock,
            simpleServiceResponse = {
                then: function () {
                    return {result: {}};
                }
            };

        beforeEach(module('EloueDashboardApp'));

        beforeEach(function () {

            endpointsMock = {
                api_url: "/api/2.0/"
            };

            addressesServiceMock = {
                getAddress: function (addressId) {
                    console.log("addressesServiceMock:getAddress called with addressId = " + addressId);
                    return simpleServiceResponse;
                },
                updateAddress: function (addressId, formData) {
                    console.log("addressesServiceMock:updateAddress called with addressId = " + addressId + ", formData = " + formData);
                    return simpleServiceResponse;
                },
                deleteAddress: function (addressId) {
                    console.log("addressesServiceMock:deleteAddress called with addressId = " + addressId);
                    return simpleServiceResponse;
                }
            };
            productsServiceMock = {
                getProductsByAddress: function (addressId) {
                    console.log("productsServiceMock:getProductsByAddress called with addressId = " + addressId);
                    return simpleServiceResponse;
                }
            };

            usersServiceMock = {
                updateUser: function (user) {
                    console.log("usersServiceMock:updateUser");
                    return simpleServiceResponse;
                }
            };

            utilsServiceMock = {
                translate: function(msg) {

                }
            };

            module(function ($provide) {
                $provide.value("AddressesService", addressesServiceMock);
                $provide.value("ProductsService", productsServiceMock);
                $provide.value("UsersService", usersServiceMock);
                $provide.value("UtilsService", utilsServiceMock);
            });
        });

        beforeEach(inject(function ($rootScope, $controller) {
            scope = $rootScope.$new();
            scope.showNotification = function(object, action, bool){};
            state = {};
            stateParams = {
                id: 1
            };
            spyOn(addressesServiceMock, "getAddress").and.callThrough();
            spyOn(addressesServiceMock, "updateAddress").and.callThrough();
            spyOn(addressesServiceMock, "deleteAddress").and.callThrough();
            spyOn(productsServiceMock, "getProductsByAddress").and.callThrough();
            spyOn(usersServiceMock, "updateUser").and.callThrough();
            spyOn(utilsServiceMock, "translate").and.callThrough();

            AccountAddressDetailCtrl = $controller('AccountAddressDetailCtrl', { $scope: scope, $state: state, $stateParams: stateParams, Endpoints: endpointsMock, AddressesService: addressesServiceMock, ProductsService: productsServiceMock, UsersService: usersServiceMock });
        }));

        it("AccountAddressDetailCtrl should be not null", function () {
            expect(!!AccountAddressDetailCtrl).toBe(true);
        });

        it("AccountAddressDetailCtrl:submitAddress", function () {
            scope.submitAddress();
            expect(addressesServiceMock.updateAddress).toHaveBeenCalled();
        });

        it("AccountAddressDetailCtrl:finaliseAddressUpdate", function () {
            scope.showNotification = function(notification){};
            scope.showNotificationMessage = function(notification, succeed){};
            state.transitionTo = function(current, stateParams, opts) {};
            scope.finaliseAddressUpdate();
        });

        it("AccountAddressDetailCtrl:deleteAddress", function () {
            scope.deleteAddress();
            expect(addressesServiceMock.deleteAddress).toHaveBeenCalled();
        });

        it("AccountAddressDetailCtrl:processAddressUpdateResponse", function () {
            scope.processAddressUpdateResponse();
        });
    });
});