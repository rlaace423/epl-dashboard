import streamlit as st
import plotly.graph_objects as go
import numpy as np


def show_page():
    st.title("🏆 프리미어 리그(EPL) 팀 분석")
    st.markdown("##### 우리 팀의 현재 위치와 약점을 분석합니다.")
    st.markdown("---")

    # ---------------------------------------------------------
    # 1. 상단 팀 순위 카드 (HTML/CSS 활용)
    # ---------------------------------------------------------
    st.markdown("""
    <style>
    .rank-card {
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .rank-card:hover { transform: translateY(-5px); }
    .rank-title { font-size: 1.2rem; font-weight: bold; margin-bottom: 10px; opacity: 0.9; }
    .team-name { font-size: 2.0rem; font-weight: 800; margin-bottom: 10px; }
    .stats { font-size: 1.0rem; opacity: 0.95; line-height: 1.5; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    # 1위 아스날
    with col1:
        st.markdown("""
        <div class="rank-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div class="rank-title">🥇 1st Place</div>
            <div class="team-name">Arsenal</div>
            <div class="stats">
                W: 22 | D: 4 | L: 3<br>
                GF: 70 | GA: 24 (Diff: +46)
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 2위 맨시티
    with col2:
        st.markdown("""
        <div class="rank-card" style="background: linear-gradient(135deg, #30cfd0 0%, #330867 100%);">
            <div class="rank-title">🥈 2nd Place</div>
            <div class="team-name">Man City</div>
            <div class="stats">
                W: 21 | D: 6 | L: 2<br>
                GF: 68 | GA: 26 (Diff: +42)
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3위 리버풀
    with col3:
        st.markdown("""
        <div class="rank-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <div class="rank-title">🥉 3rd Place</div>
            <div class="team-name">Liverpool</div>
            <div class="stats">
                W: 20 | D: 7 | L: 3<br>
                GF: 65 | GA: 30 (Diff: +35)
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # 2. 팀별 지표 히트맵
    # ---------------------------------------------------------
    st.subheader("📊 팀별 세부 지표 분석 (Heatmap)")
    st.info("💡 붉은색이 진할수록 해당 지표에서 리그 상위권임을 의미합니다. 푸른색은 약점을 나타냅니다.")

    # [목업 데이터 생성]
    # 실제로는 팀별 통계 CSV를 로드해서 사용해야 하지만,
    # 지금은 화면 구성을 위해 랜덤/임의 데이터를 사용합니다.

    teams = ['Arsenal', 'Man City', 'Liverpool', 'Aston Villa', 'Tottenham', 'Man Utd', 'Newcastle', 'Chelsea',
             'West Ham', 'Brighton']
    metrics = ['득점력', '유효슈팅', '패스성공률', '점유율', '태클성공', '공중볼', '활동량', '압박성공']

    # 임의의 데이터 생성 (0~1 사이 값)
    # 특정 팀(예: 우리 팀)의 약점을 강조하고 싶다면 여기서 데이터를 조작하면 됩니다.
    np.random.seed(42)
    data = np.random.rand(len(teams), len(metrics))

    # 히트맵 그리기
    fig = go.Figure(data=go.Heatmap(
        z=data,
        x=metrics,
        y=teams,
        colorscale='RdBu_r',  # Red(강점) ~ Blue(약점)
        xgap=2,  # 셀 간격
        ygap=2,
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.2f}<extra></extra>"
    ))

    fig.update_layout(
        title='EPL 상위 10개팀 퍼포먼스 비교',
        height=600,
        xaxis_nticks=36,
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=50, b=10)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.success("👉 분석 결과: 현재 우리 팀은 **'골 결정력'**과 **'유효슈팅'** 부문에서 약세를 보이고 있습니다. 이를 해결할 공격수 유망주를 찾아봅시다.")
