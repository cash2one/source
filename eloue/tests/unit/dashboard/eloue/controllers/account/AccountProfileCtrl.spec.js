define(["angular-mocks", "eloue/controllers/account/AccountProfileCtrl"], function () {

    describe("Controller: AccountProfileCtrl", function () {

        var AccountProfileCtrl,
            scope,
            timeout,
            usersServiceMock,
            addressesServiceMock,
            phoneNumbersServiceMock,
            endpointsMock,
            civilityChoicesMock;

        beforeEach(module('EloueDashboardApp'));

        beforeEach(function () {
            usersServiceMock = {
                sendForm: function (userId, form, successCallback, errorCallback) {
                    console.log("usersServiceMock:sendForm called with userId = " + userId);
                },

                updateUser: function (user) {
                    console.log("usersServiceMock:updateUser");
                    return {$promise: {then: function () {
                        return {result: {}}
                    }}}
                },

                getMe: function () {
                    console.log("usersServiceMock:getMe called");
                    return {$promise: {then: function () {
                        return {result: {}}
                    }}}
                }
            };

            addressesServiceMock = {
                getAddressesByPatron: function (patronId) {
                    console.log("addressesServiceMock:getAddressesByPatron called with patronId = " + patronId);
                    return {then: function () {
                        return {response: {}}
                    }}
                },

                saveAddress: function (address) {
                    console.log("addressesServiceMock:saveAddress called");
                    return {$promise: {then: function () {
                        return {result: {}}
                    }}}
                }
            };

            phoneNumbersServiceMock = {
                savePhoneNumber: function (phoneNumber) {
                    console.log("phoneNumbersServiceMock:savePhoneNumber called");
                    return {$promise: {then: function () {
                        return {result: {}}
                    }}}
                },
                updatePhoneNumber: function (phoneNumber) {
                    console.log("phoneNumbersServiceMock:updatePhoneNumber called");
                    return {$promise: {then: function () {
                        return {result: {}}
                    }}}
                }
            };

            endpointsMock = {
                api_url: "/api/2.0/"
            };

            civilityChoicesMock = {

            };

            module(function ($provide) {
                $provide.value("UsersService", usersServiceMock);
                $provide.value("AddressesService", addressesServiceMock);
                $provide.value("PhoneNumbersService", phoneNumbersServiceMock);
                $provide.value("Endpoints", endpointsMock);
                $provide.value("CivilityChoices", civilityChoicesMock);
            })
        });

        beforeEach(inject(function ($rootScope, $timeout, $controller) {
            scope = $rootScope.$new();
            timeout = $timeout;
            scope.currentUserPromise = {
                then: function () {
                }
            };
            scope.currentUser = { id: 1};
            scope.markListItemAsSelected = function (prefix, id) {
            };
            spyOn(usersServiceMock, "sendForm").and.callThrough();
            spyOn(usersServiceMock, "updateUser").and.callThrough();
            spyOn(usersServiceMock, "getMe").and.callThrough();
            spyOn(addressesServiceMock, "getAddressesByPatron").and.callThrough();
            spyOn(addressesServiceMock, "saveAddress").and.callThrough();
            spyOn(phoneNumbersServiceMock, "savePhoneNumber").and.callThrough();
            spyOn(phoneNumbersServiceMock, "updatePhoneNumber").and.callThrough();

            AccountProfileCtrl = $controller('AccountProfileCtrl', {$scope: scope, $timeout: timeout,
                UsersService: usersServiceMock, AddressesService: addressesServiceMock,
                PhoneNumbersService: phoneNumbersServiceMock, Endpoints: endpointsMock,
                CivilityChoices: civilityChoicesMock});
        }));

        it("AccountProfileCtrl should be not null", function () {
            expect(!!AccountProfileCtrl).toBe(true);
        });

        it("AccountProfileCtrl:onFileChanged", function () {
            scope.onFileChanged();
            expect(usersServiceMock.sendForm).toHaveBeenCalled();
        });

        it("AccountProfileCtrl:dataFormSubmit", function () {
            scope.dataFormSubmit();
            expect(usersServiceMock.sendForm).toHaveBeenCalled();
        });
    });
});