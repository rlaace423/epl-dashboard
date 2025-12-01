import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data_processor import FootballDataProcessor
from streamlit_plotly_events import plotly_events


def show_page():
    # 캐싱을 통한 데이터 로드 최적화
    @st.cache_data
    def load_data():
        """데이터 로드 및 처리 (캐싱)"""
        processor = FootballDataProcessor('dataset_new.csv')
        df = processor.process_all()
        return df, processor

    # 데이터 로드
    with st.spinner('데이터를 로딩 중입니다...'):
        df, processor = load_data()

    # 타이틀
    st.title("⚽ 선수 탐색 대시보드")
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
        help="선수를 찾기 위한 나이 범위를 선택하세요"
    )

    st.sidebar.markdown("---")

    # 점수 산출 방식 설명 (클릭하여 확인)
    with st.sidebar.expander("📖 점수 산출 방식 (클릭하여 확인)"):
        st.markdown("""
            ### 🎯 유망주 점수 계산 방식

            **1. 필터 기반 점수 (현재 적용)**
            - 아래 슬라이더에서 설정한 능력치들의 **평균값**으로 순위 결정
            - 각 능력치에 **동등한 가중치** 적용

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
            if stat_name in df_filtered.columns:
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
                    available_active_stats = [s for s in active_stats if s in df_score.columns]
                    if available_active_stats:
                        df_score['Filter_Score'] = df_score[available_active_stats].mean(axis=1)
                    else:
                        df_score['Filter_Score'] = df_score['Overall_Rating']

                    # 나이 가중치 적용
                    # age_weight = np.where(df_score['Age'] <= 21, 1.2,
                    #                       np.where(df_score['Age'] <= 24, 1.0, 0.8))
                    age_weight = 1.0
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
                    plot_bgcolor='rgba(0,0,0,0)',  # 배경 투명
                    paper_bgcolor='rgba(0,0,0,0)',
                    template='plotly_dark',
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

        # 선택된 선수가 없으면 안내 메시지
        if len(st.session_state.clicked_players) == 0:
            st.warning("⚠️ 선수 발굴 탭에서 선수를 먼저 선택해주세요.")
            st.info("👈 **선수 발굴** 탭에서 비교할 선수를 클릭하면 여기서 비교할 수 있습니다.")
        else:
            # 선택된 선수들만 필터링
            top_compare = df_filtered[df_filtered['Name'].isin(st.session_state.clicked_players)]
            
            if len(top_compare) == 0:
                st.warning("⚠️ 선택된 선수가 현재 필터 조건에 맞지 않습니다.")
            else:
                st.info(
                    f"💡 **선택된 {len(top_compare)}명의 선수**를 평행 좌표계로 비교합니다. "
                    "각 축에서 드래그하여 범위를 지정하면 해당 조건에 맞는 선수만 필터링됩니다."
                )

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

                # 존재하는 컬럼만 사용
                compare_attrs = [a for a in compare_attrs if a in top_compare.columns]

                # 데이터 준비
                compare_data = top_compare[compare_attrs + ['Name', 'Position_Category']].copy()

                # 선수별 색상 정의
                player_colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A']
                
                # 라인 차트 기반 평행좌표계 (hover 지원)
                fig_parallel = go.Figure()
                
                # 각 축의 범위 계산
                attr_ranges = {}
                for attr in compare_attrs:
                    attr_ranges[attr] = {
                        'min': top_compare[attr].min(),
                        'max': top_compare[attr].max()
                    }
                
                # 정규화 함수 (0-1 범위로)
                def normalize_value(value, attr):
                    min_val = attr_ranges[attr]['min']
                    max_val = attr_ranges[attr]['max']
                    if max_val == min_val:
                        return 0.5
                    return (value - min_val) / (max_val - min_val)
                
                # 각 선수별 라인 추가
                for idx, (_, player_row) in enumerate(top_compare.iterrows()):
                    player_name = player_row['Name']
                    
                    # 정규화된 y값
                    y_values = [normalize_value(player_row[attr], attr) for attr in compare_attrs]
                    
                    # 실제 값 (hover용)
                    actual_values = [player_row[attr] for attr in compare_attrs]
                    
                    fig_parallel.add_trace(go.Scatter(
                        x=compare_attrs,
                        y=y_values,
                        mode='lines+markers',
                        name=player_name,
                        line=dict(color=player_colors[idx % len(player_colors)], width=3),
                        marker=dict(size=10, color=player_colors[idx % len(player_colors)]),
                        customdata=[[actual_values[i]] for i in range(len(compare_attrs))],
                        hovertemplate='<b>%{customdata[0]:.1f}</b><extra></extra>'
                    ))
                
                # x축 레이블 설정
                fig_parallel.update_layout(
                    title=f'선택된 {len(top_compare)}명 선수 비교 - {selected_position if selected_position != "All" else "전체 포지션"}',
                    height=500,
                    margin=dict(l=50, r=50, t=80, b=120),
                    xaxis=dict(
                        tickangle=45,
                        tickfont=dict(size=11)
                    ),
                    yaxis=dict(
                        title='정규화된 값 (0-1)',
                        range=[-0.05, 1.05],
                        showgrid=True,
                        gridcolor='lightgray'
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.25,
                        xanchor="center",
                        x=0.5
                    ),
                    hovermode='x unified',
                    hoverlabel=dict(
                        bgcolor="white",
                        font_size=12,
                        namelength=-1
                    )
                )
                
                # 각 축에 실제 범위 표시 (상단/하단에 주석)
                for i, attr in enumerate(compare_attrs):
                    # 최대값 표시 (상단)
                    fig_parallel.add_annotation(
                        x=attr, y=1.08,
                        text=f"{attr_ranges[attr]['max']:.1f}",
                        showarrow=False,
                        font=dict(size=9, color='gray')
                    )
                    # 최소값 표시 (하단)
                    fig_parallel.add_annotation(
                        x=attr, y=-0.08,
                        text=f"{attr_ranges[attr]['min']:.1f}",
                        showarrow=False,
                        font=dict(size=9, color='gray')
                    )

                st.plotly_chart(fig_parallel, use_container_width=True)
                
                st.caption("💡 **Tip**: 마우스를 라인 위에 올리면 선수 이름과 해당 능력치 값을 확인할 수 있습니다.")

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
                selected_players_tab2 = st.multiselect(
                    "비교할 선수 선택 (최대 3명)",
                    options=top_compare['Name'].tolist(),
                    default=top_compare['Name'].tolist()[:min(3, len(top_compare))],
                    max_selections=3,
                    help="선택한 선수들의 능력치를 레이더 차트로 비교합니다"
                )

                if len(selected_players_tab2) > 0:
                    col1, col2 = st.columns(2)

                    with col1:
                        # 5개 대분류 레이더 차트
                        st.markdown("#### 능력치 프로필 비교 (5개 대분류)")

                        fig_compare_radar = go.Figure()

                        categories = ['공격력', '수비력', '기술', '멘탈', '신체']
                        colors = ['#636EFA', '#EF553B', '#00CC96']

                        for idx, player_name in enumerate(selected_players_tab2):
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

                        # 존재하는 컬럼만 사용
                        key_stats = [s for s in key_stats if s in top_compare.columns]

                        fig_bar_compare = go.Figure()

                        for player_name in selected_players_tab2:
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
        st.header("🏆 선택된 유망주 랭킹")

        # 선택된 선수가 없으면 안내 메시지
        if len(st.session_state.clicked_players) == 0:
            st.warning("⚠️ 선수 발굴 탭에서 선수를 먼저 선택해주세요.")
            st.info("👈 **선수 발굴** 탭에서 유망주를 클릭하면 여기서 상세 정보를 볼 수 있습니다.")
        else:
            # 선택된 선수들만 필터링
            selected_talents = df_filtered[df_filtered['Name'].isin(st.session_state.clicked_players)]
            
            if len(selected_talents) == 0:
                st.warning("⚠️ 선택된 선수가 현재 필터 조건에 맞지 않습니다.")
            else:
                st.subheader(f"선택된 {len(selected_talents)}명의 유망주")

                # 선택된 선수들 바 차트
                fig_bar = px.bar(
                    selected_talents.sort_values('Talent_Score_Normalized', ascending=True),
                    x='Talent_Score_Normalized',
                    y='Name',
                    orientation='h',
                    color='Age',
                    title='선택된 유망주 순위',
                    labels={
                        'Talent_Score_Normalized': '유망주 점수',
                        'Name': '선수명',
                        'Age': '나이'
                    },
                    color_continuous_scale='RdYlGn_r',
                    hover_data=['Position_Category', 'Overall_Rating']
                )

                fig_bar.update_layout(
                    height=max(300, len(selected_talents) * 50),
                    yaxis={'categoryorder': 'total ascending'}
                )

                st.plotly_chart(fig_bar, use_container_width=True)

                # 상위 유망주 테이블
                st.subheader("선택된 유망주 상세 리스트")

                display_cols = [
                    'Name', 'Age', 'Position_Category', 'Overall_Rating',
                    'Technical_Rating', 'Mental_Rating', 'Physical_Rating',
                    'Talent_Score_Normalized'
                ]

                display_df = selected_talents[display_cols].copy()
                display_df.columns = [
                    '이름', '나이', '포지션', '종합능력치',
                    '기술', '정신', '신체', '유망주점수'
                ]

                # 숫자 포맷팅
                for col in ['종합능력치', '기술', '정신', '신체', '유망주점수']:
                    display_df[col] = display_df[col].round(2)

                st.dataframe(
                    display_df.sort_values('유망주점수', ascending=False),
                    use_container_width=True,
                    height=400
                )

                # CSV 다운로드
                csv = selected_talents.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 선택된 유망주 데이터 다운로드 (CSV)",
                    data=csv,
                    file_name='selected_talents.csv',
                    mime='text/csv',
                )

    # 탭 4: 포지션별 분석
    with tab4:
        st.header("📈 포지션별 분석")

        if len(df_filtered) > 0:
            # 포지션별 통계
            position_stats_df = df_filtered.groupby('Position_Category').agg({
                'Talent_Score_Normalized': ['mean', 'max', 'count'],
                'Overall_Rating': 'mean',
                'Age': 'mean'
            }).round(2)

            position_stats_df.columns = ['평균 유망주 점수', '최고 유망주 점수', '선수 수', '평균 능력치', '평균 나이']
            position_stats_df = position_stats_df.reset_index()
            position_stats_df.columns = ['포지션', '평균 유망주 점수', '최고 유망주 점수', '선수 수', '평균 능력치', '평균 나이']

            col1, col2 = st.columns(2)

            with col1:
                # 포지션별 평균 유망주 점수
                fig_pos_avg = px.bar(
                    position_stats_df,
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
                    position_stats_df,
                    values='선수 수',
                    names='포지션',
                    title='포지션별 선수 분포',
                    hole=0.4
                )
                fig_pos_count.update_layout(height=400)
                st.plotly_chart(fig_pos_count, use_container_width=True)

            # 포지션별 통계 테이블
            st.subheader("포지션별 상세 통계")
            st.dataframe(position_stats_df, use_container_width=True)

            # 포지션별 능력치 비교 (박스 플롯)
            st.subheader("포지션별 능력치 분포 비교")

            fig_box = go.Figure()

            for category in ['Technical_Rating', 'Mental_Rating', 'Physical_Rating']:
                if category in df_filtered.columns:
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
        st.header("👤 선수 프로필 - 상세 비교 분석")

        # 선택된 선수가 없으면 안내 메시지
        if len(st.session_state.clicked_players) == 0:
            st.warning("⚠️ 선수 발굴 탭에서 선수를 먼저 선택해주세요.")
            st.info("👈 **선수 발굴** 탭에서 선수를 클릭하면 여기서 상세 프로필을 비교할 수 있습니다.")
        else:
            # 선택된 선수들만 필터링
            selected_for_profile = df_filtered[df_filtered['Name'].isin(st.session_state.clicked_players)]
            
            if len(selected_for_profile) == 0:
                st.warning("⚠️ 선택된 선수가 현재 필터 조건에 맞지 않습니다.")
            else:
                st.info(f"💡 선택된 **{len(selected_for_profile)}명**의 선수를 비교 분석합니다.")

                # 선수 기본 정보 비교 테이블
                st.subheader("📋 선수 기본 정보 비교")
                
                basic_info_cols = ['Name', 'Age', 'Position_Category', 'Overall_Rating', 'Talent_Score_Normalized']
                basic_df = selected_for_profile[basic_info_cols].copy()
                basic_df.columns = ['선수명', '나이', '포지션', '종합능력', '유망주점수']
                basic_df = basic_df.round(2)
                st.dataframe(basic_df, use_container_width=True, hide_index=True)

                st.markdown("---")

                # 5개 대분류 레이더 차트 비교
                st.subheader("🕸️ 5대 분류 능력치 비교")
                
                categories = ['Attacking', 'Defending', 'Technical', 'Mental', 'Physical']
                attacking_attrs = ['Finishing', 'LongShots', 'Heading', 'OffTheBall']
                defending_attrs = ['Marking', 'Tackling', 'Positioning', 'Anticipation']
                technical_attrs = ['Dribbling', 'Passing', 'FirstTouch', 'Technique', 'Crossing']
                mental_attrs = ['Composure', 'Vision', 'Decisions', 'Determination', 'Workrate']
                physical_attrs = ['Pace', 'Acceleration', 'Stamina', 'Strength', 'Agility']
                
                colors_profile = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A']
                
                col_radar, col_bar = st.columns([1, 1])
                
                with col_radar:
                    fig_radar_compare = go.Figure()
                    
                    all_player_values = []
                    for idx, (_, player_row) in enumerate(selected_for_profile.iterrows()):
                        values = [
                            player_row[[a for a in attacking_attrs if a in df_filtered.columns]].mean(),
                            player_row[[a for a in defending_attrs if a in df_filtered.columns]].mean(),
                            player_row[[a for a in technical_attrs if a in df_filtered.columns]].mean(),
                            player_row[[a for a in mental_attrs if a in df_filtered.columns]].mean(),
                            player_row[[a for a in physical_attrs if a in df_filtered.columns]].mean()
                        ]
                        all_player_values.append({'name': player_row['Name'], 'values': values})
                        
                        fig_radar_compare.add_trace(go.Scatterpolar(
                            r=values,
                            theta=categories,
                            fill='toself',
                            name=player_row['Name'],
                            line_color=colors_profile[idx % 5],
                            fillcolor=f'rgba{tuple(list(int(colors_profile[idx % 5][i:i + 2], 16) for i in (1, 3, 5)) + [0.2])}',
                            line_width=2
                        ))
                    
                    fig_radar_compare.update_layout(
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
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                        height=450,
                        title="5대 분류 레이더 차트"
                    )
                    
                    st.plotly_chart(fig_radar_compare, use_container_width=True)
                
                with col_bar:
                    # 그룹 바 차트로 5대 분류 비교
                    fig_bar_5cat = go.Figure()
                    
                    for pv in all_player_values:
                        fig_bar_5cat.add_trace(go.Bar(
                            name=pv['name'],
                            x=categories,
                            y=pv['values'],
                            text=[f'{v:.1f}' for v in pv['values']],
                            textposition='auto'
                        ))
                    
                    fig_bar_5cat.update_layout(
                        barmode='group',
                        height=450,
                        yaxis=dict(range=[0, 20], title="점수"),
                        xaxis_title="분류",
                        title="5대 분류 바 차트 비교",
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
                    )
                    
                    st.plotly_chart(fig_bar_5cat, use_container_width=True)

                st.markdown("---")

                # 포지션별 핵심 스텟 비교
                st.subheader("🎯 핵심 스텟 비교")
                
                # 첫 번째 선수의 포지션 기준으로 핵심 스텟 결정
                first_position = selected_for_profile.iloc[0]['Position_Category']
                
                if first_position == 'Goalkeeper':
                    key_attrs = ['Reflexes', 'Handling', 'OneOnOnes', 'CommandOfArea', 'Kicking', 'Agility']
                elif first_position == 'Defender':
                    key_attrs = ['Marking', 'Tackling', 'Heading', 'Positioning', 'Strength', 'Pace']
                elif first_position == 'Midfielder':
                    key_attrs = ['Passing', 'Vision', 'Technique', 'Stamina', 'Workrate', 'FirstTouch']
                else:  # Forward
                    key_attrs = ['Finishing', 'Dribbling', 'Pace', 'Acceleration', 'Composure', 'OffTheBall']
                
                key_attrs = [a for a in key_attrs if a in df_filtered.columns]
                
                col_key_radar, col_key_bar = st.columns([1, 1])
                
                with col_key_radar:
                    fig_key_radar = go.Figure()
                    
                    for idx, (_, player_row) in enumerate(selected_for_profile.iterrows()):
                        key_values = [player_row[attr] for attr in key_attrs]
                        
                        fig_key_radar.add_trace(go.Scatterpolar(
                            r=key_values,
                            theta=key_attrs,
                            fill='toself',
                            name=player_row['Name'],
                            line_color=colors_profile[idx % 5],
                            fillcolor=f'rgba{tuple(list(int(colors_profile[idx % 5][i:i + 2], 16) for i in (1, 3, 5)) + [0.2])}',
                            line_width=2
                        ))
                    
                    fig_key_radar.update_layout(
                        polar=dict(
                            bgcolor='rgba(240,240,240,0.5)',
                            radialaxis=dict(visible=True, range=[0, 20])
                        ),
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                        height=450,
                        title=f"{first_position} 핵심 스텟 레이더"
                    )
                    
                    st.plotly_chart(fig_key_radar, use_container_width=True)
                
                with col_key_bar:
                    fig_key_bar = go.Figure()
                    
                    for idx, (_, player_row) in enumerate(selected_for_profile.iterrows()):
                        key_values = [player_row[attr] for attr in key_attrs]
                        
                        fig_key_bar.add_trace(go.Bar(
                            name=player_row['Name'],
                            x=key_attrs,
                            y=key_values,
                            text=[f'{v:.1f}' for v in key_values],
                            textposition='auto'
                        ))
                    
                    fig_key_bar.update_layout(
                        barmode='group',
                        height=450,
                        yaxis=dict(range=[0, 20], title="점수"),
                        xaxis_title="능력치",
                        title=f"{first_position} 핵심 스텟 바 차트",
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
                    )
                    
                    st.plotly_chart(fig_key_bar, use_container_width=True)

                st.markdown("---")

                # 상세 능력치 비교 테이블
                st.subheader("📊 상세 능력치 비교")
                
                tab_tech, tab_mental, tab_phys = st.tabs(["⚙️ 기술 능력치", "🧠 정신 능력치", "💪 신체 능력치"])
                
                with tab_tech:
                    tech_cols = [c for c in processor.TECHNICAL_ATTRIBUTES if c in df_filtered.columns]
                    tech_compare_df = selected_for_profile[['Name'] + tech_cols].copy()
                    tech_compare_df = tech_compare_df.set_index('Name').T
                    tech_compare_df = tech_compare_df.round(1)
                    tech_compare_df.index.name = '능력치'
                    st.dataframe(tech_compare_df, use_container_width=True, height=400)
                    
                    # 기술 능력치 히트맵
                    fig_tech_heat = px.imshow(
                        tech_compare_df.values,
                        labels=dict(x="선수", y="능력치", color="점수"),
                        x=tech_compare_df.columns.tolist(),
                        y=tech_compare_df.index.tolist(),
                        color_continuous_scale='RdYlGn',
                        title="기술 능력치 히트맵"
                    )
                    fig_tech_heat.update_layout(height=500)
                    st.plotly_chart(fig_tech_heat, use_container_width=True)
                
                with tab_mental:
                    mental_cols = [c for c in processor.MENTAL_ATTRIBUTES if c in df_filtered.columns]
                    mental_compare_df = selected_for_profile[['Name'] + mental_cols].copy()
                    mental_compare_df = mental_compare_df.set_index('Name').T
                    mental_compare_df = mental_compare_df.round(1)
                    mental_compare_df.index.name = '능력치'
                    st.dataframe(mental_compare_df, use_container_width=True, height=400)
                    
                    # 정신 능력치 히트맵
                    fig_mental_heat = px.imshow(
                        mental_compare_df.values,
                        labels=dict(x="선수", y="능력치", color="점수"),
                        x=mental_compare_df.columns.tolist(),
                        y=mental_compare_df.index.tolist(),
                        color_continuous_scale='RdYlGn',
                        title="정신 능력치 히트맵"
                    )
                    fig_mental_heat.update_layout(height=500)
                    st.plotly_chart(fig_mental_heat, use_container_width=True)
                
                with tab_phys:
                    phys_cols = [c for c in processor.PHYSICAL_ATTRIBUTES if c in df_filtered.columns]
                    phys_compare_df = selected_for_profile[['Name'] + phys_cols].copy()
                    phys_compare_df = phys_compare_df.set_index('Name').T
                    phys_compare_df = phys_compare_df.round(1)
                    phys_compare_df.index.name = '능력치'
                    st.dataframe(phys_compare_df, use_container_width=True, height=300)
                    
                    # 신체 능력치 히트맵
                    fig_phys_heat = px.imshow(
                        phys_compare_df.values,
                        labels=dict(x="선수", y="능력치", color="점수"),
                        x=phys_compare_df.columns.tolist(),
                        y=phys_compare_df.index.tolist(),
                        color_continuous_scale='RdYlGn',
                        title="신체 능력치 히트맵"
                    )
                    fig_phys_heat.update_layout(height=400)
                    st.plotly_chart(fig_phys_heat, use_container_width=True)

                st.markdown("---")

                # 종합 점수 비교 바 차트
                st.subheader("🏆 종합 점수 비교")
                
                score_cols = ['Name', 'Overall_Rating', 'Technical_Rating', 'Mental_Rating', 'Physical_Rating', 'Talent_Score_Normalized']
                score_df = selected_for_profile[score_cols].copy()
                
                fig_score = go.Figure()
                
                for _, row in score_df.iterrows():
                    fig_score.add_trace(go.Bar(
                        name=row['Name'],
                        x=['종합능력', '기술', '정신', '신체', '유망주점수'],
                        y=[row['Overall_Rating'], row['Technical_Rating'], row['Mental_Rating'], 
                           row['Physical_Rating'], row['Talent_Score_Normalized'] / 5],  # 유망주점수 스케일 조정
                        text=[f'{row["Overall_Rating"]:.1f}', f'{row["Technical_Rating"]:.1f}', 
                              f'{row["Mental_Rating"]:.1f}', f'{row["Physical_Rating"]:.1f}',
                              f'{row["Talent_Score_Normalized"]:.1f}'],
                        textposition='auto'
                    ))
                
                fig_score.update_layout(
                    barmode='group',
                    height=500,
                    margin=dict(t=30, b=120, l=50, r=50),
                    yaxis=dict(range=[0, 25], title="점수"),
                    xaxis_title="분류",
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5)
                )
                
                st.plotly_chart(fig_score, use_container_width=True)
                st.caption("※ 유망주점수는 0-100 범위를 0-20 스케일로 조정하여 표시")

    # 푸터
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            ⚽ 선수 탐색 대시보드<br>
            데이터: Football Manager 선수 데이터베이스
        </div>
        """,
        unsafe_allow_html=True
    )

