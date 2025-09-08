# 🚀 TF Project Manager & Email Generator

해커톤용 Streamlit 프로젝트 - 파일 업로드, LLM 기반 내용 정리, 역할별 맞춤 이메일 생성 도구

## ✨ 주요 기능

### 📄 기능 1: 파일 업로드 & 내용 정리
- 파일 업로드 (텍스트, 마크다운, 워드, PDF 지원)
- TF 프로젝트명 입력
- 커스텀 템플릿을 이용한 LLM 기반 내용 정리
- 프로젝트별 폴더에 정리된 내용 저장

### 📧 기능 2: 역할별 맞춤 이메일 생성
- 저장된 프로젝트 데이터를 RAG 방식으로 활용
- 4가지 역할별 맞춤 이메일 생성:
  - 🎯 **Marketer**: 시장성, 고객, 마케팅 전략 중심
  - 🎨 **Designer**: UI/UX, 디자인, 사용자 경험 중심
  - ⚙️ **Engineer**: 기술 구현, 아키텍처, 개발 중심
  - 📊 **Project Manager**: 일정, 리소스, 리스크 관리 중심

### 📊 기능 3: 프로젝트 현황 대시보드
- 모든 프로젝트 현황 조회
- 프로젝트별 파일 목록 및 메타데이터 표시

## 🛠️ 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd ch-gs-hackathon
```

### 2. 가상환경 생성 및 의존성 설치
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 환경변수 설정
```bash
# .env 파일 생성
cp env_template.txt .env

# .env 파일을 편집하여 OpenAI API 키 입력
OPENAI_API_KEY=your_actual_api_key_here
```

### 4. 애플리케이션 실행
```bash
streamlit run app.py
```

## 🔑 OpenAI API 키 발급

1. [OpenAI Platform](https://platform.openai.com/) 접속
2. 계정 생성/로그인
3. API Keys 섹션에서 새 키 생성
4. `.env` 파일에 키 입력

## 📁 프로젝트 구조

```
ch-gs-hackathon/
├── app.py                 # 메인 Streamlit 애플리케이션
├── requirements.txt       # Python 의존성
├── env_template.txt      # 환경변수 템플릿
├── README.md             # 프로젝트 문서
└── tf_projects/          # 프로젝트 데이터 저장 폴더 (자동 생성)
    ├── project1/
    ├── project2/
    └── ...
```

## 🎯 사용 방법

### 파일 업로드 및 정리
1. 사이드바에서 "📄 파일 업로드 & 정리" 선택
2. 파일 업로드
3. TF 프로젝트명 입력
4. 정리 템플릿 작성
5. "내용 정리 및 저장" 버튼 클릭

### 역할별 이메일 생성
1. 사이드바에서 "📧 역할별 이메일 생성" 선택
2. 저장된 프로젝트 선택
3. 역할 선택 (Marketer, Designer, Engineer, Project Manager)
4. "이메일 생성" 버튼 클릭

## 🚀 배포

### GitHub Pages (정적 호스팅은 불가)
Streamlit 앱은 서버 실행이 필요하므로 다음 플랫폼 사용 권장:

### Streamlit Cloud
1. GitHub에 코드 푸시
2. [Streamlit Cloud](https://streamlit.io/cloud) 접속
3. GitHub 저장소 연결
4. 환경변수에 OpenAI API 키 설정
5. 앱 배포

### Heroku
```bash
# Procfile 생성
echo "web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0" > Procfile

# Heroku 배포
heroku create your-app-name
heroku config:set OPENAI_API_KEY=your_api_key
git push heroku main
```

## 🔧 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python
- **LLM**: OpenAI GPT-3.5-turbo
- **Data Storage**: 로컬 JSON 파일
- **File Processing**: 텍스트 기반 파일 지원

## 🤝 기여

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

## 🆘 문제 해결

### 일반적인 문제
1. **OpenAI API 오류**: API 키가 올바른지 확인
2. **파일 업로드 오류**: 지원되는 파일 형식인지 확인
3. **메모리 부족**: 큰 파일의 경우 작은 단위로 분할

### 지원
이슈가 발생하면 GitHub Issues에 문제를 보고해주세요.
