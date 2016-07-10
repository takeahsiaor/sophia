var ContactPage = function () {

    return {

    	//Basic Map
        initMap: function () {
			var map;
			$(document).ready(function(){
			  map = new GMaps({
				div: '#map',
				scrollwheel: false,
				lat: 42.054434,
				lng: -87.988861
			  });

			  var marker = map.addMarker({
                lat: 42.054434,
                lng: -87.988861,
	            title: 'Our Location'
		       });
			});
        },

        //Panorama Map
        initPanorama: function () {
		    var panorama;
		    $(document).ready(function(){
		      panorama = GMaps.createPanorama({
		        el: '#panorama',
                lat: 42.054434,
                lng: -87.988861
		      });
		    });
		}

    };
}();
