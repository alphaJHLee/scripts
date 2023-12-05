import os
from requests.adapters import HTTPAdapter, Retry
import requests
import json
import time
import re
import pandas as pd
from python_Db_jh import DbCon as db
from idodb_key import gpt_key,naver_local_key


session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)



#시작문구 설정
question_dict = {'general_opinion': '',
                 'traffic': '',
                 'peripheral_facility': '',
                 'complex_environment': '',
                 'living_environment': ''}



#네이버번역기
def naver_translation(string_trans):
    url = 'https://naveropenapi.apigw.ntruss.com/nmt/v1/translation'
    header = naver_local_key
    param = {'source': 'en',
             'target': 'ko',
             'text': string_trans,
             'honorific': True}

    res = requests.post(url, param, headers=header)
    try:
        json_data = json.loads(res.text)
        return json_data['message']['result']['translatedText']
    except Exception as e:
        print(string_trans)
        print(e)
        print(res.text)
        return ''


#gpt번역기
def gpt_translation(phase_string):
    url = 'https://api.openai.com/v1/chat/completions'
    header = gpt_key
    data = {"model":"gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 256,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0}

    data.update({'messages': [{'role':'user',
                               'content':'"' + re.sub('\n',' ',phase_string.strip()) + '" please translate these sentences into Korean'  + '\n'}]})
    res = requests.post(url, data=json.dumps(data), headers=header)
    try :
        print(json.loads(res.text)['choices'][0]['message']['content'])
        a = json.loads(res.text)['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(e)
        print(res.text)
        a = ''
    return a




#gpt 대화문구 도출함수
def gpt3_requests(phase_string):
    url = 'https://api.openai.com/v1/chat/completions'
    header = gpt_key
    data = {"model":"gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1024,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0}

    data.update({'messages': [{'role':'user',
                               'content':re.sub('\n', ' ', phase_string) + '\n'}]})


    for i in range(3):
        try:
            res = session.post(url, data=json.dumps(data), headers=header, timeout=(15 + i*3))
            print(json.loads(res.text))
            if 'error' in list(json.loads(res.text).keys()):
                a = 'invalid_request_error'
            else:
                a = json.loads(res.text)['choices'][0]['message']['content'].strip()
            break

        except Exception as e:
            time.sleep(8)
            if i != 2:
                pass
            else:
                print(e)
#                print(res.text)
                a = ''

    return a


#입력 텍스트 문법 가공
def review_text_proccess(stringdata):
    a = stringdata.strip()
    if bool(re.match(',', a[-1])):
        a = a[-1].strip()
    if bool(re.match(r'[.?!]',a[-1])) == False:
        a = a + '.'

    a = re.sub('  ',' ',re.sub('\n{1,100}',' ',a))
    return a.strip()








if __name__ == '__main__':

    gpt_string = gpt3_requests('hi')
    print(gpt_string)




