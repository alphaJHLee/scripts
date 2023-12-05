import re
import pandas as pd
import requests
import pymysql
import json
import multiprocessing as mp
import time
from shapely.geometry import Point,Polygon,LineString
import math
import geopandas as gpd
from python_Db_jh import DbCon as db
from geo_util_jh import GeoUtil



#두 위치데이터에 대해 특정거리 내의 데이터쌍을 묶는 함수(epsg4326 위경도를 디폴트로 계산)
def extract_distance_by_gpd(aptdata,otherdata,crs,max_dist,aptdata_coord = ['lon','lat'],otherdata_coord = ['lon','lat'],
                            apt_crs = {'init': 'epsg:4326'},other_crs = {'init': 'epsg:4326'}):
    otherdata['geometry'] = otherdata[otherdata_coord].astype(float).apply(lambda x: Point(x[0], x[1]), axis=1)
    otherdata = gpd.GeoDataFrame(otherdata, geometry='geometry', crs=other_crs)
    otherdata = otherdata.to_crs(crs)

    aptdata['geometry'] = aptdata[aptdata_coord].astype(float).apply(lambda x: Point(x[0], x[1]), axis=1)
    aptdata = gpd.GeoDataFrame(aptdata, geometry='geometry', crs=apt_crs)
    aptdata = aptdata.to_crs(crs)
    aptdata.geometry = aptdata.geometry.buffer(int(max_dist))

    resultdata = gpd.sjoin(aptdata, otherdata, 'inner', predicate='contains')
    if aptdata_coord == ['lon','lat'] and otherdata_coord == ['lon','lat']:
        coord_columns = ['lon_left','lat_left','lon_right','lat_right']
    else :
        coord_columns = list(otherdata_coord) + list(aptdata_coord)


    resultdata['dist'] = resultdata.loc[:, coord_columns].astype(float).apply(
        lambda x: GeoUtil.get_harversion_distance(x[0], x[1], x[2], x[3]), axis=1)
    return resultdata



##############################################################################################################################################
if __name__ == '__main__':
    apt = db('local').extractCodeDf('''select apt_seq,lat,lon from aptinfo''')
    hosp = db('local').extractCodeDf('''select * from hospital_info''').iloc[:, :-1]
    hosp.columns = ['요양기관명', '종별코드', '종별코드명', '주소', '개설일자', '총의사수', 'x좌표', 'y좌표']

    result = extract_distance_by_gpd(apt, hosp, {'init': 'epsg:5186' }, 800, ['lon', 'lat'], ['x좌표', 'y좌표'])
    result = result[['apt_seq', '요양기관명', 'y좌표', 'x좌표', '종별코드명', '주소', 'dist']]


