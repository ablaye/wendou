from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import *
from utilities import *
from app import Waterwatch as app


def home(request):
    """
    Controller for the app home page.
    """
    geoserver_engine = app.get_spatial_dataset_service(name='geoserver_tethys', as_engine=True)

    options = []

    response = geoserver_engine.list_layers(with_properties=False)

    if response['success']:
        for layer in response['result']:
            options.append((layer.title(), layer))

    select_options = SelectInput(
        display_text='Choose Layer',
        name='layer',
        multiple=False,
        options=options
    )

    map_layers = []
    selected_layer = u'wendou:Village'
    legend_title = u'Wendou:Village'
    geoserver_layer = MVLayer(
        source='ImageWMS',
        options={
            'url': 'http://localhost:8080/geoserver/wms',
            'params': {'LAYERS': selected_layer},
            'serverType': 'geoserver'
        },
        legend_title=legend_title,
        legend_extent=[-114, 36.5, -109, 42.5],
        legend_classes=[
            MVLegendClass('polygon', 'County', fill='#999999'),
    ])

    map_layers.append(geoserver_layer)


#    if request.POST and 'layer' in request.POST:
        #selected_layer = request.POST['layer']
 #       selected_layer = u'wendou:Village'
        #legend_title = selected_layer.title()
  #      legend_title = u'Wendou:Village'
   #     print('selected_layer',selected_layer)
    #    print('legend_title',legend_title)
     #   geoserver_layer = MVLayer(
      #      source='ImageWMS',
       #     options={
        #        'url': 'http://localhost:8080/geoserver/wms',
         #       'params': {'LAYERS': selected_layer},
          #      'serverType': 'geoserver'
           # },
            #legend_title=legend_title,
            #legend_extent=[-114, 36.5, -109, 42.5],
            #legend_classes=[
             #   MVLegendClass('polygon', 'County', fill='#999999'),
#        ])
#
 #       map_layers.append(geoserver_layer)

    view_options = MVView(
        projection='EPSG:4326',
        center=[-100, 40],
        zoom=4,
        maxZoom=18,
        minZoom=2
    )

    map_options = MapView(
        height='500px',
        width='100%',
        layers=map_layers,
        legend=True,
        view=view_options
    )

    ponds, region, commune, arrondissement, mndwiImg, village = initLayers()

    context = {
        'ponds_mapid':ponds['mapid'],
        'ponds_token':ponds['token'],
        'region_mapid':region['mapid'],
        'region_token':region['token'], 
        'commune_mapid':commune['mapid'],
        'commune_token':commune['token'], 
        'arrondissement_mapid':arrondissement['mapid'],
        'arrondissement_token':arrondissement['token'],
        'mndwiImg_mapid':mndwiImg['mapid'],
        'mndwiImg_token':mndwiImg['token'],
        'village_mapid':village['mapid'],
        'village_token':village['token'],
        'map_options': map_options,
        'select_options': select_options
    }
    return render(request, 'waterwatch/home.html', context)
