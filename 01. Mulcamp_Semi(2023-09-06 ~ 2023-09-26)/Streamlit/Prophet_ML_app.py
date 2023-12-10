# -*- coding:utf-8 -*-

import streamlit as st
import joblib
from joblib import load
import os
import pandas as pd
import pandas_ta as ta
import numpy as np
import matplotlib.pyplot as plt
from prophet import Prophet
import matplotlib.dates as mdates

# -------------------- 전역변수 관련파트 -------------------- #

selected_date = None
model_file_path = None
Data_path = './models/'
File_name = ''
loaded_model = None

# -------------------- 함수관련 세팅파트 -------------------- #

# 예측 모델 불러오는 함수
def Model_data_load():

    # 모델 파일의 전체 경로 생성
    model_file_path = os.path.join(Data_path, File_name)
    
    # 모델 불러오기
    with open(model_file_path, 'rb') as f:
        loaded_model = joblib.load(f)

    return loaded_model

# 예측 모델 예측값 표기 함수
def make_ml_app():
    global File_name, selected_date, loaded_model

    # Prophet 모델 불러오기
    loaded_model = Model_data_load()

    # st.write(loaded_model) >> 모델 이름 표기하니까 도움말이 자동으로 떠서 주석처리함

    # 미래 날짜 생성 (Prophet 모델의 예측 범위 내에서)
    future_dates = loaded_model.make_future_dataframe(periods=36, freq='MS')

    # 선택한 날짜에 대한 예측값 추출
    selected_date_prediction = loaded_model.predict(future_dates.iloc[[selected_date - 1]])

    # selected_date를 datetime 자료형으로 변환
    selected_date_prediction['ds'] = pd.to_datetime(selected_date_prediction['ds'])

    # 예측 가격을 소수점 자리 반올림하여 제거
    rounded_prediction = round(selected_date_prediction['yhat'].values[0])

    # 예측 가격을 형식화하여 숫자 단위 쉼표 추가
    formatted_prediction = '{:,.0f}'.format(rounded_prediction)

    # 예측값 출력
    return st.write(f"<h4>선택한 날짜 값({selected_date_prediction['ds'].dt.strftime('%Y-%m-%d').iloc[0]})의 예측 가격: {formatted_prediction} 만원</h4>", unsafe_allow_html=True)

# 모델의 데이터 프레임 불러오기 함수
def load_Model_df():

    # 모델 불러오기
    loaded_model = Model_data_load()

    # 미래 날짜 생성 (Prophet 모델의 예측 범위 내에서)
    future_dates = loaded_model.make_future_dataframe(periods=36, freq='MS')
    
    # 데이터 future_prices 함수에 불러와서 데이터 프레임화 시키기
    future_prices = loaded_model.predict(future_dates)
    future_prices_df = pd.DataFrame(future_prices)

    # 데이터 출력
    st.dataframe(future_prices_df)

# 모델 데이터 시각화 함수
def Model_data_Visualization():

    # 모델 불러오기
    loaded_model = Model_data_load()

    # 미래 날짜 생성 (Prophet 모델의 예측 범위 내에서)
    future_dates = loaded_model.make_future_dataframe(periods=36, freq='MS')

    # 데이터 future_prices 함수에 불러와서 데이터 프레임화 시키기
    future_prices = loaded_model.predict(future_dates)
    future_prices_df = pd.DataFrame(future_prices)

    # 'ds' 열의 값을 원하는 출력 형식('YYYY-MM-DD')으로 변환
    future_prices_df['ds'] = future_prices_df['ds'].dt.strftime('%Y-%m-%d')

    # 열 이름을 'ds'를 'Date'로, 'yhat'를 'Predicted_Price'로 변경
    future_prices_df.rename(columns={'ds': 'Date', 'yhat': 'Predicted_Price'}, inplace=True)

    # "Date" 열을 날짜 및 시간 형식으로 변환합니다 (만약 이미 날짜 형식이 아닌 경우에만).
    future_prices_df['Date'] = pd.to_datetime(future_prices_df['Date'])

    # "Date" 열에서 일(day)이 1일 (월의 첫 번째 날)인 행(row)들만 추출합니다.
    future_prices_df = future_prices_df[future_prices_df['Date'].dt.day == 1]

    # Plot Setting
    f, ax = plt.subplots(figsize=(60, 40))
    ax.plot(future_prices_df['Date'], future_prices_df['Predicted_Price'], linewidth=10)
    ax.set_xlabel('날짜', fontsize=60, labelpad=30)
    ax.set_ylabel('예측 가격', fontsize=60, labelpad=30)
    ax.set_title('월간 전세 가격 예측 그래프', fontsize=60, pad=30)
    ax.tick_params(axis='x', rotation=45)

    # 월 간격 눈금 설정
    monthly_ticks = pd.date_range(start=future_prices_df['Date'].min(), end=future_prices_df['Date'].max(), freq='MS')
    plt.xticks(monthly_ticks, [date.strftime('%Y-%m-%d') if date.month == 1 else '' for date in monthly_ticks], rotation=45, fontsize=36)

    # Y축 눈금 폰트 사이즈 설정
    ax.tick_params(axis='y', labelsize=36)

    # 4개월, 8개월, 12개월 이동평균 계산
    for monthly_ticks in [4, 8, 12]:

        # monthly_ticks 단위로 이동평균 컬럼 만들기
        ma_column = f'ma_{monthly_ticks}'
        future_prices_df[ma_column] = ta.sma(future_prices_df['Predicted_Price'], length=monthly_ticks)

    # 추세선 및 이동평균선 그리기
    ax.plot(future_prices_df['Date'], future_prices_df['trend'], linewidth=4, linestyle='--', color='red', label='Trend')
    ax.plot(future_prices_df['Date'], future_prices_df['ma_4'], linewidth=4, linestyle='--', color='green', label='ma_4개월')
    ax.plot(future_prices_df['Date'], future_prices_df['ma_8'], linewidth=4, linestyle='--', color='orange', label='ma_8개월')
    ax.plot(future_prices_df['Date'], future_prices_df['ma_12'], linewidth=4, linestyle='--', color='purple', label='ma_12개월')

    # 출력
    ax.legend(loc=2, fontsize=52) # 1=좌상단, 2=우상단, 3=좌하단, 4=우하단
    ax.grid(True)
    st.pyplot(f)

# 주식의 매도, 매수 신호 시각화 그래프인데 부동산 시장에선 의미 없을 듯 하여 제외
def Model_data_RSI(): # 일시보류
    loaded_model = Model_data_load()

    # 미래 날짜 생성 (Prophet 모델의 예측 범위 내에서)
    future_dates = loaded_model.make_future_dataframe(periods=365 * 3)

    # 데이터 all_predictions 함수에 불러와서 데이터 프레임화 시키기
    all_predictions = loaded_model.predict(future_dates)
    all_predictions_df = pd.DataFrame(all_predictions)

    # "Date" 열을 날짜 및 시간 형식으로 변환합니다 (만약 이미 날짜 형식이 아닌 경우에만).
    all_predictions_df['ds'] = pd.to_datetime(all_predictions_df['ds'])

    # "Date" 열에서 일(day)이 1일 (월의 첫 번째 날)인 행(row)들만 추출합니다.
    all_predictions_df = all_predictions_df[all_predictions_df['ds'].dt.day == 1]

    # Plot Setting
    f, ax = plt.subplots(figsize=(10, 4))
    ax.plot(all_predictions_df['rsi_14'])
    ax.axhline(y=40, color='r', linestyle='--', label='RSI 40')
    ax.axhline(y=60, color='g', linestyle='--', label='RSI 60')
    ax.axhline(y=all_predictions_df['rsi_14'].mean(), color='b', linestyle='--', label='RSI Mean')

    # x-축의 눈금(틱)을 월별 시작일을 1일 간격으로 설정
    monthly_ticks = pd.date_range(start=all_predictions_df['ds'].min(), end=all_predictions_df['ds'].max(), freq='MS')
    plt.xticks(monthly_ticks, [date.strftime('%Y-%m-%d') for date in monthly_ticks], rotation=45)

    # 상대강도지수 (RSI) 지표 계산
    all_predictions_df['rsi_14'] = ta.rsi(monthly_ticks, length=1)

    ax.set_title('상대강도지수 (RSI) 지표 계산')
    ax.set_xlabel('Date')
    ax.set_ylabel('RSI Value')

    # 출력
    ax.legend(loc=1, fontsize=12) # 1=좌상단, 2=우상단, 3=좌하단, 4=우하단
    ax.grid(True)
    st.pyplot(f)

# -------------------- 레이아웃 관련파트 -------------------- #

# 주식의 매도, 매수 신호 시각화 레이아웃인데 부동산 시장에선 의미 없을 듯 하여 제외
def RSI_Layout(): # 일시 보류
    with st.expander("Predictions_RSI_Section", expanded=False):
        
        # 레이아웃 구성
        tab1, tab2, tab3 = st.tabs(["Apart Plot", "Officetel Plot", "Townhouse Plot"])

        with tab1 :
            st.write("아파트 가격 예측 시각화")
            File_name = 'Prophet_model_230924_APT_.pkl'
            Model_data_load()

        with tab2 :
            st.write("오피스텔 가격 예측 시각화")
            File_name = 'Prophet_model_230924_OFC_.pkl'
            Model_data_load()


        with tab3 :
            st.write("타운하우스 가격 예측 시각화")
            File_name = 'Prophet_model_230924_TWN_.pkl'
            Model_data_load()

# 프로핏 모델 예측 모델 및 시각화 내용을 담은 레이아웃
def Prophet_ML_app_Layout():
    global File_name, selected_date

    with st.expander("ML_Predictions_Section", expanded=True):

        st.write("<h4>사용 방법 안내</h4>", unsafe_allow_html=True)
        st.write("<h5>예측하실 날짜를 조정하기 위해 슬라이드를 이동시키세요.</h5>", unsafe_allow_html=True)
        st.markdown('---')

        # 레이아웃 구성
        tab1, tab2, tab3 = st.tabs(["아파트", "오피스텔", "연립다세대"])

        with tab1 :
            col1, col2 = st.columns(2)
            with col1:

                st.subheader("아파트 전세 가격 예측")
                selected_date = st.select_slider("Option : Month", options=np.arange(1, 190), key="ML_APT_Slider")
                selected_date_list = [selected_date]

            with col2:
                st.subheader("모델 결과 확인")

                # 아파트 예측모델 불러오기 위한 File_name 전역 변수화
                File_name = '230924_Prophet_APT_Model.pkl'
                make_ml_app()

        with tab2 :
            col1, col2 = st.columns(2)
            with col1:

                st.subheader("오피스텔 전세 가격 예측")
                selected_date = st.select_slider("Option : Month", options=np.arange(1, 190), key="ML_OFC_Slider")
                selected_date_list = [selected_date]

            with col2:
                st.subheader("모델 결과 확인")

                # 오피스텔 예측모델 불러오기 위한 File_name 전역 변수화
                File_name = '230924_Prophet_Officetel_Model.pkl'
                make_ml_app()

        with tab3 :
            col1, col2 = st.columns(2)
            with col1:
                

                st.subheader("타운하우스 전세 가격 예측")
                selected_date = st.select_slider("Option : Month", options=np.arange(1, 190), key="ML_TWN_Slider")
                selected_date_list = [selected_date]

            with col2:
                st.subheader("모델 결과 확인")

                # 타운하우스 예측모델 불러오기 위한 File_name 전역 변수화
                File_name = '230924_Prophet_Townhouse_Model.pkl'
                make_ml_app()

    # 2023-12-09 예측 모델 데이터 프레임 주석 처리
    # with st.expander("Model_DataFrame_Section", expanded=False):

    #     # 레이아웃 구성
    #     tab1, tab2, tab3 = st.tabs(["아파트 데이터 프레임", "오피스텔 데이터 프레임", "연립다세대 데이터 프레임"])

    #     with tab1 :
    #         File_name = '230924_Prophet_APT_Model.pkl'
    #         load_Model_df()

    #     with tab2 :
    #         File_name = '230924_Prophet_Officetel_Model.pkl'
    #         load_Model_df()

    #     with tab3 :
    #         File_name = '230924_Prophet_Townhouse_Model.pkl'
    #         load_Model_df()
        
    # with st.expander("Visualize_Predictions_Section", expanded=True):
        
    #     # 레이아웃 구성
    #     tab1, tab2, tab3 = st.tabs(["아파트 그래프", "오피스텔 그래프", "연립다세대 그래프"])

    #     with tab1 :
    #         st.write("아파트 전세 가격 예측 시각화")
    #         File_name = '230924_Prophet_APT_Model.pkl'
    #         Model_data_load()
    #         Model_data_Visualization()

    #     with tab2 :
    #         st.write("오피스텔 전세 가격 예측 시각화")
    #         File_name = '230924_Prophet_Officetel_Model.pkl'
    #         Model_data_load()
    #         Model_data_Visualization()

    #     with tab3 :
    #         st.write("타운하우스 전세 가격 예측 시각화")
    #         File_name = '230924_Prophet_Townhouse_Model.pkl'
    #         Model_data_load()
    #         Model_data_Visualization()

