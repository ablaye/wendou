#!/usr/bin/python
# -*- coding: utf-8 -*-

import ee
from ee.ee_exception import EEException
import requests
import json
import math
import random
import datetime,time
import os, sys
import gettext

pathname= os.path.dirname(sys.argv[0])
localdir = os.path.abspath(pathname) + "/locale/fr_FR/LC_MESSAGES"
gettext.install("messages", localdir)


try:
    ee.Initialize()
except EEException as e:
    from oauth2client.service_account import ServiceAccountCredentials
    credentials = ServiceAccountCredentials.from_p12_keyfile(
    service_account_email='',
    filename='',
    private_key_password='notasecret',
    scopes=ee.oauth.SCOPE + ' https://www.googleapis.com/auth/drive ');
    ee.Initialize(credentials)

def addArea(feature):
    return feature.set('area',feature.area());


studyArea = ee.Geometry.Rectangle([-15.866, 14.193, -12.990, 16.490])
lc8 = ee.ImageCollection('LANDSAT/LC08/C01/T1_RT')
st2 = ee.ImageCollection('COPERNICUS/S2')

ponds = ee.FeatureCollection('projects/servir-wa/services/ephemeral_water_ferlo/ferlo_ponds')\
                .map(addArea).filter(ee.Filter.gt("area",10000))

region = ee.FeatureCollection('users/satigebelal/region')\
				.map(addArea)
commune = ee.FeatureCollection('users/satigebelal/commune')\
				.map(addArea)
arrondissement = ee.FeatureCollection('users/satigebelal/arrondissement')
countries = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017')
area_senegal = ee.FeatureCollection(countries).filter(ee.Filter.eq('country_na','Senegal'));
village = ee.FeatureCollection('users/satigebelal/Village');

def rescale(img, thresholds):
    return img.subtract(thresholds[0]).divide(thresholds[1] - thresholds[0])

def s2CloudMask(img):
    score = ee.Image(1.0)
    qa = img.select("QA60").unmask()

    score = score.min(rescale(img.select(['B2']), [0.1, 0.5]))
    score = score.min(rescale(img.select(['B1']), [0.1, 0.3]))
    score = score.min(rescale(img.select(['B1']).add(img.select(['B10'])), [0.15, 0.2]))
    score = score.min(rescale(img.select(['B4']).add(img.select(['B3'])).add(img.select('B2')), [0.2, 0.8]))

    #Clouds are moist
    ndmi = img.normalizedDifference(['B8A','B11'])
    score=score.min(rescale(ndmi, [-0.1, 0.1]))

    # However, clouds are not snow.
    ndsi = img.normalizedDifference(['B3', 'B11'])
    score=score.min(rescale(ndsi, [0.8, 0.6]))
    score = score.multiply(100).byte().lte(cloudThresh)
    mask = score.And(qa.lt(1024)).rename(['cloudMask'])\
                .clip(img.geometry())
    img = img.addBands(mask)
    return img.divide(10000).set("system:time_start", img.get("system:time_start"),
                                 'CLOUD_COVER',img.get('CLOUD_COVERAGE_ASSESSMENT'),
                                 'SUN_AZIMUTH',img.get('MEAN_SOLAR_AZIMUTH_ANGLE'),
                                 'SUN_ZENITH',img.get('MEAN_SOLAR_ZENITH_ANGLE'),
                                 'scale',ee.Number(10))

def lsCloudMask(img):
    blank = ee.Image(0)
    scored = ee.Algorithms.Landsat.simpleCloudScore(img)
    clouds = blank.where(scored.select(['cloud']).lte(cloudThresh), 1)\
                .clip(img.geometry())
    img = img.addBands(clouds.rename(['cloudMask']))
    return img.updateMask(clouds).set("system:time_start", img.get("system:time_start"),
                   "SUN_ZENITH",ee.Number(90).subtract(img.get('SUN_ELEVATION')),
                   "scale",ee.Number(30))

def simpleTDOM2(collection, zScoreThresh, shadowSumThresh, dilatePixels):
    def darkMask(img):
        zScore = img.select(shadowSumBands).subtract(irMean).divide(irStdDev)
        irSum = img.select(shadowSumBands).reduce(ee.Reducer.sum())
        TDOMMask = zScore.lt(zScoreThresh).reduce(ee.Reducer.sum()).eq(2).And(irSum.lt(shadowSumThresh)).Not()
        TDOMMask = TDOMMask.focal_min(dilatePixels)
        img = img.addBands(TDOMMask.rename(['TDOMMask']))
        # Combine the cloud and shadow masks
        combinedMask = img.select('cloudMask').mask().And(img.select('TDOMMask'))\
            .rename('cloudShadowMask');
        return img.addBands(combinedMask).updateMask(combinedMask)

    shadowSumBands = ['nir','swir1','swir2']
    irStdDev = collection.select(shadowSumBands).reduce(ee.Reducer.stdDev())
    irMean = collection.select(shadowSumBands).mean()

    collection = collection.map(darkMask)

    return collection

def lsTOA(img):
    return ee.Algorithms.Landsat.TOA(img)

# Function for wrapping cloud and shadow masking together.
# Assumes image has cloud mask band called "cloudMask" and a TDOM mask called "TDOMMask".
def cloudProject(img):

    azimuthField = 'SUN_AZIMUTH'
    zenithField = 'SUN_ZENITH'

    def projectHeights(cloudHeight):
      cloudHeight = ee.Number(cloudHeight);
      shadowCastedDistance = zenR.tan().multiply(cloudHeight); #Distance shadow is cast
      x = azR.cos().multiply(shadowCastedDistance).divide(nominalScale).round(); #X distance of shadow
      y = azR.sin().multiply(shadowCastedDistance).divide(nominalScale).round(); #Y distance of shadow
      return cloud.changeProj(proj, proj.translate(x, y));

    # Get the cloud mask
    cloud = img.select(['cloudMask']).Not();
    cloud = cloud.focal_max(dilatePixels);
    cloud = cloud.updateMask(cloud);

    # Get TDOM mask
    TDOMMask = img.select(['TDOMMask']).Not();

    # Project the shadow finding pixels inside the TDOM mask that are dark and
    # inside the expected area given the solar geometry
    # Find dark pixels
    darkPixels = img.select(['nir','swir1','swir2'])\
      .reduce(ee.Reducer.sum()).lt(shadowSumThresh);#.gte(1);

    proj = img.select('cloudMask').projection()

    # Get scale of image
    nominalScale = proj.nominalScale();

    #Find where cloud shadows should be based on solar geometry
    #Convert to radians
    meanAzimuth = img.get(azimuthField);
    meanZenith = img.get(zenithField);
    azR = ee.Number(meanAzimuth).multiply(math.pi).divide(180.0)\
      .add(ee.Number(0.5).multiply(math.pi));
    zenR = ee.Number(0.5).multiply(math.pi)\
      .subtract(ee.Number(meanZenith).multiply(math.pi).divide(180.0));

    # Find the shadows
    shadows = cloudHeights.map(projectHeights);

    shadow = ee.ImageCollection.fromImages(shadows).max();

    # Create shadow mask
    shadow = shadow.updateMask(cloud.mask().Not());
    shadow = shadow.focal_max(dilatePixels);
    shadow = shadow.updateMask(darkPixels.And(TDOMMask));

    # Combine the cloud and shadow masks
    combinedMask = cloud.mask().Or(shadow.mask()).eq(0);

    # Update the image's mask and return the image
    img = img.updateMask(combinedMask);
    img = img.addBands(combinedMask.rename(['cloudShadowMask']));
    return img.clip(img.geometry());

def mergeCollections(l8, s2, studyArea, t1, t2):
    lc8rename = l8.filterBounds(studyArea).filterDate(t1, t2).map(lsTOA).filter(
        ee.Filter.lt('CLOUD_COVER', 75)).map(lsCloudMask).select(['B2', 'B3', 'B4', 'B5', 'B6', 'B7','cloudMask'],
                                                                 ['blue', 'green', 'red', 'nir', 'swir1', 'swir2','cloudMask'])

    st2rename = s2.filterBounds(studyArea).filterDate(t1, t2).filter(
        ee.Filter.lt('CLOUD_COVERAGE_ASSESSMENT', 75)).map(s2CloudMask).select(
        ['B2', 'B3', 'B4', 'B8', 'B11', 'B12','cloudMask'],
        ['blue', 'green', 'red', 'nir', 'swir1', 'swir2','cloudMask'])#.map(bandPassAdjustment)

    return ee.ImageCollection(lc8rename.merge(st2rename))

def bandPassAdjustment(img):
    bands = ['blue','green','red','nir','swir1','swir2']
    # linear regression coefficients for adjustment
    gain = ee.Array([[0.977], [1.005], [0.982], [1.001], [1.001], [0.996]])
    bias = ee.Array([[-0.00411],[-0.00093],[0.00094],[-0.00029],[-0.00015],[-0.00097]])
    # Make an Array Image, with a 1-D Array per pixel.
    arrayImage1D = img.select(bands).toArray()

    # Make an Array Image with a 2-D Array per pixel, 6x1.
    arrayImage2D = arrayImage1D.toArray(1)

    componentsImage = ee.Image(gain).multiply(arrayImage2D).add(ee.Image(bias))\
    .arrayProject([0])\
    .arrayFlatten([bands]).float()

    return componentsImage.set('system:time_start',img.get('system:time_start'))

def calcWaterIndex(img):
    mndwi = img.expression('0.1511*B1 + 0.1973*B2 + 0.3283*B3 + 0.3407*B4 + -0.7117*B5 + -0.4559*B7',{
        'B1': img.select('blue'),
        'B2': img.select('green'),
        'B3': img.select('red'),
        'B4': img.select('nir'),
        'B5': img.select('swir1'),
        'B7': img.select('swir2'),
    }).rename('mndwi')

    return mndwi.addBands(img.select('cloudShadowMask')).copyProperties(img, ["system:time_start","CLOUD_COVER"])

def waterClassifier(img):
    THRESHOLD = ee.Number(-0.1304)

    water = ee.Image(0).where(img.select('cloudShadowMask'), img.select('mndwi').gt(THRESHOLD))

    result = img.addBands(water.rename(['water']))
    return result.copyProperties(img, ["system:time_start","CLOUD_COVER"])

def pondClassifier(shape):
    waterList = waterCollection.filterBounds(shape.geometry())\
                .sort('system:time_start',False)
    latest = ee.Image(waterList.first())
    # dates = ee.Array(waterCollection.aggregate_array('system:time_start'))

    # true = ee.Image(ee.Algorithms.If(latest.geometry().contains(shape.geometry),latest,
    #         waterList.get(1)))

    avg = latest.reduceRegion(
        reducer=ee.Reducer.mean(),
        scale=10,
        geometry=shape.geometry(),
        bestEffort=True
    )

    try:
        val = ee.Number(avg.get('water'))
        mVal = ee.Number(avg.get('cloudShadowMask'))

        test = ee.Number(ee.Algorithms.If(mVal.lt(0.5),ee.Number(3),ee.Number(0)))
        cls = test.add(val.gt(0.25))

        cls = cls.add(val.gt(0.75))
    except:
        val = random.choice(range(2))
        cls = ee.Number(val)

    return ee.Feature(shape).set({'pondCls': cls.int8()})

def makeTimeSeries(collection,feature,key=None,hasMask=False):

    def reducerMapping(img):
        if hasMask:
            img = img.updateMask(img.select('cloudShadowMask'))

        reduction = img.reduceRegion(
            ee.Reducer.mean(), feature.geometry(), 10)

        outVal = ee.Number(reduction.get(key))

        time = img.get('system:time_start')

        return img.set('indexVal',[ee.Number(time),outVal])

    collection = collection.filterBounds(feature.geometry()) #.getInfo()

    indexCollection = collection.map(reducerMapping)

    indexSeries = indexCollection.aggregate_array('indexVal').getInfo()

    formattedSeries = [[x[0],round(float(x[1]),3)] for x in indexSeries if x[1] > 0]

    # days_with_data = [[datetime.datetime.fromtimestamp((int(x[0]) / 1000)).strftime('%Y %B %d'),round(float(x[1]),3)] for x in indexSeries if x[1] > 0 ]

    return sorted(formattedSeries)

def getClickedImage(xValue,yValue,feature):

    equalDate = ee.Date(int(xValue))

#    true_image = ee.Image(mergedCollection.filterBounds(area_senegal).filterDate(equalDate,equalDate.advance(7,'day')).first())
    true_image = ee.Image(mergedCollection.filterDate(equalDate,equalDate.advance(7,'day')).first())
    true_imageid = true_image.getMapId({'min':0.05,'max':0.50,'gamma':1.5,'bands':'swir2,nir,green'})

 #   water_image = ee.Image(waterCollection.select('mndwi').filterBounds(area_senegal).filterDate(equalDate,equalDate.advance(2,'day')).first())
    water_image = ee.Image(waterCollection.select('mndwi').filterDate(equalDate,equalDate.advance(2,'day')).first())
    water_imageid = water_image.getMapId({'min':-0.2,'max':-0.05,'palette':'d3d3d3,84adff,9698d1,0000cc'})

    properties =  water_image.getInfo()['properties']

    return true_imageid,water_imageid,properties

def accumGFS(collection,startDate,nDays):
  if (nDays>16):
    raise Warning(_('Max forecast days is 16, only producing forecast for 16 days...'))
    nDays = 16
  cnt = 1
  imgList = []
  precipScale = ee.Image(1).divide(ee.Image(1e3))
  for i in range(nDays+1):
    cntMax =(24*(i+1))
    forecastMeta = []
    for j in range(cnt,cntMax+1):
        forecastMeta.append(cnt)
        cnt+=1
    dayPrecip = collection.filter(ee.Filter.inList('forecast_hours', forecastMeta))
    imgList.append(dayPrecip.sum().multiply(precipScale)
      .set('system:time_start',startDate.advance(i,'day')))
  return ee.ImageCollection(imgList)

def accumCFS(collection,startDate,nDays):
    imgList = []
    precipScale = ee.Image(86400).divide(ee.Image(1e3))
    for i in range(nDays):
        newDate = startDate.advance(i,'day')
        dayPrecip = collection.filterDate(newDate,newDate.advance(24,'hour'))
        imgList.append(dayPrecip.sum().multiply(precipScale)\
          .set('system:time_start',newDate.millis()))
    return ee.ImageCollection(imgList)

def calcInitIap(collection,startDate,pastDays):
    off = pastDays*-1
    s = startDate.advance(off,'day')
    e = s.advance(pastDays,'day')
    prevPrecip = collection.filterDate(s,e)

    dailyPrev = accumCFS(prevPrecip,s,pastDays)

    imgList = dailyPrev.toList(pastDays)
    outList = []

    for i in range(pastDays):
        pr = ee.Image(imgList.get(i))
        antecedent = pr.multiply(ee.Image(1).divide(pastDays-i))
        outList.append(antecedent)

    Iap = ee.ImageCollection(outList).sum().rename(['Iap'])

    return Iap

class fClass(object):
    def __init__(self,feature,initCond,initTime,
                 k=0.45,Gmax=15,L=0.1,Kr=0.9,n=10,alpha=0.9):
        # set parameters to EE variables
        self.k = ee.Image(k)
        self.Gmax = ee.Image(Gmax)
        self.L = ee.Image(L)
        self.Kr = ee.Image(Kr)
        self.n = ee.Image(n)
        self.alpha = ee.Image(alpha)
        self.pArea = feature.geometry().area()
        self.initial = ee.Image(initCond)
        self.initTime = initTime
        self.pond = feature

    def forecast(self):
        # calculate volume - area/height relationship parameters
        self.Ac = self.n.multiply(self.pArea)
        self.h0 = ee.Image(1)

        pondMin = ee.Number(elv.reduceRegion(
          geometry=self.pond.geometry(),
          reducer=ee.Reducer.min(),
          scale=30
        ).get('elevation'))
        SoInit = ee.Image(0).where(elv.gte(pondMin).And(elv.lte(pondMin.add(3))),1)
        self.So = ee.Image(ee.Number(SoInit.reduceRegion(
          geometry=self.pond.geometry(),
          reducer=ee.Reducer.sum(),
          scale=30
        ).get('constant'))).multiply(900)

        # begin forecasting water area
        forecastDays = 15
        modelDate = self.initTime

        # calculate initial conditions
        A = ee.Image(self.pArea).multiply(self.initial)
        hInit = A.divide(self.So).pow(self.h0.divide(self.alpha))
        self.Vo = self.So.multiply(self.h0).divide(self.alpha.add(1))

        precipData = gfs.filterDate(modelDate,modelDate.advance(1,'hour'))\
                        .filterMetadata('forecast_hours','greater_than',0)\
                        .select(['total_precipitation_surface'],['precip'])
        dailyPrecip = accumGFS(precipData,modelDate,forecastDays)

        initIap = calcInitIap(cfs,modelDate,7)

        # set model start with t-1 forcing
        first = ee.Image(cfs.filterDate(modelDate.advance(-1,'day'),modelDate).select(['precip']).sum())\
              .multiply(ee.Image(86400).divide(ee.Image(1e3))).addBands(initIap.multiply(1000))\
              .addBands(A.multiply(hInit)).addBands(A).addBands(hInit)\
              .rename(['precip','Iap','vol','area','height']).clip(studyArea)\
              .set('system:time_start',modelDate.advance(-12,'hour').millis()).float()

        modelOut = ee.List(dailyPrecip.iterate(self._accumVolume,ee.List([first]))).slice(1)
        modelOut = ee.ImageCollection.fromImages(modelOut)

        pondPct = modelOut.select('area').map(self._pctArea)

        ts = makeTimeSeries(pondPct.select('area'),self.pond,key='area')
        return ts

    def _accumVolume(self,img,imgList):
        # extract out forcing and state variables
        past = ee.Image(ee.List(imgList).get(-1)).clip(studyArea)
        pastIt = past.select('Iap')
        pastPr = past.select('precip')
        pastAr = past.select('area')
        #pastHt = past.select('height')
        pastVl = past.select('vol')
        nowPr = img.select('precip').clip(studyArea)
        date = ee.Date(img.get('system:time_start'))

        # change in volume model
        deltaIt = pastIt.add(pastPr).multiply(self.k)
        Gt = self.Gmax.subtract(deltaIt)
        Gt = Gt.where(Gt.lt(0),0)
        Pe = nowPr.subtract(Gt)
        Pe = Pe.where(Pe.lt(0),0)
        Qin = self.Kr.multiply(Pe).multiply(self.Ac)
        dV = nowPr.multiply(self.pArea).add(Qin).subtract(self.L.multiply(pastAr))
        # convert dV to actual volume
        volume = pastVl.add(dV).rename(['vol'])
        volume = volume.where(volume.lt(0),0)

        # empirical model for volume to area/height relationship
        ht = volume.divide(self.Vo).pow(ee.Image(1).divide(self.alpha))\
                  .divide(ee.Image(1).divide(self.h0)).rename(['height'])
        area = self.So.multiply(ht.divide(self.h0).pow(self.alpha)).rename(['area'])
        area = area.where(area.lt(0),1) # contrain area to real values

        # set state variables to output model step
        step = nowPr.addBands(deltaIt).addBands(volume).addBands(area).addBands(ht)\
                  .set('system:time_start',date.advance(6,'hour').millis())

        return ee.List(imgList).add(step.float())

    def _pctArea(self,img):
        pct = ee.Image(img.divide(ee.Image(self.pArea)).copyProperties(img,['system:time_start']))
        return pct.where(pct.gt(1),1)#.rename('pctArea')#

today = time.strftime("%Y-%m-%d")
iniTime = ee.Date('2015-01-01')
endTime = ee.Date(today)

dilatePixels = 2;
cloudHeights = ee.List.sequence(200,5000,500);
zScoreThresh = -0.8;
shadowSumThresh = 0.35;
cloudThresh = 10;

mergedCollection = mergeCollections(lc8, st2, studyArea, iniTime, endTime).sort('system:time_start', False);

mergedCollection = simpleTDOM2(mergedCollection, zScoreThresh, shadowSumThresh, dilatePixels)#.map(cloudProject)

mndwiCollection = mergedCollection.map(calcWaterIndex)

waterCollection = mndwiCollection.map(waterClassifier)

ponds_cls = ponds.map(pondClassifier)

visParams = {'min': 0, 'max': 3, 'palette': 'red,yellow,green,gray'}

pondsImg = ponds_cls.reduceToImage(properties=['pondCls'], reducer=ee.Reducer.first())

pondsImgID = pondsImg.getMapId(visParams)
regionImgID = region.getMapId()
arrondissementImgID = arrondissement.getMapId()
communeImgID = commune.getMapId()
villageImgID = village.getMapId()

img = mergedCollection.median().clip(studyArea)

print('img', img)
mndwiImg = mndwiCollection.select('mndwi').median().clip(area_senegal).getMapId({'min':-0.2,'max':-0.05,'palette':'d3d3d3,84adff,9698d1,0000cc'})

gfs = ee.ImageCollection('NOAA/GFS0P25')
cfs = ee.ImageCollection('NOAA/CFSV2/FOR6H').select(['Precipitation_rate_surface_6_Hour_Average'],['precip'])
elv = ee.Image('USGS/SRTMGL1_003')

def initLayers():
    return pondsImgID, regionImgID, communeImgID, arrondissementImgID, mndwiImg, villageImgID

def regionLayers():
    return region
def communeLayers():
    return commune
def arrondissementLayers():
    return arrondissement
def villageLayers():
    return village

def filterPond(lon, lat):
    point = ee.Geometry.Point(float(lon), float(lat))
    sampledPoint = ee.Feature(ponds.filterBounds(point).first())

    computedValue = sampledPoint.getInfo()['properties']['uniqID']

    selPond = ponds.filter(ee.Filter.eq('uniqID', computedValue))

    return selPond

def filterDetails(lon, lat):
    point = ee.Geometry.Point(float(lon), float(lat))

    sampledPoint = ee.Feature(ponds.filterBounds(point).first())
    sampledRegion = ee.Feature(region.filterBounds(point).first())
    sampledCommune = ee.Feature(commune.filterBounds(point).first())
    sampledArrondissement = ee.Feature(arrondissement.filterBounds(point).first())

    computedValuePonds = sampledPoint.getInfo()['properties']['uniqID']
    computedValueRegion = sampledRegion.getInfo()['properties']['id_reg']
    computedValueCommune = sampledCommune.getInfo()['properties']['id_com']
    computedValueArrondissement = sampledArrondissement.getInfo()['properties']['id_arro']

    selPond = ponds.filter(ee.Filter.eq('uniqID', computedValuePonds))
    selRegion = ponds.filter(ee.Filter.eq('id_reg', computedValueRegion))
    selCommune = ponds.filter(ee.Filter.eq('id_com', computedValueCommune))
    selArrondissement = ponds.filter(ee.Filter.eq('id_arro', computedValueArrondissement))

    return selPond, selRegion, selCommune, selArrondissement

def checkFeature(lon,lat):

    selPond = filterPond(lon,lat)

    ts_values = makeTimeSeries(waterCollection,selPond,key='water',hasMask=True)
    name = selPond.getInfo()['features'][0]['properties']['Nom']
    if len(name) < 2:
        name = _('Unnamed Pond')

    coordinates = selPond.getInfo()['features'][0]['geometry']['coordinates']
    return ts_values,coordinates,name

def checkPonds():
    coordinates = ponds.getInfo()['features']
    return coordinates

def checkVillage():
    coordinates = village.getInfo()['features']
    return coordinates


def forecastFeature(lon,lat):
    selPond = filterPond(lon,lat)

    featureImg = ee.Image(waterCollection.filterBounds(selPond).sort('system:time_start',False).first())

    lastTime = ee.Date(featureImg.get('system:time_start'))

    pondFraction = ee.Number(featureImg.reduceRegion(ee.Reducer.mean(), selPond.geometry(), 10).get('water'))

    fModel = fClass(selPond,pondFraction,lastTime)

    ts_values = fModel.forecast()
    name = selPond.getInfo()['features'][0]['properties']['Nom']
    if len(name) < 2:
        name = _('Unnamed Pond')

    coordinates = selPond.getInfo()['features'][0]['geometry']['coordinates']

    return ts_values,coordinates,name

def getMNDWI(lon,lat,xValue,yValue):

    selPond = filterPond(lon, lat)

    mndwi_img = getClickedImage(xValue,yValue,selPond)

    return mndwi_img

def detailsFeature(lon,lat):
    point = ee.Geometry.Point(float(lon), float(lat))

    sampledPoint = ee.Feature(ponds.filterBounds(point).first())
    sampledRegion = ee.Feature(region.filterBounds(point).first())
    sampledCommune = ee.Feature(commune.filterBounds(point).first())
    sampledArrondissement = ee.Feature(arrondissement.filterBounds(point).first())

    computedValuePonds = sampledPoint.getInfo()['properties']['uniqID']
    computedValueRegion = sampledRegion.getInfo()['properties']['id_reg']
    computedValueCommune = sampledCommune.getInfo()['properties']['id_com']
    computedValueArrondissement = sampledArrondissement.getInfo()['properties']['id_arro']

    selPond = ponds.filter(ee.Filter.eq('uniqID', computedValuePonds))
    selRegion = ponds.filter(ee.Filter.eq('id_reg', computedValueRegion))
    selCommune = ponds.filter(ee.Filter.eq('id_com', computedValueCommune))
    selArrondissement = ponds.filter(ee.Filter.eq('id_arro', computedValueArrondissement))

    return selPond, selRegion, selCommune, selArrondissement

def filterRegion(lon, lat):

    point = ee.Geometry.Point(float(lon), float(lat))
    sampledPoint = ee.Feature(region.filterBounds(point).first())

    computedValue = sampledPoint.getInfo()['properties']['id_reg']

    selRegion = region.filter(ee.Filter.eq('id_reg', computedValue))

    return selRegion

def filterCommune(lon, lat):
    point = ee.Geometry.Point(float(lon), float(lat))
    sampledPoint = ee.Feature(commune.filterBounds(point).first())

    computedValue = sampledPoint.getInfo()['properties']['id_com']

    selCommune = commune.filter(ee.Filter.eq('id_com', computedValue))

    return selCommune

def filterArrondissement(lon, lat):
    point = ee.Geometry.Point(float(lon), float(lat))
    sampledPoint = ee.Feature(arrondissement.filterBounds(point).first())

    computedValue = sampledPoint.getInfo()['properties']['id_arro']

    selArrondissement = arrondissement.filter(ee.Filter.eq('id_arro', computedValue))

    return selArrondissement

def filterVillage(lon, lat):

    point = ee.Geometry.Point(float(lon), float(lat))
    sampledPoint = ee.Feature(village.filterBounds(point).first())

    computedValue = sampledPoint.getInfo()['properties']['OBJECTID']

    selVillage = village.filter(ee.Filter.eq('OBJECTID', computedValue))

    return selVillage
