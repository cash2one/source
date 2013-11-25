// js/views/ads/adspillcontent.js

var app = app || {};

app.AdsPillContentView = app.ListView.extend({
	id:'content-ads',

	className: 'content-pill clearfix',

	item: app.NavTabItemView.extend({
		template: _.template($("#navpillsitem-template").html()),

		path: 'ads/', 

		icon: 'show_thumbnails_with_lines', 

		labelName: 'Annonces'
	}),

	listItemsView: app.ListItemsView.extend({ collection: app.ProductsCollection }),

	detailView: app.AdsDetailsView,

	initialize: function() {
		this.constructor.__super__.initialize.apply(this, [this.options]);
		
	}
});