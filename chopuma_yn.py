import os
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
from python_Db_jh import copy_table

"""
초품아정의 : 학교와 주택이 한블럭 내에 있는 경우(횡단보도를 건너지 않고 초등학교를 갈 수 있는 단지)

도로망 공공데이터를 이용해 초등학교와 주택간 직선과 도로 라인을 조인
"""
#도로망데이터 url
#http://data.nsdi.go.kr/dataset/12902
#https://www.its.go.kr/nodelink/nodelinkRef

#주택과 배정초등학교 관계데이터 호출(비즈니스로직)
data1 = db('local').extractCodeDf('''query''')
data1 = [{'apt_seq': '1', 'school_id': '1', 'school_nm': '에이초등학교', 'school_grade_div': '초등학교', 
          'dist': 0.46328, 'lat': '35.33153947', 'lon': '129.0058469', 'ctprvn_code': '11', 
          'dgis_x': '129.0089263', 'dgis_y': '35.33486323',}]

#예제에선 수도권만 시행

ctprvn_lst = [['11','서울'],['41','경기'],['28','인천']]

templist = []
#도로망데이터 압축 풀고 세팅
a = gpd.read_file(r'NODELINKDATA\MOCT_LINK.shp')
a['SIG_CD'] = '1'
a.to_crs(5181,inplace=True)
for ct in ctprvn_lst:
    data2 = data1[data1.ctprvn_code == ct[0]]
    data2['geometry'] = data2[['dgis_x', 'dgis_y', 'lon', 'lat']].astype(float).apply(
        lambda x: LineString([Point(x[0], x[1]), Point(x[2], x[3])]), axis=1)
    data2 = gpd.GeoDataFrame(data2, crs=4326, geometry='geometry')
    data2 = data2.to_crs(5181)
    filelst = [x for x in os.listdir() if re.search(ct[1],x)][0]
    road_data = pd.concat([gpd.read_file(os.getcwd() + '\\' + filelst + '\\' + [x for x in os.listdir(os.getcwd() + '\\' + filelst) if re.search('\.shp',x)][0]),
                           a[['LINK_ID','geometry','SIG_CD']]])

    resultdata = gpd.sjoin(data2, road_data, 'left', predicate='intersects')
    result = resultdata[resultdata.SIG_CD.isna()][
        ['apt_seq', 'apt_nm', 'school_id', 'school_nm', 'dist', 'dgis_y', 'dgis_x']].reset_index(drop=True)
    result = result[result['dist'] <= 0.3]
    templist.append(result)
    print(ct[0] + ' success!!')

result = pd.concat(templist)

"""
result['geometry'] =  result[['dgis_x','dgis_y']].apply(lambda x : Point(float(x[0]),float(x[1])),axis=1)
result = gpd.GeoDataFrame(result,crs = 4326,geometry = 'geometry')
result.to_crs(5181,inplace=True)

result['geometry1'] = result.geometry.map(lambda x : ','.join([str(t) for sublst in x.xy for t in sublst]))
"""
#result : 초품아단지 목록


