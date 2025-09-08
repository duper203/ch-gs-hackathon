#!/bin/bash

# TF Project Manager & Email Generator 실행 스크립트

echo "🚀 TF Project Manager & Email Generator 시작..."

# 가상환경 활성화 확인
if [[ "$VIRTUAL_ENV" != "" ]]
then
    echo "✅ 가상환경이 활성화되어 있습니다: $VIRTUAL_ENV"
else
    echo "⚠️  가상환경이 활성화되지 않았습니다. 다음 명령어로 활성화하세요:"
    echo "   source venv/bin/activate"
    echo ""
fi

# .env 파일 존재 확인
if [ -f ".env" ]; then
    echo "✅ 환경변수 파일(.env)이 존재합니다"
else
    echo "⚠️  .env 파일이 존재하지 않습니다. env_template.txt를 참조하여 생성하세요:"
    echo "   cp env_template.txt .env"
    echo "   편집기로 .env 파일을 열어 OpenAI API 키를 입력하세요"
    echo ""
fi

# Streamlit 앱 실행
echo "🌐 Streamlit 앱을 실행합니다..."
streamlit run app.py
