
import pandas as pd
import os
import multiprocessing as mp
import time
from shapely.geometry import Point,Polygon,LineString
import geopandas as gpd
from fiona.crs import from_string
import re
from python_Db_jh import DbCon as db



#epsg5181로 계산
epsg5181_qgis = from_string("+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=500000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")

#녹지추출모듈 : 지적도파일 다운받아 실핼(연속지적중 녹지만 추출)
#http://data.nsdi.go.kr/dataset/12771 연속지적 파일 다운
#filepath에 압축풀어 세팅
def shpgreenarea(filepath):
    starttime = time.time()
    filelist = os.listdir(filepath)
    geodata = gpd.GeoDataFrame(columns=['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'geometry', 'place'])
    epsg5181_qgis = from_string(
        "+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=500000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")

    for lists in filelist:
        foldershp = [lsts for lsts in os.listdir(filepath + '\\' + lists) if re.search('shp', lsts)]
        for shps in foldershp:
            try:
                shppath = filepath + '\\' + lists + '\\' + shps
                landdata = gpd.read_file(shppath, encoding='cp949')
                landdata = landdata.to_crs(epsg5181_qgis)
                landdata = landdata[landdata.A5.notnull()]
                landdata['place'] = landdata.A5.map(lambda x: x[-1])
                landdata = landdata[landdata.place.isin(['전', '답', '과', '임', '염', '천', '유', '공', '유', '사'])]
                landdata.to_file(filepath + '\\' + lists + '\\processed_' + shps,encoding = 'cp949' )
                print(time.time() - starttime)

                del (landdata)

            except Exception as e:
                print('error: ', e, '\n')
                break


    return print('successed!')




def calc_green_rate(apt_data,ctprvn_code,filepath):
    print(os.getpid())
    sido_code = [ctprvn_code]
    print(ctprvn_code, '\n')
    epsg5181_qgis = from_string(
        "+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=500000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")


    apt_data.city_code = apt_data.city_code.map(lambda x: str(int(x) // 1000))
    apt_data = apt_data[apt_data.city_code.isin(sido_code)]
    if len(apt_data) != 0:
        neighborlist = sido_code
        starttime = time.time()
        #filelist = ['AL_' + sido_codes + '_D002_20220101' for sido_codes in neighborlist]
        filelist = [x for x in os.listdir(filepath) if bool(re.match('AL_'+str(ctprvn_code),x)) and os.path.isdir(filepath + '/' + x)]
        geodata = gpd.GeoDataFrame(columns=['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'geometry', 'place'])


        for lists in filelist:
            foldershp = [lsts for lsts in os.listdir(filepath + '/' + lists) if
                         re.search('shp', lsts) and re.search('processed', lsts)]
            for shps in foldershp:
                try:
                    shppath = filepath + '/' + lists + '/' + shps
                    landdata = gpd.read_file(shppath, encoding='cp949')
                    landdata = landdata.to_crs(epsg5181_qgis)
                    landdata = landdata[landdata.A5.notnull()]
                    geodata = pd.concat([geodata, landdata])

                    print(time.time() - starttime)

                    del (landdata)

                except Exception as e:
                    print('error: ', e, '\n')
                    break

        geodata.crs = epsg5181_qgis
        x1 = mappinggreen_temp(apt_data, geodata)
    else:
        print('no_data!!')
        x1 = pd.DataFrame([])
    print(ctprvn_code, ' finished!!')
    return x1


def mappinggreen_temp(dataframe,geodata):
    starttime = time.time()
    apt_data = dataframe
    apt_data['geometry'] = apt_data.apply(lambda row: Point([float(row['dgis_x']), float(row['dgis_y'])]), axis=1)
    apt_data = gpd.GeoDataFrame(apt_data, geometry='geometry')
    apt_data.crs = {'init': 'epsg:4326'}
    apt_data = apt_data.to_crs(epsg5181_qgis)
    apt_data.geometry = apt_data.geometry.map(lambda x: x.buffer(1000))
    xarea = apt_data.iloc[0,-1].area

    apt_data = gpd.overlay(apt_data,geodata,how='intersection')
    apt_data['sumarea'] = apt_data.geometry.map(lambda x : x.area)
    apt_data1 = apt_data.groupby('apt_seq',as_index=False)['sumarea'].sum().rename(columns = {'sumarea':'녹지율'})
    apt_data1['녹지율'] = apt_data1['녹지율'].map(lambda x : str(round(100*x/xarea,2)) + '%')

    print(time.time()-starttime)
    return pd.DataFrame(apt_data1.loc[:,['apt_seq','녹지율']])


############################################################################################################################
if __name__ == '__main__':
    starttime = time.time()
    #전국 시도 코드(서울 : 11, 경기 : 41, 인천 : 28
    sidocode = ['11','41','28']
    aptdata = pd.DataFrame([{'apt_seq':'1','city_code' : '11560','dgis_x':'127.0105','dgis_y':'37.501'}])
    pooled_df = calc_green_rate(aptdata,'11','./지적도')
    pooled_df.to_csv('녹지율.csv', encoding='utf-8-sig', index=False)







