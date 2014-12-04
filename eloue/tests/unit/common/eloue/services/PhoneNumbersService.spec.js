define(["angular-mocks", "eloue/commonApp", "eloue/services"], function () {

    describe("Service: PhoneNumbersService", function () {

        var PhoneNumbersService,
            phoneNumbersMock;

        beforeEach(module("EloueCommon"));

        beforeEach(function () {
            phoneNumbersMock = {
                get: function () {
                },
                update: function () {
                }
            };

            module(function ($provide) {
                $provide.value("PhoneNumbers", phoneNumbersMock);
            });
        });

        beforeEach(inject(function (_PhoneNumbersService_) {
            PhoneNumbersService = _PhoneNumbersService_;
            spyOn(phoneNumbersMock, "get").and.callThrough();
            spyOn(phoneNumbersMock, "update").and.callThrough();
        }));

        it("PhoneNumbersService should be not null", function () {
            expect(!!PhoneNumbersService).toBe(true);
        });

        it("PhoneNumbersService:updatePhoneNumber", function () {
            var phoneNumbersId = 1;
            PhoneNumbersService.updatePhoneNumber({id: phoneNumbersId});
            expect(phoneNumbersMock.update).toHaveBeenCalledWith({id: phoneNumbersId}, {id: phoneNumbersId});
        });
    });
});