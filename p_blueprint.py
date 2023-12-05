
import cv2
import numpy as np
import pandas as pd
import os
import time
import math
import re
import multiprocessing as mp
import warnings
import datetime
from python_Db_jh import DbCon as db
warnings.filterwarnings(action='ignore')

#타일사진 확보
template = cv2.imdecode(np.fromfile('전실타일1.jpg', np.uint8), cv2.IMREAD_COLOR)

#템플릿매칭
def templatemat(img):
    method_name = 'cv2.TM_CCOEFF_NORMED'
    img_draw = img.copy()
    method = eval(method_name)
    # 타일사진과 템플릿 매칭   ---①
    res = cv2.matchTemplate(img, template, method)
    # 최솟값, 최댓값과 그 좌표 구하기 ---②
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
#    print(method_name, min_val, max_val, min_loc, max_loc)

    # TM_SQDIFF의 경우 최솟값이 좋은 매칭, 나머지는 그 반대 ---③

    top_left = max_loc
    match_val = max_val
    # 매칭 좌표 구해서 사각형 표시   ---④
    return (top_left[1] + 9,top_left[0] + 9)

#그림확인하기용
def c(imgs):
    cv2.imshow('labeled', imgs)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
#그림확인하기용
def c1(imgs,labels,i):
    imgs[labels != i] = [0,0,0]
    imgs[labels == i] = [254,254,254]
    cv2.imshow('labeled', imgs)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def expand_ind(imgdata,labels,label_ind,dimk):
    backg_expand = imgdata.copy()
    backg_expand[np.where(np.isin(labels, label_ind))] = [180, 180, 180]
    backg_expand[np.where(np.isin(labels, label_ind) == False)] = [30, 30, 30]

    _, backg_expand = cv2.threshold(backg_expand, 127, 255, cv2.THRESH_BINARY)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (dimk, dimk))
    # 팽창 연산 적용 ---②
    backg_expand = np.mean(cv2.dilate(backg_expand, k), axis=2)
    return backg_expand

#거실/방/발코니/화장실 구분
def room_classification(df):
    living_ind = df[df.blue <= 140].index
    restroom_ind = df[df[['blue','green','red']].max(axis=1) ==df.blue].index
    df1 = df.loc[list(set(df.index) - set(list(living_ind) + list(restroom_ind)))]
    if df1['blue'].std() >= 4.5:
        balchony_ind = df1[df1['blue'] > df1['blue'].mean(axis=0)].index
        room_ind = df1[df1['blue'] <= df1['blue'].mean(axis=0)].index
    else :
        balchony_ind = df1[df1['blue'] > 215].index
        room_ind = df1[df1['blue'] <= 215].index
    return (living_ind,restroom_ind,balchony_ind,room_ind)


def connectcomponent(real_img,img,label,conn):
    cnt, labels, stats, centroids = cv2.connectedComponentsWithStats(img, labels=label,connectivity = conn)
    stats = pd.DataFrame(stats, columns=['x', 'y', 'width', 'height', 'area'])
    centroids = pd.DataFrame(centroids, columns=['x_c', 'y_c'])
    stats = pd.concat([stats, centroids], axis=1)
    stats[['blue', 'green', 'red']] = list([real_img[labels == i].mean(axis=0) for i in range(cnt)])
    stats['mean_pix'] = stats[['blue', 'green', 'red']].mean(axis=1)
    return cnt,labels,stats


#특정방 기준 창문의 방위 추정(기울기분모가 0인경우 방지)
#창문들의 무게중심을 이용해 방 무게중심과의 기울기각도 계산하는 방식
def det_direction(x_c,y_c,window_lst,stats_frame):
    templist = []
    if len(window_lst) != 0:
        w_x_c = stats_frame.loc[window_lst, 'x_c'].mean()
        w_y_c = stats_frame.loc[window_lst, 'y_c'].mean()
        if w_x_c - x_c <= 0.05 and w_x_c - x_c>= -0.05:
            dir_vector = (0.05,y_c - w_y_c)
        else:
            dir_vector = (w_x_c - x_c, y_c - w_y_c)



        angle = math.atan(dir_vector[1] / dir_vector[0]) * 180 / np.pi
        if dir_vector[0] < 0:
            angle = angle + 180
        elif dir_vector[1] < 0:
            angle = angle + 360

        if angle <= 44:
            dir = '동'
        elif angle <= 136:
            dir = '북'
        elif angle <= 224:
            dir = '서'
        elif angle <= 316:
            dir = '남'
        else:
            dir = '동'
        templist.append(dir)

    return templist



def det_direction_living(x_c,y_c,window_lst,stats_frame):
    templist = []
    if len(window_lst) != 0:
        for window_idx in window_lst:
            w_x_c = stats_frame.loc[window_idx, 'x_c']
            w_y_c = stats_frame.loc[window_idx, 'y_c']

            if w_x_c - x_c <= 0.05 and w_x_c - x_c >= -0.05:
                dir_vector = (0.05, y_c - w_y_c)
            else:
                dir_vector = (w_x_c - x_c, y_c - w_y_c)
            angle = math.atan(dir_vector[1] / dir_vector[0]) * 180 / np.pi
            if dir_vector[0] < 0:
                angle = angle + 180
            elif dir_vector[1] < 0:
                angle = angle + 360

            if angle <= 44:
                dir = '동'
            elif angle <= 136:
                dir = '북'
            elif angle <= 224:
                dir = '서'
            elif angle <= 316:
                dir = '남'
            else:
                dir = '동'
            templist.append(dir)

    return templist

#기존 무게중심 기울기를 이용한 방식에 창문의 구조를 고려한 방식을 합산해 방위 추정
def det_direction_living1(x_c,y_c,window_lst,stats_frame,living_index,img,labels):
    templist = []
    living_idx_frame = pd.DataFrame(np.transpose(np.array(living_index)), columns=['x', 'y'])
    if len(window_lst) != 0:
        for window_idx in window_lst:
            w_x_c = stats_frame.loc[window_idx, 'x_c']
            w_y_c = stats_frame.loc[window_idx, 'y_c']

            if w_x_c - x_c <= 0.05 and w_x_c - x_c >= -0.05:
                dir_vector = (0.05, y_c - w_y_c)
            else:
                dir_vector = (w_x_c - x_c, y_c - w_y_c)

            angle = math.atan(dir_vector[1] / dir_vector[0])
            if dir_vector[0] < 0:
                angle_xy = (-math.cos(angle),-math.sin(angle))
            else :
                angle_xy = (math.cos(angle), math.sin(angle))

            window_living_int = pd.merge(
                pd.DataFrame(np.transpose(np.array(np.where(expand_ind(img, labels, window_idx, 30) >= 250))),
                             columns=['x', 'y']),
                living_idx_frame, 'inner', ['x', 'y'])

            liv_x_c = window_living_int['y'].mean()
            liv_y_c = window_living_int['x'].mean()
            if w_x_c - liv_x_c <= 0.05 and w_x_c - liv_x_c >= -0.05:
                new_dir_vector = (0.05, liv_y_c - w_y_c)
            else:
                new_dir_vector = (w_x_c - liv_x_c, liv_y_c - w_y_c)
            new_angle = math.atan(new_dir_vector[1] / new_dir_vector[0])
            if new_dir_vector[0] < 0:
                new_angle_xy  = (-math.cos(new_angle),-math.sin(new_angle))
            else :
                new_angle_xy = (math.cos(new_angle), math.sin(new_angle))

            total_angle_xy = (angle_xy[0] + new_angle_xy[0], angle_xy[1] + new_angle_xy[1])
            angle = math.atan(total_angle_xy[1] / total_angle_xy[0]) * 180 / np.pi


            if total_angle_xy[0] < 0:
                angle = angle + 180
            elif total_angle_xy[1] < 0:
                angle = angle + 360

            if angle <= 44:
                dir = '동'
            elif angle <= 136:
                dir = '북'
            elif angle <= 224:
                dir = '서'
            elif angle <= 316:
                dir = '남'
            else:
                dir = '동'
            templist.append(dir)

    return templist


def dir_angle(angle):
    if angle <= 44:
        dir = '동'
    elif angle <= 136:
        dir = '북'
    elif angle <= 224:
        dir = '서'
    elif angle <= 316:
        dir = '남'
    else:
        dir = '동'
    return dir




#거실의 경우 창문 위치구조를 이용한 방식과 무게중심을 고려한 방식을 비교해 같을경우에만 방위 추가
def get_direction_living(x_c,y_c,window_lst,stats_frame,living_index,img,labels):
    templist = []
    living_idx_frame = pd.DataFrame(np.transpose(np.array(living_index)), columns=['x', 'y'])
    if len(window_lst) != 0:
        for window_idx in window_lst:
            w_x_c = stats_frame.loc[window_idx, 'x_c']
            w_y_c = stats_frame.loc[window_idx, 'y_c']

            if w_x_c - x_c <= 0.05 and w_x_c - x_c >= -0.05:
                dir_vector = (0.05, y_c - w_y_c)
            else:
                dir_vector = (w_x_c - x_c, y_c - w_y_c)

            angle = math.atan(dir_vector[1] / dir_vector[0])
            if dir_vector[0] < 0:
                angle_xy = (-math.cos(angle),-math.sin(angle))
            else :
                angle_xy = (math.cos(angle), math.sin(angle))

            window_living_int = pd.merge(
                pd.DataFrame(np.transpose(np.array(np.where(expand_ind(img, labels, window_idx, 30) >= 250))),
                             columns=['x', 'y']),
                living_idx_frame, 'inner', ['x', 'y'])

            liv_x_c = window_living_int['y'].mean()
            liv_y_c = window_living_int['x'].mean()
            if w_x_c - liv_x_c <= 0.05 and w_x_c - liv_x_c >= -0.05:
                new_dir_vector = (0.05, liv_y_c - w_y_c)
            else:
                new_dir_vector = (w_x_c - liv_x_c, liv_y_c - w_y_c)
            new_angle = math.atan(new_dir_vector[1] / new_dir_vector[0])
            if new_dir_vector[0] < 0:
                new_angle_xy  = (-math.cos(new_angle),-math.sin(new_angle))
            else :
                new_angle_xy = (math.cos(new_angle), math.sin(new_angle))

            angle = angle*180/np.pi
            new_angle = new_angle * 180 / np.pi
            if angle_xy[0] < 0:
                angle = angle + 180
            elif angle_xy[1] < 0:
                angle = angle + 360

            if new_angle_xy[0] < 0:
                new_angle = new_angle + 180
            elif new_angle_xy[1] < 0:
                new_angle = new_angle + 360

            if dir_angle(angle) == dir_angle(new_angle):
                templist.append(dir_angle(angle))

    return templist







def calc_img_pixel(img,store_url):
    img2 = np.zeros_like(img)
    # 그레이 스케일과 바이너리 스케일 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))

    erosion = cv2.erode(th, k)
    th = erosion.copy()

    # 연결된 요소 레이블링 적용 ---①
    cnt, labels, stats = connectcomponent(img, th, img2, 8)

    for i in range(cnt):
        img2[labels == i] = stats[['blue', 'green', 'red']].iloc[i].to_list()

    backg_ind = 1
    line_ind = stats[stats.mean_pix <= 127].area.idxmax()
    stats_real = stats.loc[stats.index.delete([backg_ind, line_ind])]
    tough_space = stats_real[
        (stats_real[['blue', 'green', 'red']].max(axis=1) - stats_real[['blue', 'green', 'red']].min(axis=1) <= 8) &
        (stats_real.area >= stats_real.area.sum() * 0.01)]

    stats_real = stats_real[
        (stats_real[['blue', 'green', 'red']].max(axis=1) - stats_real[['blue', 'green', 'red']].min(axis=1) >= 8) &
        (stats_real.area >= 240)]


    stats_ind = room_classification(stats_real)
    living_frame = stats_real.loc[stats_ind[0]]
    restroom_frame = stats_real.loc[stats_ind[1]]
    balchony_frame = stats_real.loc[stats_ind[2]]
    room_frame = stats_real.loc[stats_ind[3]]
    room_frame['window'] = ''

    balchony_frame = balchony_frame[balchony_frame.area >= 500]
    room_frame = room_frame[room_frame.area >= 500]
    stats_real = stats_real.loc[list(living_frame.index) + list(restroom_frame.index) + list(balchony_frame.index) + list(room_frame.index)]



    backg_expand_ind = list([backg_ind] + list(balchony_frame.index))
    backg_expand = expand_ind(img2,labels, backg_expand_ind, 13)
    if len(room_frame.index) != 0:
        for room_ind in room_frame.index:
            room1_expand = expand_ind(img2, labels,[room_ind], 13)

            intersection_ind = np.where((backg_expand > 250) & (room1_expand > 250))
            nonin_ind = np.where((backg_expand <= 250) | (room1_expand <= 250))

            window_mat = set(labels[intersection_ind]) - set(backg_expand_ind + [line_ind] + list(stats_real.index))

            room_frame.at[room_ind, 'window'] = list(window_mat)

    living_img = img.copy()
    living_img = living_img.astype(np.int32)
    living_ind = np.where(
        (living_img[:, :, 1] - living_img[:, :, 0] >= 35) & (living_img[:, :, 2] - living_img[:, :, 1] >= 35))
    living_img[np.where(((living_img[:, :, 1] - living_img[:, :, 0] >= 35) & (
                living_img[:, :, 2] - living_img[:, :, 1] >= 35)) == False)] = [0, 0, 0]

    living_img = living_img.astype(np.uint8)

    living_expand = living_img.copy()

    living_expand[living_ind] = [255, 255, 255]
    k1 = cv2.getStructuringElement(cv2.MORPH_RECT, (6, 6))
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
    # 팽창 연산 적용 ---②
    living_expand = cv2.erode(living_expand, k1)
    living_expand = np.mean(cv2.dilate(living_expand, k), axis=2)

    intersection_ind = np.where((backg_expand > 250) & (living_expand > 250))
    nonin_ind = np.where((backg_expand <= 250) | (living_expand <= 250))
    living_window_mat = set(labels[intersection_ind]) - set(backg_expand_ind + [line_ind])
    living_window_mat1 = living_window_mat.copy()


    hy_ind = np.where((labels == labels[templatemat(img)]) &
                       (living_expand < 100))

    #########################################################################################################


    living_window_mat = living_window_mat - set(stats_real.index) - set(sum(room_frame.window.to_list(),[]))
    living_window_mat_stat = stats.loc[list(living_window_mat)]
    living_window_mat = set(living_window_mat_stat[(living_window_mat_stat.area >= 10) & (living_window_mat_stat.area <= 1000)].index)


    gray_downs = gray.copy()
    _, th_downs = cv2.threshold(gray_downs, 150, 255, cv2.THRESH_BINARY)

    cnt1, label1, stats1 = connectcomponent(img, th_downs, np.zeros_like(th_downs), 8)
    rest_label = set(
        label1[tuple((restroom_frame['y_c'].astype(int).values, restroom_frame['x_c'].astype(int).values))])
    rest_label = stats1.loc[list(rest_label)]
    if 0 in list(rest_label.index) or 1 in list(rest_label.index):
        stats1 = stats1.loc[stats1.index.delete([0, 1])]
        stats1 = stats1[
            (stats1[['blue', 'green', 'red']].max(axis=1) - stats1[['blue', 'green', 'red']].min(axis=1) >= 7.4) &
            (stats1.area >= 240)]
        rest_label = stats1[stats1[['blue', 'green', 'red']].max(axis=1) == stats1.blue]

    ###화장실 정보 이용 문 면적 찾기
    if len(rest_label) != 0:
        list_label = np.where(np.isin(label1, list(rest_label.index)))
        door_lst = set(labels[list_label]) - set(
            [backg_ind, line_ind] + list(tough_space.index) + list(balchony_frame.index)
            + list(restroom_frame.index))
        door_lst = stats.loc[list(door_lst)]
        door_lst = door_lst[door_lst.area >= 10].sort_values('area')

        door_lst['val_data'] = door_lst['area'] / (door_lst['width'] * door_lst['height'])
        door_lst = door_lst[(door_lst.val_data <= 0.82) & (door_lst.val_data >= 0.76)]
        if len(door_lst) != 0:
            door_area = max(max(door_lst.area),1000)
        else :
            door_area = 600
    else :
        door_area = 600


    room_frame['area'] = room_frame['area'] + door_area

    #########################################################################################################
    # rest_label,balchony_frame,room_frame
    if len(restroom_frame) >= 0:
        restroom_total_area = stats.loc[
            list((set(labels[np.where(expand_ind(img, labels, list(restroom_frame.index), 7) >= 250)])
                 - set([0, 1]) - set(stats_real.index)))]


        restroom_total_area = restroom_total_area[restroom_total_area.area <= 15000]
        restroom_total_area = stats.loc[list(set(list(restroom_total_area.index) + list(restroom_frame.index)))].area.sum()


    else:
        restroom_total_area = 0

    total_size = stats.loc[stats.index.delete([backg_ind, line_ind] + list(tough_space.index) + list(balchony_frame.index))].area.sum()
    #total_size = living_frame.area_sum() + room_frame.area.sum() + rest_label.area.sum()
    total_size = total_size + max((len(living_ind[0]) - living_frame.area.sum()), 0)




    if len(room_frame) != 0:
        room_frame['idx'] = room_frame.index
        room_frame['direction_real'] = room_frame[['x_c', 'y_c', 'window','idx']].apply(
            lambda x: list(set(det_direction_living1(x[0], x[1], x[2], stats,np.where(labels == x[3]),img,labels))), axis=1)

        room_frame['direction'] = room_frame[['x_c', 'y_c', 'window']].apply(
            lambda x: det_direction(x[0], x[1], x[2], stats), axis=1)
    room_frame['area_rate'] = room_frame['area'] / total_size
    balchony_frame['area_rate'] = balchony_frame['area'] / total_size
    #bathroom_frame = restroom_frame.copy()
    bathroom_frame = rest_label.copy()
    bathroom_frame['area'] = bathroom_frame.index.map(lambda x : len(np.where((np.isin(labels,list(living_frame.index) +
                                                                                   list(balchony_frame.index) +
                                                                                   list(tough_space.index) +
                                                                                   list(room_frame.index)) == False)
                                                                          & (label1 == x))[0]))
    bathroom_frame['area_rate'] = bathroom_frame['area'] / total_size
    living_frame['area_rate'] = living_frame['area'] / total_size

    room_frame.to_csv(store_url + '_room_frame.csv',encoding = 'utf-8-sig')
    balchony_frame.to_csv(store_url + '_balchony_frame.csv',encoding = 'utf-8-sig')
    bathroom_frame.to_csv(store_url + 'bathroom_frame.csv',encoding = 'utf-8-sig')
    living_frame.to_csv(store_url + 'living_frame.csv',encoding = 'utf-8-sig')

    living_y_c, living_x_c = [x.mean() for x in living_ind]
    living_direction_lst = set(get_direction_living(living_x_c, living_y_c, living_window_mat1, stats,living_ind,img,labels))
    living_direction_real_lst = set(get_direction_living(living_x_c, living_y_c, living_window_mat, stats,living_ind,img,labels))


    living_dict = {'total_area': total_size, 'living_area': len(living_ind[0]) / total_size,
                   'living_direction': str(living_direction_lst),'living_direction_real': str(living_direction_real_lst),
                   'window_size': len(living_window_mat),'hy_size':len(hy_ind[0]),
                   'restroom_total_area' : restroom_total_area / total_size}

    return living_dict




def calcstore(folder_lsts):
    file_nm_lst = [re.sub('\.jpg', '', re.split('/', x)[-1]) for x in folder_lsts]
    starttime = time.time()
    templist = []
    for i, file_url in enumerate(folder_lsts):
        try:
            img = cv2.imdecode(np.fromfile(file_url, np.uint8), cv2.IMREAD_COLOR)
            living_dict = calc_img_pixel(img, str_dir + '/' + file_nm_lst[i])
            living_dict.update({'apt_seq' : file_nm_lst[i]})
        except Exception as e:
            print(file_nm_lst[i] + ' : ' + str(e))
            continue
        else:
            templist.append(living_dict)
        if i % 1000 == 0:
            print(str(i) + 'th success!!')
            print(time.time() - starttime)

    tempframe = pd.DataFrame(templist)
    return tempframe



############################################################################################################

if __name__ == '__main__':
    ##multiprocessing을 이용해 병렬계산하지 않을 시 시간 소모
    str_dir = ''
    blueprint_dir = ''
    folder_lst = sum([[blueprint_dir + '/' + x + '/' + y for y in os.listdir(blueprint_dir + '/' + x)
                       if os.path.isfile(blueprint_dir + '/' + x + '/' + y)]
                      for x in os.listdir(blueprint_dir) if
                      x != 'tutorial-env' and os.path.isdir(blueprint_dir + '/' + x)], [])

    n = int(len(folder_lst) / 32) - 1
    lsts = [folder_lst[i:i + n] for i in range(0, len(folder_lst), n)]
    mp.set_start_method('fork')
    print(n)
    print(len(folder_lst))
    pool = mp.Pool(16)
    pooldata_lst = list(pool.map(calcstore, lsts))
    pooldata_frame = pd.concat(pooldata_lst, axis=0)
    pooldata_frame.to_csv(r'blueprint_living_data.csv', encoding='utf-8-sig')
    # pooldata = pooldata[['apt_seq','total_area','living_area','living_direction','living_direction_real','window_size','hy_size','restroom_total_area']]
    # db('local').insertData('db_name',10000,pooldata1)

############################################################################################################

