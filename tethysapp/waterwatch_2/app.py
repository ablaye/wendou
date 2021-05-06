#!/usr/bin/python
# -*- coding: utf-8 -*-

from tethys_sdk.app_settings import SpatialDatasetServiceSetting
from tethys_sdk.base import TethysAppBase, url_map_maker
import os, sys
import gettext

pathname= os.path.dirname(sys.argv[0])
localdir = os.path.abspath(pathname) + "/locale/fr_FR/LC_MESSAGES"
gettext.install("messages", localdir)

class Waterwatch(TethysAppBase):
    """
    Tethys app class for Water ENvironment for Observation in support of Users (WENDOU) in Ferlo, Senegal.
    """
    name = 'WENDOU '
    index = 'waterwatch_2:home'
    icon = 'waterwatch_2/images/logo_2.png'
    package = 'waterwatch_2'
    root_url = 'waterwatch_2'
    color = '#2c3e50'
    description = 'View Water ENvironment Dashboard for Observation in support of Users (WENDOU) in Ferlo, Senegal'
    tags = 'Hydrology', 'Remote-Sensing'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)
        url_maps = (
            UrlMap(
                name='home',
                url='waterwatch_2',
                controller='waterwatch_2.controllers.home'
            ),
            UrlMap(
                name='timeseries',
                url='waterwatch_2/timeseries',
                controller='waterwatch_2.ajax_controllers.timeseries'
            ),
            UrlMap(
                name='forecast',
                url='waterwatch_2/forecast',
                controller='waterwatch_2.ajax_controllers.forecast'
            ),
            UrlMap(
                name='details',
                url='waterwatch_2/details',
                controller='waterwatch_2.ajax_controllers.details'
            ),
            UrlMap(
                name='mnwdi',
                url='waterwatch_2/mndwi',
                controller='waterwatch_2.ajax_controllers.mndwi'
            ),
            UrlMap(
                name='coucheMares',
                url='waterwatch_2/coucheMares',
                controller='waterwatch_2.ajax_controllers.coucheMares'
            ),
            UrlMap(
                name='coucheVillages',
                url='waterwatch_2/coucheVillages',
                controller='waterwatch_2.ajax_controllers.coucheVillages'
            ),
            UrlMap(
                name='getPonds',
                url='waterwatch_2/api/getPonds',
                controller='waterwatch_2.api.api_get_ponds'
            ),
            UrlMap(
                name='getTimeseries',
                url='waterwatch_2/api/getTimeseries',
                controller='waterwatch_2.api.api_get_timeseries'
            ),
            UrlMap(
                name='getRegion',
                url='waterwatch_2/api/getRegion',
                controller='waterwatch_2.api.api_get_region'
            ),
            UrlMap(
                name='getCommune',
                url='waterwatch_2/api/getCommune',
                controller='waterwatch_2.api.api_get_commune'
            ),
            UrlMap(
                name='getArrondissement',
                url='waterwatch_2/api/getArrondissement',
                controller='waterwatch_2.api.api_get_arrondissement'
            ),
            UrlMap(
                name='getVillage',
                url='waterwatch_2/api/getVillage',
                controller='waterwatch_2.api.api_get_village'
            ),
        )
        return url_maps
    def spatial_dataset_service_settings(self):
        """
        Example spatial_dataset_service_settings method.
        """
        sds_settings = (
            SpatialDatasetServiceSetting(
                name='SCO',
                description='service de jeu de données spatiales à utiliser par l\'application',
                engine=SpatialDatasetServiceSetting.GEOSERVER,
                required=True,
            ),
        )

        return sds_settings

