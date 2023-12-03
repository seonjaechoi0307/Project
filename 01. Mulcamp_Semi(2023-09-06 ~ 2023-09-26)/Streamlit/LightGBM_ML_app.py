# -*- coding:utf-8 -*-

import streamlit as st
import pandas as pd
import folium
import numpy as np
import requests
from streamlit_folium import st_folium
import os
import requests
import json
import re
from math import radians, sin, cos, sqrt, atan2
import datetime
import lightgbm as lgb
import joblib
import xgboost as xgb

# -------------------- 전역변수 세팅파트 -------------------- #

# 자치구 필터링할 데이터 프레임 불러오기
School_df = pd.read_csv('./data/School.csv')
University_df = pd.read_csv('./data/University.csv')
Subway_df = pd.read_csv('./data/서울지하철주소종합.csv')

# -------------------- 함수관련 세팅파트 -------------------- #

# Function to calculate Haversine distance = Haversine 공식에 따라 두 좌표간의 최단거리를 구하는 함수
def haversine_distance(lat1, lon1, lat2, lon2):

    """
    lat1 및 lon1: 첫 번째 지점의 위도와 경도입니다.
    lat2 및 lon2: 두 번째 지점의 위도와 경도입니다.
    R: 지구의 반지름 (평균 반지름 6,371,000 미터)
    phi1 및 phi2: 위도를 라디안 단위로 변환한 값입니다.
    delta_phi 및 delta_lambda: 위도와 경도의 차이를 라디안 단위로 표현한 값입니다.

    1. 두 지점의 위도 및 경도를 라디안 단위로 변환
    2. 위도와 경도의 차이를 계산
    3. Haversine 공식을 사용하여 위도와 경도 차이에 기반한 중간 값 'a' 계산
    4. 중간 값 'a'를 사용하여 최단거리 'a'를 계산합니다.
    """

    R = 6371000  # Radius of Earth in meters
    phi1 = radians(lat1)
    phi2 = radians(lat2)

    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)

    a = sin(delta_phi / 2) * sin(delta_phi / 2) + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) * sin(delta_lambda / 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c  # Distance in meters
    return distance

# 기준 좌표(위도,경도)를 기준으로 데이터 프레임에서 가장 가까운 위도, 경도값을 구하는 함수
def Find_Nearest_distance(data, lat, lng):

    # 초기 최단거리와 인덱스 설정
    min_distance = float('inf')  # 초기 최단거리를 무한대로 설정
    closest_index = -1

    # 기준 위도 경도를 주소 입력한 위도, 경도값으로 맞춰놓기
    Reference_latitude = lat
    Reference_longitude = lng

    # 반복문을 통해 데이터 프레임의 row[위도, 경도] 불러와서 최단거리 찾기
    for index, row in data.iterrows():
        infra_latitude = row['위도']
        infra_longitude = row['경도']

         # 기준 좌표(위도, 경도)와 현재 인프라(위도, 경도) 사이의 최단거리 계산
        distance = haversine_distance(Reference_latitude, Reference_longitude, infra_latitude, infra_longitude)

        # 현재의 거리가 지금까지 계산된 거리 보다 작은지 확인합니다.
        if distance < min_distance:
            
            # 최단거리 업데이트
            min_distance = distance

            # 최단거리의 인덱스 업데이트
            closest_index = index

    # 가장 가까운 위도, 경도 값
    closest_coordinates = data.iloc[closest_index]   # 가장 가까운 좌표(위도, 경도)
    closest_latitude = closest_coordinates['위도']   # 가장 가까운 위도
    closest_longitude = closest_coordinates['경도']  # 가장 가까운 경도

    return closest_latitude, closest_longitude

# 기준 좌표(위도,경도)와 가장 가까운 좌표(위도,경도)의 최단거리를 구하는 함수
def calculate_shortest_distance(data, lat, lng):

    # 가장 가까운 위도 경도 찾는 함수 불러오기 clat = 가장 가까운 위도, clng = 가장 가까운 경도
    clat, clng = Find_Nearest_distance(data, lat, lng)

    # 최단 거리 계산하는 함수를 통해 최단거리 계산 =>>> 기준 좌표를 기준으로 최단 거리 좌표와의 최단 거리 계산하기
    shortest_distance = haversine_distance(lat, lng, clat, clng)

    # 최단 거리 값 반환
    return shortest_distance

# 선택된 년, 월을 기준으로 데이터 프레임을 필터링하는 함수
def Filter_df_by_date(data, column_list, select_year, select_month):
    
    # 모델을 데이터프레임으로 변환
    df = pd.DataFrame(data)

    # 선택한 연도와 월 값으로 year와 month 컬럼의 값과 일치하는 행을 필터링
    filter_df = df[(df['Year'] == select_year) & (df['Month'] == select_month)]
    
    # 필터된 데이터 프레임에서 특정 컬럼 리스트 값들만 추출하기
    selected_columns_df = filter_df[column_list]

    # 필터된 데이터 프레임 반환
    return selected_columns_df

# -------------------- 레이아웃 관련파트 -------------------- #

# 입력값 기준으로 딕셔너리에 값 반영하는 함수
def generate_prediction_dict(address, year, month, Building_Age_option, JS_Price_option, JS_BA_option, Floor_option, add_dict):
    # Google Geocoding API 키, 분당 사용량 제한 : 100회, 일일 사용량 제한 : 1000회, 도로명 주소로 검색해야할듯.. 지번주소랑 위도 경도값 차이남
    api_key = "AIzaSyCrhAVjetsFGeMQExKGnfFhOdUyb9LQQSs"

    # API 호출
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}&language=ko"
    response = requests.get(url)

    # 응답 처리
    if response.status_code == 200:
        data = response.json()
        if data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            lat, lng = location["lat"], location["lng"]
            # print(f"주소: {address}")
            # print(f"위도: {lat}")
            # print(f"경도: {lng}")

            full_address = data["results"][0].get("formatted_address", "주소를 찾을 수 없습니다.")
            # print(f"주소: {full_address}")
            
            # 받아온 주소 값에서 "구" 텍스트를 찾아 OO구 값 받아오기
            match = re.search(r"(\w+구)", full_address)

            if match:

                Found_Name = match.group()
            
            else:
                print("일치하는 자치구 이름을 찾을 수 없습니다.")

        # 검색한 주소와 가장 가까운 주변 지하철 인프라와의 최단거리
        SD_to_Subway = calculate_shortest_distance(Subway_df, lat, lng)
        SD_to_University = calculate_shortest_distance(University_df, lat, lng)
        SD_to_School = calculate_shortest_distance(School_df, lat, lng)
        
        # 데이터 포인트 생성
        data_point = {
            'Building_Age': Building_Age_option,
            'JS_BA': JS_BA_option,
            'JS_Price': JS_Price_option,
            'Floor': Floor_option,
            'Year': year,
            'Month': month,
            # ↓ ↓ ↓ 임의 지정값 ↓ ↓ ↓ #
            # 따로 불러오는 걸로 변경함
            # 'IR': 3.5, # 3.5 고정
            # 'Population': 4000000, # 천천히 감소, 평균 값
            # 'LC_index': 100, # 등차수열 천천히 증가?
            # 'TC_index': 100, # 등차수열 천천히 증가?
            # 'SDT_index': 100, # 등차수열 천천히 증가?
            # 'Crime_Rates': 1400, # ↑↑↑ 평균 
            # ↑ ↑ ↑ 임의 지정값 ↑ ↑ ↑ #
            '위도': lat,
            '경도': lng,
            'Region_강남구': 1 if Found_Name == '강남구' else 0,
            'Region_강동구': 1 if Found_Name == '강동구' else 0,
            'Region_강북구': 1 if Found_Name == '강북구' else 0,
            'Region_강서구': 1 if Found_Name == '강서구' else 0,
            'Region_관악구': 1 if Found_Name == '관악구' else 0,
            'Region_광진구': 1 if Found_Name == '광진구' else 0,
            'Region_구로구': 1 if Found_Name == '구로구' else 0,
            'Region_금천구': 1 if Found_Name == '금천구' else 0,
            'Region_노원구': 1 if Found_Name == '노원구' else 0,
            'Region_도봉구': 1 if Found_Name == '도봉구' else 0,
            'Region_동대문구': 1 if Found_Name == '동대문구' else 0,
            'Region_동작구': 1 if Found_Name == '동작구' else 0,
            'Region_마포구': 1 if Found_Name == '마포구' else 0,
            'Region_서대문구': 1 if Found_Name == '서대문구' else 0,
            'Region_서초구': 1 if Found_Name == '서초구' else 0,
            'Region_성동구': 1 if Found_Name == '성동구' else 0,
            'Region_성북구': 1 if Found_Name == '성북구' else 0,
            'Region_송파구': 1 if Found_Name == '송파구' else 0,
            'Region_양천구': 1 if Found_Name == '양천구' else 0,
            'Region_영등포구': 1 if Found_Name == '영등포구' else 0,
            'Region_용산구': 1 if Found_Name == '용산구' else 0,
            'Region_은평구': 1 if Found_Name == '은평구' else 0,
            'Region_종로구': 1 if Found_Name == '종로구' else 0,
            'Region_중구': 1 if Found_Name == '중구' else 0,
            'Region_중랑구': 1 if Found_Name == '중랑구' else 0,
            'Shortest_Distance_to_Subway': SD_to_Subway,
            'Shortest_Distance_to_University': SD_to_University,
            'Shortest_Distance_to_School': SD_to_School
        }
        
        data_point.update(add_dict)

    return data_point

# 예측 결과를 계산하고 표시하는 함수
def calculate_dict_result(data_point, File_Name, JS_Price_option):
    user_input_values = [data_point['Floor'], data_point['Building_Age'], data_point['JS_BA'], data_point['JS_Price']]
    
    if all(value is not None for value in data_point.values()) and all(value != 0 for value in user_input_values):
        model = joblib.load('./models/' + File_Name)
        data_array = np.array(list(data_point.values()))
        data_array = data_array.reshape(1, -1)

        # 정수로 만들기 위한 소수점 0자리 까지 반올림
        predicted_value = int(np.round(model.predict(data_array), decimals=0))

        # 전세가율 계산하기
        CR_Rate = int(JS_Price_option / predicted_value * 100)
        
        # 안전성 평가
        Safety = ''
        if (CR_Rate >= 90):
            Safety = '안전성 : 매우위험'
        elif (CR_Rate >= 80):
            Safety = '안전성 : 위험'
        elif (CR_Rate >= 70):
            Safety = '안전성 : 조금 위험'
        elif (CR_Rate >= 50):
            Safety = '안전성 : 보통'
        else :
            Safety = '안전성 : 안전'

        # 숫자 구분 , 추가
        predicted_value = '{:,.0f}'.format(predicted_value)

        st.write(f'<h4>예측 결과 값 : {predicted_value}만원 / 전세가율 : {CR_Rate}% / {Safety}</h4>', unsafe_allow_html=True)

        m = folium.Map(location=[data_point['위도'], data_point['경도']], zoom_start=16)
        m.add_child(folium.LatLngPopup())
        map = st_folium(m, height=500, width=850)

    else:
        st.write('<h5>값을 전부 입력하지 않았거나 0인 값이 있으므로 예측이 불가능합니다.</h5>', unsafe_allow_html=True)

# 머신러닝 모델 레이아웃을 배치하는 함수
def ML_LightGBM_app_Layout():

    # 변수 설정
    data_point = {}
    File_Name = None
    Found_Name = None

    # 컬럼 리스트 = 데이터 프레임에서 특정 컬럼만 갖고올 때 사용함
    Cal_column_list = ['IR', 'Population', 'LC_index', 'TC_index', 'SDT_index', 'Crime_Rates']

    tab1, tab2, tab3 = st.tabs(["아파트 전세 안전성 예측", "오피스텔 전세 안전성 예측", "연립다세대 전세 안전성 예측"])

    with tab1 :
    
        with st.expander("Light GBM ML Section", expanded=True):
            
            st.write("<h4>사용 방법 안내</h4>", unsafe_allow_html=True)
            st.write("<h5>1. 좌측에 조건 값을 입력하세요.</h5>", unsafe_allow_html=True)
            st.write("<h5>2. 조건 값 입력 후 엔터를 누르세요.</h5>", unsafe_allow_html=True)
            st.write("<h5>3. 조건 값 전체 입력 시 우측에 예측 결과 값이 나옵니다.</h5>", unsafe_allow_html=True)
            st.markdown('---')

            col1, col2 = st.columns([1, 2])
            
            with col1 :

                # 사용자에게 예측값 Input 받기

                # 주소 입력
                address = st.text_input("주변 인프라를 확인할 기준 도로명 주소를 입력 후 엔터를 누르세요.", key='LightGBM_address_APT')
                # address = "서울역"

                # 날짜 입력
                input_date = st.date_input("예측하고 싶은 날짜를 선택하세요.", datetime.date(2023, 10, 1), key='LightGBM_date_APT')
                if input_date:
                    year = input_date.year
                    month = input_date.month
                    # ml_df = Filter_df_by_date(Test_df, column_list, year, month)
                else:
                    st.write("날짜를 선택하지 않았습니다.")

                # 임의 값 입력
                # step : 기본값 float 소수점 두자리, 1 = int
                Building_Age_option = st.number_input("건물 연식을 입력하세요", key='LightGBM_Building_Age_APT', step=1)
                JS_Price_option = st.number_input("계약하시는 물건의 전세 가격을 입력하세요. (단위 : 만원)", key='LightGBM_JS_Price_APT', step=1)
                JS_BA_option = st.number_input("임대 면적을 입력하세요. (단위 : 제곱미터)", key='LightGBM_JS_BA_APT', step=1)
                Floor_option = st.number_input("임대 건물의 층수를 입력하세요.", key='LightGBM_Floor_APT', step=1)

                add_dict = {
                    'Population': 376000,
                    'IR': 3.5,
                    'LC_index': 105,
                    'SDT_index': 85,
                    'Crime_Rates': 1
                }

                if (address != "") :

                    # 입력값 기준으로 딕셔너리 값 반영하는 함수 실행
                    data_point = generate_prediction_dict(address, year, month, Building_Age_option, JS_Price_option, JS_BA_option, Floor_option, add_dict)
                    # st.write(data_point) 딕셔너리 형태 및 값 파악하는 코드

                else:
                    pass

                with col2 :
                    if (address != ""):
                        
                        # 불러올 모델 파일 이름 지정
                        File_Name = '230924_APT_LightGBM_model.pkl'

                        # 딕셔너리값 기준으로 결과 나타내기
                        calculate_dict_result(data_point, File_Name, JS_Price_option)
                        
                    else:
                        st.write('<h5>주소를 입력하지 않으셨습니다. 도로명 주소를 입력해주세요.</h5>', unsafe_allow_html=True)

    with tab2 :
    
        with st.expander("Light GBM ML Section", expanded=True):
            
            st.write("<h4>사용 방법 안내</h4>", unsafe_allow_html=True)
            st.write("<h5>1. 좌측에 조건 값을 입력하세요.</h5>", unsafe_allow_html=True)
            st.write("<h5>2. 조건 값 입력 후 엔터를 누르세요.</h5>", unsafe_allow_html=True)
            st.write("<h5>3. 조건 값 전체 입력 시 우측에 예측 결과 값이 나옵니다.</h5>", unsafe_allow_html=True)
            st.markdown('---')

            col1, col2 = st.columns([1, 2])
            
            with col1 :

                # 사용자에게 예측값 Input 받기

                # 주소 입력
                address = st.text_input("주변 인프라를 확인할 기준 도로명 주소를 입력 후 엔터를 누르세요.", key='LightGBM_address_OFC')
                # address = "서울역"

                # 날짜 입력
                input_date = st.date_input("예측하고 싶은 날짜를 선택하세요.", datetime.date(2023, 10, 1), key='LightGBM_date_OFC')
                if input_date:
                    year = input_date.year
                    month = input_date.month
                    # ml_df = Filter_df_by_date(Test_df, column_list, year, month)
                else:
                    st.write("날짜를 선택하지 않았습니다.")

                # 임의 값 입력
                # step : 기본값 float 소수점 두자리, 1 = int
                Building_Age_option = st.number_input("건물 연식을 입력하세요", key='LightGBM_Building_Age_OFC', step=1)
                JS_Price_option = st.number_input("계약하시는 물건의 전세 가격을 입력하세요. (단위 : 만원)", key='LightGBM_JS_Price_OFC', step=1)
                JS_BA_option = st.number_input("임대 면적을 입력하세요. (단위 : 제곱미터)", key='LightGBM_JS_BA_OFC', step=1)
                Floor_option = st.number_input("임대 건물의 층수를 입력하세요.", key='LightGBM_Floor_OFC', step=1)

                add_dict = {
                    'Population': 376000,
                    'UR': 3.5,
                    'LC_index': 105,
                    'SDT_index': 85,
                    'HSP_index': 150,
                    'Crime_Rates': 1
                }

                if (address != "") :

                    # 입력값 기준으로 딕셔너리 값 반영하는 함수 실행
                    data_point = generate_prediction_dict(address, year, month, Building_Age_option, JS_Price_option, JS_BA_option, Floor_option, add_dict)
                    # st.write(data_point) 딕셔너리 형태 및 값 파악하는 코드

                else:
                    pass

                with col2 :
                    if (address != ""):
                        
                        # 불러올 모델 파일 이름 지정
                        File_Name = '230926_Officetel_xgb_model.pkl'

                        # 딕셔너리값 기준으로 결과 나타내기
                        calculate_dict_result(data_point, File_Name, JS_Price_option)
                        
                    else:
                        st.write('<h5>주소를 입력하지 않으셨습니다. 도로명 주소를 입력해주세요.</h5>', unsafe_allow_html=True)

    with tab3 :
    
        with st.expander("Light GBM ML Section", expanded=True):
            
            st.write("<h4>사용 방법 안내</h4>", unsafe_allow_html=True)
            st.write("<h5>1. 좌측에 조건 값을 입력하세요.</h5>", unsafe_allow_html=True)
            st.write("<h5>2. 조건 값 입력 후 엔터를 누르세요.</h5>", unsafe_allow_html=True)
            st.write("<h5>3. 조건 값 전체 입력 시 우측에 예측 결과 값이 나옵니다.</h5>", unsafe_allow_html=True)
            st.markdown('---')

            col1, col2 = st.columns([1, 2])
            
            with col1 :

                # 사용자에게 예측값 Input 받기

                # 주소 입력
                address = st.text_input("주변 인프라를 확인할 기준 도로명 주소를 입력 후 엔터를 누르세요.", key='LightGBM_address_TWN')
                # address = "서울역"

                # 날짜 입력
                input_date = st.date_input("예측하고 싶은 날짜를 선택하세요.", datetime.date(2023, 10, 1), key='LightGBM_date_TWN')
                if input_date:
                    year = input_date.year
                    month = input_date.month
                    # ml_df = Filter_df_by_date(Test_df, column_list, year, month)
                else:
                    st.write("날짜를 선택하지 않았습니다.")

                # 임의 값 입력
                # step : 기본값 float 소수점 두자리, 1 = int
                Building_Age_option = st.number_input("건물 연식을 입력하세요", key='LightGBM_Building_Age_TWN', step=1)
                JS_Price_option = st.number_input("계약하시는 물건의 전세 가격을 입력하세요. (단위 : 만원)", key='LightGBM_JS_Price_TWN', step=1)
                JS_BA_option = st.number_input("임대 면적을 입력하세요. (단위 : 제곱미터)", key='LightGBM_JS_BA_TWN', step=1)
                Floor_option = st.number_input("임대 건물의 층수를 입력하세요.", key='LightGBM_Floor_TWN', step=1)

                add_dict = {
                    'Population': 376000,
                    'IR': 3.5,
                    'UR': 2.4,
                    'LC_index': 105,
                    'SDT_index': 85,
                    'HSP_index': 150,
                    'Crime_Rates': 1
                }

                if (address != "") :

                    # 입력값 기준으로 딕셔너리 값 반영하는 함수 실행
                    data_point = generate_prediction_dict(address, year, month, Building_Age_option, JS_Price_option, JS_BA_option, Floor_option, add_dict)
                    # st.write(data_point) 딕셔너리 형태 및 값 파악하는 코드

                else:
                    pass

                with col2 :
                    if (address != ""):
                        
                        # 불러올 모델 파일 이름 지정
                        File_Name = '230924_Townhouse_LightGBM_model.pkl'

                        # 딕셔너리값 기준으로 결과 나타내기
                        calculate_dict_result(data_point, File_Name, JS_Price_option)
                        
                    else:
                        st.write('<h5>주소를 입력하지 않으셨습니다. 도로명 주소를 입력해주세요.</h5>', unsafe_allow_html=True)

    st.markdown('---')
    st.write("<h4>전세사기 예방 가이드라인</h4>", unsafe_allow_html=True)

    # 데이터 프레임 생성
    data = {
        "사이트 이름": [
            "건축행정시스템 세움터",
            "대법원인터넷 등기소",
            "홈텍스",
            "위텍스",
            "부동산거래관리시스템",
            "대법원인터넷 등기소",
            "정부24",
            "HUG(주택도시보증공사)",
            "HF(한국주택금융공사)",
            "SGI(서울보증)"
        ],
        "가이드": [
            "계약 전 → 주택상태(불법 무허가주택 여부)확인",
            "계약 전 → 선순위 권리관계 확인, 근저당 등 권리관계 확인",
            "계약 중 → 임대인 세금 체납 여부 확인",
            "계약 중 → 임대인 세금 체납 여부 확인",
            "계약 중 → 주택임대차 표준계약서 확인, 주택임대차 계약 여부 신고하기",
            "계약 중 → 등기 상 권리관계 재확인",
            "계약 후 → 전입 신고하기",
            "계약 후 → 전세보증금반환보증 보험가입",
            "계약 후 → 전세보증금반환보증 보험가입",
            "계약 후 → 전세보증금반환보증 보험가입"
        ],
        "사이트 주소": [
            "http://cloud.eais.go.kr",
            "http://www.iros.go.kr",
            "https://www.hometax.go.kr/",
            "https://www.wetax.go.kr",
            "https://rtms.molit.go.kr/",
            "http://www.iros.go.kr",
            "http://gov.kr",
            "https://www.khug.or.kr/index.jsp",
            "https://www.hf.go.kr/ko/index.do",
            "https://www.sgic.co.kr/chp/main.mvc"
        ]
    }

    df = pd.DataFrame(data)

    # 하이퍼링크 함수 정의
    def make_clickable(link):
        return f'<a href="{link}" target="_blank">{link}</a>'

    # Styler를 사용하여 스타일 및 하이퍼링크 적용
    styled_df = df.style \
        .set_properties(**{'text-align': 'Left'}) \
        .format({'사이트 주소': make_clickable})

    # 스트림릿에 렌더링
    st.write(styled_df.to_html(escape=False), unsafe_allow_html=True)