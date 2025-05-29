# app.py (네이버 API 버전)
import os
import json
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Render에 설정할 새로운 환경 변수
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')

# 예시 좌표 (경도,위도 순서)
STATION_COORDS = {
    '222': '127.02761,37.49794', # 강남역
    '216': '127.10022,37.51336'  # 잠실역
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search_route')
def search_route():
    start_station_id = request.args.get('start_station')
    end_station_id = request.args.get('end_station')

    if not start_station_id or not end_station_id:
        return "출발역과 도착역 ID를 모두 입력해주세요."

    # 좌표 가져오기
    start_coords = STATION_COORDS.get(start_station_id)
    end_coords = STATION_COORDS.get(end_station_id)
    
    if not start_coords or not end_coords:
        return f"좌표를 찾을 수 없는 역 ID가 포함되어 있습니다: {start_station_id}, {end_station_id}"

    # 네이버 대중교통 길찾기 API URL
    api_url = f"https://naveropenapi.apigw.ntruss.com/map-direction/v1/transit"
    
    # 요청 파라미터 및 헤더 설정
    params = {
        'start': start_coords,
        'goal': end_coords
    }
    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET
    }

    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0: # 네이버 API는 code 0이 성공
             return f"API 오류가 발생했습니다: {data.get('message')}"
        
        # 첫 번째 경로를 결과로 사용
        path_data = data.get('route', {}).get('trafast', [])[0]

        return render_template('result_naver.html', path_data=path_data)

    except requests.exceptions.RequestException as e:
        return f"API 서버에 연결하는 중 오류가 발생했습니다: {e}"

# 로컬 테스트용
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)