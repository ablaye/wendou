from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import *
from .utilities import initLayers
from .app import Waterwatch as app


def home(request):
    """
    Controller for the app home page.
    """
    ponds, region, commune, arrondissement, mndwiImg, village = initLayers()
    context = {
        'ponds_mapid':ponds,
        # 'ponds_token':ponds['token'],
        'region_mapid':region['mapid'],
        'region_token':region['token'],
        'commune_mapid':commune['mapid'],
        'commune_token':commune['token'],
        'arrondissement_mapid':arrondissement['mapid'],
        'arrondissement_token':arrondissement['token'],
        'mndwiImg_mapid':mndwiImg,
        # 'mndwiImg_token':mndwiImg['token'],
        'village_mapid':village['mapid'],
        'village_token':village['token']
    }
    return render(request, 'waterwatch_2/home.html', context)
