from tethys_sdk.base import TethysAppBase, url_map_maker


class Waterwatch(TethysAppBase):
    """
    Tethys app class for Water ENvironment for Observation in support of Users (WENDOU) in Ferlo, Senegal.
    """

    name = 'WENDOU (Water ENvironment Dashboard for Observation in support of Users in Ferlo, Senegal)'
    index = 'waterwatch:home'
    icon = 'waterwatch/images/logo_2.png'
    package = 'waterwatch'
    root_url = 'waterwatch'
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
                url='waterwatch',
                controller='waterwatch.controllers.home'
            ),
            UrlMap(
                name='timeseries',
                url='waterwatch/timeseries',
                controller='waterwatch.ajax_controllers.timeseries'
            ),
            UrlMap(
                name='forecast',
                url='waterwatch/forecast',
                controller='waterwatch.ajax_controllers.forecast'
            ),
            UrlMap(
                name='details',
                url='waterwatch/details',
                controller='waterwatch.ajax_controllers.details'
            ),
            UrlMap(
                name='mnwdi',
                url='waterwatch/mndwi',
                controller='waterwatch.ajax_controllers.mndwi'
            ),
            UrlMap(
                name='getPonds',
                url='waterwatch/api/getPonds',
                controller='waterwatch.api.api_get_ponds'
            ),
            UrlMap(
                name='getTimeseries',
                url='waterwatch/api/getTimeseries',
                controller='waterwatch.api.api_get_timeseries'
            ),
            UrlMap(
                name='getRegion',
                url='waterwatch/api/getRegion',
                controller='waterwatch.api.api_get_region'
            ),
            UrlMap(
                name='getCommune',
                url='waterwatch/api/getCommune',
                controller='waterwatch.api.api_get_commune'
            ),
            UrlMap(
                name='getArrondissement',
                url='waterwatch/api/getArrondissement',
                controller='waterwatch.api.api_get_arrondissement'
            ),
        )

        return url_maps

