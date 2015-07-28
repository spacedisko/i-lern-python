/*global define*/
define(
	function()
	{
		var signals;
		var image;
		var initialized = false;
		var defaultimage = document.body.getAttribute( 'data-defaultimage' );

		function init( shared )
		{
			signals = shared.signals;
			image = new Image();

			signals['set-new-src'].add( setSrc );

			image.addEventListener( 'load', imageLoaded, false );
			setSrc( defaultimage );
		}

		function imageLoaded()
		{
			signals['image-loaded'].dispatch( image );

			initialized = true;
		}

		function setSrc( src )
		{
			image.src = src;

			if (
				initialized &&
				image.naturalWidth !== undefined &&
				image.naturalWidth !== 0
			)
			{
				setTimeout( imageLoaded, 10 );
			}
		}

		return { init: init };
	}
);