define(["angular-mocks", "eloue/services/CategoriesService"], function () {

    describe("Service: CategoriesService", function () {

        var CategoriesService,
            q,
            categoriesMock,
            utilsServiceMock,
            simpleResourceResponse = {
                $promise: {
                    then: function () {
                        return {results: []};
                    }
                }
            };

        beforeEach(module("EloueCommon"));

        beforeEach(function () {
            categoriesMock = {
                get: function () {
                    return simpleResourceResponse;
                },
                getChildren: function () {
                    return simpleResourceResponse;
                },
                getAncestors: function () {
                    return simpleResourceResponse;
                }
            };
            utilsServiceMock = {
                getIdFromUrl: function (url) {
                    var trimmedUrl = url.slice(0, url.length - 1);
                    return trimmedUrl.substring(trimmedUrl.lastIndexOf("/") + 1, url.length);
                }
            };
            module(function ($provide) {
                $provide.value("Categories", categoriesMock);
                $provide.value("UtilsService", utilsServiceMock);
            });
        });

        beforeEach(inject(function (_CategoriesService_, $q) {
            CategoriesService = _CategoriesService_;
            q = $q;
            spyOn(categoriesMock, "get").and.callThrough();
            spyOn(categoriesMock, "getChildren").and.callThrough();
            spyOn(categoriesMock, "getAncestors").and.callThrough();
            spyOn(utilsServiceMock, "getIdFromUrl").and.callThrough();
        }));

        it("CategoriesService should be not null", function () {
            expect(!!CategoriesService).toBe(true);
        });

        it("CategoriesService:getCategory", function () {
            var categoryId = 1;
            CategoriesService.getCategory(categoryId);
            expect(categoriesMock.get).toHaveBeenCalledWith({id: categoryId, _cache: jasmine.any(Number)});
        });

        it("CategoriesService:getParentCategory", function () {
            var parentId = "1", category = {parent: "http://10.0.5.47:8200/api/2.0/categories/" + parentId + "/"};
            CategoriesService.getParentCategory(category);
            expect(utilsServiceMock.getIdFromUrl).toHaveBeenCalledWith(category.parent);
            expect(categoriesMock.get).toHaveBeenCalledWith({id: parentId, _cache: jasmine.any(Number) });
        });

        it("CategoriesService:getRootCategories", function () {
            CategoriesService.getRootCategories();
            expect(categoriesMock.get).toHaveBeenCalledWith({parent__isnull: true});
        });

        it("CategoriesService:getChildCategories", function () {
            var parentId = 1;
            CategoriesService.getChildCategories(parentId);
            expect(categoriesMock.getChildren).toHaveBeenCalledWith({id: parentId});
        });

        it("CategoriesService:getAncestors", function () {
            var parentId = 1;
            CategoriesService.getAncestors(parentId);
            expect(categoriesMock.getAncestors).toHaveBeenCalledWith({id: parentId});
        });
    });
});