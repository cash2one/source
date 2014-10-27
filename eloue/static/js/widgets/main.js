var STATIC_URL = "/static/";
var scripts = document.getElementsByTagName('script');
for(var i = 0, l = scripts.length; i < l; i++){
    if(scripts[i].getAttribute('data-static-path')){
        STATIC_URL = scripts[i].getAttribute('data-static-path');
        break;
    }
}
require.config({
    baseUrl: STATIC_URL + "js/widgets",
    paths: {
        "bootstrap": "../../bower_components/bootstrap/dist/js/bootstrap.min",
        "lodash": "../../bower_components/lodash/dist/lodash.min",
        "jQuery": "../../bower_components/jquery/dist/jquery.min",
        "jquery-ui": "../../bower_components/jqueryui/jquery-ui.min",
        "jshashtable": "../jshashtable-2.1_src",
        "jquery.numberformatter": "../jquery.numberformatter-1.2.3",
        "tmpl": "../tmpl",
        "jquery.dependClass": "../jquery.dependClass-0.1",
        "draggable": "../draggable-0.1",
        "slider": "../jquery.slider",
        "core": "../../bower_components/jqueryui/ui/minified/core.min",
        "mouse": "../../bower_components/jqueryui/ui/minified/mouse.min",
        "widget": "../../bower_components/jqueryui/ui/minified/widget.min",
        "angular": "../../bower_components/angular/angular.min",
        "angular-resource": "../../bower_components/angular-resource/angular-resource.min",
        "angular-route": "../../bower_components/angular-route/angular-route.min",
        "angular-cookies": "../../bower_components/angular-cookies/angular-cookies.min",
        "angular-sanitize": "../../bower_components/angular-sanitize/angular-sanitize.min",
        "moment": "../../bower_components/moment/min/moment.min",
        "angular-moment": "../../bower_components/angular-moment/angular-moment.min",
        "bootstrap-datepicker": "../../bower_components/bootstrap-datepicker/js/bootstrap-datepicker",
        "bootstrap-datepicker-fr": "../../bower_components/bootstrap-datepicker/js/locales/bootstrap-datepicker.fr",
        "jquery-form": "../../bower_components/jquery-form/jquery.form",
        "datejs": "../../bower_components/datejs/build/production/date.min",
        "chosen": "../../bower_components/chosen/chosen.jquery.min",
        "html5shiv": "../../bower_components/html5shiv/dist/html5shiv.min",
        "respond": "../../bower_components/respond/respond.min",
        "placeholders-utils": "../../bower_components/placeholders/lib/utils",
        "placeholders-main": "../../bower_components/placeholders/lib/main",
        "placeholders-jquery": "../../bower_components/placeholders/lib/adapters/placeholders.jquery",
        "custom-scrollbar": "../../bower_components/malihu-custom-scrollbar-plugin/jquery.mCustomScrollbar",
        "jquery-mousewheel": "../../bower_components/jquery-mousewheel/jquery.mousewheel",
        "toastr": "../../bower_components/toastr/toastr.min",
        "formmapper": "../formmapper"
    },
    shim: {
        "angular": {"exports": "angular"},
        "angular-route": ["angular"],
        "angular-cookies": ["angular"],
        "angular-sanitize": ["angular"],
        "angular-resource": ["angular"],
        "angular-moment": ["angular"],
        "angular-mocks": {
            deps: ["angular"],
            "exports": "angular.mock"
        },
        "jQuery": {exports: "jQuery"},
        "jquery-ui": ["jQuery"],
        "jshashtable": ["jQuery"],
        "jquery.numberformatter": ["jQuery"],
        "tmpl": ["jQuery"],
        "jquery.dependClass": ["jQuery"],
        "draggable": ["jQuery"],
        "slider": ["jQuery"],
        "core": ["jQuery"],
        "mouse": ["jQuery"],
        "widget": ["jQuery"],
        "bootstrap": ["jQuery"],
        "jquery-form": ["jQuery"],
        "moment": ["jQuery"],
        "bootstrap-datepicker": ["jQuery"],
        "bootstrap-datepicker-fr": ["jQuery", "bootstrap-datepicker"],
        "chosen": ["jQuery"],
        "placeholders-jquery": ["jQuery"],
        "formmapper": ["jQuery"],
        "jquery-mousewheel": ["jQuery"],
        "custom-scrollbar": ["jQuery", "jquery-mousewheel"],
        "toastr": ["jQuery"]
    }
});

require([
    "jQuery",
    "lodash",
    "angular",
    "bootstrap",
    "moment",
    "angular-moment",
    "datejs",
    "chosen",
    "html5shiv",
    "respond",
    "placeholders-utils",
    "placeholders-main",
    "placeholders-jquery",
    "formmapper",
    "toastr",
    "jquery-form",
//    "jquery-ui",
    "jshashtable",
    "jquery.numberformatter",
    "tmpl",
    "jquery.dependClass",
    "draggable",
    "slider",
    "core",
    "mouse",
    "widget",
    "bootstrap-datepicker",
    "bootstrap-datepicker-fr",
    "../common/eloue/commonApp",
    "eloue/route"
], function ($, _, angular) {
    "use strict";
    $(function () {

        angular.bootstrap(document, ["EloueApp"]);

        var slide_imgs = [].slice.call($('.carousel-wrapper').find('img'));
        for (var index = 0; index < slide_imgs.length; index++) {
            var proportions = $(slide_imgs[index]).width() / $(slide_imgs[index]).height(),
                parent = $(slide_imgs[index]).parent(),
                parent_proportions = $(parent).width() / $(parent).height();

            if (proportions < parent_proportions) {
                $(slide_imgs[index]).addClass('expand-v');
            } else {
                $(slide_imgs[index]).addClass('expand-h');
            }
        }

        var layout_switcher = $('.layout-switcher'), article = $('article');
        if (layout_switcher && article) {
            // switch grid/list layouts
            $(layout_switcher).on('click', 'i', function () {
                if ($(this).hasClass('grid')) {
                    article.removeClass('list-layout');
                    article.addClass('grid-layout')
                } else {
                    article.removeClass('grid-layout');
                    article.addClass('list-layout')

                }
            });
        }

        var categorySelection = $("#category-selection");
        var detailSearchForm = $("#detail-search");
        if (detailSearchForm && categorySelection) {
            categorySelection.change(function() {
                var location = $(this).find(":selected").attr("location");
                detailSearchForm.attr("action", location);
            });
        }
        var rangeSlider = $("#range-slider");
        var priceSlider = $("#price-slider");
        if (priceSlider) {
            var priceMinInput = $("#price-min"), priceMaxInput = $("#price-max");
            var min = priceSlider.attr("min-value");
            var max = priceSlider.attr("max-value");
            if (!min || !max) {
                priceSlider.hide();
                $("#price-label").hide();
            } else {
                priceSlider.slider({
                    from: Number(min),
                    to: Number(max),
                    limits: false,
                    dimension: '&nbsp;&euro;',
                    onstatechange: function( value ){
                        var values = value.split(";");
                        priceMinInput.attr("value", Number(values[0]));
                        priceMaxInput.attr("value", Number(values[1]));
                    }
                });
                priceSlider.slider("value", min, max);
            }

        }

        (function (d, s, id) {
            var js, fjs = d.getElementsByTagName(s)[0];
            if (d.getElementById(id)) return;
            js = d.createElement(s);
            js.id = id;
            js.src = "//connect.facebook.net/en_US/sdk.js#xfbml=1&version=v2.0";
            fjs.parentNode.insertBefore(js, fjs);
        }(document, 'script', 'facebook-jssdk'));

        window.___gcfg = {lang: 'fr'};
        (function () {
            var po = document.createElement('script');
            po.type = 'text/javascript';
            po.async = true;
            po.src = 'https://apis.google.com/js/platform.js';
            var s = document.getElementsByTagName('script')[0];
            s.parentNode.insertBefore(po, s);
        })();

        !function (d, s, id) {
            var js, fjs = d.getElementsByTagName(s)[0], p = /^http:/.test(d.location) ? 'http' : 'https';
            if (!d.getElementById(id)) {
                js = d.createElement(s);
                js.id = id;
                js.src = p + '://platform.twitter.com/widgets.js';
                fjs.parentNode.insertBefore(js, fjs);
            }
        }(document, 'script', 'twitter-wjs');

        // Insert YouTube video into defined container, add play on modal open and stop on modal hide
        var tag = document.createElement('script');

        tag.src = "https://www.youtube.com/iframe_api";
        var firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        var videoModal = $('#videoModal');
        var player;

        videoModal.on('shown.bs.modal', function () {
            player = new YT.Player('videoContainer', {
                height: '480',
                width: '640',
                videoId: 'nERu_2pSSb0',
                events: {
                    'onReady': onPlayerReady
                }
            });
        });
        videoModal.on('hidden.bs.modal', function () {
            player.destroy();
        });

        function onPlayerReady(event) {
            event.target.playVideo();
        }


        window.google_maps_loaded = function () {
            $('#geolocate').formmapper({
                details: "form"
            });

            var mapCanvas = document.getElementById("map-canvas");

            if (!!mapCanvas) {

                $('#where').formmapper({
                    details: "form"
                });

                $('#start-date').datepicker({
                    language: "fr",
                    autoclose: true,
                    todayHighlight: true,
                    startDate: Date.today()
                });

                $('#end-date').datepicker({
                    language: "fr",
                    autoclose: true,
                    todayHighlight: true,
                    startDate: Date.today()
                });

                var radius = Number($("#range").val().replace(',', '.'));
                var mapOptions = {
                    zoom: zoom(radius),
                    disableDefaultUI: true,
                    zoomControl: true,
                    mapTypeId: google.maps.MapTypeId.ROADMAP
                };
                var map = new google.maps.Map(mapCanvas, mapOptions);
                var geocoder = new google.maps.Geocoder();
                geocoder.geocode(
                    {address: document.getElementById("where").value},
                    function (result, status) {
                        if (status == google.maps.GeocoderStatus.OK) {
                            map.setCenter(result[0].geometry.location);
                            var circle = new google.maps.Circle({
                                map: map,
                                radius: radius * 1000,
                                fillColor: '#FFFFFF',
                                editable: false
                            });
                        }
                    }
                );

                if (rangeSlider) {
                    var rangeInput = $("#range");
                    rangeSlider.slider({
                        from: 1,
                        to: rangeSlider.attr("max-value"),
                        limits: false,
                        dimension: 'km',
                        onstatechange: function( value ){
                            var values = value.split(";");
                            rangeInput.attr("value", values[1]);
                            map.setZoom(zoom(values[1]));
                        }
                    });
                    rangeSlider.slider("value", 0, rangeInput.attr("value"));
                }

                var products = [];
                $('li[id^="marker-"]').each(function () {
                    var item = $(this);
                    var product = {
                        title: item.attr("name"),
                        lat: item.attr("locationX"),
                        lng: item.attr("locationY"),
                        zIndex: Number(item.attr("id").replace("marker-", ""))
                    };
                    products.push(product);
                });


                setMarkers(map, products, 'li#marker-');
            }

            var mapCanvasSmall = document.getElementById("map-canvas-small");

            if (!!mapCanvasSmall) {
                var mapContainer = $("#map-canvas-small");
                var product = {
                    lat: mapContainer.attr("locationX"),
                    lng: mapContainer.attr("locationY")
                };

                var productMapOptions = {
                    zoom: 16,
                    disableDefaultUI: true,
                    zoomControl: true,
                    center: new google.maps.LatLng(product.lat, product.lng),
                    mapTypeId: google.maps.MapTypeId.ROADMAP
                };
                var productMap = new google.maps.Map(mapCanvasSmall, productMapOptions);
                var circleOptions = {
                    strokeColor: "#3c763d",
                    strokeOpacity: 0.8,
                    strokeWeight: 2,
                    fillColor: "#3c763d",
                    fillOpacity: 0.35,
                    map: productMap,
                    center: new google.maps.LatLng(product.lat, product.lng),
                    radius: 100
                };
                var locationCircle = new google.maps.Circle(circleOptions);
            }
        };

        function load_google_maps() {
            var script = document.createElement("script");
            script.type = "text/javascript";
            script.src = "https://maps.googleapis.com/maps/api/js?sensor=false&libraries=places&language=fr&callback=google_maps_loaded";
            document.body.appendChild(script);
        }

        function zoom(radius) {
            if (radius <= 0.5)
                return 14;
            if (radius <= 1)
                return 13;
            if (radius <= 3)
                return 12;
            if (radius <= 6)
                return 11;
            if (radius <= 15)
                return 10;
            if (radius <= 25)
                return 9;
            if (radius <= 100)
                return 7;
            if (radius <= 200)
                return 6;
            if (radius <= 300)
                return 5;
            if (radius <= 700)
                return 4;
            return 3;
        }

        function setMarkers(map, locations, markerId) {
            for (var i = 0; i < locations.length; i++) {
                var product = locations[i];

                var image, image_hover;

                if (markerId == "li#marker-") {
                    image = new google.maps.MarkerImage(STATIC_URL + 'images/markers_smooth_aligned.png',
                        new google.maps.Size(26, 28),
                        new google.maps.Point(0, 28 * i),
                        new google.maps.Point(14, 28));

                    image_hover = new google.maps.MarkerImage(STATIC_URL + 'images/markers_smooth_aligned.png',
                        new google.maps.Size(26, 28),
                        new google.maps.Point(29, 28 * i),
                        new google.maps.Point(14, 28));
                }

                var myLatLng = new google.maps.LatLng(product.lat, product.lng);

                var marker = new google.maps.Marker({
                    position: myLatLng,
                    map: map,
                    title: product.title,
                    zIndex: product.zIndex,
                    icon: image
                });

                marker.set("myZIndex", marker.getZIndex());

                google.maps.event.addListener(marker, "mouseover", mouseOverListenerGenerator(image_hover, marker, markerId));
                google.maps.event.addListener(marker, "click", mouseClickListenerGenerator(marker, markerId));
                google.maps.event.addListener(marker, "mouseout", mouseOutListenerGenerator(image, marker, markerId));

                $(markerId + marker.get("myZIndex")).mouseover(triggerMouseOverGenerator(marker));

                $(markerId + marker.get("myZIndex")).mouseout(triggerMouseOutGenerator(marker));
            }
        }

        function mouseClickListenerGenerator(marker, markerId) {
            return function () {
                // Jump to product item
                $('html, body').animate({
                    scrollTop: $(markerId + marker.get("myZIndex")).offset().top - 20
                }, 1000);
            }
        }

        function mouseOverListenerGenerator(image_hover, marker, markerId) {
            return function () {
                this.setOptions({
                    icon: image_hover,
                    zIndex: 200
                });

                //TODO: toggle ":hover" styles
//                $(markerId + marker.get("myZIndex")).find(".declarer-container")[0].trigger("hover");
            }
        }

        function mouseOutListenerGenerator(image, marker, markerId) {
            return function () {
                this.setOptions({
                    icon: image,
                    zIndex: this.get("myZIndex")
                });
                $(markerId + marker.get("myZIndex")).removeAttr("style");
            }
        }

        function triggerMouseOverGenerator(marker) {
            return function () {
                marker.setAnimation(google.maps.Animation.BOUNCE);
                google.maps.event.trigger(marker, 'mouseover');
            }
        }

        function triggerMouseOutGenerator(marker) {
            return function () {
                marker.setAnimation(null);
                google.maps.event.trigger(marker, 'mouseout');
            }
        }

        load_google_maps();
    });
});
