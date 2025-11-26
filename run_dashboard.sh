#!/bin/bash

echo "⚽ 축구 유망주 탐색 대시보드를 시작합니다..."
echo ""
echo "📦 필요한 패키지가 설치되어 있는지 확인 중..."

# 필요한 패키지가 설치되어 있는지 확인
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "❌ Streamlit이 설치되어 있지 않습니다."
    echo "📥 패키지를 설치하시겠습니까? (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        echo "📦 패키지를 설치합니다..."
        pip install -r requirements.txt
    else
        echo "❌ 설치를 취소했습니다."
        exit 1
    fi
fi

echo ""
echo "✅ 준비가 완료되었습니다!"
echo "🌐 브라우저가 자동으로 열립니다..."
echo "📊 대시보드 URL: http://localhost:8501"
echo ""
echo "⚠️  종료하려면 Ctrl+C를 누르세요"
echo ""

# Streamlit 앱 실행
streamlit run app.py

