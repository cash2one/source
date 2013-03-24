// js/routers/routes.js

var app = app || {}


var Workspace = Backbone.Router.extend({
	routes: {
		'': 				'home',
		'stats/': 			'stats',
		'stats/:metric/': 	'stats',
		'messages/': 		'messages',
		'ads/': 			'ads',
		'settings/':		'settings',
	},

	initialize: function() {
		app.layoutView = new app.LayoutView();
	},

	home: function() {
		app.layoutView.navPillsView.navPillsItemViews[0].setSelectedPillItem();
		var homeNavPillContentView = new app.NavPillContentView();
		homeNavPillContentView.id = 'accueil';
		app.layoutView.setCurrentNavPillContent(homeNavPillContentView);
		app.layoutView.renderNavPillContent();
	},

	stats: function(metric) {
		app.layoutView.navPillsView.navPillsItemViews[1].setSelectedPillItem();
		
		if (app.layoutView.currentNavPillContent instanceof app.StatsNavPillContentView) {
			var statsNavPillContentView = app.layoutView.currentNavPillContent;
		} else {
			var statsNavPillContentView = new app.StatsNavPillContentView();
			app.layoutView.setCurrentNavPillContent(statsNavPillContentView);
			app.layoutView.renderNavPillContent();
		}

		if (metric == undefined) {
			var navTabContentView = new app.NavTabContentView({titleName: 'Vue d\'ensemble'});
			statsNavPillContentView.navTabsView.navTabsItemViews[0].setSelectedTabItem();
		} else if (metric == 'redirection') {
			var navTabContentView = new app.RedirectionNavTabContentView({titleName: 'Redirections'});
			statsNavPillContentView.navTabsView.navTabsItemViews[3].setSelectedTabItem();
		} else if (metric == 'traffic') {
			var navTabContentView = new app.NavTabContentView({titleName: 'Visites'});
			statsNavPillContentView.navTabsView.navTabsItemViews[1].setSelectedTabItem();
		} else if (metric == 'phone') {
			var navTabContentView = new app.NavTabContentView({titleName: 'Appels'});
			statsNavPillContentView.navTabsView.navTabsItemViews[2].setSelectedTabItem();
		}

		statsNavPillContentView.setCurrentNavTabContentView(navTabContentView);
		statsNavPillContentView.renderNavTabContent();
	},

	messages: function() {
		app.layoutView.navPillsView.navPillsItemViews[2].setSelectedPillItem();
		var messagesNavPillContentView = new app.NavPillContentView();
		messagesNavPillContentView.id = 'messages';
		app.layoutView.setCurrentNavPillContent(messagesNavPillContentView);
		app.layoutView.renderNavPillContent();
	},

	ads: function() {
		app.layoutView.navPillsView.navPillsItemViews[3].setSelectedPillItem();
		var adsNavPillContentView = new app.NavPillContentView();
		adsNavPillContentView.id = 'ads';
		app.layoutView.setCurrentNavPillContent(adsNavPillContentView);
		app.layoutView.renderNavPillContent();
	},

	settings: function() {
		app.layoutView.navPillsView.navPillsItemViews[4].setSelectedPillItem();
		var settingsNavPillContentView = new app.NavPillContentView();
		settingsNavPillContentView.id = 'settings';
		app.layoutView.setCurrentNavPillContent(settingsNavPillContentView);
		app.layoutView.renderNavPillContent();
	}
});