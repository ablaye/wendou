#!/usr/bin/python
# -*- coding: utf-8 -*-
from utilities import *
import json
import os, sys
from django.http import JsonResponse
import gettext

pathname= os.path.dirname(sys.argv[0])
localdir = os.path.abspath(pathname) + "/locale/fr_FR/LC_MESSAGES"
gettext.install("messages", localdir)

def api_get_ponds(request):
    json_obj = {}
    if request.method == 'GET':
        try:
            ponds = initLayers()
            json_obj = {
                'ponds_mapid': ponds['mapid'],
                'ponds_token': ponds['token'],
                'success':'success'
            }
        except:
            json_obj = {"Error": _("Error Processing Request")}
    return  JsonResponse(json_obj)

def api_get_region(request):
    json_obj = {}
    if request.method == 'GET':
        try:
            region = regionLayers()
            json_obj = {
                'region_mapid': region['mapid'],
                'region_token': region['token'],
                'success':'success'
            }
        except:
            json_obj = {"Error": _("Error Processing Request")}
    return  JsonResponse(json_obj)

def api_get_commune(request):
    json_obj = {}
    if request.method == 'GET':
        try:
            commune = communeLayers()
            json_obj = {
                'commune_mapid': commune['mapid'],
                'commune_token': commune['token'],
                'success':'success'
            }
        except:
            json_obj = {"Error": _("Error Processing Request")}
    return  JsonResponse(json_obj)

def api_get_arrondissement(request):
    json_obj = {}
    if request.method == 'GET':
        try:
            arrondissement = arrondissementLayers()
            json_obj = {
                'arrondissement_mapid': arrondissement['mapid'],
                'arrondissement_token': arrondissement['token'],
                'success':'success'
            }
        except:
            json_obj = {"Error": _("Error Processing Request")}
    return  JsonResponse(json_obj)

def api_get_village(request):
    json_obj = {}
    if request.method == 'GET':
        try:
            village = villageLayers()
            json_obj = {
                'village_mapid': village['mapid'],
                'village_token': village['token'],
                'success':'success'
            }
        except:
            json_obj = {"Error": _("Error Processing Request")}
    return  JsonResponse(json_obj)

def api_get_timeseries(request):
    json_obj = {}
    if request.method == 'GET':
        info = request.GET
        lat = info.get('latitude')
        lon = info.get('longitude')
        try:
            ts_vals,coordinates,name = checkFeature(lon,lat)
            json_obj["values"] = ts_vals
            json_obj["coordinates"] = coordinates
            json_obj["name"] = name
            json_obj["success"] = "success"
        except Exception as e:
            json_obj["error"] = _("Error Processing Request. Error: ")+ str(e)
    return JsonResponse(json_obj)

def api_get_details(request):
    json_obj = {}
    if request.method == 'GET':
        info = request.GET
        lat = info.get('latitude')
        lon = info.get('longitude')
        try:
            namePond, sup_Pond, coordinates, nameRegion, nameCommune, nameArrondissement = detailsFeature(lon,lat)
            json_obj["namePond"] = namePond
            json_obj["sup_Pond"] = sup_Pond
            json_obj["coordinates"] = coordinates
            json_obj["nameRegion"] = nameRegion
            json_obj["nameCommune"] = nameCommune
            json_obj["nameArrondissement"] = nameArrondissement
            json_obj["success"] = "success"
        except Exception as e:
            json_obj["error"] = _("Error Processing Request. Error: ")+ str(e)
    return JsonResponse(json_obj)
