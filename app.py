import os
import json
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Render에 설정한 네이버 API 키
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')

# 장소 이름을 좌표로 변환하는 함수 (네이버 지오코딩 API 사용)
def get_coords_from_name(station_name):
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("API 키가 설정되지 않았습니다.")
        return None

    # 네이버 지오코딩 API v2 엔드포인트 주소로 수정
    geocode_url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode" # <--- 버전 'v2'로 변경!
    
    params = {'query': station_name}
    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET
    }
    
    try:
        response = requests.get(geocode_url, params=params, headers=headers)
        response.raise_for_status() 
        data = response.json()
        
        # v2 응답 형식에 맞게 수정 (응답 상태 코드 'status'와 주소 목록 'addresses' 확인)
        if data.get('status') == 'OK' and data.get('addresses') and len(data['addresses']) > 0:
            # 첫 번째 주소 정보의 x(경도), y(위도) 값을 사용
            x = data['addresses'][0]['x'] 
            y = data['addresses'][0]['y'] 
            return f"{x},{y}"
    except requests.exceptions.HTTPError as http_err:
        print(f"지오코딩 API HTTP 오류: {http_err} - 응답: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"지오코딩 API 요청 오류: {e}")
    except KeyError as e:
        print(f"지오코딩 API 응답 파싱 오류: 키 {e}를 찾을 수 없음 - 응답: {data}")
    except IndexError:
        print(f"지오코딩 API 응답 파싱 오류: 'addresses' 리스트가 비어있거나 형식이 다름 - 응답: {data}")
        
    return None

@app.route('/')
def index():
    """메인 페이지, 검색 폼을 보여줍니다."""
    return render_template('index.html')

@app.route('/search_route')
def search_route():
    """경로 검색 결과를 처리하고 보여줍니다."""
    start_station_name = request.args.get('start_station_name')
    end_station_name = request.args.get('end_station_name')

    if not start_station_name or not end_station_name:
        return "출발역과 도착역 이름을 모두 입력해주세요."

    # 입력받은 역 이름을 좌표로 변환
    start_coords = get_coords_from_name(start_station_name)
    end_coords = get_coords_from_name(end_station_name)
    
    if not start_coords:
        return f"출발역 '{start_station_name}'의 좌표를 찾을 수 없습니다. 역 이름을 확인해주세요."
    if not end_coords:
        return f"도착역 '{end_station_name}'의 좌표를 찾을 수 없습니다. 역 이름을 확인해주세요."

    # 네이버 대중교통 길찾기 API URL
    directions_url = "https://naveropenapi.apigw.ntruss.com/map-direction/v1/transit"
    
    params = {
        'start': start_coords,
        'goal': end_coords
    }
    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET
    }

    try:
        response = requests.get(directions_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0: # 네이버 API는 code 0이 성공
             return f"길찾기 API 오류가 발생했습니다: {data.get('message', '알 수 없는 오류')}"
        
        # 첫 번째 추천 경로를 결과로 사용
        path_data = data.get('route', {}).get('trafast', [])[0] if data.get('route', {}).get('trafast') else None

        if not path_data:
            return "추천 경로를 찾지 못했습니다. 입력한 역 간의 대중교통 경로가 없거나 API 응답에 문제가 있을 수 있습니다."

        return render_template('result_naver.html', 
                               start_name=start_station_name, 
                               end_name=end_station_name, 
                               path_data=path_data)

    except requests.exceptions.RequestException as e:
        return f"길찾기 API 서버에 연결하는 중 오류가 발생했습니다: {e}"
    except Exception as e:
        print(f"알 수 없는 오류 발생: {e}") # 상세 로깅
        return "경로를 검색하는 중 알 수 없는 오류가 발생했습니다."


if __name__ == '__main__':
    # 로컬 테스트 시 환경 변수 설정 (실제 배포 시에는 Render 대시보드에서 설정)
    # os.environ['NAVER_CLIENT_ID'] = 'YOUR_LOCAL_NAVER_CLIENT_ID'
    # os.environ['NAVER_CLIENT_SECRET'] = 'YOUR_LOCAL_NAVER_CLIENT_SECRET'
    app.run(host='0.0.0.0', port=10000, debug=True)
