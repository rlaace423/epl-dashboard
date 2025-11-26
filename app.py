import streamlit as st
# views 폴더에서 페이지 모듈들을 가져옵니다
from views import league_overview, player_dashboard

# 1. 페이지 기본 설정 (앱 전체에서 가장 먼저 실행되어야 함)
st.set_page_config(
    page_title="축구 유망주 탐색 대시보드",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 사이드바 네비게이션 구성
st.sidebar.title("Navigation")
selection = st.sidebar.radio(
    "이동할 페이지 선택",
    ["🏆 1. 리그 오버뷰 (팀 분석)", "🔍 2. 유망주 탐색 (선수 발굴)"]
)

st.sidebar.markdown("---")

# 3. 선택에 따른 페이지 라우팅
if selection == "🏆 1. 리그 오버뷰 (팀 분석)":
    # 새로 만든 순위/히트맵 페이지 실행
    league_overview.show_page()

elif selection == "🔍 2. 유망주 탐색 (선수 발굴)":
    # 기존 대시보드 실행
    player_dashboard.show_page()
