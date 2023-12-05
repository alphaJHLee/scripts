import pandas as pd
import math
import numbers
from urllib.parse import urlencode, unquote_plus
import requests
import json
from idodb_key import kakao_local_key,naver_local_key




class GeoUtil:
    """
    Geographical Utils
    """


    def degree2radius(degree):
        return degree * (math.pi / 180)


    def get_harversion_distance(x1, y1, x2, y2, round_decimal_digits=5):
        """
        경위도 (x1,y1)과 (x2,y2) 점의 거리를 반환
        Harversion Formula 이용하여 2개의 경위도간 거래를 구함(단위:Km)
        """
        if x1 is None or y1 is None or x2 is None or y2 is None:
            return None
        assert isinstance(x1, numbers.Number) and -180 <= x1 and x1 <= 180
        assert isinstance(y1, numbers.Number) and -90 <= y1 and y1 <= 90
        assert isinstance(x2, numbers.Number) and -180 <= x2 and x2 <= 180
        assert isinstance(y2, numbers.Number) and -90 <= y2 and y2 <= 90

        R = 6371  # 지구의 반경(단위: km)
        dLon = GeoUtil.degree2radius(x2 - x1)
        dLat = GeoUtil.degree2radius(y2 - y1)

        a = math.sin(dLat / 2) * math.sin(dLat / 2) \
            + (math.cos(GeoUtil.degree2radius(y1)) \
               * math.cos(GeoUtil.degree2radius(y2)) \
               * math.sin(dLon / 2) * math.sin(dLon / 2))
        b = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * b, round_decimal_digits)


    def get_euclidean_distance(x1, y1, x2, y2, round_decimal_digits=5):
        """
        유클리안 Formula 이용하여 (x1,y1)과 (x2,y2) 점의 거리를 반환
        """
        if x1 is None or y1 is None or x2 is None or y2 is None:
            return None
        assert isinstance(x1, numbers.Number) and -180 <= x1 and x1 <= 180
        assert isinstance(y1, numbers.Number) and -90 <= y1 and y1 <= 90
        assert isinstance(x2, numbers.Number) and -180 <= x2 and x2 <= 180
        assert isinstance(y2, numbers.Number) and -90 <= y2 and y2 <= 90

        dLon = abs(x2 - x1)  # 경도 차이
        if dLon >= 180:  # 반대편으로 갈 수 있는 경우
            dLon -= 360  # 반대편 각을 구한다
        dLat = y2 - y1  # 위도 차이
        return round(math.sqrt(pow(dLon, 2) + pow(dLat, 2)), round_decimal_digits)




def kakao_addr_point(frame_addr, zip_addr_col, road_addr_col, df_col):
    url = 'https://dapi.kakao.com/v2/local/search/address.json?'
    headers = kakao_local_key
    addr_list = frame_addr.to_dict('records')
    templist = []
    for i, addrs in enumerate(addr_list):
        road_addr = addrs[road_addr_col]
        zip_addr = addrs[zip_addr_col]
        try:
            param = urlencode({unquote_plus('analyze_type'): 'similar', unquote_plus('query'): zip_addr})
            res = requests.get(url, param, headers=headers)
            json_data = json.loads(res.text)['documents']
            if len(json_data) != 0:
                json_data = json_data[0]
            else:
                param = urlencode({unquote_plus('analyze_type'): 'similar', unquote_plus('query'): road_addr})
                res = requests.get(url, param, headers=headers)
                json_data = json.loads(res.text)['documents'][0]

            addrs.update({'lat': json_data['y'], 'lon': json_data['x']})
            templist.append(addrs)
        except Exception as e:
            print(e, end=' => ', flush=True)
            print('\n')
            continue

        if i % 500 == 0:
            print(str(i) + 'th success!!')
            print('\n')

    df = pd.DataFrame(templist)
    if len(df) != 0:
        df = df[df_col + ['lat', 'lon']]
    else:
        df = pd.DataFrame([],columns=df_col + ['lat','lon'])
    return df




def naver_addr_point(frame_addr, zip_addr_col, road_addr_col, df_col):
    url = 'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode'
    header = naver_local_key

    addr_list = frame_addr.to_dict('records')
    templist = []
    for i, addrs in enumerate(addr_list):
        road_addr = addrs[road_addr_col]
        zip_addr = addrs[zip_addr_col]
        try:
            param = urlencode({'query': zip_addr})
            res = requests.get(url, param, headers=header)
            json_data = json.loads(res.text)['addresses']
            if len(json_data) != 0:
                json_data = json_data[0]
            else :
                param = urlencode({'query': road_addr})
                res = requests.get(url, param, headers=header)
                json_data = json.loads(res.text)['addresses'][0]
            addrs.update({'lat': json_data['y'], 'lon': json_data['x']})
            templist.append(addrs)
        except Exception as e:
            print(e, end=' => ', flush=True)
            print('\n')
            continue

        if i % 500 == 0:
            print(str(i) + 'th success!!')
            print('\n')
    if len(templist) != 0:
        df = pd.DataFrame(templist)[df_col + ['lat', 'lon']]
    else :
        df = pd.DataFrame([],columns = df_col + ['lat', 'lon'])
    return df

