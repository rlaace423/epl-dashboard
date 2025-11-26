import streamlit as st
import plotly.graph_objects as go
import numpy as np
import streamlit.components.v1 as components
import textwrap
import os
import toml
import base64
import mimetypes


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
        {"rank": 1, "name": "Arsenal", "w": 22, "d": 4, "l": 3, "pts": 70, "gf": 70, "ga": 24,
         "color": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "logo": "assets/logos/Arsenal_FC_logo.svg"},
        {"rank": 2, "name": "Man City", "w": 21, "d": 6, "l": 2, "pts": 69, "gf": 68, "ga": 26,
         "color": "linear-gradient(135deg, #30cfd0 0%, #330867 100%)", "logo": "assets/logos/Manchester_City_2016.svg"},
        {"rank": 3, "name": "Liverpool", "w": 20, "d": 7, "l": 3, "pts": 67, "gf": 65, "ga": 30,
         "color": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)", "logo": "assets/logos/Liverpool_FC_logo.svg"},
        {"rank": 4, "name": "Aston Villa", "w": 18, "d": 5, "l": 6, "pts": 59, "gf": 50, "ga": 35,
         "color": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)", "logo": "assets/logos/Aston_Villa_FC_2015.webp"},
        {"rank": 5, "name": "Tottenham", "w": 17, "d": 6, "l": 6, "pts": 57, "gf": 55, "ga": 39,
         "color": "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)", "logo": "assets/logos/Tottenham_Hotspur_FC_logo.svg"},
        {"rank": 6, "name": "Man Utd", "w": 16, "d": 4, "l": 9, "pts": 52, "gf": 45, "ga": 38,
         "color": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)", "logo": "assets/logos/Manchester_United_FC_logo.svg"},
        {"rank": 7, "name": "Newcastle", "w": 15, "d": 5, "l": 9, "pts": 50, "gf": 48, "ga": 40,
         "color": "linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)", "logo": "assets/logos/Newcastle_United_FC_logo.svg"},
        {"rank": 8, "name": "Chelsea", "w": 14, "d": 6, "l": 9, "pts": 48, "gf": 42, "ga": 40,
         "color": "linear-gradient(135deg, #209cff 0%, #68e0cf 100%)", "logo": "assets/logos/Chelsea_FC_logo.svg"},
        {"rank": 9, "name": "West Ham", "w": 13, "d": 7, "l": 10, "pts": 46, "gf": 40, "ga": 44,
         "color": "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)", "logo": "assets/logos/West_Ham_United_FC_logo_(2016).svg"},
        {"rank": 10, "name": "Brighton", "w": 11, "d": 9, "l": 10, "pts": 42, "gf": 38, "ga": 38,
         "color": "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)", "logo": "assets/logos/Brighton_&_Hove_Albion_FC_logo.svg"},
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
    # 2. 팀별 지표 히트맵
    # ---------------------------------------------------------
    st.subheader("📊 팀별 세부 지표 분석 (Heatmap)")
    st.info("💡 붉은색이 진할수록 해당 지표에서 리그 상위권임을 의미합니다. 푸른색은 약점을 나타냅니다.")

    # [목업 데이터 생성]
    teams = ['Arsenal', 'Man City', 'Liverpool', 'Aston Villa', 'Tottenham', 'Man Utd', 'Newcastle', 'Chelsea',
             'West Ham', 'Brighton']
    metrics = ['득점력', '유효슈팅', '패스성공률', '점유율', '태클성공', '공중볼', '활동량', '압박성공']

    np.random.seed(42)
    data = np.random.rand(len(teams), len(metrics))

    fig = go.Figure(data=go.Heatmap(
        z=data,
        x=metrics,
        y=teams,
        colorscale='RdBu_r',
        xgap=2,
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