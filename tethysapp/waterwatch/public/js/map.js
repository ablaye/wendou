/*****************************************************************************
 * FILE:    MAP JS
 * DATE:    29 September 2017
 * AUTHOR: Sarva Pulla
 * COPYRIGHT: (c) SERVIR GLOBAL 2017
 * LICENSE: BSD 2-Clause
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/
var LIBRARY_OBJECT = (function() {
    // Wrap the library in a package function
    "use strict"; // And enable strict mode for this library
    /************************************************************************
     *                      MODULE LEVEL / GLOBAL VARIABLES
     *************************************************************************/
    var base_map2,
		baseLayer,
        current_layer,
        layers,
        map,
        ponds_mapid,
        ponds_token,
        region_mapid,
        region_token,
        commune_mapid,
        commune_token,
        arrondissement_mapid,
        arrondissement_token,
        mndwi_mapid,
        mndwi_token,
        public_interface,				// Object returned by the module
        select_feature_source,
        select_feature_layer,
        $chartModal,
        water_source,
        water_layer,
        true_source,
        projectionSelect,
        precisionInput,
		mousePositionControl,
		true_layer;
    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/
    var generate_chart,
		generate_details,
        generate_forecast,
        init_all,
        init_events,
        init_vars,
        init_map;
    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/
    init_vars = function(){
        var $layers_element = $('#layers');
        ponds_mapid = $layers_element.attr('data-ponds-mapid');
        ponds_token = $layers_element.attr('data-ponds-token');
        region_mapid = $layers_element.attr('data-region-mapid');
        region_token = $layers_element.attr('data-region-token');
        commune_mapid = $layers_element.attr('data-commune-mapid');
        commune_token = $layers_element.attr('data-commune-token');
        arrondissement_mapid = $layers_element.attr('data-arrondissement-mapid');
        arrondissement_token = $layers_element.attr('data-arrondissement-token');
        mndwi_mapid = $layers_element.attr('data-mndwi-mapid');
        mndwi_token = $layers_element.attr('data-mndwi-token');
        $chartModal = $("#chart-modal");
    };
    init_map = function(){
        var attribution = new ol.Attribution({
            html: 'Tiles © <a href="https://services.arcgisonline.com/ArcGIS/rest/services/">ArcGIS</a>'
        });
        var base_map = new ol.layer.Tile({
            crossOrigin: 'anonymous',
            source: new ol.source.XYZ({
                attributions: [attribution],
                url: 'https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/' +
                'World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}'
            }),
            visible: true,
            name:'base_map'
        });
        base_map2 = new ol.layer.Tile({
            source: new ol.source.BingMaps({
                key: '5TC0yID7CYaqv3nVQLKe~xWVt4aXWMJq2Ed72cO4xsA~ApdeyQwHyH_btMjQS1NJ7OHKY8BK-W-EMQMrIavoQUMYXeZIQOUURnKGBOC7UCt4',
                imagerySet: 'AerialWithLabels' // Options 'Aerial', 'AerialWithLabels', 'Road'
            }),
            visible: false,
            name:'base_map2'            
        });

        var west_africa = new ol.Feature(new ol.geom.Polygon([[[-1600000,1580000],[-1370000,1580000],[-1370000,1860000],[-1800000,1860000],[-1800000,1580000]]]));

        var boundary_layer = new ol.layer.Vector({
            title:'Boundary Layer',
            source: new ol.source.Vector(),
            style: new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: "red",
                    width: 1
                })
            }),
            visible: true,
            name:'boundary_layer'                     
        });

        var defaultStyles = [
		   new ol.style.Style({
				fill: new ol.style.Fill({
					color: 'white'
				}),
				stroke: new ol.style.Stroke({color: 'black', width: 2})
		   })
		];
        boundary_layer.getSource().addFeatures([west_africa]);

         var mndwi_layer = new ol.layer.Tile({
            source: new ol.source.XYZ({
                url: "https://earthengine.googleapis.com/map/"+mndwi_mapid+"/{z}/{x}/{y}?token="+mndwi_token
            }),
            visible: true,
            name:'mndwi_layer'
        });

         var ponds_layer = new ol.layer.Tile({
            source: new ol.source.XYZ({
                url: "https://earthengine.googleapis.com/map/"+ponds_mapid+"/{z}/{x}/{y}?token="+ponds_token
            }),
            visible: true,
            name:'ponds_layer'
        });
         var region_layer = new ol.layer.Tile({
            source: new ol.source.XYZ({
                url: "https://earthengine.googleapis.com/map/"+region_mapid+"/{z}/{x}/{y}?token="+region_token
            }),
            style: defaultStyles,
            visible: false,
            name:'region_layer'
        });
         var commune_layer = new ol.layer.Tile({
            source: new ol.source.XYZ({
                url: "https://earthengine.googleapis.com/map/"+commune_mapid+"/{z}/{x}/{y}?token="+commune_token
            }),
            style: defaultStyles,
            visible: false,
            name:'commune_layer'
        });
         var arrondissement_layer = new ol.layer.Tile({
            source: new ol.source.XYZ({
                url: "https://earthengine.googleapis.com/map/"+arrondissement_mapid+"/{z}/{x}/{y}?token="+arrondissement_token
            }),
            style: defaultStyles,
            visible: false,
            name:'arrondissement_layer'
        });
        select_feature_source = new ol.source.Vector();
        select_feature_layer = new ol.layer.Vector({
            source: select_feature_source,
            style: new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: "black",
                    width: 8
                })
            })
        });

        water_source = new ol.source.XYZ();
        water_layer = new ol.layer.Tile({
            source: water_source
            // url:""
        });

        true_source = new ol.source.XYZ();
        true_layer = new ol.layer.Tile({
            source: true_source
            // url:""
        });

        layers = [base_map,mndwi_layer,ponds_layer,true_layer,water_layer,select_feature_layer,region_layer,commune_layer,arrondissement_layer];
        map = new ol.Map({
			target: 'map',
			controls: ol.control.defaults().extend([
				new ol.control.ScaleLine(),
				new ol.control.ZoomSlider()
			]),
			renderer: 'canvas',
            layers: layers,
            view: new ol.View({
                center: ol.proj.fromLonLat([-14.222,15.2]),
                zoom: 8,
                maxZoom: 19,
                minZoom:2
            })
        });       

		var mouse_position = new ol.control.MousePosition({
			coordinateFormat: ol.coordinate.createStringXY(4),
			projection: 'EPSG:4326',
			className: 'custom-mouse-position',
			target:'coordonnees',
			undefinedHTML: '&nbsp;'
		});
		map.addControl(mouse_position);
        
		map.getLayers().item(1).setVisible(false);

		init_events = init_events = function() {
			(function () {
				var target, observer, config;
				// select the target node
				target = $('#app-content-wrapper')[0];

				observer = new MutationObserver(function () {
					window.setTimeout(function () {
						map.updateSize();
					}, 350);
				});
				$(window).on('resize', function () {
					map.updateSize();
				});

				config = {attributes: true};

				observer.observe(target, config);
			}());
		  }

        //Map on zoom function. To keep track of the zoom level. Data can only be viewed can only be added at a certain zoom level.
        map.on("moveend", function() {
            var zoom = map.getView().getZoom();
            var zoomInfo = '<p style="color:green;">Current Zoom level = ' + zoom.toFixed(3)+'.</p>';
            document.getElementById('zoomlevel').innerHTML = zoomInfo;
 //           if (zoom > 14){
  //              base_map2.setVisible(true);
   //         }else{
    //           base_map2.setVisible(false);
     //       }

            // Object.keys(layersDict).forEach(function(key){
            //     var source =  layersDict[key].getSource();
            // });
        });
        map.on("singleclick",function(evt){

            var zoom = map.getView().getZoom();
            $chartModal.modal('show');
            if (zoom < 14){
                $('.info').html('<b>The zoom level has to be 14 or greater. Please check and try again.</b>');
                $('#info').removeClass('hidden');
                return false;
            }else{
                $('.info').html('');
                $('#info').addClass('hidden');
            }

            var clickCoord = evt.coordinate;
            var proj_coords = ol.proj.transform(clickCoord, 'EPSG:3857','EPSG:4326');
            $("#current-lat").val(proj_coords[1]);
            $("#current-lon").val(proj_coords[0]);
            var $loading = $('#view-file-loading');
            var $loadingF = $('#f-view-file-loading');
            $loading.removeClass('hidden');
            $loadingF.removeClass('hidden');
            $("#plotter").addClass('hidden');
            $("#forecast-plotter").addClass('hidden');
            $("#details-plotter").addClass('hidden');
            //$tsplotModal.modal('show');
            var xhr = ajax_update_database('timeseries',{'lat':proj_coords[1],'lon':proj_coords[0]},'name');
            xhr.done(function(data) {
                if("success" in data) {
                    $('.info').html('');
                    map.getLayers().item(3).getSource().setUrl("");
                    map.getLayers().item(4).getSource().setUrl("");
                    var polygon = new ol.geom.Polygon(data.coordinates);
                    polygon.applyTransform(ol.proj.getTransform('EPSG:4326', 'EPSG:3857'));
                    var feature = new ol.Feature(polygon);

                    map.getLayers().item(5).getSource().clear();
                    select_feature_source.addFeature(feature);

                    generate_chart(data.values,proj_coords[1],proj_coords[0],data.name);

                    $loading.addClass('hidden');
                    $("#plotter").removeClass('hidden');

                }else{
                    $('.info').html('<b>Error processing the request. Please be sure to click on a feature.'+data.error+'</b>');
                    $('#info').removeClass('hidden');
                    $loading.addClass('hidden');
                }
              });
            var yhr = ajax_update_database('forecast',{'lat':proj_coords[1],'lon':proj_coords[0]},'name');
            yhr.done(function(data) {
                if("success" in data) {
                    $('.info').html('');
                    map.getLayers().item(3).getSource().setUrl("");
                    var polygon = new ol.geom.Polygon(data.coordinates);
                    polygon.applyTransform(ol.proj.getTransform('EPSG:4326', 'EPSG:3857'));
                    var feature = new ol.Feature(polygon);

                    map.getLayers().item(5).getSource().clear();
                    select_feature_source.addFeature(feature);

                    generate_forecast(data.values,proj_coords[1],proj_coords[0],data.name);

                    $loadingF.addClass('hidden');
                    $("#forecast-plotter").removeClass('hidden');

                }else{
                    $('.info').html('<b>Error processing the request. Please be sure to click on a feature.'+data.error+'</b>');
                    $('#info').removeClass('hidden');
                    $loadingF.addClass('hidden');
                }
            });
            var zhr = ajax_update_database('details',{'lat':proj_coords[1],'lon':proj_coords[0]},'name');
            zhr.done(function(data) {
                if("success" in data) {
                    $('.info').html('');
                    map.getLayers().item(3).getSource().setUrl("");
                    var polygon = new ol.geom.Polygon(data.coordinates);
                    polygon.applyTransform(ol.proj.getTransform('EPSG:4326', 'EPSG:3857'));
                    var feature = new ol.Feature(polygon);

                    map.getLayers().item(5).getSource().clear();
                    select_feature_source.addFeature(feature);
                    generate_details(proj_coords[1],proj_coords[0],data.namePond,data.sup_Pond,data.coordinates,data.nameRegion,data.nameCommune,data.nameArrondissement);

                    $loadingF.addClass('hidden');
  //                  $("#details-plotter").removeClass('hidden');

                }else{
                    $('.info').html('<b>Error processing the request. Please be sure to click on a feature.'+data.error+'</b>');
                    $('#info').removeClass('hidden');
                    $loadingF.addClass('hidden');
                }
            });
		});

        map.on('pointermove', function(evt) {
				var clickCoord = evt.coordinate;
				var proj_coords = ol.proj.transform(clickCoord, 'EPSG:3857','EPSG:4326');
				$("#latitude").val(proj_coords[1]);
				$("#longitude").val(proj_coords[0]);
			});
      };

    generate_chart = function(data,lat,lon,name){
        Highcharts.stockChart('plotter',{
            chart: {
                type:'line',
                zoomType: 'x'
            },
            plotOptions: {
                series: {
                    marker: {
                        enabled: true
                    },
                    allowPointSelect:true,
                    cursor: 'pointer',
                    point: {
                        events: {
                            click: function () {
                                $('.info').html('');
                                $("#meta-table").html('');
                                $("#reset").addClass('hidden');
                                $("#layers_checkbox").addClass('hidden');
                                var lat = $("#current-lat").val();
                                var lon = $("#current-lon").val();
                                var xhr = ajax_update_database('mndwi',{'xValue':this.x,'yValue':this.y,'lat':lat,'lon':lon});
                                xhr.done(function(data) {
                                    if("success" in data) {
                                        map.getLayers().item(3).getSource().setUrl("https://earthengine.googleapis.com/map/"+data.true_mapid+"/{z}/{x}/{y}?token="+data.true_token);
                                        map.getLayers().item(4).getSource().setUrl("https://earthengine.googleapis.com/map/"+data.water_mapid+"/{z}/{x}/{y}?token="+data.water_token);
                                        $("#meta-table").append('<tbody><tr><th>Latitude</th><td>'+(parseFloat(lat).toFixed(6))+'</td></tr><tr><th>Longitude</th><td>'+(parseFloat(lon).toFixed(6))+'</td></tr><tr><th>Current Date</th><td>'+data.date+'</td></tr><tr><th>Scene Cloud Cover</th><td>'+data.cloud_cover+'</td></tr></tbody>');
                                        $("#reset").removeClass('hidden');
                                        $("#layers_checkbox").removeClass('hidden');
                                    }else{
                                        $('.info').html('<b>Error processing the request. Please be sure to click on a feature.'+data.error+'</b>');
                                        $('#info').removeClass('hidden');
                                        $("#layers_checkbox").addClass('hidden');
                                    }
                                });

                            }
                        }
                    }
                }
            },
            title: {
                text:'Percent coverage of water at '+(name)+' ('+(lon.toFixed(3))+','+(lat.toFixed(3))+')'
                // style: {
                //     fontSize: '13px',
                //     fontWeight: 'bold'
                // }
            },
            xAxis: {
                type: 'datetime',
                labels: {
                    format: '{value:%d %b %Y}'
                    // rotation: 90,
                    // align: 'left'
                },
                title: {
                    text: 'Date'
                }
            },
            yAxis: {
                title: {
                    text: '%'
                },
                max: 1
            },
            exporting: {
                enabled: true
            },
            series: [{
                data:data,
                name: 'Historical percent coverage of water'
            }]
        });
    };
    generate_forecast = function(data,lat,lon,name){
        Highcharts.stockChart('forecast-plotter',{
          chart: {
              type:'line',
              zoomType: 'x'
          },
          plotOptions: {
              series: {
                  marker: {
                      enabled: true
                  },
                  allowPointSelect:true,
                  cursor: 'pointer',
                  point: {
                      events: {
                          click: function () {
                              $('.info').html('');
                              $("#meta-table").html('');
                              $("#reset").addClass('hidden');
                              $("#layers_checkbox").addClass('hidden');
                              var lat = $("#current-lat").val();
                              var lon = $("#current-lon").val();
                              var xhr = ajax_update_database('mndwi',{'xValue':this.x,'yValue':this.y,'lat':lat,'lon':lon});

                              xhr.done(function(data) {
                                  if("success" in data) {
                                      map.getLayers().item(3).getSource().setUrl("https://earthengine.googleapis.com/map/"+data.true_mapid+"/{z}/{x}/{y}?token="+data.true_token);
                                      map.getLayers().item(4).getSource().setUrl("https://earthengine.googleapis.com/map/"+data.water_mapid+"/{z}/{x}/{y}?token="+data.water_token);
                                      $("#meta-table").append('<tbody><tr><th>Latitude</th><td>'+(parseFloat(lat).toFixed(6))+'</td></tr><tr><th>Longitude</th><td>'+(parseFloat(lon).toFixed(6))+'</td></tr><tr><th>Current Date</th><td>'+data.date+'</td></tr><tr><th>Scene Cloud Cover</th><td>'+data.cloud_cover+'</td></tr></tbody>');
                                      $("#reset").removeClass('hidden');
                                      $("#layers_checkbox").removeClass('hidden');
                                  }else{
                                      $('.info').html('<b>Error processing the request. Please be sure to click on a feature.'+data.error+'</b>');
                                      $('#info').removeClass('hidden');
                                      $("#layers_checkbox").addClass('hidden');
                                  }
                              });

                          }
                      }
                  }
              }
          },
          title: {
              text:'Percent coverage of water at '+(name)+' ('+(lon.toFixed(3))+','+(lat.toFixed(3))+')'
              // style: {
              //     fontSize: '13px',
              //     fontWeight: 'bold'
              // }
          },
          xAxis: {
              type: 'datetime',
              labels: {
                  format: '{value:%d %b %Y}'
                  // rotation: 90,
                  // align: 'left'
              },
              title: {
                  text: 'Date'
              }
          },
          yAxis: {
              title: {
                  text: '%'
              },
              max: 1
          },
          exporting: {
              enabled: true
          },
          series: [{
              data:data,
              name: 'Forecast percent coverage of water'
          }]
      });
  };
    generate_details = function(lat,lon,namePond,sup_Pond,coordinates,nameRegion,nameCommune,nameArrondissement){
        $("#meta-table-details").html('');
        $("#meta-table-details").append('<tbody><tr><th>Latitude</th><td>'+(lat.toFixed(6))+'</td></tr><tr><th>Longitude</th><td>'+(lon.toFixed(6))+'</td></tr><tr><th>Nom Pond</th><td>'+namePond+'</td></tr><tr><th>Area Pond</th><td>'+sup_Pond+'</td></tr><tr><th>Nom Region</th><td>'+nameRegion+'</td></tr><tr><th>Nom Region</th><td>'+nameArrondissement+'</td></tr><tr><th>Nom Region</th><td>'+nameCommune+'</td></tr></tbody>');
        $("#reset").removeClass('hidden');

    };

    //onClick="vector_summer.setVisible(!vector_summer.getVisible());"

    init_all = function(){
        init_vars();
        init_map();
        init_events();
    };


    /************************************************************************
     *                        DEFINE PUBLIC INTERFACE
     *************************************************************************/
    /*
     * Library object that contains public facing functions of the package.
     * This is the object that is returned by the library wrapper function.
     * See below.
     * NOTE: The functions in the public interface have access to the private
     * functions of the library because of JavaScript function scope.
     */
    public_interface = {

    };

    /************************************************************************
     *                  INITIALIZATION / CONSTRUCTOR
     *************************************************************************/

    // Initialization: jQuery function that gets called when
    // the DOM tree finishes loading

    $(function() {
        init_all();
        $(".alert").click(function(){
            $(".alert").alert("close");
        });
        $('#base_map').change(function() {
            // this will contain a reference to the checkbox
            if (this.checked) {
                map.getLayers().item(0).setVisible(true);
            } else {
                map.getLayers().item(0).setVisible(false);
            }
        });
        $('#base_map2').change(function() {
            // this will contain a reference to the checkbox
            if (this.checked) {
                map.getLayers().item(1).setVisible(true);
            } else {
                map.getLayers().item(1).setVisible(false);
            }
        });
        $('#ponds_layer').change(function() {
            // this will contain a reference to the checkbox
            if (this.checked) {
                map.getLayers().item(2).setVisible(true);
            } else {
                map.getLayers().item(2).setVisible(false);
            }
        });
        $('#true_toggle').change(function() {
            // this will contain a reference to the checkbox
            if (this.checked) {
                map.getLayers().item(3).setVisible(true);
            } else {
                map.getLayers().item(3).setVisible(false);
            }
        });
        $('#mndwi_toggle').change(function() {
            // this will contain a reference to the checkbox
            if (this.checked) {
                map.getLayers().item(4).setVisible(true);
            } else {
                map.getLayers().item(4).setVisible(false);
            }
        });
        $('#select_region_layer').change(function() {
            // this will contain a reference to the checkbox
            if (this.checked) {
                map.getLayers().item(6).setVisible(true);
            } else {
                map.getLayers().item(6).setVisible(false);
            }
        });
        $('#select_commune_layer').change(function() {
            // this will contain a reference to the checkbox
            if (this.checked) {
                map.getLayers().item(7).setVisible(true);
            } else {
                map.getLayers().item(7).setVisible(false);
            }
        });
        $('#select_arrondissement_layer').change(function() {
            // this will contain a reference to the checkbox
            if (this.checked) {
                map.getLayers().item(8).setVisible(true);
            } else {
                map.getLayers().item(8).setVisible(false);
            }
        });
        $('#select_mndwi_layer').change(function() {
            // this will contain a reference to the checkbox
            if (this.checked) {
                map.getLayers().item(1).setVisible(true);
            } else {
                map.getLayers().item(1).setVisible(false);
            }
        });
    });

    return public_interface;

}());
// End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.
