# -*- coding:utf-8 -*-

# --------------- 라이브러리 설정 --------------- #

import streamlit as st
import pandas as pd
import folium
import numpy as np
import requests
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import os
import json

from geopy.distance import geodesic
from geopy.geocoders import Nominatim

# --------------- 전역 변수 설정 --------------- #

infra_df = pd.read_csv('./data/Infra.csv')

# 함수 파트

# 위도, 경도 받아오는 함수
def get_pos(lat, lng) :
    return lat, lng

# 기준 주소의 Nkm 반경의 인프라 목록을 구하는 함수
def get_nearby_infra_list(infra_df, base_lat, base_lng, radius_km):

    """
    Parameters:
        - infra_df (DataFrame): 인프라 데이터를 담고 있는 DataFrame.
        - base_lat (float): 기준 주소의 위도.
        - base_lng (float): 기준 주소의 경도.
        - radius_km (float): 반경 (킬로미터) 내에 있는 인프라를 검색할 거리.
        - distance (float): 기준 주소와 주변 인프라와의 거리

    Returns:
        - DataFrame: 반경 내에 있는 인프라 목록을 담은 DataFrame.
    """


    # 결과를 저장할 빈 리스트 설정
    infra_within_distance = []

    # 받아올 컬럼 설정
    selected_columns = ['Legion_Name', 'Name', 'Kind', 'Distance']

    # 반복문을 통한 반경 내 행값 가져오기
    for index, row in infra_df.iterrows():
        infra_lat, infra_lng = row['latitude'], row['longitude']

        # 기준 주소와 인프라의 위도, 경도를 사용하여 거리 계산
        distance = geodesic((base_lat, base_lng), (infra_lat, infra_lng)).meters

        # 거리가 반경 내에 있는 경우 결과 리스트에 추가
        if distance <= radius_km:
            row_with_distance = row.copy()
            row_with_distance['Distance'] = distance
            infra_within_distance.append(row_with_distance[selected_columns])

    # 반경 내에 인프라가 있는 경우에만 'Distance' 열을 포함한 데이터프레임을 생성
    if infra_within_distance:
        # 결과 리스트를 데이터프레임으로 변환하여 반환 // 거리를 기준으로 오름차순 정렬, 인덱스 값 초기화
        result_df = pd.DataFrame(infra_within_distance).sort_values(by='Distance').reset_index(drop=True)
        result_df['Distance'] = result_df['Distance'].round(2)
        
    elif not infra_within_distance:
        # 반경 내에 인프라가 없는 경우 빈 데이터프레임 반환
        result_df = None

    return result_df

# 기준 주소의 주변 인프라 탐색 및 데이터 프레임 레이아웃 형성 함수
def Create_Map_Layout():

    location = None  # location 변수 초기화

    col1, col2 = st.columns(2)

    with col1 :

        # 주소 입력
        address = st.text_input("주변 인프라를 확인할 기준 주소를 입력하고 엔터를 누르세요.", key='Search_infra_condition')

        if (address != ""):
            # OpenCage Geocoding API 키 // 일일 제한횟수 : 2500회
            api_key = "9b234a70713041749b360493fc572fb7"

            # API 호출 // API 발급 사이트 : https://opencagedata.com/api#rate-limiting
            url = f"https://api.opencagedata.com/geocode/v1/json?q={address}&key={api_key}"
            response = requests.get(url)

            # 응답 처리
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    location = data["results"][0]["geometry"]
                    lat, lng = location["lat"], location["lng"]

                    # Folium 지도 생성
                    m = folium.Map(location=[lat, lng], zoom_start=16)  # 해당 주소의 위도, 경도 값을 기준으로 지도 생성
                    m.add_child(folium.LatLngPopup())  # 마커 클릭 시 위도와 경도 표시
                    map = st_folium(m, height=500, width=650)
                    
                    # 사용자가 마커를 클릭한 경우 클릭한 위치의 위도, 경도 데이터를 보여줌
                    if map.get("last_clicked") :
                        data = get_pos(map["last_clicked"]["lat"], map["last_clicked"]["lng"])
                else:
                    print("주소를 찾을 수 없습니다.")
            else:
                print("API 호출에 실패했습니다.")
        else:
            pass # 입력 주소가 없으므로 Pass

    with col2 :

        # location이 None 아닐 시 아래 코드 실행
        if location is not None:

            # 기준 위도, 경도를 입력한 주소 기준으로 설정
            base_lat = location["lat"]
            base_lng = location["lng"]
        
            # 반경 3km 이내의 인프라 필터링
            Radius_meter = st.select_slider("인프라 검색 반경 (단위 : meter)", options=np.arange(1, 3001), key="Create_Map_Slider")
            infra_within_Nkm_df = get_nearby_infra_list(infra_df, base_lat, base_lng, Radius_meter)

            # 데이터 프레임 출력
            st.dataframe(infra_within_Nkm_df, width=650, height=500)
        else:
            st.write("입력 주소값이 없습니다.")

# 자치구별 인프라 베이스 맵 생성
def Create_folium_map_base(df, condition):

    # 서울 행정구역 json raw파일(githubcontent)
    r = requests.get('https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json')
    c = r.content
    seoul_geo = json.loads(c)

    # Legion_Name 밸류 카운트
    seoul_group_data = df[df["Class"] == condition]["Legion_Name"].value_counts()

    # Folium 맵 생성
    m = folium.Map(
        location=[37.559819, 126.963895],
        zoom_start=10,
        tiles='cartodbpositron'
    )

    # 지역구 경계 표시
    folium.GeoJson(
        seoul_geo,
        name='지역구'
    ).add_to(m)

    # Choropleth 레이어 추가
    m.choropleth(
        geo_data=seoul_geo,
        data=seoul_group_data,
        fill_color='YlOrRd',
        fill_opacity=0.5,
        line_opacity=0.2,
        key_on='properties.name',
        legend_name="지역구별 인프라 개수"
    )    

    # 지역구 내 인프라 위치 표시
    df = df[df['Class'] == condition]
    for index, row in df.iterrows():
        sub_lat, sub_lng = row['latitude'], row['longitude']

        # 아이콘 색상 설정
        icon_color = 'blue'
        radius = 200

        # 마커 생성 및 추가
        folium.CircleMarker(
            [sub_lat, sub_lng],
            radius=1,
            color=icon_color,
        ).add_to(m)

    return m

# 자치구별 인프라 종류 조건으로 스트림릿에 맵 표시
def Home_create_infra_map(selected_tab):

    # 선택한 탭에 따라 데이터를 렌더링하고 지도를 표시
    if selected_tab == "공원 위치정보":

        condition = 'Park'
        m = Create_folium_map_base(infra_df, condition)
        st_folium(m, height=600, width=900, key='map_1')
        
    elif selected_tab == "대학 위치정보":
        
        condition = 'College'
        m = Create_folium_map_base(infra_df, condition)
        st_folium(m, height=600, width=900, key='map_2')
        
    elif selected_tab == "지하철 위치정보":
        
        condition = 'Subway'
        m = Create_folium_map_base(infra_df, condition)
        st_folium(m, height=600, width=900, key='map_3')
        
    elif selected_tab == "학교 위치정보":
        
        condition = 'School'
        m = Create_folium_map_base(infra_df, condition)
        st_folium(m, height=600, width=900, key='map_4')

# 경기종합지수 변동추이 그래프 생성 함수
def make_chart_ECI(df):

    # Economic Composite Index : 경제 종합 지수
    # 전처리 데이터 이름 >>> df = pd.read_csv('경기종합지리_전처리완료.csv')

    # 년, 월 컬럼값 정수로 변환 및 날짜라는 컬럼에 년, 월 데이터 합친 값 넣기
    df['날짜'] = df['년'].astype(str) + '.' + df['월'].astype(str)

    plt.figure(figsize=(30, 16))
    plt.plot(df['날짜'], df['선행종합지수(2020=100)'], marker='o', label='선행종합지수', linestyle='-')  # 선 그래프 그리기
    plt.plot(df['날짜'], df['동행종합지수(2020=100)'], marker='o', label='동행종합지수', linestyle='-')
    plt.plot(df['날짜'], df['후행종합지수(2020=100)'], marker='o', label='후행종합지수', linestyle='-')

    plt.title('경기종합지수')
    plt.xlabel('날짜')

    plt.grid(True)
    plt.xticks(rotation=45)

    plt.xlim(['2011.1', '2023.7'])
    plt.legend()
    st.pyplot(plt)

# 범죄율 변동추이 그래프 생성 함수
def make_chart_CR(df):
    
    # Crime Rate : 범죄율
    # 전처리 데이터 이름 >>> df = pd.read_csv('서울시5대범죄전처리완료.csv')

    df_must = df[["년도", "자치구별", "범죄율"]]

    x = ["종로구", "중구", "용산구", "성동구", "광진구", "동대문구", "중랑구", "성북구", "강북구",
        "도봉구", "노원구", "은평구", "서대문구", "마포구", "양천구", "강서구", "구로구",  "금천구",
        "영등포구", "동작구", "관악구", "서초구", "강남구", "송파구", "강동구"]

    y1 = df_must[df_must["년도"] == 2014]["범죄율"]
    y2 = df_must[df_must["년도"] == 2015]["범죄율"]
    y3 = df_must[df_must["년도"] == 2016]["범죄율"]
    y4 = df_must[df_must["년도"] == 2017]["범죄율"]
    y5 = df_must[df_must["년도"] == 2018]["범죄율"]
    y6 = df_must[df_must["년도"] == 2019]["범죄율"]
    y7 = df_must[df_must["년도"] == 2020]["범죄율"]
    y8 = df_must[df_must["년도"] == 2021]["범죄율"]


    fig, ax = plt.subplots(figsize=(10, 6))
    plt.plot(x, y1, label='2014')
    plt.plot(x, y2, label='2015')
    plt.plot(x, y3, label='2016')
    plt.plot(x, y4, label='2017')
    plt.plot(x, y5, label='2018')
    plt.plot(x, y6, label='2019')
    plt.plot(x, y7, label='2020')
    plt.plot(x, y8, label='2021')

    plt.title('자치구별 범죄율')
    plt.xticks(rotation=80, ha='right')

    plt.xlim(['종로구', '강동구'])
    plt.ylim([500, 4000])

    plt.legend()
    plt.grid()
    st.pyplot(fig)

# 연령별 인구수 변동추이 그래프 생성 함수
def make_chart_PBA(df):
    
    # Population by age : 연령별 인구수
    # 전처리 데이터 이름 >>> df = pd.read_csv('서울_연령별_인구수_전처리.csv')

    x = ["종로구", "중구", "용산구", "성동구", "광진구", "동대문구", "중랑구", "성북구", "강북구",
        "도봉구", "노원구", "은평구", "서대문구", "마포구", "양천구", "강서구", "구로구",  "금천구",
        "영등포구", "동작구", "관악구", "서초구", "강남구", "송파구", "강동구"]

    y1 = df[(df["시점"] == 2014) & (df["행정구역(시군구)별"] != "서울특별시")]["계"]
    y2 = df[(df["시점"] == 2015) & (df["행정구역(시군구)별"] != "서울특별시")]["계"]
    y3 = df[(df["시점"] == 2016) & (df["행정구역(시군구)별"] != "서울특별시")]["계"]
    y4 = df[(df["시점"] == 2017) & (df["행정구역(시군구)별"] != "서울특별시")]["계"]
    y5 = df[(df["시점"] == 2018) & (df["행정구역(시군구)별"] != "서울특별시")]["계"]
    y6 = df[(df["시점"] == 2019) & (df["행정구역(시군구)별"] != "서울특별시")]["계"]
    y7 = df[(df["시점"] == 2020) & (df["행정구역(시군구)별"] != "서울특별시")]["계"]
    y8 = df[(df["시점"] == 2021) & (df["행정구역(시군구)별"] != "서울특별시")]["계"]
    y9 = df[(df["시점"] == 2022) & (df["행정구역(시군구)별"] != "서울특별시")]["계"]


    fig, ax = plt.subplots(figsize=(10, 6))
    plt.plot(x, y1, label='2014')
    plt.plot(x, y2, label='2015')
    plt.plot(x, y3, label='2016')
    plt.plot(x, y4, label='2017')
    plt.plot(x, y5, label='2018')
    plt.plot(x, y6, label='2019')
    plt.plot(x, y7, label='2020')
    plt.plot(x, y8, label='2021')
    plt.plot(x, y9, label='2022')

    plt.title("서울시 인구수")
    plt.xticks(rotation=45, ha='right')
    plt.xlim(['종로구', '강동구'])
    plt.legend()
    plt.grid()
    st.pyplot(fig)

# 재개발 횟수 변동추이 그래프 생성 함수
def make_chart_HR(df):
    
    # Housing Redevelopment : 주택 재개발
    # 전처리 데이터 이름 >>> df = pd.read_csv('서울주택재개발_전처리완료.csv')

    # 컬럼 분류값 만들기
    df['건립가구 (가구)_완료'] = np.where(df['건립가구 (가구)_완료'] == 0, np.nan, df['건립가구 (가구)_완료'])
    
    x = ["종로구", "중구", "용산구", "성동구", "광진구", "동대문구", "중랑구", "성북구", "강북구",
        "도봉구", "노원구", "은평구", "서대문구", "마포구", "양천구", "강서구", "구로구",  "금천구",
        "영등포구", "동작구", "관악구", "서초구", "강남구", "송파구", "강동구"]

    y1 = df[df["년"] == 2014]["건립가구 (가구)_완료"]
    y2 = df[df["년"] == 2015]["건립가구 (가구)_완료"]
    y3 = df[df["년"] == 2016]["건립가구 (가구)_완료"]
    y4 = df[df["년"] == 2017]["건립가구 (가구)_완료"]
    y5 = df[df["년"] == 2018]["건립가구 (가구)_완료"]
    y6 = df[df["년"] == 2019]["건립가구 (가구)_완료"]
    y7 = df[df["년"] == 2020]["건립가구 (가구)_완료"]
    y8 = df[df["년"] == 2021]["건립가구 (가구)_완료"]
    y9 = df[df["년"] == 2022]["건립가구 (가구)_완료"]


    fig, ax = plt.subplots(figsize=(10, 6))
    plt.scatter(x, y1, label='2014')
    plt.scatter(x, y2, label='2015')
    plt.scatter(x, y3, label='2016')
    plt.scatter(x, y4, label='2017')
    plt.scatter(x, y5, label='2018')
    plt.scatter(x, y6, label='2019')
    plt.scatter(x, y7, label='2020')
    plt.scatter(x, y8, label='2021')
    # plt.scatter(x, y9, label='2022')

    plt.xticks(rotation=80, ha='right')
    plt.legend()
    plt.grid()
    st.pyplot(fig)

# 경제성장률 및 금리 변동추이 그래프 생성 함수
def make_chart_EGR_IR(df):
    
    # Economic Growth and Interest Rates : 경제성장률 and 금리
    # 전처리 데이터 이름 >>> df = pd.read_csv('lr_uer_merged.csv')
    
    # 년, 월 컬럼값 정수로 변환 및 날짜라는 컬럼에 년, 월 데이터 합친 값 넣기
    df['년'] = df['년'].astype(int)
    df['월'] = df['월'].astype(int)
    df['날짜'] = df['년'].astype(str) + '.' + df['월'].astype(str)

    plt.figure(figsize=(30, 16))
    plt.plot(df['날짜'], df['금리'], marker='o', label='금리', linestyle='-')
    plt.plot(df['날짜'], df['실업률'], marker='o', label='실업률', linestyle='-')

    plt.title('금리와 실업률')
    plt.xlabel('날짜')
    plt.grid()
    plt.xticks(rotation=45)

    plt.xlim(['2011.1', '2023.7'])
    plt.legend()
    st.pyplot(plt)


# --------------- 최종 레이아웃 --------------- #

# 메인 화면에 표시할 레이아웃 함수
def Home_app_Layout():
    
    # 전역변수 설정
    location = None

    with st.expander("주변 인프라 탐색 구역", expanded=True):
        
        Create_Map_Layout()

    # 자치구 별 인프라 지도 생성 구역
    with st.expander("주변 인프라 탐색 구역", expanded=True):
            
        # 각 탭 선택 옵션 리스트 만들기
            tabs = ["공원 위치정보", "대학 위치정보", "지하철 위치정보", "학교 위치정보"]

            # 확인할 인프라 탭을 선택하세요.
            selected_tab = st.selectbox("확인할 인프라 지도 탭을 선택하세요.", tabs, key='infra_map_condition')

            # 선택한 인프라 탭에 따른 인프라 맵 구현
            Home_create_infra_map(selected_tab)

    with st.expander("경기변동 동향탐색 구역", expanded=True):

        tab1, tab2, tab3, tab4 = st.tabs(["경제성장률 및 금리 변동추이", "경기종합지수 변동추이", "범죄율 변동추이", "연령별 인구수 변동추이"])

        with tab1:
            # 경제성장률 및 금리
            df = pd.read_csv('./data/lr_uer_merged.csv')
            make_chart_EGR_IR(df)

        with tab2:
            # 경기종합지수
            df = pd.read_csv('./data/경기종합지리_전처리완료.csv')
            make_chart_ECI(df)

        with tab3:
            # 범죄율
            df = pd.read_csv('./data/서울시5대범죄전처리완료.csv')
            make_chart_CR(df)

        with tab4:
            # 연령별 인구수
            df = pd.read_csv('./data/서울_연령별_인구수_전처리.csv')
            make_chart_PBA(df)

        # 삭제하기로
        # with tab5:
        #     # 재개발
        #     df = pd.read_csv('./data/서울주택재개발_전처리완료.csv')
        #     make_chart_HR(df)
