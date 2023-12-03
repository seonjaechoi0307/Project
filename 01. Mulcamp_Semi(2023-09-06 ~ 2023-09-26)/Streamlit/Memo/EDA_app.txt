# -*- utf-8 -*-

# --------------- 라이브러리 설정 --------------- #

import streamlit as st
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
import numpy as np

# --------------- 함수 관련 설정 --------------- #

def plot_line_chart(x, y):
    f, ax = plt.subplots(figsize=(8, 6))
    ax.plot(x, y, marker='o', linestyle='-')
    ax.set_xlabel('X 축')
    ax.set_ylabel('Y 축')
    ax.set_title('선 그래프')
    plt.xticks(rotation=90)  # x 축 라벨을 90도 회전하여 보기 편하게 설정
    plt.tight_layout()
    st.pyplot(f)

def plot_bar_chart(x, y):
    f, ax = plt.subplots(figsize=(8, 6))
    ax.bar(x, y)
    ax.set_xlabel('X 축')
    ax.set_ylabel('Y 축')
    ax.set_title('막대 그래프')
    plt.xticks(rotation=90)  # x 축 라벨을 90도 회전하여 보기 편하게 설정
    plt.tight_layout()
    st.pyplot(f)

# Scatter 차트 그리는 함수
def plot_scatter_chart(x, y):
    f, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(x, y)
    ax.set_xlabel('X 축')
    ax.set_ylabel('Y 축')
    ax.set_title('산점도 그래프')
    plt.xticks(rotation=90)  # x 축 라벨을 90도 회전하여 보기 편하게 설정
    plt.tight_layout()
    st.pyplot(f)

# box 차트 그리는 함수
def plot_box_chart(x, y):
    f, ax = plt.subplots(figsize=(8, 6))
    sns.boxplot(x=x, y=y, ax=ax)
    ax.set_xlabel('X 축')
    ax.set_ylabel('Y 축')
    ax.set_title('박스 그래프')
    plt.xticks(rotation=90)  # x 축 라벨을 90도 회전하여 보기 편하게 설정
    plt.tight_layout()
    st.pyplot(f)

# heatmap 차트 그리는 함수
def plot_heatmap_chart(data, target_column):

    f, ax = plt.subplots(figsize=(8, 6))
    corrmat = data.corr()
    k = 10
    cols = corrmat.nlargest(k, target_column)[target_column].index
    cm = np.corrcoef(data[cols].values.T)
    
    # Seaborn 라이브러리 폰트 설정
    sns.set(font_scale=1.25)

    # 상관 관계 히트맵 그리기
    hm = sns.heatmap(cm, cbar=True, annot=True, square=True, fmt='.2f',
                     annot_kws={'size': 10}, yticklabels=cols.values,
                     xticklabels=cols.values)
    
    ax.set_title('상관관계 히트맵 그래프')
    
    plt.tight_layout()
    st.pyplot(f)

    # hm = sns.heatmap 사용 옵션 정리
    #   corrmat = data.corr() = 데이터프레임 내의 변수들 간의 상관 관계를 계산하여 상관 계수(correlation coefficient)를 행렬 형태로 저장
    #   cm: 상관 관계 행렬을 입력 데이터로 지정합니다.
    #   cbar=True: 컬러 바(색상 막대)를 표시합니다.
    #   annot=True: 각 셀에 숫자 값을 표시합니다.
    #   square=True: 히트맵을 정사각형 모양으로 표시합니다.
    #   fmt='.2f': 숫자 값의 형식을 소수점 두 자리까지 표시하도록 지정합니다.
    #   annot_kws={'size': 10}: 히트맵에 표시되는 숫자의 크기를 조절합니다.
    #   yticklabels=cols.values, xticklabels=cols.values: 히트맵의 축 라벨에 cols 변수에 저장된 컬럼명을 사용합니다.

# --------------- 최종 레이아웃 --------------- #

def EDA_app_Layout():

    st.subheader("탐색적 자료 분석 페이지")
    data = pd.read_csv("./data/month_at.csv")

    tab1, tab2, tab3 = st.tabs(["📈 Chart", "📘 Data", "📄 ETC"])

    with tab1 :
        with st.expander("Option Select Section", expanded=True) :
            col1, col2 = st.columns([1, 2])

            with col1 :
                st.markdown("<h4>옵션 선택</h4>", unsafe_allow_html=True)
                
                # 데이터 프레임의 컬럼 목록을 옵션으로 사용
                # key = 고유 세션값 (셀렉박스 연속 구현 시 오류를 방지하기 위한 고유 세션값 주기)
                options1 = data.columns.tolist()
                selected_option1 = st.selectbox("Y 컬럼을 선택하세요 : ", options1, key="SelectBox_1")

                options2 = data.columns.tolist()
                selected_option2 = st.selectbox("X 컬럼을 선택하세요 : ", options2, key="SelectBox_2")

                options3 = ['plot_line_chart', 'plot_bar_chart', 'plot_scatter_chart', 'plot_box_chart', 'plot_heatmap_chart']
                selected_option3 = st.selectbox("시각화 종류를 선택하세요 : ", options3, key="SelectBox_3")
            
            with col2 :
                st.markdown("<h4>시각화</h4>", unsafe_allow_html=True)

                # Select options to Graph Setting
                y = data[selected_option1]
                x = data[selected_option2]

                if (selected_option1 == selected_option2) :
                    st.write("X와 Y의 값이 같습니다.")

                elif (selected_option3 == 'plot_line_chart'):
                    plot_line_chart(x, y)

                elif (selected_option3 == 'plot_bar_chart'):
                    plot_bar_chart(x, y)

                elif (selected_option3 == 'plot_scatter_chart'):
                    plot_scatter_chart(x, y)

                elif (selected_option3 == 'plot_box_chart'):
                    plot_box_chart(x, y)

                elif (selected_option3 == 'plot_heatmap_chart'):
                    target_column = selected_option1
                    plot_heatmap_chart(data, target_column)

                else:
                    pass

    with tab2 :
        st.dataframe(data, height=500)
        with st.expander("Column List", expanded=False) :
            st.write("해당 데이터 프레임의 컬럼 리스트")
            st.write(data.columns.tolist())

    with tab3 :
        # 선택한 옵션을 기반으로 데이터프레임 필터링
        # filtered_column = pd.concat([data[selected_option1], data[selected_option2]], axis=1)

        # 선택한 옵션과 열 데이터를 목록으로 출력
        st.write("선택한 옵션:", selected_option1)
        st.write("열 데이터 목록:")
        st.write(data[selected_option1])