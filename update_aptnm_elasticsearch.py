import requests
from elasticsearch import Elasticsearch as es
from elasticsearch import helpers
from python_Db_jh import DbCon as db
import pandas as pd
import datetime
import time
from idodb_key import es_server

#es_server = {'host': hostname, 'port': 9200,"scheme": "http"}
es_connector = es([es_server])
page = es_connector.search(
    index='index_name',
    scroll = '1m',
    body={
 	"size": 500,
 	"query" : {"match_all": {}}
})
#elasticserach : index_name 리스트 가져오기
starttime = time.time()
result = []
sid = page['_scroll_id']
scroll_size = len(page['hits']['hits'])
result.extend([x['_source'] for x in page['hits']['hits']])

while (scroll_size > 0):
    page = es_connector.scroll(scroll_id=sid, scroll='2m')
    # Update the scroll ID
    sid = page['_scroll_id']
    # Get the number of results that we returned in the last scroll
    result.extend([x['_source'] for x in page['hits']['hits']])
    scroll_size = len(page['hits']['hits'])
    if len(result)  % 5000 == 0:
        print(len(result))
        print(time.time()-starttime)

resultdata = pd.DataFrame(result)
#DB상 데이터와 비교
aptnmdata = db('test').extractCodeDf('''select apt_seq,apt_nm as apt_nm_new from 
aptdata''')
resultdata1 = pd.merge(aptnmdata,resultdata,'outer','apt_seq')
##delete index(실제 지우지는 않는다) : delete /index_name/_doc/{apt_seq}
deletedata = resultdata1[resultdata1.apt_nm_new.isna()]


##insert new index
insertdata = resultdata1[resultdata1.apt_nm.isna()]
#elasticsearch 서버에 없는 단지 정보 가져오기
aptnmdata = db('test').extractCodeDf('''select apt_seq,sido,sigungu,dong,apt_nm from 
aptdata where apt_seq in ''' + str(tuple(insertdata.apt_seq.to_list())))
#단지정보 index format에 맞춰 json으로 가공
aptnmdata['nm_forsearch'] = aptnmdata.iloc[:,1:-1].apply(lambda x : (' '.join([x for x in list(x) if bool(x)])).lower(),axis=1)
aptnmdata['timestamp'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
aptnmdata['_source'] = aptnmdata.to_dict('records')
aptnmdata['_index'] = 'index_name'
aptnmdata['_id'] = aptnmdata['apt_seq']

data = aptnmdata[['_index','_id','_source']].to_dict('records')
#json데이터 벌크 insert
helpers.bulk(es_connector, data)

## change and update index
updatedata = resultdata1[(resultdata1.apt_nm.notna()) & (resultdata1.apt_nm_new.notna())]
updatedata = updatedata[updatedata.apt_nm_new != updatedata.apt_nm]
#기존 단지명에 신규 단지명 추가하기
updatedata['nm_forsearch'] = updatedata['nm_forsearch'] + ' ' + updatedata['apt_nm_new']
updatedata['apt_nm'] = updatedata['apt_nm_new']
updatedata['timestamp'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
updatedata['doc'] = updatedata[['apt_nm','nm_forsearch','timestamp']].to_dict('records')
updatedata['doc'] = updatedata[['doc']].to_dict('records')
data_update = updatedata[['apt_seq','doc']].values.tolist()
urll = 'http://%s:%s/index_name/_update/'%(es_server['host'],es_server['port'])
for kk,aptseq_inds in enumerate(data_update):
    res = requests.post(urll + aptseq_inds[0],json = aptseq_inds[1])
    if kk % 50 == 0:
        print(kk)

