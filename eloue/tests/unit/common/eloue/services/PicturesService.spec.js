define(["angular-mocks", "eloue/commonApp", "eloue/services"], function () {

    describe("Service: PicturesService", function () {

        var PicturesService,
            picturesMock,
            endpointsMock,
            formServiceMock;

        beforeEach(module("EloueCommon"));

        beforeEach(function () {
            picturesMock = {
                get: function () {
                }
            };
            endpointsMock = {

            };
            formServiceMock = {
                send: function (method, url, form, successCallback, errorCallback) {
                }
            };

            module(function ($provide) {
                $provide.value("Pictures", picturesMock);
                $provide.value("Endpoints", endpointsMock);
                $provide.value("FormService", formServiceMock);
            });
        });

        beforeEach(inject(function (_PicturesService_) {
            PicturesService = _PicturesService_;
            spyOn(picturesMock, "get").and.callThrough();
            spyOn(formServiceMock, "send").and.callThrough();
        }));

        it("PicturesService should be not null", function () {
            expect(!!PicturesService).toBe(true);
        });

        it("PicturesService:savePicture", function () {
            var productId = 1;
            PicturesService.savePicture(productId, {}, undefined, undefined);
            expect(formServiceMock.send).toHaveBeenCalled();
        });
    });
});