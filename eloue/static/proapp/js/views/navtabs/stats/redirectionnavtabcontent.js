// js/views/navtabs/stats/redirectionnavtabcontent.js

var app = app || {};


app.RedirectionNavTabContentView = app.NavTabContentView.extend({

	initialize: function() {
		if (this.options.titleName) this.titleName = this.options.titleName;
		this.loadingView = new app.LoadingView();
		//this.chartView = new app.ChartsView();
	},

	setTimeSeriesView: function(timeSeries) {
		this.timeSeries = timeSeries;
		this.timeSeriesView = new app.TimeSeriesView();
		this.timeSeriesView.on('timeseriesform:submited', this.fetchModel, this);

		this.model = new app.RedirectionEventModel();
		this.model.on('request', this.renderLoading, this);
		this.model.on('sync', this.render, this);
		this.fetchModel();
	},

	fetchModel: function() {
		var self = this;
		var params;

		if(this.timeSeriesView.serializeForm()) {
			params = this.timeSeriesView.serializeForm();
		} else if (this.timeSeries) {
			params = $.param(this.timeSeries);
		} else {
			params = null;
		}

		this.model.fetch({data: params})
			.success(function () {
				self.timeSeries = self._getTimeSeries();
				self.trigger('timeSeries:change');
			});
		delete params;
		delete self;
	},

	render: function() {
		this.$el.html("<h3>" + this.titleName + "</h3>");

		if (this.timeSeriesView) {
			this.$el.children("h3").append(this.timeSeriesView.$el);
			this.timeSeriesView.render(this._getTimeSeries());
		}

		//this.$el.append(this.chartView.$el);
		//this.chartView.render();

		return this;
	},

	renderLoading: function() {
		this.$el.html(this.loadingView.$el);
		this.loadingView.render();
	},

	_getTimeSeries: function() {
		return {
			start_date: String(this.model.get('start_date')), 
			end_date: String(this.model.get('end_date')), 
			interval: String(this.model.get('interval'))
		};
	},

	onClose: function() {
		this.timeSeriesView.close();
		this.loadingView.close();
		this.model.unbind();
		delete this.model;
	}
});