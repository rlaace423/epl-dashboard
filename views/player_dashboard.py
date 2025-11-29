import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
# todo
# from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from data_processor import FootballDataProcessor
from streamlit_plotly_events import plotly_events


def show_page():
    # 캐싱을 통한 데이터 로드 최적화
    @st.cache_data
    def load_data():
        """데이터 로드 및 처리 (캐싱)"""
        processor = FootballDataProcessor('dataset.csv')
        df = processor.process_all()
        return df, processor

    # 데이터 로드
    with st.spinner('데이터를 로딩 중입니다... (약 16만 명의 선수 데이터)'):
        df, processor = load_data()

    # 타이틀
    st.title("⚽ 축구 유망주 탐색 대시보드")
    st.markdown("---")

    # 사이드바 - 필터
    st.sidebar.header("🔍 필터 옵션")

    # 포지션 필터 (가장 먼저)
    position_options = ['All', 'Goalkeeper', 'Defender', 'Midfielder', 'Forward']
    selected_position = st.sidebar.selectbox(
        "⚽ 포지션 선택",
        options=position_options,
        help="포지션을 선택하면 해당 포지션에 중요한 스텟 필터가 나타납니다"
    )

    st.sidebar.markdown("---")

    # 나이 범위 필터
    age_min, age_max = st.sidebar.slider(
        "📅 나이 범위",
        min_value=int(df['Age'].min()),
        max_value=int(df['Age'].max()),
        value=(18, 25),
        help="유망주를 찾기 위한 나이 범위를 선택하세요"
    )

    st.sidebar.markdown("---")

    # 점수 산출 방식 설명 (클릭하여 확인)
    with st.sidebar.expander("📖 점수 산출 방식 (클릭하여 확인)"):
        st.markdown("""
            ### 🎯 유망주 점수 계산 방식

            **1. 필터 기반 점수 (현재 적용)**
            - 아래 슬라이더에서 설정한 능력치들의 **평균값**으로 순위 결정
            - 각 능력치에 **동등한 가중치** 적용
            - 나이 가중치: 젊을수록 보너스
              - 18-21세: ×1.2
              - 22-24세: ×1.0
              - 25세 이상: ×0.8

            **2. 포지션별 핵심 능력치**
            - 🥅 **GK**: 반사신경, 핸들링, 일대일, 박스장악, 킥력, 민첩성
            - 🛡️ **DF**: 마크, 태클, 헤딩, 포지셔닝, 예측력, 근력, 스피드
            - 🎯 **MF**: 패스, 시야, 기술, 볼터치, 스태미나, 활동량, 판단력
            - ⚽ **FW**: 골결정력, 드리블, 스피드, 가속력, 오프더볼, 침착성, 기술

            **💡 사용법**
            1. 포지션 선택
            2. 중요하게 생각하는 능력치 슬라이더 조정
            3. 조정된 능력치 기준으로 순위가 실시간 변경!
            """)

    st.sidebar.subheader("📊 포지션별 핵심 능력치 필터")
    st.sidebar.caption("⬇️ 슬라이더를 조정하면 순위가 실시간으로 변경됩니다")

    # 포지션별 중요 스텟 정의
    position_key_stats = {
        'Goalkeeper': {
            'Reflexes': {'label': '🤚 반사신경', 'default': 0, 'help': '슛을 막는 반응 속도'},
            'Handling': {'label': '✋ 핸들링', 'default': 0, 'help': '공을 잡는 능력'},
            'OneOnOnes': {'label': '🎯 일대일', 'default': 0, 'help': '일대일 상황 대처'},
            'CommandOfArea': {'label': '🏟️ 박스장악', 'default': 0, 'help': '페널티 박스 지배력'},
            'Kicking': {'label': '🦵 킥력', 'default': 0, 'help': '발 차기 능력'},
            'Agility': {'label': '🤸 민첩성', 'default': 0, 'help': '움직임의 민첩함'}
        },
        'Defender': {
            'Marking': {'label': '👤 대인마크', 'default': 0, 'help': '상대 선수 마크 능력'},
            'Tackling': {'label': '⚔️ 태클', 'default': 0, 'help': '태클 능력'},
            'Heading': {'label': '🎯 헤딩', 'default': 0, 'help': '헤더 능력'},
            'Positioning': {'label': '📍 포지셔닝', 'default': 0, 'help': '수비 위치 선정'},
            'Anticipation': {'label': '🔮 예측력', 'default': 0, 'help': '상황 예측 능력'},
            'Strength': {'label': '💪 근력', 'default': 0, 'help': '몸싸움 능력'},
            'Pace': {'label': '⚡ 스피드', 'default': 0, 'help': '최고 속도'}
        },
        'Midfielder': {
            'Passing': {'label': '🎯 패스', 'default': 0, 'help': '패스 정확도'},
            'Vision': {'label': '👁️ 시야', 'default': 0, 'help': '창의적 패스 능력'},
            'Technique': {'label': '⚽ 기술', 'default': 0, 'help': '기술적 완성도'},
            'FirstTouch': {'label': '✨ 볼터치', 'default': 0, 'help': '첫 터치 능력'},
            'Stamina': {'label': '🔋 스태미나', 'default': 0, 'help': '지구력'},
            'Workrate': {'label': '🏃 활동량', 'default': 0, 'help': '경기 중 움직임'},
            'Decisions': {'label': '🧠 판단력', 'default': 0, 'help': '상황 판단 능력'}
        },
        'Forward': {
            'Finishing': {'label': '🎯 골결정력', 'default': 0, 'help': '슈팅 마무리 능력'},
            'Dribbling': {'label': '🎪 드리블', 'default': 0, 'help': '드리블 능력'},
            'Pace': {'label': '⚡ 스피드', 'default': 0, 'help': '최고 속도'},
            'Acceleration': {'label': '🚀 가속력', 'default': 0, 'help': '순간 가속'},
            'OffTheBall': {'label': '🏃 오프더볼', 'default': 0, 'help': '공 없을 때 움직임'},
            'Composure': {'label': '😌 침착성', 'default': 0, 'help': '압박 상황 침착함'},
            'Technique': {'label': '⚽ 기술', 'default': 0, 'help': '기술적 완성도'}
        }
    }

    # 포지션에 따른 동적 필터 생성
    stat_filters = {}

    if selected_position == 'All':
        st.sidebar.info("💡 포지션을 선택하면 해당 포지션에 중요한 능력치 필터가 나타납니다.")

        # All 선택 시 기본 필터
        stat_filters['Overall_Rating'] = st.sidebar.slider(
            "📈 최소 종합 능력치",
            min_value=0.0,
            max_value=20.0,
            value=10.0,
            step=0.5,
            help="최소 종합 능력치 기준"
        )
    else:
        st.sidebar.markdown(f"**{selected_position}** 포지션 핵심 능력치:")

        # 선택한 포지션의 핵심 스텟 필터 생성
        stats = position_key_stats[selected_position]

        for stat_name, stat_info in stats.items():
            stat_filters[stat_name] = st.sidebar.slider(
                stat_info['label'],
                min_value=0,
                max_value=20,
                value=stat_info['default'],
                step=1,
                help=stat_info['help']
            )

    st.sidebar.markdown("---")

    # 표시할 상위 유망주 수
    top_n_display = st.sidebar.slider(
        "🏆 상위 유망주 표시 수",
        min_value=1,
        max_value=10,
        value=10,
        step=1,
        help="차트에 표시할 상위 유망주 수 (1~10명)"
    )

    st.sidebar.markdown("---")

    # 적용된 필터 요약
    active_filters = []
    if selected_position != 'All':
        active_filters.append(f"포지션: {selected_position}")
    if age_min != int(df['Age'].min()) or age_max != int(df['Age'].max()):
        active_filters.append(f"나이: {age_min}-{age_max}세")
    for stat, val in stat_filters.items():
        if val > 0:
            active_filters.append(f"{stat} ≥ {val}")

    if active_filters:
        st.sidebar.success(f"✅ **적용된 필터**: {len(active_filters)}개")
        with st.sidebar.expander("필터 상세보기"):
            for f in active_filters:
                st.write(f"• {f}")

    st.sidebar.info(
        "💡 **사용법**:\n"
        "1. 포지션을 먼저 선택하세요\n"
        "2. 해당 포지션의 핵심 스텟을 조절하세요\n"
        "3. 슬라이더를 오른쪽으로 이동하면 더 엄격한 기준이 적용됩니다"
    )

    # 데이터 필터링
    df_filtered = df.copy()

    # 나이 필터 적용
    df_filtered = df_filtered[
        (df_filtered['Age'] >= age_min) &
        (df_filtered['Age'] <= age_max)
        ]

    # 포지션 필터 적용
    if selected_position != 'All':
        df_filtered = df_filtered[df_filtered['Position_Category'] == selected_position]

    # 능력치 필터 적용 (포지션별 스텟 필터)
    for stat_name, min_value in stat_filters.items():
        if min_value > 0:  # 0보다 큰 값만 필터로 적용
            df_filtered = df_filtered[df_filtered[stat_name] >= min_value]

    # 상위 유망주 추출
    top_talents = df_filtered.nlargest(top_n_display, 'Talent_Score_Normalized')

    # 메트릭 표시
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        original_count = len(df) if selected_position == 'All' else len(
            df[df['Position_Category'] == selected_position])
        filter_ratio = (len(df_filtered) / original_count * 100) if original_count > 0 else 0
        st.metric(
            "필터링된 선수 수",
            f"{len(df_filtered):,}명",
            f"{filter_ratio:.1f}%",
            help="현재 필터 조건에 맞는 선수 수"
        )

    with col2:
        if len(df_filtered) > 0:
            avg_age = df_filtered['Age'].mean()
            st.metric(
                "평균 나이",
                f"{avg_age:.1f}세",
                help="필터링된 선수들의 평균 나이"
            )
        else:
            st.metric("평균 나이", "N/A")

    with col3:
        if len(df_filtered) > 0:
            avg_rating = df_filtered['Overall_Rating'].mean()
            st.metric(
                "평균 능력치",
                f"{avg_rating:.2f}",
                help="필터링된 선수들의 평균 종합 능력치"
            )
        else:
            st.metric("평균 능력치", "N/A")

    with col4:
        if len(top_talents) > 0:
            top_talent_score = top_talents.iloc[0]['Talent_Score_Normalized']
            st.metric(
                "최고 유망주 점수",
                f"{top_talent_score:.1f}",
                help="가장 높은 유망주 점수"
            )
        else:
            st.metric("최고 유망주 점수", "N/A")

    with col5:
        if selected_position != 'All' and len(df_filtered) > 0:
            # 선택한 포지션의 평균 포지션 특화 점수
            avg_specialized = df_filtered['Position_Specialized_Score'].mean()
            st.metric(
                "평균 특화 점수",
                f"{avg_specialized:.2f}",
                help=f"{selected_position} 포지션 특화 능력치 평균"
            )
        else:
            st.metric("평균 특화 점수", "N/A")

    st.markdown("---")

    # 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 선수 발굴 (Scatter)",
        "📊 선수 비교 (Parallel)",
        "🏆 상위 유망주",
        "📈 포지션별 분석",
        "👤 선수 프로필"
    ])

    # 탭 1: 선수 발굴 (Scatter Plot)
    with tab1:
        if len(df_filtered) == 0:
            st.warning("⚠️ 필터 조건에 맞는 선수가 없습니다. 필터를 조정해주세요.")
        else:
            st.header("🎯 선수 발굴 - 차트에서 클릭하여 분석")

            # 세션 스테이트 초기화 (선수 선택 저장용)
            if 'clicked_players' not in st.session_state:
                st.session_state.clicked_players = []

            # 필터 요약 및 리셋 버튼
            col_info, col_reset = st.columns([4, 1])

            with col_info:
                if selected_position != 'All':
                    st.info(
                        f"📌 **{selected_position}** 포지션 {len(df_filtered):,}명 | 💡 **왼쪽 차트에서 선수를 클릭**하면 오른쪽에 능력치가 표시됩니다!")
                else:
                    st.info(f"📌 전체 포지션 {len(df_filtered):,}명 | 💡 **왼쪽 차트에서 선수를 클릭**하면 오른쪽에 능력치가 표시됩니다!")

            with col_reset:
                if st.button("🔄 선택 초기화", use_container_width=True):
                    st.session_state.clicked_players = []
                    st.rerun()

            st.markdown("---")

            # 메인 레이아웃: 왼쪽 순위 바 차트, 오른쪽 레이더 차트 (동일 비율)
            col_ranking, col_radar = st.columns([1, 1])

            # 왼쪽: 실시간 순위 바 차트
            with col_ranking:
                st.subheader("🏆 선수 순위 (필터 기준)")

                # 필터 기반 점수 계산 (동등 가중치)
                df_score = df_filtered.copy()

                # 활성화된 필터의 능력치들만 사용하여 점수 계산
                active_stats = [k for k, v in stat_filters.items() if v > 0 and k != 'Overall_Rating']

                if active_stats and selected_position != 'All':
                    # 각 능력치의 실제 값을 사용하여 평균 계산 (동등 가중치)
                    # 슬라이더 값은 필터링에만 사용되고, 점수는 실제 능력치 값의 평균으로 계산
                    df_score['Filter_Score'] = df_score[active_stats].mean(axis=1)

                    # 나이 가중치 적용
                    age_weight = np.where(df_score['Age'] <= 21, 1.2,
                                          np.where(df_score['Age'] <= 24, 1.0, 0.8))
                    df_score['Filter_Score'] = df_score['Filter_Score'] * age_weight

                    # 0-100 정규화
                    min_score = df_score['Filter_Score'].min()
                    max_score = df_score['Filter_Score'].max()
                    if max_score > min_score:
                        df_score['Display_Score'] = (
                                (df_score['Filter_Score'] - min_score) / (max_score - min_score) * 100)
                    else:
                        df_score['Display_Score'] = df_score['Filter_Score']

                    score_column = 'Display_Score'
                    score_label = "필터 기반 점수"

                    # 어떤 능력치가 적용되었는지 표시 + 계산 방식 설명
                    applied_stats = [position_key_stats[selected_position][s]['label'] for s in active_stats if
                                     s in position_key_stats.get(selected_position, {})]
                    stat_values = {s: stat_filters[s] for s in active_stats if s in stat_filters}

                    if applied_stats:
                        # 계산 방식 상세 표시
                        with st.expander(f"📊 점수 계산 방식 상세 (클릭하여 확인)", expanded=False):
                            st.markdown(f"""
                                **✅ 적용된 능력치 및 최소 기준**:
                                """)
                            for stat, label in zip(active_stats, applied_stats):
                                min_val = stat_values.get(stat, 0)
                                st.write(f"- **{label}**: 최소 {min_val} 이상 (실제 값 사용)")

                            st.markdown(f"""
                                ---

                                **📐 계산 공식**:
                                1. **필터링**: 슬라이더 값 이상인 선수만 선택
                                2. **점수 계산**: 선택된 능력치들의 **실제 값 평균** (동등 가중치)
                                   - 예: 골결정력 15, 스피드 14, 드리블 13 → (15+14+13)/3 = 14.0
                                3. **나이 가중치**:
                                   - 18-21세: ×1.2 (젊을수록 유리)
                                   - 22-24세: ×1.0
                                   - 25세 이상: ×0.8
                                4. **정규화**: 0-100 범위로 변환

                                **💡 예시**:
                                - 선수 A (20세): 골결정력 15, 스피드 14, 드리블 13
                                  - 평균: 14.0
                                  - 나이 가중치: 14.0 × 1.2 = **16.8**
                                - 선수 B (23세): 골결정력 16, 스피드 15, 드리블 14
                                  - 평균: 15.0
                                  - 나이 가중치: 15.0 × 1.0 = **15.0**
                                - → 선수 A가 더 높은 점수! (젊은 나이 보너스)

                                **🎯 핵심**: 슬라이더는 **최소 기준**만 설정하고, 
                                실제 점수는 **능력치 값의 평균**으로 계산됩니다.
                                """)

                        # 슬라이더 값 요약
                        slider_summary = ', '.join([f"{label}≥{stat_values.get(stat, 0)}"
                                                    for stat, label in zip(active_stats, applied_stats)])
                        st.caption(f"📊 필터: {slider_summary} | 점수 = (능력치 평균) × 나이가중치")
                    else:
                        st.caption("💡 슬라이더를 조정하면 순위가 실시간 변경됩니다")
                else:
                    # 기본 유망주 점수 사용
                    df_score['Display_Score'] = df_score['Talent_Score_Normalized']
                    score_column = 'Display_Score'
                    score_label = "유망주 점수"
                    st.caption("💡 능력치 슬라이더를 조정하면 순위가 실시간 변경됩니다")

                # 상위 N명 표시 (사이드바 슬라이더로 조절)
                df_display = df_score.nlargest(top_n_display, score_column).copy()
                df_display['Rank'] = range(1, len(df_display) + 1)
                df_display['Display_Name'] = df_display.apply(
                    lambda x: f"{x['Rank']}. {x['Name']} ({int(x['Age'])}세)", axis=1
                )

                # 선택된 선수 표시용 색상
                df_display['Is_Selected'] = df_display['Name'].isin(st.session_state.clicked_players)

                # 바 차트 색상 설정
                colors_bar = []
                for idx, row in df_display.iterrows():
                    if row['Name'] in st.session_state.clicked_players:
                        colors_bar.append('#FF4B4B')  # 빨간색 (선택됨)
                    else:
                        # 나이에 따른 색상 (젊을수록 밝은 색)
                        age = row['Age']
                        if age <= 21:
                            colors_bar.append('#00CC96')  # 녹색 (젊음)
                        elif age <= 24:
                            colors_bar.append('#636EFA')  # 파란색
                        else:
                            colors_bar.append('#AB63FA')  # 보라색

                # 수평 바 차트
                fig_ranking = go.Figure()

                fig_ranking.add_trace(go.Bar(
                    y=df_display['Display_Name'],
                    x=df_display[score_column],
                    orientation='h',
                    marker=dict(
                        color=colors_bar,
                        line=dict(width=1, color='white')
                    ),
                    text=df_display[score_column].round(1),
                    textposition='inside',
                    textfont=dict(color='white', size=11),
                    hovertemplate=(
                            "<b>%{y}</b><br>" +
                            f"{score_label}: " + "%{x:.1f}<br>" +
                            "<extra></extra>"
                    ),
                    customdata=df_display[['Name', 'Age', 'Position_Category', 'Overall_Rating']].values
                ))

                fig_ranking.update_layout(
                    height=550,
                    margin=dict(t=10, b=50, l=180, r=20),
                    xaxis=dict(
                        title=score_label,
                        range=[0, 105],
                        showgrid=True,
                        gridcolor='lightgray',
                        title_standoff=10
                    ),
                    yaxis=dict(
                        title="",
                        autorange="reversed",  # 1등이 위에
                        tickfont=dict(size=10),
                        tickmode='array',
                        tickvals=list(range(len(df_display))),
                        ticktext=df_display['Display_Name'].tolist()
                    ),
                    # plot_bgcolor='rgba(248,248,248,0.8)',
                    plot_bgcolor='rgba(0,0,0,0)',  # [중요] 배경 완전 투명
                    paper_bgcolor='rgba(0,0,0,0)',  # [중요] 배경 완전 투명
                    template='plotly_dark',  # 다크 템플릿
                    showlegend=False
                )

                # 클릭 이벤트 캡처
                clicked_points = plotly_events(
                    fig_ranking,
                    click_event=True,
                    hover_event=False,
                    select_event=False,
                    key="ranking_click"
                )

                # 클릭된 선수 처리
                if clicked_points:
                    point_index = clicked_points[0].get('pointIndex', None)
                    if point_index is not None and point_index < len(df_display):
                        clicked_name = df_display.iloc[point_index]['Name']
                        if clicked_name not in st.session_state.clicked_players:
                            if len(st.session_state.clicked_players) >= 5:
                                st.session_state.clicked_players.pop(0)
                            st.session_state.clicked_players.append(clicked_name)
                            st.rerun()

                # 범례 표시
                st.markdown("""
                    <div style='font-size: 12px; margin-top: 5px;'>
                        <span style='color: #00CC96;'>●</span> 21세 이하 &nbsp;
                        <span style='color: #636EFA;'>●</span> 22-24세 &nbsp;
                        <span style='color: #AB63FA;'>●</span> 25세 이상 &nbsp;
                        <span style='color: #FF4B4B;'>●</span> 선택됨
                    </div>
                    """, unsafe_allow_html=True)

                # 현재 선택된 선수 표시
                if st.session_state.clicked_players:
                    st.success(f"⭐ 선택된 선수: {', '.join(st.session_state.clicked_players)}")

            # 오른쪽: 레이더 차트
            with col_radar:
                colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A']

                if len(st.session_state.clicked_players) > 0:
                    # 가장 최근 클릭한 선수 정보
                    latest_player = st.session_state.clicked_players[-1]
                    latest_data = df_filtered[df_filtered['Name'] == latest_player]

                    if len(latest_data) > 0:
                        latest_data = latest_data.iloc[0]
                        player_position = latest_data['Position_Category']
                        st.subheader(f"Profile: {latest_player}")

                        # 선수 기본 정보
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("나이", f"{int(latest_data['Age'])}세")
                        with col2:
                            st.metric("포지션", player_position)
                        with col3:
                            st.metric("유망주점수", f"{latest_data['Talent_Score_Normalized']:.1f}")

                        # 포지션별 핵심 능력치 가져오기
                        if player_position in position_key_stats:
                            position_stats = position_key_stats[player_position]
                            stat_names = list(position_stats.keys())
                            stat_labels = [position_stats[s]['label'] for s in stat_names]
                        else:
                            # 기본값 (All 포지션인 경우)
                            stat_names = ['Finishing', 'Dribbling', 'Passing', 'Tackling', 'Pace', 'Stamina']
                            stat_labels = ['골결정력', '드리블', '패스', '태클', '스피드', '스태미나']

                        st.caption(f"📊 **{player_position}** 포지션 핵심 능력치")

                    # 레이더 차트 생성
                    fig_radar = go.Figure()

                    # 첫 번째 선수의 포지션 기준으로 카테고리 설정
                    first_player_data = df_filtered[df_filtered['Name'] == st.session_state.clicked_players[0]]
                    if len(first_player_data) > 0:
                        base_position = first_player_data.iloc[0]['Position_Category']
                        if base_position in position_key_stats:
                            position_stats = position_key_stats[base_position]
                            stat_names = list(position_stats.keys())
                            stat_labels = [position_stats[s]['label'] for s in stat_names]
                        else:
                            stat_names = ['Finishing', 'Dribbling', 'Passing', 'Tackling', 'Pace', 'Stamina']
                            stat_labels = ['골결정력', '드리블', '패스', '태클', '스피드', '스태미나']

                    for idx, player_name in enumerate(st.session_state.clicked_players):
                        player_data = df_filtered[df_filtered['Name'] == player_name]
                        if len(player_data) > 0:
                            player_data = player_data.iloc[0]

                            # 포지션별 핵심 능력치 값 가져오기
                            values = []
                            for stat in stat_names:
                                if stat in df_filtered.columns:
                                    values.append(player_data[stat])
                                else:
                                    values.append(0)

                            fig_radar.add_trace(go.Scatterpolar(
                                r=values,
                                theta=stat_labels,
                                fill='toself',
                                name=f"{player_name}",
                                line_color=colors[idx % 5],
                                fillcolor=f'rgba{tuple(list(int(colors[idx % 5][i:i + 2], 16) for i in (1, 3, 5)) + [0.2])}',
                                hovertemplate=f"<b>{player_name}</b><br>%{{theta}}: %{{r:.1f}}<extra></extra>"
                            ))

                    fig_radar.update_layout(
                        polar=dict(
                            bgcolor='rgba(250,250,250,0.5)',
                            radialaxis=dict(
                                visible=True,
                                range=[0, 20],
                                tickmode='linear',
                                tick0=0,
                                dtick=5,
                                gridcolor='lightgray',
                                linecolor='lightgray'
                            ),
                            angularaxis=dict(
                                gridcolor='lightgray',
                                linecolor='lightgray'
                            )
                        ),
                        showlegend=True if len(st.session_state.clicked_players) > 1 else False,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.15,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=10)
                        ),
                        height=480,
                        margin=dict(t=20, b=60, l=40, r=40)
                    )

                    st.plotly_chart(fig_radar, use_container_width=True)

                    # 선택된 선수들 비교 테이블
                    if len(st.session_state.clicked_players) > 0:
                        st.markdown("##### 📋 선택된 선수 비교")
                        compare_data = df_filtered[df_filtered['Name'].isin(st.session_state.clicked_players)][
                            ['Name', 'Age', 'Position_Category', 'Overall_Rating', 'Talent_Score_Normalized']
                        ].copy()
                        compare_data.columns = ['이름', '나이', '포지션', '종합능력', '유망주점수']
                        compare_data = compare_data.round(2)
                        st.dataframe(compare_data, use_container_width=True, hide_index=True, height=150)

                else:
                    st.subheader("⚡ Profile")
                    st.info("👈 왼쪽 차트에서 선수를 **클릭**하세요!")

                    # 포지션에 따른 빈 레이더 차트 카테고리
                    if selected_position in position_key_stats:
                        empty_stats = position_key_stats[selected_position]
                        empty_labels = [empty_stats[s]['label'] for s in empty_stats.keys()]
                    else:
                        empty_labels = ['공격력', '수비력', '기술', '멘탈', '신체']

                    # 빈 레이더 차트 표시
                    fig_empty = go.Figure()
                    fig_empty.add_trace(go.Scatterpolar(
                        r=[10] * len(empty_labels),
                        theta=empty_labels,
                        fill='toself',
                        name='클릭하여 선택',
                        line_color='lightgray',
                        fillcolor='rgba(200, 200, 200, 0.2)'
                    ))
                    fig_empty.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 20],
                                tickmode='linear',
                                tick0=0,
                                dtick=5
                            )
                        ),
                        showlegend=False,
                        height=480,
                        margin=dict(t=20, b=60, l=40, r=40),
                        template='plotly_dark',
                    )
                    st.plotly_chart(fig_empty, use_container_width=True)

                    st.markdown("""
                        **사용법:**
                        1. 왼쪽 차트에서 선수 막대를 클릭
                        2. 오른쪽에 해당 선수의 핵심 능력치 표시
                        3. 최대 5명까지 비교 가능
                        4. 초기화 버튼으로 리셋
                        """)

    # 탭 2: 선수 비교 (Parallel Coordinates)
    with tab2:
        st.header("📊 선수 비교 - 평행 좌표계")

        if len(df_filtered) == 0:
            st.warning("⚠️ 필터 조건에 맞는 선수가 없습니다. 필터를 조정해주세요.")
        else:
            st.info(
                "💡 **사용법**: 평행 좌표계를 통해 여러 선수를 동시에 비교할 수 있습니다. "
                "각 축에서 드래그하여 범위를 지정하면 해당 조건에 맞는 선수만 필터링됩니다."
            )

            # 비교할 선수 수 선택
            comparison_count = st.slider(
                "비교할 상위 유망주 수",
                min_value=3,
                max_value=20,
                value=10,
                help="유망주 점수 기준 상위 N명을 비교합니다"
            )

            # 상위 N명 선택
            top_compare = df_filtered.nlargest(comparison_count, 'Talent_Score_Normalized')

            # 포지션별 핵심 스텟 선택
            if selected_position == 'Goalkeeper':
                compare_attrs = ['Age', 'Reflexes', 'Handling', 'OneOnOnes', 'CommandOfArea', 'Kicking', 'Agility',
                                 'Talent_Score_Normalized']
            elif selected_position == 'Defender':
                compare_attrs = ['Age', 'Marking', 'Tackling', 'Heading', 'Positioning', 'Pace', 'Strength',
                                 'Anticipation', 'Talent_Score_Normalized']
            elif selected_position == 'Midfielder':
                compare_attrs = ['Age', 'Passing', 'Vision', 'Technique', 'Stamina', 'Workrate', 'Dribbling',
                                 'FirstTouch', 'Talent_Score_Normalized']
            elif selected_position == 'Forward':
                compare_attrs = ['Age', 'Finishing', 'Dribbling', 'Pace', 'Acceleration', 'Composure', 'OffTheBall',
                                 'Technique', 'Talent_Score_Normalized']
            else:
                compare_attrs = ['Age', 'Overall_Rating', 'Technical_Rating', 'Mental_Rating', 'Physical_Rating',
                                 'Pace', 'Passing', 'Finishing', 'Talent_Score_Normalized']

            # 데이터 준비
            compare_data = top_compare[compare_attrs + ['Name', 'Position_Category']].copy()

            # Parallel Coordinates 차트
            fig_parallel = go.Figure(data=
            go.Parcoords(
                line=dict(
                    color=top_compare['Talent_Score_Normalized'],
                    colorscale='Viridis',
                    showscale=True,
                    cmin=top_compare['Talent_Score_Normalized'].min(),
                    cmax=top_compare['Talent_Score_Normalized'].max()
                ),
                dimensions=[
                    dict(
                        range=[top_compare[attr].min(), top_compare[attr].max()],
                        label=attr,
                        values=top_compare[attr]
                    ) for attr in compare_attrs
                ]
            )
            )

            fig_parallel.update_layout(
                title=f'상위 {comparison_count}명 유망주 비교 - {selected_position if selected_position != "All" else "전체 포지션"}',
                height=600,
                margin=dict(l=100, r=100, t=100, b=100)
            )

            st.plotly_chart(fig_parallel, use_container_width=True)

            # 비교 대상 선수 리스트
            st.subheader("📋 비교 대상 선수 목록")

            # 중복 컬럼 제거 (Age가 compare_attrs에 이미 포함됨)
            base_cols = ['Name', 'Position_Category']
            display_cols = base_cols + [col for col in compare_attrs if col not in base_cols]
            display_df = top_compare[display_cols].copy()
            display_df = display_df.round(2)

            st.dataframe(display_df, use_container_width=True, height=300)

            # 선수별 상세 비교
            st.markdown("---")
            st.subheader("🔍 선수별 상세 비교")

            # 2-3명 선택하여 레이더 차트로 직접 비교
            selected_players = st.multiselect(
                "비교할 선수 선택 (최대 3명)",
                options=top_compare['Name'].tolist(),
                max_selections=3,
                help="선택한 선수들의 능력치를 레이더 차트로 비교합니다"
            )

            if len(selected_players) > 0:
                col1, col2 = st.columns(2)

                with col1:
                    # 5개 대분류 레이더 차트
                    st.markdown("#### 능력치 프로필 비교 (5개 대분류)")

                    fig_compare_radar = go.Figure()

                    categories = ['공격력', '수비력', '기술', '멘탈', '신체']
                    colors = ['#636EFA', '#EF553B', '#00CC96']

                    for idx, player_name in enumerate(selected_players):
                        player_data = top_compare[top_compare['Name'] == player_name].iloc[0]

                        attacking_attrs = ['Finishing', 'LongShots', 'Heading', 'OffTheBall']
                        defending_attrs = ['Marking', 'Tackling', 'Positioning', 'Anticipation']
                        technical_attrs = ['Dribbling', 'Passing', 'FirstTouch', 'Technique', 'Crossing']
                        mental_attrs = ['Composure', 'Vision', 'Decisions', 'Determination', 'Workrate']
                        physical_attrs = ['Pace', 'Acceleration', 'Stamina', 'Strength', 'Agility']

                        values = [
                            player_data[[a for a in attacking_attrs if a in df_filtered.columns]].mean(),
                            player_data[[a for a in defending_attrs if a in df_filtered.columns]].mean(),
                            player_data[[a for a in technical_attrs if a in df_filtered.columns]].mean(),
                            player_data[[a for a in mental_attrs if a in df_filtered.columns]].mean(),
                            player_data[[a for a in physical_attrs if a in df_filtered.columns]].mean()
                        ]

                        fig_compare_radar.add_trace(go.Scatterpolar(
                            r=values,
                            theta=categories,
                            fill='toself',
                            name=player_name,
                            line_color=colors[idx % 3],
                            fillcolor=f'rgba{tuple(list(int(colors[idx % 3][i:i + 2], 16) for i in (1, 3, 5)) + [0.2])}'
                        ))

                    fig_compare_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 20]
                            )
                        ),
                        height=500,
                        showlegend=True
                    )

                    st.plotly_chart(fig_compare_radar, use_container_width=True)

                with col2:
                    # 포지션별 핵심 스텟 비교 바 차트
                    st.markdown("#### 핵심 스텟 비교")

                    # 포지션별 핵심 스텟 3-4개 선택
                    if selected_position == 'Goalkeeper':
                        key_stats = ['Reflexes', 'Handling', 'OneOnOnes', 'Kicking']
                    elif selected_position == 'Defender':
                        key_stats = ['Marking', 'Tackling', 'Pace', 'Strength']
                    elif selected_position == 'Midfielder':
                        key_stats = ['Passing', 'Vision', 'Stamina', 'Technique']
                    elif selected_position == 'Forward':
                        key_stats = ['Finishing', 'Pace', 'Dribbling', 'Composure']
                    else:
                        key_stats = ['Overall_Rating', 'Technical_Rating', 'Mental_Rating', 'Physical_Rating']

                    fig_bar_compare = go.Figure()

                    for player_name in selected_players:
                        player_data = top_compare[top_compare['Name'] == player_name].iloc[0]
                        values = [player_data[stat] for stat in key_stats]

                        fig_bar_compare.add_trace(go.Bar(
                            name=player_name,
                            x=key_stats,
                            y=values,
                            text=[f'{v:.1f}' for v in values],
                            textposition='auto'
                        ))

                    fig_bar_compare.update_layout(
                        barmode='group',
                        height=500,
                        yaxis=dict(range=[0, 20]),
                        xaxis_title="능력치",
                        yaxis_title="수치",
                        showlegend=True
                    )

                    st.plotly_chart(fig_bar_compare, use_container_width=True)

    # 탭 3: 상위 유망주
    with tab3:
        st.header("🏆 상위 유망주 랭킹")
        st.subheader(f"상위 {len(top_talents)}명의 유망주")

        if len(top_talents) > 0:
            # 상위 20명 바 차트
            top_20 = top_talents.head(20)

            fig_bar = px.bar(
                top_20,
                x='Talent_Score_Normalized',
                y='Name',
                orientation='h',
                color='Age',
                title='상위 20명 유망주 순위',
                labels={
                    'Talent_Score_Normalized': '유망주 점수',
                    'Name': '선수명',
                    'Age': '나이'
                },
                color_continuous_scale='RdYlGn_r',
                hover_data=['Position_Category', 'Overall_Rating']
            )

            fig_bar.update_layout(
                height=600,
                yaxis={'categoryorder': 'total ascending'}
            )

            st.plotly_chart(fig_bar, use_container_width=True)

            # 상위 유망주 테이블
            st.subheader("상위 유망주 상세 리스트")

            display_cols = [
                'Name', 'Age', 'Position_Category', 'Overall_Rating',
                'Technical_Rating', 'Mental_Rating', 'Physical_Rating',
                'Talent_Score_Normalized'
            ]

            display_df = top_talents[display_cols].copy()
            display_df.columns = [
                '이름', '나이', '포지션', '종합능력치',
                '기술', '정신', '신체', '유망주점수'
            ]

            # 숫자 포맷팅
            for col in ['종합능력치', '기술', '정신', '신체', '유망주점수']:
                display_df[col] = display_df[col].round(2)

            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )

            # CSV 다운로드
            csv = top_talents.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 상위 유망주 데이터 다운로드 (CSV)",
                data=csv,
                file_name='top_talents.csv',
                mime='text/csv',
            )
        else:
            st.warning("필터 조건에 맞는 선수가 없습니다.")

    # 탭 4: 포지션별 분석
    with tab4:
        st.header("📈 포지션별 분석")

        if len(df_filtered) > 0:
            # 포지션별 통계
            position_stats = df_filtered.groupby('Position_Category').agg({
                'Talent_Score_Normalized': ['mean', 'max', 'count'],
                'Overall_Rating': 'mean',
                'Age': 'mean'
            }).round(2)

            position_stats.columns = ['평균 유망주 점수', '최고 유망주 점수', '선수 수', '평균 능력치', '평균 나이']
            position_stats = position_stats.reset_index()
            position_stats.columns = ['포지션', '평균 유망주 점수', '최고 유망주 점수', '선수 수', '평균 능력치', '평균 나이']

            col1, col2 = st.columns(2)

            with col1:
                # 포지션별 평균 유망주 점수
                fig_pos_avg = px.bar(
                    position_stats,
                    x='포지션',
                    y='평균 유망주 점수',
                    color='평균 유망주 점수',
                    title='포지션별 평균 유망주 점수',
                    color_continuous_scale='Blues'
                )
                fig_pos_avg.update_layout(height=400)
                st.plotly_chart(fig_pos_avg, use_container_width=True)

            with col2:
                # 포지션별 선수 수
                fig_pos_count = px.pie(
                    position_stats,
                    values='선수 수',
                    names='포지션',
                    title='포지션별 선수 분포',
                    hole=0.4
                )
                fig_pos_count.update_layout(height=400)
                st.plotly_chart(fig_pos_count, use_container_width=True)

            # 포지션별 통계 테이블
            st.subheader("포지션별 상세 통계")
            st.dataframe(position_stats, use_container_width=True)

            # 포지션별 능력치 비교 (박스 플롯)
            st.subheader("포지션별 능력치 분포 비교")

            fig_box = go.Figure()

            for category in ['Technical_Rating', 'Mental_Rating', 'Physical_Rating']:
                for position in df_filtered['Position_Category'].unique():
                    data = df_filtered[df_filtered['Position_Category'] == position][category]
                    fig_box.add_trace(go.Box(
                        y=data,
                        name=f"{position}",
                        boxmean='sd'
                    ))

            fig_box.update_layout(
                title='포지션별 능력치 분포 (기술/정신/신체)',
                yaxis_title='능력치',
                height=500,
                showlegend=True
            )

            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.warning("필터 조건에 맞는 선수가 없습니다.")

    # 탭 5: 선수 프로필 (상세 분석)
    with tab5:
        st.header("👤 선수 프로필 - 상세 분석")

        if len(top_talents) > 0:
            st.info("💡 선수를 선택하면 5개 대분류 레이더 차트와 상세 능력치를 확인할 수 있습니다.")

            # 선수 선택
            player_names = top_talents['Name'].tolist()
            selected_player_name = st.selectbox(
                "선수 선택 (상위 유망주 기준)",
                options=player_names,
                help="상위 유망주 중에서 선수를 선택하세요"
            )

            # 선수 정보 가져오기
            player_data = top_talents[top_talents['Name'] == selected_player_name].iloc[0]

            st.markdown("---")

            # 선수 기본 정보 표시
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("🏃 이름", player_data['Name'])
                st.metric("📅 나이", f"{int(player_data['Age'])}세")

            with col2:
                st.metric("⚽ 포지션", player_data['Position_Category'])
                st.metric("📍 주 포지션", player_data['Primary_Position'])

            with col3:
                st.metric("📊 종합 능력치", f"{player_data['Overall_Rating']:.2f}")
                st.metric("⭐ 유망주 점수", f"{player_data['Talent_Score_Normalized']:.1f}")

            with col4:
                st.metric("📏 키", f"{int(player_data['Height'])} cm" if pd.notna(player_data['Height']) else "N/A")
                st.metric("⚖️ 몸무게", f"{int(player_data['Weight'])} kg" if pd.notna(player_data['Weight']) else "N/A")

            st.markdown("---")

            # 레이더 차트 - 5개 대분류
            col1, col2 = st.columns([1.2, 0.8])

            with col1:
                st.subheader(f"⚡ Profile: {player_data['Name']}")

                categories = ['Attacking', 'Defending', 'Technical', 'Mental', 'Physical']

                # 각 대분류별 평균 계산
                attacking_attrs = ['Finishing', 'LongShots', 'Heading', 'OffTheBall']
                defending_attrs = ['Marking', 'Tackling', 'Positioning', 'Anticipation']
                technical_attrs = ['Dribbling', 'Passing', 'FirstTouch', 'Technique', 'Crossing']
                mental_attrs = ['Composure', 'Vision', 'Decisions', 'Determination', 'Workrate']
                physical_attrs = ['Pace', 'Acceleration', 'Stamina', 'Strength', 'Agility']

                values = [
                    player_data[[a for a in attacking_attrs if a in df_filtered.columns]].mean(),
                    player_data[[a for a in defending_attrs if a in df_filtered.columns]].mean(),
                    player_data[[a for a in technical_attrs if a in df_filtered.columns]].mean(),
                    player_data[[a for a in mental_attrs if a in df_filtered.columns]].mean(),
                    player_data[[a for a in physical_attrs if a in df_filtered.columns]].mean()
                ]

                fig_radar_profile = go.Figure()

                fig_radar_profile.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name=player_data['Name'],
                    line_color='#636EFA',
                    fillcolor='rgba(99, 110, 250, 0.3)',
                    line_width=2
                ))

                fig_radar_profile.update_layout(
                    polar=dict(
                        bgcolor='rgba(240,240,240,0.5)',
                        radialaxis=dict(
                            visible=True,
                            range=[0, 20],
                            tickmode='linear',
                            tick0=0,
                            dtick=5,
                            gridcolor='white',
                            gridwidth=2
                        ),
                        angularaxis=dict(
                            gridcolor='white',
                            gridwidth=2
                        )
                    ),
                    showlegend=False,
                    height=500,
                    font=dict(size=14)
                )

                st.plotly_chart(fig_radar_profile, use_container_width=True)

            with col2:
                st.subheader("📊 대분류 점수")
                st.markdown(f"**Attacking**: {values[0]:.1f}")
                st.progress(min(values[0] / 20, 1.0))

                st.markdown(f"**Defending**: {values[1]:.1f}")
                st.progress(min(values[1] / 20, 1.0))

                st.markdown(f"**Technical**: {values[2]:.1f}")
                st.progress(min(values[2] / 20, 1.0))

                st.markdown(f"**Mental**: {values[3]:.1f}")
                st.progress(min(values[3] / 20, 1.0))

                st.markdown(f"**Physical**: {values[4]:.1f}")
                st.progress(min(values[4] / 20, 1.0))

                st.markdown("---")
                st.markdown("### 💪 강점")
                strengths = [(categories[i], values[i]) for i in range(5)]
                strengths.sort(key=lambda x: x[1], reverse=True)
                for cat, val in strengths[:2]:
                    st.success(f"✅ {cat}: {val:.1f}")

                st.markdown("### ⚠️ 약점")
                for cat, val in strengths[-2:]:
                    st.warning(f"❗ {cat}: {val:.1f}")

            st.markdown("---")

            # 포지션별 핵심 스텟 상세
            st.subheader("🎯 포지션별 핵심 스텟")

            # 주요 능력치 선택 (포지션에 따라)
            if player_data['Position_Category'] == 'Goalkeeper':
                key_attrs = ['Reflexes', 'Handling', 'OneOnOnes', 'CommandOfArea', 'Kicking', 'Agility']
            elif player_data['Position_Category'] == 'Defender':
                key_attrs = ['Marking', 'Tackling', 'Heading', 'Positioning', 'Strength', 'Pace']
            elif player_data['Position_Category'] == 'Midfielder':
                key_attrs = ['Passing', 'Vision', 'Technique', 'Stamina', 'Workrate', 'FirstTouch']
            else:  # Forward
                key_attrs = ['Finishing', 'Dribbling', 'Pace', 'Acceleration', 'Composure', 'OffTheBall']

            values_detail = [player_data[attr] for attr in key_attrs]

            fig_radar_detail = go.Figure()

            fig_radar_detail.add_trace(go.Scatterpolar(
                r=values_detail,
                theta=key_attrs,
                fill='toself',
                name=player_data['Name'],
                line_color='#EF553B',
                fillcolor='rgba(239, 85, 59, 0.3)',
                line_width=2
            ))

            fig_radar_detail.update_layout(
                polar=dict(
                    bgcolor='rgba(240,240,240,0.5)',
                    radialaxis=dict(
                        visible=True,
                        range=[0, 20],
                        tickmode='linear',
                        tick0=0,
                        dtick=5
                    )
                ),
                showlegend=False,
                height=450,
                title=f"{player_data['Position_Category']} 핵심 능력치"
            )

            st.plotly_chart(fig_radar_detail, use_container_width=True)

            # 상세 능력치 테이블
            st.markdown("---")
            st.subheader("📋 전체 능력치 상세")

            col1, col2, col3 = st.columns(3)

            # 기술 능력치
            with col1:
                with st.expander("⚙️ 기술 능력치", expanded=True):
                    tech_cols = processor.TECHNICAL_ATTRIBUTES
                    tech_data = {attr: player_data[attr] for attr in tech_cols if attr in player_data.index}
                    tech_df = pd.DataFrame(list(tech_data.items()), columns=['능력치', '수치'])
                    tech_df['수치'] = tech_df['수치'].round(1)
                    tech_df = tech_df.sort_values('수치', ascending=False)
                    st.dataframe(tech_df, use_container_width=True, height=300)

            # 정신 능력치
            with col2:
                with st.expander("🧠 정신 능력치", expanded=True):
                    mental_cols = processor.MENTAL_ATTRIBUTES
                    mental_data = {attr: player_data[attr] for attr in mental_cols if attr in player_data.index}
                    mental_df = pd.DataFrame(list(mental_data.items()), columns=['능력치', '수치'])
                    mental_df['수치'] = mental_df['수치'].round(1)
                    mental_df = mental_df.sort_values('수치', ascending=False)
                    st.dataframe(mental_df, use_container_width=True, height=300)

            # 신체 능력치
            with col3:
                with st.expander("💪 신체 능력치", expanded=True):
                    phys_cols = processor.PHYSICAL_ATTRIBUTES
                    phys_data = {attr: player_data[attr] for attr in phys_cols if attr in player_data.index}
                    phys_df = pd.DataFrame(list(phys_data.items()), columns=['능력치', '수치'])
                    phys_df['수치'] = phys_df['수치'].round(1)
                    phys_df = phys_df.sort_values('수치', ascending=False)
                    st.dataframe(phys_df, use_container_width=True, height=300)

        else:
            st.warning("필터 조건에 맞는 선수가 없습니다.")

    # 푸터
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            ⚽ 축구 유망주 탐색 대시보드<br>
            데이터: Football Manager 선수 데이터베이스
        </div>
        """,
        unsafe_allow_html=True
    )
