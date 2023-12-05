----------------------------------------------------------------
파일목록
----------------------------------------------------------------
djangoProject
- 매일적재되는 공인중개사 리스트 조회 rest api
- 특정 공인중개사 존재유무 체크 api(realtorapi_specific_check)

chopuma_yn.py
- 도로망데이터와 위경도좌표를 이용해 초품아(초등학교를 품은 단지) 유무를 추정하는 모듈

geo_util_jh.py
- 위경도 등 위치정보,거리 등 추출 및 계산을 위한 모듈 모음

gpt_review_jh.py
- 주어진 문자열에 대한 gpt 답변을 받는 모듈

green_rate_shp.py
- 특정 위치 기준 반경 1km구간의 녹지율을 계산하기 위한 소스

p_blueprint.py
- opencv를 이용해 평면도 img 파일에서 방,거실 등 주요 공간의 면적, 채광 방향 등을 추출하는 소스

python_Db_jh_new.py
- mysql 데이터를 파이썬 데이터프레임으로 다루기 위해 만든 모듈 모음

slack_log_jh.py
- 파이썬으로 slack bot을 다루기 위해 생성한 모듈(주로 에러로그 실시간 확인을 위해 많이 사용)
  
update_aptnm_elasticsearch.py
- 검색에 활용되는 단지명을 elasticsearch server에 추가 / 업데이트 할 때 사용
- 실시간 데이터반영이 필요하지 않은 경우 사용
- 실시간반영이 필요한 경우 logstash를 mysql과 연동해 사용

elasticsearch_setting.txt
- elasticsearch 인덱스 세팅 json에 주석 추가
- #주석 제거 후 사용

