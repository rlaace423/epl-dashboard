import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components
import textwrap
import os
import toml
import base64
import mimetypes

CSV_FILE = 'epl_2024_2025_full_stats.csv'

def get_theme_colors():
    """
    .streamlit/config.toml 파일을 읽어 테마에 맞는 배경색과 텍스트 색상을 반환합니다.
    """
    default_bg = "#0E1117"
    default_text = "white"

    try:
        config_path = ".streamlit/config.toml"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = toml.load(f)

            theme_base = config.get("theme", {}).get("base", "dark")

            if theme_base == "light":
                return "#ffffff", "black"
            else:
                return "#0E1117", "white"

    except Exception:
        pass

    return default_bg, default_text


def get_image_base64(file_path):
    """
    로컬 이미지 파일을 읽어서 HTML에서 바로 사용할 수 있는 Base64 문자열로 변환합니다.
    SVG, WebP, PNG 등 다양한 포맷을 지원합니다.
    """
    if not os.path.exists(file_path):
        # 파일이 없으면 빈 문자열 반환 (또는 기본 이미지 경로 설정 가능)
        return ""

    # 파일 확장자에 따른 MIME 타입 추론 (예: image/svg+xml, image/webp)
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "image/png"  # 기본값

    with open(file_path, "rb") as f:
        data = f.read()
        encoded = base64.b64encode(data).decode()

    return f"data:{mime_type};base64,{encoded}"


def custom_min_max_scale(series):
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return series
    return (series - min_val) / (max_val - min_val)
    
# ---------------------------------------------------------
# 분석 함수: 선택된 팀의 강점/약점을 분석하여 문구 생성
# ---------------------------------------------------------
def analyze_team_performance(team_name: str, df_scaled: pd.DataFrame, df_raw: pd.DataFrame):
    """
    선택된 팀의 총 득점 순위(Gls_Rank)를 기준으로 상위권/중위권/하위권을 판단하고, 
    13가지 확장 지표를 분석하여 포지션별 강점/약점 및 영입 포지션 제안 문구를 반환합니다.
    """
    
    # 1. 득점 순위(Rank) 부여 및 데이터 준비
    # (주의: df_raw는 전체 20팀을 포함해야 Gls_Rank가 정확함)
    df_ranked = df_raw.copy()
    # Gls 기준 내림차순 정렬 후 순위 컬럼 추가 (1부터 시작)
    df_ranked['Gls_Rank'] = df_ranked['Gls'].rank(ascending=False, method='min').astype(int)
    
    team_data_scaled = df_scaled[df_scaled['Squad'] == team_name].iloc[0]
    team_data_raw = df_raw[df_raw['Squad'] == team_name].iloc[0]
    team_rank = df_ranked[df_ranked['Squad'] == team_name].iloc[0]['Gls_Rank']

    # 2. 득점 순위 기준 Tier 분류 (상위 7, 중위 8-14, 하위 15-20)
    if team_rank <= 7:
        rank_tier = "상위권"
    elif team_rank <= 14:
        rank_tier = "중위권"
    else:
        rank_tier = "하위권"
        
    # 3. 상세 강점/약점 분석 및 포지션 매칭
    STRENGTH_THRESHOLD = 0.75 # 상위 25%
    WEAKNESS_THRESHOLD = 0.25 # 하위 25%

    all_strengths = []
    all_weaknesses = []
    recruitment_recommendations = set() # 중복 방지를 위해 set 사용

    # 포지션 및 지표 매핑 (13가지 확장 지표)
    RECRUITMENT_METRICS = {
        '공격수/피니셔': {
            'Gls': ('득점력', '골 결정력'), 'G/SoT': ('슈팅 효율', '슈팅 정확도')
        },
        '플레이메이커/윙어': {
            'Ast': ('어시스트 능력', '어시스트 부족'), 'SCA90': ('기회 창출력', '기회 창출 부족'), 'G+A': ('공격 포인트 생산성', '공격 포인트 부족')
        },
        '미드필더/빌드업': {
            'Cmp%': ('패스 성공률', '패스 정확도'), 'PrgDist': ('공격 전개 깊이', '수직 패스 부족'), 
        },
        '볼 위닝/수비수': {
            'Tkl%': ('태클 성공률', '태클 실패율'), 'Int': ('수비 공간 인지력', '인터셉트 부족'),
        },
        '수비 조직력/CB': {
            'xGA': ('수비 구조 안정성', '허용 기대 득점'), # NOTE: xGA는 역방향 처리되어 df_scaled에서 높은 값이 좋음
        },
        '골키퍼': {
            'Save%': ('선방률', '선방 부족')
        },
        '공격 볼륨': { # 공격 전반의 볼륨 측정
             'SoT/90': ('슈팅 집중도', '슈팅 볼륨 부족'),
        }
    }

    # 5가지 카테고리별로 반복하며 강점/약점 분석
    for category, metrics in RECRUITMENT_METRICS.items():
        category_has_weakness = False
        
        for col, (good_name, bad_name) in metrics.items():
            score = team_data_scaled[col]
            raw_value = team_data_raw[col]
            
            # ⬇️ 강점 (빨간색, 상위 25%)
            if score >= STRENGTH_THRESHOLD:
                all_strengths.append(f"**{good_name}** ({raw_value:.1f})")
            
            # ⬇️ 약점 (파란색, 하위 25%)
            elif score <= WEAKNESS_THRESHOLD:
                all_weaknesses.append(f"**{bad_name}** ({raw_value:.1f})")
                category_has_weakness = True
                
        # 약점이 발견된 카테고리에 대해 포지션 추천 목록에 추가
        if category_has_weakness:
            recruitment_recommendations.add(category) # 중복 방지

    # 6. 최종 메시지 조합
    
    # 득점 순위 기반 요약 문장 생성
    if team_rank <= 7:
        summary_line = f"**{team_name}** 팀은 **총 득점 {team_rank}위**로, 리그 {rank_tier}의 압도적인 공격력을 보여주고 있습니다."
    elif team_rank <= 14:
        summary_line = f"**{team_name}** 팀은 **총 득점 {team_rank}위**로, 리그 {rank_tier} 수준의 균형 잡힌 공격력을 갖추고 있습니다."
    else:
        summary_line = f"**{team_name}** 팀은 **총 득점 {team_rank}위**로, 리그 {rank_tier}의 득점력 부족이 심각합니다."
    
    # 상세 분석 문구
    strength_msg_detail = f" 🥇 주요 강점: {', '.join(all_strengths)}" if all_strengths else " 🥇 주요 강점: 특별히 두드러지는 강점은 없습니다."
    weakness_msg_detail = f" 📉 주요 약점: {', '.join(all_weaknesses)}" if all_weaknesses else " 📉 주요 약점: 심각한 약점은 발견되지 않았습니다."

    # 영입 제안 문구
    if recruitment_recommendations:
        recommendation_list = ', '.join(sorted(list(recruitment_recommendations)))
        recommendation_msg = (
            f"🎯 **유망주 영입 포지션 제안:**\n팀의 약점을 보완하기 위해 **{recommendation_list}** 포지션의 유망주 영입을 고려해야 합니다."
        )
    else:
        recommendation_msg = "🎯 **유망주 영입 포지션 제안:**\n모든 핵심 포지션이 안정적이므로, 스쿼드 뎁스 강화 위주로 전략을 세우세요."

    # 전체 메시지 통합 (줄바꿈 \n 사용)
    message = (
        f"👉 분석 결과 ({rank_tier}): {summary_line}\n\n"
        f"{strength_msg_detail}\n\n"
        f"{weakness_msg_detail}\n\n"
        f"{recommendation_msg}"
    )
    
    return message, rank_tier

def show_page():
    st.title("🏆 프리미어 리그(EPL) 팀 분석")
    st.markdown("##### 우리 팀의 현재 위치와 약점을 분석합니다.")
    st.markdown("---")

    # ---------------------------------------------------------
    # 1. 상단 팀 순위 카드 (가로 스크롤 캐러셀 UI)
    # ---------------------------------------------------------

    bg_color, text_color = get_theme_colors()

    # [데이터 준비]
    # 확장자가 섞여 있어도 상관없습니다. 실제 파일명과 경로만 정확하면 됩니다.
    team_rankings = [
        {"rank": 1, "name": "Liverpool", "w": 25, "d": 9,  "l": 4,  "pts": 84, "gf": 86, "ga": 41,
        "color": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)", "logo": "assets/logos/Liverpool_FC_logo.svg"},
        {"rank": 2, "name": "Arsenal", "w": 20, "d": 14, "l": 4,  "pts": 74, "gf": 69, "ga": 34,
        "color": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "logo": "assets/logos/Arsenal_FC_logo.svg"},
        {"rank": 3, "name": "Manchester City", "w": 21, "d": 8,  "l": 9,  "pts": 71, "gf": 72, "ga": 44,
        "color": "linear-gradient(135deg, #30cfd0 0%, #330867 100%)", "logo": "assets/logos/Manchester_City_2016.svg"},
        {"rank": 4, "name": "Chelsea", "w": 20, "d": 9,  "l": 9,  "pts": 69, "gf": 64, "ga": 43,
        "color": "linear-gradient(135deg, #209cff 0%, #68e0cf 100%)", "logo": "assets/logos/Chelsea_FC_logo.svg"},
        {"rank": 5, "name": "Newcastle Utd", "w": 20, "d": 6,  "l": 12, "pts": 66, "gf": 68, "ga": 47,
        "color": "linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)", "logo": "assets/logos/Newcastle_United_FC_logo.svg"},
        {"rank": 6, "name": "Aston Villa", "w": 19, "d": 9,  "l": 10, "pts": 66, "gf": 58, "ga": 51,
        "color": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)", "logo": "assets/logos/Aston_Villa_FC_2015.webp"},
        {"rank": 7, "name": "Nottingham Forest", "w": 19, "d": 8,  "l": 11, "pts": 65, "gf": 58, "ga": 46,
        "color": "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)", "logo": "assets/logos/Nottingham_Forest_FC_logo_(red,_two_stars_below).webp"},
        {"rank": 8, "name": "Brighton", "w": 16, "d": 13, "l": 9,  "pts": 61, "gf": 66, "ga": 59,
        "color": "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)", "logo": "assets/logos/Brighton_&_Hove_Albion_FC_logo.svg"},
        {"rank": 9, "name": "Bournemouth", "w": 15, "d": 11, "l": 12, "pts": 56, "gf": 58, "ga": 46,
        "color": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)", "logo": "assets/logos/AFC_Bournemouth_logo_(introduced_2013).svg"},
        {"rank": 10, "name": "Brentford", "w": 16, "d": 8,  "l": 14, "pts": 56, "gf": 66, "ga": 57,
        "color": "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)", "logo": "assets/logos/Brentford_FC_2017.webp"},
        # {"rank": 11, "name": "Fulham", "w": 15, "d": 9,  "l": 14, "pts": 54, "gf": 54, "ga": 54,
        #  "color": "linear-gradient(135deg, #f6d365 0%, #fda085 100%)", "logo": "assets/logos/Fulham_FC_logo.svg"},
        # {"rank": 12, "name": "Crystal Palace", "w": 13, "d": 14, "l": 11, "pts": 53, "gf": 51, "ga": 51,
        #  "color": "linear-gradient(135deg, #cfd9df 0%, #e2ebf0 100%)", "logo": "assets/logos/Crystal_Palace_FC_logo.svg"},
        # {"rank": 13, "name": "Everton", "w": 11, "d": 15, "l": 12, "pts": 48, "gf": 42, "ga": 44,
        #  "color": "linear-gradient(135deg, #74ebd5 0%, #9face6 100%)", "logo": "assets/logos/Everton_FC_logo.svg"},
        # {"rank": 14, "name": "West Ham", "w": 11, "d": 10, "l": 17, "pts": 43, "gf": 46, "ga": 62,
        #  "color": "linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%)", "logo": "assets/logos/West_Ham_United_FC_logo.svg"},
        # {"rank": 15, "name": "Manchester Utd", "w": 11, "d": 9,  "l": 18, "pts": 42, "gf": 44, "ga": 54,
        #  "color": "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)", "logo": "assets/logos/Manchester_United_FC_logo.svg"},
        # {"rank": 16, "name": "Wolves", "w": 12, "d": 6,  "l": 20, "pts": 42, "gf": 54, "ga": 69,
        #  "color": "linear-gradient(135deg, #fdcbf1 0%, #cfd9df 100%)", "logo": "assets/logos/Wolverhampton_Wanderers_FC_logo.svg"},
        # {"rank": 17, "name": "Tottenham", "w": 11, "d": 5,  "l": 22, "pts": 38, "gf": 64, "ga": 65,
        #  "color": "linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)", "logo": "assets/logos/Tottenham_Hotspur_FC_logo.svg"},
        # {"rank": 18, "name": "Leicester City", "w": 6,  "d": 7,  "l": 25, "pts": 25, "gf": 33, "ga": 80,
        #  "color": "linear-gradient(135deg, #f6d365 0%, #fda085 100%)", "logo": "assets/logos/Leicester_City_FC_logo.svg"},
        # {"rank": 19, "name": "Ipswich Town", "w": 4,  "d": 10, "l": 24, "pts": 22, "gf": 36, "ga": 82,
        #  "color": "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)", "logo": "assets/logos/Ipswich_Town_FC_logo.svg"},
        # {"rank": 20, "name": "Southampton", "w": 2,  "d": 6,  "l": 30, "pts": 12, "gf": 26, "ga": 86,
        #  "color": "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)", "logo": "assets/logos/Southampton_FC_logo.svg"},
    ]

    # [HTML 생성]
    cards_html = ""
    for team in team_rankings:
        rank_badge = "🥇" if team['rank'] == 1 else "🥈" if team['rank'] == 2 else "🥉" if team[
                                                                                            'rank'] == 3 else f"{team['rank']}th"

        # [핵심] 로컬 이미지를 Base64로 변환하여 HTML에 주입
        # 파일이 존재하지 않으면 깨진 이미지 아이콘 대신 빈 공간이 나오도록 처리됨
        img_src = get_image_base64(team['logo'])

        # 이미지가 있으면 img 태그 사용, 없으면 빈 div (또는 대체 텍스트)
        img_tag = f'<img src="{img_src}" class="team-logo" alt="{team["name"]}">' if img_src else f'<div class="team-logo-placeholder">⚽</div>'

        card_snippet = f"""
        <div class="team-card" style="background: {team['color']};">
            <div class="card-header">
                <div class="rank-badge">{rank_badge}</div>
                {img_tag}
            </div>
            <div class="team-name">{team['name']}</div>
            <div class="team-points">{team['pts']} pts</div>
            <div class="team-stats">
                W:{team['w']} D:{team['d']} L:{team['l']}<br>
                GF:{team['gf']} GA:{team['ga']}
            </div>
        </div>
        """
        cards_html += textwrap.dedent(card_snippet)

    # [HTML/CSS]
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        html, body {{
            background-color: {bg_color} !important;
            color: {text_color} !important;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            overflow: hidden;
        }}

        .carousel-wrapper {{
            position: relative;
            display: flex;
            align-items: center;
            width: 100%;
            padding: 10px 0;
        }}

        .carousel-container {{
            display: flex;
            overflow-x: auto;
            scroll-behavior: smooth;
            padding: 20px 5px;
            gap: 20px;
            width: 100%;
            -ms-overflow-style: none;
            scrollbar-width: none;
        }}
        .carousel-container::-webkit-scrollbar {{
            display: none;
        }}

        .team-card {{
            flex: 0 0 220px;
            height: 320px;
            border-radius: 20px;
            padding: 25px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            color: white;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            position: relative;
            box-sizing: border-box;
        }}

        .team-card:hover {{
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            z-index: 10;
        }}

        .card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            margin-bottom: 15px;
        }}

        .rank-badge {{
            font-size: 1.2rem;
            background: rgba(255,255,255,0.2);
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: bold;
        }}

        /* [핵심 CSS] object-fit: contain 덕분에 이미지가 찌그러지지 않고 비율을 유지하며 박스 안에 들어갑니다 */
        .team-logo {{
            width: 60px;
            height: 60px;
            object-fit: contain; 
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
        }}

        .team-logo-placeholder {{
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
        }}

        .team-name {{
            font-size: 1.5rem;
            font-weight: 800;
            margin-bottom: 5px;
            text-align: center;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            flex-grow: 1;
            display: flex;
            align-items: center;
            justify-content: center; /* 텍스트 가운데 정렬 */
            line-height: 1.1;
        }}
        .team-points {{
            font-size: 2.2rem;
            font-weight: 900;
            margin-bottom: 15px;
        }}
        .team-stats {{
            font-size: 0.9rem;
            text-align: center;
            background: rgba(0,0,0,0.2);
            padding: 10px;
            border-radius: 10px;
            width: 100%;
            line-height: 1.5;
        }}

        .nav-btn {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 50%;
            width: 45px;
            height: 45px;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            z-index: 20;
            transition: all 0.2s;
            color: {text_color};
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .nav-btn:hover {{
            background: rgba(255, 255, 255, 0.25);
            transform: scale(1.1);
        }}
        .nav-left {{ margin-right: 15px; }}
        .nav-right {{ margin-left: 15px; }}

    </style>
    </head>
    <body>
        <div class="carousel-wrapper">
            <button class="nav-btn nav-left" onclick="scrollLeftBtn()">❮</button>
            <div class="carousel-container" id="team-carousel">
                {cards_html}
            </div>
            <button class="nav-btn nav-right" onclick="scrollRightBtn()">❯</button>
        </div>

        <script>
            const container = document.getElementById('team-carousel');

            function scrollLeftBtn() {{
                container.scrollBy({{ left: -300, behavior: 'smooth' }});
            }}

            function scrollRightBtn() {{
                container.scrollBy({{ left: 300, behavior: 'smooth' }});
            }}
        </script>
    </body>
    </html>
    """

    components.html(textwrap.dedent(html_content), height=400)

    st.markdown("---")
    # ---------------------------------------------------------
    # 2. 팀별 지표 히트맵 (CSV 파일 사용)
    # ---------------------------------------------------------
    team_order_list = ['Liverpool', 'Arsenal', 'Man City', 'Chelsea', 'Newcastle Utd', 
    'Aston Villa', 'Nott\'ham Forest',  'Brighton','Bournemouth',  'Brentford',
    'Fulham','Crystal Palace','Everton', 'West Ham', 'Man Utd', 
    'Wolves','Tottenham', 'Leicester City', 'Ipswich Town', 'Southampton']
    
    # --- 데이터 로딩 ---
    try:
        df_raw = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        st.error(f"오류: 데이터 파일 '{CSV_FILE}'을(를) 찾을 수 없습니다. 파일을 확인해주세요.")
        return
    except Exception as e:
        st.error(f"데이터 로딩 중 오류 발생: {e}")
        return

    # --- 필터링 로직 ---
    st.subheader("필터 설정")
    df_raw['Squad'] = pd.Categorical(df_raw['Squad'], categories=team_order_list, ordered=True)
    df_raw = df_raw.sort_values('Squad').reset_index(drop=True)


    filter_option = st.radio(
        "📊 표시할 팀 범위를 선택하세요:",
        ('상위 10개 팀 (승점 순)', '전체 20개 팀'),
        horizontal=True
    )

    if filter_option == '상위 10개 팀 (승점 순)':
        df_display = df_raw.head(10).copy()
        st.info("✅ **승점 순위 기준 상위 10개 팀**만 히트맵에 표시됩니다.")
        map_height = 600
    else:
        df_display = df_raw.copy()
        map_height = 800
        st.info("✅ **전체 20개 팀**이 표시됩니다.")


    # --- 데이터 전처리 및 정규화 (13가지 확장 지표) ---
    # 유망주 분석을 위한 13가지 확장 지표 정의
    final_cols_map = {
        'Gls': '득점', 'Ast': '어시스트', 'G+A': '공격 포인트', 'G/SoT': '득점 효율',
        'SoT/90': '슈팅 집중도', 'SCA90': '기회 창출력', 'Save%': '선방률',
        'Tkl%': '태클 성공률', 'Cmp%': '패스 성공률','xGA': '허용 기대 득점', 'Int': '인터셉트',        'PrgDist': '드리블 전진 거리'
    }

    numeric_cols = list(final_cols_map.keys())
    df_data = df_display[['Squad'] + numeric_cols].copy()

    # 1. Min-Max 정규화 적용
    df_scaled = df_data.copy()
    df_scaled[numeric_cols] = df_data[numeric_cols].apply(custom_min_max_scale)

    # 2. 역방향 처리 (수비 지표는 낮을수록 좋음)
    df_scaled['xGA'] = 1 - df_scaled['xGA'] # 🚨 허용 기대 득점(xGA): 낮을수록 좋음 (역방향)

    teams = df_scaled['Squad'].tolist()
    metrics = list(final_cols_map.values())
    data_for_heatmap = df_scaled[numeric_cols].values


    # 2-1. 팀 선택 위젯 추가
    selected_team = st.selectbox(
        "🔎 **상세 분석을 원하는 팀을 선택하세요:**",
        options=teams,
        index=teams.index("Liverpool") if "Liverpool" in teams else 0 
    )

    # 2-2. 히트맵 시각화
    st.subheader("📊 팀별 세부 지표 분석 (Heatmap)")
    st.info("💡 푸른색이 진할수록 해당 지표에서 리그 상위권임을 의미합니다. 붉은색은 약점을 나타냅니다.")

    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=data_for_heatmap,
        x=metrics,
        y=teams,
        colorscale="RdBu",
        xgap=2,
        ygap=2,
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.2f}<extra></extra>",
        showscale=True
    ))

    # Tooltip 추가
    metric_desc = [
        "[득점]<br>경기당 득점 수",
        "[어시스트]<br>경기당 어시스트 수",
        "[공격포인트]<br>경기당 득점과 어시스트의 합산",
        "[득점효율]<br>G/SoT: G는 Goal의 약자, SoT는 Shot on Targer의 약자로, PK를 제외한 유효슈팅 대비 득점 효율을 나타내는 지표. 경기당 일정 유효슈팅 수를 채운 선수만 “Goals per shot on target” 팀 효율 순위에 반영됨(경기당 최소 0.111개의 유효슈팅을 기록해야 순위에 포함).<br><br>공격수 포지션 – 침착성, 골결정력 중요",
        "[슈팅집중도]<br>90분 기준 유효슈팅 수를 의미. 팀 내에 30분 이상 출전한 선수들 기준으로 유효슈팅을 만들어낸 기록을 90분으로 환산한 지표. 단, 패널티킥 제외<br><br>공격수 포지션 – 기술, 오프더볼",
        "[기회창출력]<br>경기당 팀이 얼마나 자주 공격을 ‘창출’하는지를 정량적으로 보여주는 지표로 슛으로 이어지기까지 공격 흐름을 실제로 움직인 행동 전체를 기록<br><br>미드필더 공격수 포지션 – 시야, 기술, 패스, 판단력, 활동량",
        "[선방률]<br>상대의 유효슈팅 중 골로 이어지지 않은 비율(골키퍼가 막아낸 비율)로, 페널티킥은 제외되며 수비가 막은 슈팅은 세이브로 계산되지 않음.<br><br>골키퍼 포지션 – 반사신경, 민첩성",
        "[태클성공률]<br>경기당 최소 0.625회 이상 상대팀 드리블러에 성공한 태클 횟수를 시도한 태클 횟수로 나눈 비율<br><br>수비수 – 태클, 예측력",
        "[패스성공률]<br>경기당 30분 이상 출전한 선수 기준으로, 인플레이상황에서 각팀별 패스 성공률<br><br>미드필더 – 패스",
        "[허용기대득점]<br>실점 기대값(상대가 만든 기대 득점)에 대한 설명으로 팀이 상대에게 허용한 슈팅의 ‘기대 실점값’을 계산한 것으로, 수치가 높을수록 수비에서의 압박이 약하다는 의미.<br><br>수비수 – 종합평가",
        "[인터셉트]<br>상대방 패스를 읽고 가로챈 횟수<br><br>수비수 – 예측력, 포지셔닝<br>미드필더 – 판단력",
        "[드리블전진거리]<br>패스 없이 드리블로 전방에 얼마나 많은 거리를 가져갔는지 나타내는 지표<br><br>공격수 – 드리블<br>미드필더 – 스태미나, 기술"
    ]

    y_pos = len(teams) + 2
    fig.add_trace(go.Scatter(
        x=metrics,
        y=[y_pos] * len(metrics),
        mode="text",
        text=metrics,
        textfont=dict(size=13, color="white"),
        hovertext=metric_desc,
        hoverinfo="text",
        showlegend=False,
        line=dict(width=0, color='rgba(0,0,0,0)'),
        hoverlabel=dict(
            bgcolor="#1E2738",
            bordercolor="#FFB300",
            font=dict(size=14, color="white"),
            align="left"
        )
    ))

    fig.update_layout(
        title=f'EPL {filter_option} 퍼포먼스 비교 (2024-2025 시즌)',
        height=map_height,
        margin=dict(l=10, r=10, t=60, b=150),
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            fixedrange=True
        ),
        yaxis=dict(
            autorange="reversed",
            showticklabels=True,
            tickvals=list(range(len(teams))),  # 0부터 9까지의 틱만 표시
            ticktext=teams,
            range=[len(teams) - 0.5, y_pos + 0.5]
        ),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------
    # 3. 분석 결과 (선택된 팀 기반 동적 생성)
    # ---------------------------------------------------------
    st.subheader(f"✨ **{selected_team}** 팀 상세 분석 결과")
    analysis_message, analysis_status = analyze_team_performance(selected_team, df_scaled, df_raw)
    st.markdown(analysis_message)