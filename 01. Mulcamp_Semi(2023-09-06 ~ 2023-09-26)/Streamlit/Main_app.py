# -*- coding:utf-8 -*-

import streamlit as st 
# wide mode로 페이지 설정
st.set_page_config(
    page_title = "3Team_Project",
    # 이모지 사이트 : https://www.emojiall.com/ko/emoji/
    page_icon = "🏦",
    initial_sidebar_state="expanded",
    layout="wide"
    )

import matplotlib.pyplot as plt
import requests
from streamlit_lottie import st_lottie

# 다른 어플에서 함수 호출하기
# 어플만 호출해도 함수는 사용 가능하다 하지만 유지보수 및 모든 함수 및 객체를 갖고오면 네임스페이스가 혼란스러워질 수 있다함(in Chat GPT)
from Home_app import Home_app_Layout
# from Prophet_ML_app import Prophet_ML_app_Layout
from LightGBM_ML_app import ML_LightGBM_app_Layout

# folium 관련 경고 무시
import warnings
from folium import folium

# Folium의 FutureWarning 경고 무시
warnings.simplefilter(action="ignore", category=FutureWarning)

# Font 관련 라이브러리
import matplotlib.font_manager as fm
import os

# Matplotlib에서 한글 폰트 설정
# 그래프에서 마이너스 폰트 깨지는 현상 방지
plt.rcParams['axes.unicode_minus'] = False

@st.cache_data()
def set_custom_font():
    # Custom Fonts 디렉토리 경로 설정
    font_dir = os.path.join(os.getcwd(), "Fonts")

    # Custom Fonts 디렉토리 내의 모든 폰트 파일 경로 가져오기
    font_files = fm.findSystemFonts(fontpaths=[font_dir])

    if font_files:
        # 첫 번째 폰트 파일을 사용하거나 다른 원하는 폰트를 선택하세요.
        selected_font_path = font_files[0]
        font_name = fm.FontProperties(fname=selected_font_path).get_name()

        # 폰트 매니저에 선택한 폰트 추가
        fm.fontManager.addfont(selected_font_path)

        # Matplotlib 폰트 설정
        plt.rcParams['font.family'] = font_name
        plt.rcParams['font.size'] = 12
        plt.rcParams['font.weight'] = 'semibold'

        print(f"한글 폰트 '{font_name}'이 설정되었습니다.")
    else:
        print("Fonts 디렉토리에서 사용 가능한 폰트 파일을 찾을 수 없습니다.")

# 한글 폰트 설정 함수 호출
set_custom_font()

# 로티 불러오는 함수
def load_lottieurl(url) -> dict:
    r = requests.get(url)
    if r.status_code != 200:
        return st.sidebar.error("Lottie 파일을 가져오는 데 문제가 발생했습니다.")
    return r.json()

# 함수 파트
def main():
    st.markdown("# 부동산 전세가격 예측 및 전세가율 분석")
    st.markdown("### 적정 전세가율을 활용한 전세사기 예방 웹사이트")
    # 구분선 추가
    st.markdown('---')

    with st.sidebar:
        # Sidebar animation
        lottie_url = "https://assets-v2.lottiefiles.com/a/f02fd2fc-1178-11ee-b799-df4a4787e702/cyDf6xxWfS.json"
        lottie_json = load_lottieurl(lottie_url)
        st_lottie(lottie_json, speed=0.1, height=200, key="initial", quality="low")
        st.markdown(
            "<h2 style='text-align: center; color: Black;'>Team Name : 건물주 </h2>",
            unsafe_allow_html=True,
        )
        menu = ["🏛️ 홈페이지", "💡 전세 안전성 예측", "🥇 서비스 제공자"]
        choice = st.sidebar.selectbox("Menu", menu)

    if choice == ("🏛️ 홈페이지"):
        Home_app_Layout()

    # Prophet 예측 모델 파일 손상으로 인한 주석처리
    # elif choice == "⚙️ 전세가격 예측" :
    #     st.write("<h4>Prophet 알고리즘을 활용한 전세가격 예측모델</h4>", unsafe_allow_html=True)
    #     Prophet_ML_app_Layout()

    elif choice == "💡 전세 안전성 예측" :
        st.write("<h4>Light GBM 알고리즘을 활용한 전세계약 안전성 평가모델</h4>", unsafe_allow_html=True)
        ML_LightGBM_app_Layout()

    elif choice == "🥇 서비스 제공자" :
        st.image("./image/Service_Provider_1.png")
        st.image("./image/Service_Provider_2.png")

    else :
        pass

# 메인 파트
if __name__ == "__main__" :
    main()