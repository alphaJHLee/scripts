import pandas as pd
import pymysql
import numpy as np
import os
import re
import math
import numpy as np
import numbers
#비즈니스로직 모듈
from idodb_class import DbCon as db_conn
from urllib.parse import urlencode, unquote_plus
import requests
from slack_log_jh import slack_message


#로컬서버/테스트서버/운영서버로 나누어 connection 정의
class DbCon:

    def __init__(self, type):
        if type == 'local':
             self.conn = db_conn.connObjectCall('l')
        elif type == 'test':
            self.conn = db_conn.connObjectCall('t')
        elif type == 'real':
            self.conn = db_conn.connObjectCall('r')
        else:
            self.conn = db_conn.connObjectCall('l')


    def insertData(self,tableNm,insert_num,dataframe):
        conn = self.conn
        cur = conn.cursor(pymysql.cursors.DictCursor)

        df = dataframe

        df = df.fillna(np.nan).replace({np.nan: None})

        dropDuplicates_df = df.drop_duplicates()
        columns = dropDuplicates_df.columns
        df_values = dropDuplicates_df.values
        sql = '(' + '%s, ' * len(columns) + 'now())'

        for num in range(0, len(df_values), insert_num):
            val = df_values[num:num + insert_num].tolist()
            try:
                insert_sql = 'INSERT INTO ' + tableNm + ' VALUES ' + (sql + ', ') * (len(val) - 1) + (sql + ';')
                val = sum(val, [])
                cur.execute(insert_sql, val)
            except Exception as e:
                print('error: ', e, '\n')
                slack_message('real_news_log','insert_error : %s \n%s' %(tableNm,str(e)))
            else:
                conn.commit()
                print('success!\n')

        cur.close()
        conn.close()

        return print('finish insertData function!\n')





#키컬럼 하나를 기준으로 업데이트 할 때 사용
    def updateData(self,tableNm, update_num, dataframe, col_nm, pk):
        df = dataframe[dataframe[col_nm].notna()]
        df = df.astype('str')  # df = df.astype({'apt_seq': 'str', 'x': 'str', 'y': 'str'})
        conn = self.conn
        cur = conn.cursor(pymysql.cursors.DictCursor)

        for num in range(0, len(df), update_num):
            time_val = df[[pk, col_nm]].values[num:num + update_num].tolist()
            val = time_val

            apt_seq = tuple(set(df[pk].values[num:num + update_num].tolist()))
            if len(apt_seq) == 1:
                apt_seq = re.sub(',\)',')',str(apt_seq))

            try:

                update_sql = 'update ' + tableNm + ' set ' \
                             + col_nm + ' = (case ' + ('when '+pk+' = %s then %s ') * len(time_val) + 'end) ' \
                                                                                                     'where '+ pk+ ' in ' + str(
                    apt_seq) + ';'

                val = sum(val, [])
                
                cur.execute(update_sql, val)

            except Exception as e:
                print('error: ', e, '\n')
                slack_message('real_news_log', 'update_error : %s / %s \n%s' % (tableNm,col_nm, str(e)))

            else:
                conn.commit()
                print(num + update_num, '번째 success!\n')

        cur.close()
        conn.close()

        return print('finish insertData function!\n')

#raw쿼리로 select문 작성 시 결과를 pd.DataFrame으로 변환
    def extractCodeDf(self,query):
        # query = re.sub(',\)',')',query)
        conn = self.conn
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(query)
        rows = cur.fetchall()  # 이후 1000건씩 진행
        df = pd.DataFrame(rows)
        if len(df) == 0:
            df = pd.DataFrame(rows,columns = [x[0] for x in cur.description])
        cur.close()
        conn.close()
        return df

#rawquery 실행
    def excuteDf(self,query):
        #query = re.sub(',\)',')',query)
        conn = self.conn
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(query)

        conn.commit()
        conn.close()
        return print('sql excuted!!')


#insert 과정에서 reg_date를 추가할 필요 없을 때 사용
    def insertData_noreg(self,tableNm,insert_num,dataframe):
        conn = self.conn
        cur = conn.cursor(pymysql.cursors.DictCursor)

        df = dataframe

        df = df.fillna(np.nan).replace({np.nan: None})

        dropDuplicates_df = df.drop_duplicates()
        columns = dropDuplicates_df.columns
        df_values = dropDuplicates_df.values
        sql = '(' + '%s, ' * (len(columns)-1) + '%s)'

        for num in range(0, len(df_values), insert_num):
            val = df_values[num:num + insert_num].tolist()
            try:
                insert_sql = 'INSERT INTO ' + tableNm + ' VALUES ' + (sql + ', ') * (len(val) - 1) + (sql + ';')
                val = sum(val, [])
                cur.execute(insert_sql, val)
            except Exception as e:
                print('error: ', e, '\n')
                slack_message('real_news_log', 'insert_error : %s \n%s' % (tableNm, str(e)))
            else:
                conn.commit()
                print('success!\n')

        cur.close()
        conn.close()

        return print('finish insertData function!\n')


#키컬럼 두개를 사용한 업데이트 쿼리 실행이 필요할 때 사용
    def updateDataDouble(self,tableNm, update_num, dataframe,key_list, col_nm):
        col1,col2 = tuple(key_list)
        df = dataframe[dataframe[col_nm].notna()]
        df = df.astype('str')  # df = df.astype({'apt_seq': 'str', 'x': 'str', 'y': 'str'})
        df_aptseq = list(set(df.apt_seq.to_list()))
        conn = self.conn
        cur = conn.cursor(pymysql.cursors.DictCursor)

        for num in range(0, len(df_aptseq), update_num):
            time_val = df[df.apt_seq.isin(df_aptseq[num:num + update_num])].loc[:,
                       [col1, col2, col_nm]].values.tolist()
            val = time_val

            apt_seq = tuple(df_aptseq[num:num + update_num])
            if len(apt_seq) == 1:
                apt_seq = re.sub(',\)',')',str(apt_seq))

            try:
                update_sql = 'update ' + tableNm + ' set ' \
                             + col_nm + ' = (case ' + 'when +' + col1 + '+ = %s and '+col2+' = %s then %s ' * len(
                    time_val) + 'end) ' \
                             + 'where '+col1+' in ' + str(apt_seq) + ';'

                val = sum(val, [])
                cur.execute(update_sql, val)

            except Exception as e:
                print('error: ', e, '\n')
                slack_message('real_news_log', 'update_error : %s / %s \n%s' % (tableNm, col_nm, str(e)))

            else:
                conn.commit()
                print(num + update_num, '번째 success!\n')

        cur.close()
        conn.close()

        return print('finish insertData function!\n')

#비즈니스로직(report_테이블 업데이트 전용)
    def updateData_grade(self,tableNm, update_num, dataframe, col_nm):
        df = dataframe
        df = df.astype('str')  # df = df.astype({'apt_seq': 'str', 'x': 'str', 'y': 'str'})
        conn = self.conn
        cur = conn.cursor(pymysql.cursors.DictCursor)

        for num in range(0, len(df), update_num):
            time_val = df[['apt_seq', 'item']].values[num:num + update_num].tolist()
            grade_val = df[['apt_seq', 'grade']].values[num:num + update_num].tolist()
            score_val = df[['apt_seq', 'score']].values[num:num + update_num].tolist()
            val = time_val + grade_val + score_val

            apt_seq = tuple(df['apt_seq'].values[num:num + update_num].tolist())
            if len(apt_seq) == 1:
                apt_seq = re.sub(',\)',')',str(apt_seq))

            try:
                update_sql = 'update ' + tableNm + ' set ' \
                             + col_nm + '_num = (case apt_seq ' + 'when %s then %s ' * len(time_val) + 'end), ' \
                             + col_nm + '_grade = (case apt_seq ' + 'when %s then %s ' * len(grade_val) + 'end), ' \
                             + col_nm + '_score = (case apt_seq ' + 'when %s then %s ' * len(score_val) + 'end) ' \
                                                                                                          'where apt_seq in ' + str(
                    apt_seq) + ';'

                val = sum(val, [])
                cur.execute(update_sql, val)

            except Exception as e:
                slack_message('real_news_log', 'update_error : %s / %s \n%s' % (tableNm, col_nm, str(e)))
                print('error: ', e, '\n')

            else:
                conn.commit()
                print(num + update_num, '번째 success!\n')

        cur.close()
        conn.close()

        return print('finish insertData function!\n')

#테이블 존재유무 확인용
    def IsExistsTable(self,Schema,tableNm):
        conn = self.conn
        cur = conn.cursor(pymysql.cursors.DictCursor)
        query = '''SELECT TABLE_NAME FROM information_schema.TABLES where TABLE_SCHEMA = %s and TABLE_NAME = %s;'''
        cur.execute(query, [Schema,tableNm])
        rows = cur.fetchall()  # 이후 1000건씩 진행
        cur.close()
        conn.close()
        return bool(rows)


#서버간 테이블 복사
def copy_table(from_server,from_db_nm,from_table_name,to_server,to_db_nm,to_table_nm,n):
    if DbCon(to_server).IsExistsTable(to_db_nm,to_table_nm) == False:
        create_statement = DbCon(from_server).extractCodeDf('''show create table ''' + from_db_nm + '.' + from_table_name).iloc[0, 1]
        create_statement = re.sub('`' + from_table_name + '`', to_db_nm + '.' + to_table_nm, create_statement)
        DbCon(to_server).excuteDf(create_statement)

    data = DbCon(from_server).extractCodeDf('''select * from ''' + from_db_nm + '.' + from_table_name)
    if len(data) != 0:
        DbCon(to_server).excuteDf('''truncate table ''' + to_db_nm + '.' + to_table_nm)
        DbCon(to_server).insertData_noreg(to_db_nm + '.' + to_table_nm,n,data)

    return print('''copy & insert table success!!''')





#################################################################################
if __name__ == "__main__":
    #scope_test()
    print("In global scope:", 'spam')

