require.config({
	paths: {
        jquery: "jquery-1.8.3.min"
	}
});
define(function (require, exports, module){
	var util = require('./util');
	util.log('Hello, world!');

	var util2 = require('./util2');
	util2.log('Holy shit!');

	// var $ = require('jquery');
	// $('html,body').css('background-color', 'silver');
	require('./merge.min');
	require('./merge2.min');
});
