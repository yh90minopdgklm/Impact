# Impact Chat API 명세서

## 개요

Impact Chat API는 Google AI (Gemini)를 활용한 채팅 애플리케이션을 위한 REST API입니다.

- **Base URL**: `http://127.0.0.1:8000`
- **API 버전**: 1.0.0
- **인증**: 현재 인증 불필요 (향후 추가 예정)

## 환경 설정

API를 사용하기 전에 다음 환경 변수를 설정해야 합니다:
h
export GOOGLE_API_KEY="your-google-api-key-here"Google AI API 키는 [Google AI Studio](https://makersuite.google.com/app/apikey)에서 발급받을 수 있습니다.

## 엔드포인트

### 1. 헬스 체크

**GET** `/api/health`

서버 상태와 Google AI 초기화 상태를 확인합니다.

**응답 예시:**
{
  "status": "ok",
  "model_initialized": true,
  "api_key_set": true
}### 2. 채팅 메시지 전송

**POST** `/api/chat`

사용자 메시지를 Google AI에 전송하고 응답을 받습니다.

**요청 본문:**
{
  "messages": [
    {
      "role": "user",
      "content": "리액트가 뭐야?"
    },
    {
      "role": "ai",
      "content": "리액트(React)는..."
    },
    {
      "role": "user",
      "content": "JSX 문법 알려줘"
    }
  ]
}**주의사항:**
- `messages` 배열의 마지막 요소는 반드시 `role: "user"`여야 합니다.
- 대화 히스토리를 포함하여 컨텍스트를 유지할 수 있습니다.

**응답 예시:**
{
  "content": "JSX는 자바스크립트의 확장 문법으로...",
  "role": "ai"
}**오류 응답:**

- `400 Bad Request`: 마지막 메시지가 사용자 메시지가 아닌 경우
- `500 Internal Server Error`: 
  - Google AI가 초기화되지 않은 경우
  - API 키가 유효하지 않은 경우
  - API 할당량을 초과한 경우
  - 기타 Google AI API 오류

### 3. 대화 제목 생성

**POST** `/api/generate-title`

첫 번째 사용자 메시지를 기반으로 대화 제목을 자동 생성합니다.

**요청 본문:**son
{
  "first_message": "리액트가 뭐야?"
}**응답 예시:**
{
  "title": "리액트에 대한 질문"
}**동작 방식:**
1. Google AI를 사용하여 제목 생성 시도
2. AI 생성 실패 시 메시지의 앞부분(최대 50자)을 제목으로 사용
3. 메시지가 50자를 초과하면 "..."으로 잘라냄

## 데이터 모델

### Message
{
  role: "user" | "ai"
  content: string
}### ChatRequestypescript
{
  messages: Message[]
}### ChatResponseipt
{
  content: string
  role: "ai"
}### TitleRequestypescript
{
  first_message: string
}
### TitleResponsepescript
{
  title: string  // 최대 50자
}## 오류 처리

모든 오류 응답은 다음 형식을 따릅니다:

{
  "detail": "오류 메시지"
}### 주요 오류 코드

- `400`: 잘못된 요청 형식
- `500`: 서버 내부 오류

## 사용 예시

### cURL 예시

**헬스 체크:**
curl http://127.0.0.1:8000/api/health**채팅 메시지 전송:**
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "리액트가 뭐야?"}
    ]
  }'**제목 생성:**
curl -X POST http://127.0.0.1:8000/api/generate-title \
  -H "Content-Type: application/json" \
  -d '{
    "first_message": "리액트가 뭐야?"
  }'### JavaScript 예시
cript
// 채팅 메시지 전송
const response = await fetch('http://127.0.0.1:8000/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    messages: [
      { role: 'user', content: '리액트가 뭐야?' }
    ]
  })
});

const data = await response.json();
console.log(data.content); // AI 응답### Python 예시

import requests

# 채팅 메시지 전송
response = requests.post(
    'http://127.0.0.1:8000/api/chat',
    json={
        'messages': [
            {'role': 'user', 'content': '리액트가 뭐야?'}
        ]
    }
)

data = response.json()
print(data['content'])  # AI 응답## CORS 설정

현재 API는 모든 origin에서의 요청을 허용하도록 설정되어 있습니다 (`allow_origins=["*"]`). 프로덕션 환경에서는 특정 origin만 허용하도록 변경하는 것을 권장합니다.

## 제한사항

- Google AI API의 할당량 제한이 적용됩니다.
- 제목 생성 시 최대 50자로 제한됩니다.
- 채팅 메시지의 길이 제한은 Google AI API의 제한을 따릅니다.

## 버전 정보

- **현재 버전**: 1.0.0
- **최종 업데이트**: 2024년