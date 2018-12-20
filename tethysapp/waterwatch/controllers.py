from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import *
from utilities import *

def home(request):
    """
    Controller for the app home page.
    """
    ponds, region, commune, arrondissement, mndwiImg = initLayers()

    print('Ponds :',ponds['token']);
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
        'mndwiImg_token':mndwiImg['token']
    }
    return render(request, 'waterwatch/home.html', context)
