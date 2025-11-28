# Impact Chat

**Impact Chat**은 Google AI(Gemini)를 활용한 대화형 채팅 애플리케이션입니다. 대화를 트리 구조로 분기해 여러 방향으로 탐색할 수 있습니다.

## 주요 특징

- **AI 대화**: Google Gemini Pro와 실시간 대화
- **대화 분기**: 특정 메시지에서 새 대화를 시작해 여러 경로 탐색
- **트리 구조**: 재귀적 채팅 트리로 대화 흐름 시각화
- **이중 실행 환경**: Streamlit 또는 순수 HTML/JavaScript로 실행 가능
- **REST API**: FastAPI 기반 백엔드로 독립 사용 가능

## 기능

- 채팅 메시지 전송 및 수신
- Google AI (Gemini)와의 실시간 대화
- 대화 분기 생성
- 재귀적 채팅 트리 구조

## 기술 스택

- **프론트엔드**: Streamlit, HTML/JavaScript (Tailwind CSS)
- **백엔드**: FastAPI, Uvicorn
- **AI 엔진**: Google Generative AI (Gemini Pro)
- **데이터 형식**: JSON 기반 프로젝트/채팅 구조

## 사용 사례

- 학습: 주제를 여러 각도로 탐색
- 브레인스토밍: 아이디어를 분기해 발전
- 기술 질문: 다양한 접근 방식 비교
- 대화 실험: 같은 질문에서 다른 응답 경로 탐색

## Google AI 통합

이 애플리케이션은 Google의 Gemini Pro 모델을 사용하여 AI 대화 기능을 제공합니다. API 키를 설정하면 실제 AI와 대화할 수 있습니다.

## 실행 방법

Streamlit으로 실행할 수 있습니다.

### Streamlit으로 실행

1. 의존성 설치:
```bash
pip install -r requirements.txt
```

2. Google AI API 키 설정:
```bash
# Linux/Mac
export GOOGLE_API_KEY="your-api-key-here"

# Windows (PowerShell)
$env:GOOGLE_API_KEY="your-api-key-here"

# Windows (CMD)
set GOOGLE_API_KEY=your-api-key-here
```

Google AI API 키는 [Google AI Studio](https://makersuite.google.com/app/apikey)에서 발급받을 수 있습니다.

3. Streamlit 앱 실행:
```bash
streamlit run app.py
```

브라우저에서 자동으로 열립니다.

**참고**: API 키가 설정되지 않은 경우 경고 메시지가 표시되며, AI 대화 기능은 작동하지 않습니다.

### 순수 HTML/JavaScript로 실행

1. 로컬 웹 서버 실행 (프로젝트 루트에서):
```bash
# Python 3
python3 -m http.server 8000

# 또는 Node.js
npx http-server -p 8000
```

2. 브라우저에서 접속:
```
http://localhost:8000
```

## 파일 구조

- `app.py`: Streamlit 메인 애플리케이션
- `index.html`: 순수 HTML 버전
- `srcs/app.js`: JavaScript 애플리케이션 로직
- `srcs/icons.js`: SVG 아이콘 정의
- `requirements.txt`: Python 의존성
