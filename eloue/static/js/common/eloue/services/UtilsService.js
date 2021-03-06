define(["../../../common/eloue/commonApp", "../../../common/eloue/services/AuthService"], function (EloueCommon) {
    "use strict";
    /**
     * Utils service.
     */
    EloueCommon.factory("UtilsService", ["$filter", "AuthService", "$document", '$translate', 'moment', 'MAP_CONFIG', 'CivilityChoices', function ($filter, AuthService, $document, $translate, moment ,MAP_CONFIG, CivilityChoices) {
        var utilsService = {};
                
        
        utilsService.date = moment;
                
        utilsService.locale = function(){
            return $document[0].documentElement.lang;      
        };
        
        utilsService.country = function(){
            return MAP_CONFIG[utilsService.locale()];
        };
        
        utilsService.choicesHonorific = function(){
            return CivilityChoices[utilsService.locale()];
        };
        
        utilsService.choicesHours = function(){
            var choices = [];
            for (var i=0; i<24; i++){
                var time = moment({hour:i});
                choices.push({
                    label:time.format("LT"),
                    value:time.format("HH:mm:ss")
                });
            }  
            return choices;
        };
                  
        utilsService.dateInternal = function(dateStr){
            return moment(dateStr, "L").format('DD/MM/YYYY');
        };
        
        utilsService.dateRepr = function(dateStr){
            return moment(dateStr, 'DD/MM/YYYY').format("L");
        };
        
        utilsService.formatDate = function (date, format) {
            return $filter("date")(date, format);
        };
        

        /**
         * Translates message using provided key.
         * @param msgKey message key for eloue/static/js/common/eloue/i18n.js
         * @returns Translation
         */
        utilsService.translate = function (msgKey, params, ip) {
            return $filter("translate")(msgKey, params, ip);
        };

        utilsService.formatMessageDate = function (dateString, shortFormat, fullFormat) {
            var sentDate = new Date(dateString), nowDate = new Date(), dateFormat;
            // If date is today
            if (sentDate.setHours(0, 0, 0, 0) === nowDate.setHours(0, 0, 0, 0)) {
                dateFormat = shortFormat;
            } else {
                dateFormat = fullFormat;
            }
            return this.formatDate(sentDate, dateFormat);
        };

        utilsService.getIdFromUrl = function (url) {
            var trimmedUrl = url.slice(0, url.length - 1);
            return trimmedUrl.substring(trimmedUrl.lastIndexOf("/") + 1, url.length);
        };

        utilsService.calculatePeriodBetweenDates = function (startDateString, endDateString) {
            var hourTime = 60 * 60 * 1000,
                dayTime = 24 * hourTime,
                startTime = Date.parse(startDateString).getTime(),
                endTime = Date.parse(endDateString).getTime(),
                diffTime = endTime - startTime,
                periodDays = Math.floor(diffTime / dayTime),
                periodHours = Math.floor((diffTime - dayTime * periodDays) / hourTime);
            return {
                period_days: periodDays,
                period_hours: periodHours
            };
        };

        utilsService.isToday = function (dateStr) {
            var date = Date.parse(dateStr), today = new Date();
            return !!date && date.getDate() === today.getDate() && date.getMonth() === today.getMonth() && date.getFullYear() === today.getFullYear();
        };

        utilsService.downloadPdfFile = function (url, filename) {
            var xhr = new XMLHttpRequest(),
                userToken = AuthService.getUserToken(),
                csrftoken = AuthService.getCSRFToken();
            xhr.open("GET", url, true);
            if (userToken && userToken.length > 0) {
                xhr.setRequestHeader("Authorization", "Bearer " + userToken);
            }
            if (csrftoken && csrftoken.length > 0) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
            xhr.responseType = "blob";

            xhr.onload = function (e) {
                if (this.status === 200) {
                    var file = new Blob([this.response], {type: "application/pdf"});
                    saveAs(file, filename);
                }
            };

            xhr.send();
        };

        /**
         * Set valid sender for messages.
         * @param messages messages to modify.
         * @param replacer in case of sender is not current user, sender filed will be replaced with this object.
         * @param currentUser current user.
         */
        utilsService.updateMessagesSender = function(messages, replacer, currentUser) {
            // Replace sender as url with real object for all messages.
            for (var i = 0; i < messages.length; i++) {
                if (angular.isObject(messages[i].sender)) {
                    continue;
                }
                var senderId = utilsService.getIdFromUrl(messages[i].sender);

                if (senderId == replacer.id) {
                    messages[i].sender = replacer;
                } else {
                    messages[i].sender = currentUser;
                }
            }
        };

        /**
         * Get unread messages ids.
         * @param messages messages to check.
         * @param currentUser current user to prevent selecting outcoming messages.
         * @returns {Array} array of unread messages ids.
         */
        utilsService.getUnreadMessagesIds = function(messages, currentUser) {
            var unreadMessagesIds = [];
            for (var i = 0; i < messages.length; i++) {
                if (messages[i].read_at == null && (messages[i].sender.id != currentUser.id || messages[i].sender.id == utilsService.getIdFromUrl(messages[i].recipient))) {
                    unreadMessagesIds.push(messages[i].id);
                }
            }
            return unreadMessagesIds;
        };

        // The method to initiate custom scrollbars
        utilsService.initCustomScrollbars = function(scrollbarSelector) {

                // custom scrollbar
                $(".chosen-drop").mCustomScrollbar({
                    scrollInertia: "100",
                    autoHideScrollbar: true,
                    theme: "dark-thin",
                    scrollbarPosition: "outside",
                    advanced: {
                        autoScrollOnFocus: false,
                        updateOnContentResize: true
                    }
                });
                $(scrollbarSelector ? scrollbarSelector : ".scrollbar-custom").mCustomScrollbar({
                    scrollInertia: "100",
                    autoHideScrollbar: true,
                    theme: "dark-thin",
                    advanced: {
                        updateOnContentResize: true,
                        autoScrollOnFocus: false
                    }
                });
                $(".textarea-wrapper").mCustomScrollbar({
                    scrollInertia: "100",
                    autoHideScrollbar: true,
                    theme: "dark-thin",
                    mouseWheel: {
                        updateOnContentResize: true,
                        disableOver: false
                    }
                });
            };

        utilsService.getQueryParams = function () {
            var query_string = [];
            var query = decodeURIComponent(window.location.search.substring(1));
            var vars = query.split("&");
            for (var i = 0; i < vars.length; i++) {
                var pair = vars[i].split("=");
                // If first entry with this name
                if (typeof query_string[pair[0]] === "undefined") {
                    query_string[pair[0]] = pair[1];
                    // If second entry with this name
                } else if (typeof query_string[pair[0]] === "string") {
                    query_string[pair[0]] = [query_string[pair[0]], pair[1]];
                    // If third or later entry with this name
                } else {
                    query_string[pair[0]].push(pair[1]);
                }
            }
            return query_string;
        };
        
        utilsService.range = function (zoom) {
            if (zoom >= 14) {
                return 0.5;
            }
            if (zoom >= 13) {
                return 1;
            }
            if (zoom >= 12) {
                return 3;
            }
            if (zoom >= 11) {
                return 6;
            }
            if (zoom >= 10) {
                return 15;
            }
            if (zoom >= 9) {
                return 25;
            }
            if (zoom >= 8) {
                return 100;
            }
            if (zoom >= 7) {
                return 200;
            }
            if (zoom >= 6) {
                return 350;
            }
            if (zoom >= 5) {
                return 500;
            }
            if (zoom >= 4) {
                return 700;
            }
            return 1000;
        };

        utilsService.zoom = function (radius) {
            if (radius <= 0.5) {
                return 14;
            }
            if (radius <= 1) {
                return 13;
            }
            if (radius <= 3) {
                return 12;
            }
            if (radius <= 6) {
                return 11;
            }
            if (radius <= 15) {
                return 10;
            }
            if (radius <= 25) {
                return 9;
            }
            if (radius <= 100) {
                return 8;
            }
            if (radius <= 200) {
                return 7;
            }
            if (radius <= 350) {
                return 6;
            }
            if (radius <= 500) {
                return 5;
            }
            if (radius <= 700) {
                return 4;
            }
            return 3;
        };
        
        utilsService.urlEncodeObject = function(obj) {
            var params = [];
            for(var p in obj)
            	params.push(encodeURIComponent(p) + 
            			"=" + encodeURIComponent(obj[p]));
            return params.join("&");
        };

        // https://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript
        utilsService.getParameterByName = function(name) {
            name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
            var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
                results = regex.exec(location.search);
            return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
        };
        
        return utilsService;
    }]);
});
