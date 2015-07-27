/*global define*/
define(
	function()
	{
		var signals;
		var export_button;
		var default_file_name;
		var file_name;
		var download_file_name;
		var file_suffix = '.png';
		var file_suffix_regex = /(\.)(jpg|jpeg|png|gif|bmp)/ig;
		var parameters;

		function init( shared )
		{
			signals = shared.signals;
			imgdata_input = document.getElementById('postdatimgdata');
			info_display = document.getElementById('infodisplay');
			export_button = document.getElementById( 'export-button' );
			file_name = default_file_name;
			download_file_name = default_file_name;

			export_button.addEventListener( 'click', exportButtonClicked, false );

			signals['load-file'].add( updateFileName );
			signals['load-file'].add( updateDownloadFileName );
			signals['control-updated'].add( updateParameters );
			signals['control-updated'].add( updateDownloadFileName );
		}

		function exportButtonClicked( event )
		{
			signals['image-data-url-requested'].dispatch( updatePNGLinkAddress );
		}

		function updateFileName( file )
		{
			if (
				file &&
				typeof file.name === 'string'
			)
			{
				file_name = file.name.replace( file_suffix_regex, '' );
			}
		}

		function updateParameters( new_parameters )
		{
			parameters = new_parameters || parameters;
		}

		function updateDownloadFileName()
		{
			download_file_name = file_name + '-glitched-' + objToString( parameters ) + file_suffix;
		}

		function updatePNGLinkAddress( data_url )
		{
			new_data_url = data_url.split(',')[1];
			info_display.innerHTML = new_data_url.slice(0, 48); 
			imgdata_input.value = encodeURIComponent(new_data_url);
		}

		function objToString( obj )
		{
			var result = [ ];

			for ( var key in obj )
			{
				result.push( key[0] + '' + obj[key] );
			}

			return result.join( '-' );
		}

		return { init: init };
	}
);