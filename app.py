import streamlit as st
import json
import os
import threading
from streamlit.components.v1 import html
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import google.generativeai as genai
from pydantic import BaseModel
from typing import List, Dict

# 페이지 설정
st.set_page_config(
    page_title="Impact Chat Prototype",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 초기 데이터 (예제 - 실제 사용 시 빈 상태로 시작)
INITIAL_PROJECTS_EXAMPLE = [
    {
        "id": "project-1",
        "name": "프로젝트 A",
        "chats": [
            {
                "id": "1",
                "title": "리액트 탐색 (메인)",
                "parentId": None,
                "level": 0,
                "messages": [
                    {"id": 1, "role": "user", "content": "리액트가 뭐야?"},
                    {"id": 2, "role": "ai", "content": "리액트(React)는 페이스북에서 개발한 사용자 인터페이스를 만들기 위한 자바스크립트 라이브러리입니다. 컴포넌트 기반 아키텍처를 가지고 있습니다."},
                    {"id": 3, "role": "user", "content": "JSX 문법 알려줘"},
                    {"id": 4, "role": "ai", "content": "JSX는 자바스크립트의 확장 문법으로, HTML과 비슷하게 생겼지만 자바스크립트 내에서 UI 요소를 설명하는 데 사용됩니다."}
                ]
            },
            {
                "id": "1-1",
                "title": "JSX 문법 심화",
                "parentId": "1",
                "level": 1,
                "branchFromMessageId": 4,
                "messages": [
                    {"id": 1, "role": "user", "content": "JSX 더 자세히 알려줘"},
                    {"id": 2, "role": "ai", "content": "JSX의 핵심은 Babel을 통해 일반 자바스크립트 코드로 변환된다는 점입니다. React.createElement() 호출로 바뀝니다."}
                ]
            },
            {
                "id": "1-2",
                "title": "Vue 비교",
                "parentId": "1",
                "level": 1,
                "branchFromMessageId": 2,
                "messages": [
                    {"id": 1, "role": "user", "content": "그럼 Vue랑은 뭐가 달라?"},
                    {"id": 2, "role": "ai", "content": "Vue는 템플릿 기반이고 양방향 바인딩을 기본 지원하지만, 리액트는 단방향 데이터 흐름을 강조합니다."}
                ]
            },
            {
                "id": "1-2-1",
                "title": "Svelte도 보기",
                "parentId": "1-2",
                "level": 2,
                "branchFromMessageId": 2,
                "messages": [
                    {"id": 1, "role": "user", "content": "Svelte는?"},
                    {"id": 2, "role": "ai", "content": "Svelte는 런타임 라이브러리가 없는 컴파일러 방식의 프레임워크입니다."}
                ]
            },
            {
                "id": "2",
                "title": "독립 대화",
                "parentId": None,
                "level": 0,
                "messages": [
                    {"id": 1, "role": "user", "content": "오늘 점심 뭐 먹지?"},
                    {"id": 2, "role": "ai", "content": "개발자라면 역시 국밥 어떠신가요?"}
                ]
            }
        ]
    }
]

# 실제 초기 데이터 (빈 상태로 시작)
INITIAL_PROJECTS = [
    {
        "id": "project-1",
        "name": "프로젝트 A",
        "chats": []
    }
]

# Session state 초기화
if 'projects' not in st.session_state:
    st.session_state.projects = INITIAL_PROJECTS
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None
if 'expanded_groups' not in st.session_state:
    st.session_state.expanded_groups = {}
if 'api_server_started' not in st.session_state:
    st.session_state.api_server_started = False

# Google AI 초기화
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        # 간단한 테스트로 API 키 유효성 확인
        try:
            test_response = model.generate_content("test")
        except Exception as e:
            st.warning(f"⚠️ Google AI API 키가 유효하지 않을 수 있습니다: {str(e)}")
    except Exception as e:
        model = None
        st.error(f"⚠️ Google AI 초기화 실패: {str(e)}")
else:
    model = None
    st.warning("⚠️ GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다. Google AI 기능을 사용하려면 API 키를 설정하세요.")

# FastAPI 앱 생성
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델
class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

class TitleRequest(BaseModel):
    first_message: str

# 헬스 체크 엔드포인트
@app.get("/api/health")
async def health_check():
    return JSONResponse({
        "status": "ok",
        "model_initialized": model is not None,
        "api_key_set": GOOGLE_API_KEY is not None
    })

# 제목 생성 API 엔드포인트
@app.post("/api/generate-title")
async def generate_title_endpoint(request: TitleRequest):
    try:
        if not model:
            raise HTTPException(status_code=500, detail="Google AI가 초기화되지 않았습니다. GOOGLE_API_KEY를 설정하세요.")
        
        # 첫 메시지를 기반으로 간단한 제목 생성
        first_msg = request.first_message.strip()
        if len(first_msg) > 50:
            # 메시지가 길면 앞부분만 사용
            title = first_msg[:47] + "..."
        else:
            title = first_msg
        
        # AI로 더 나은 제목 생성 시도 (선택사항)
        try:
            prompt = f"다음 메시지를 기반으로 간단하고 명확한 대화 제목을 생성해주세요. 제목만 출력하고 다른 설명은 하지 마세요:\n\n{first_msg}"
            response = model.generate_content(prompt)
            ai_title = response.text.strip()
            # AI 응답이 너무 길면 잘라내기
            if len(ai_title) > 50:
                title = ai_title[:47] + "..."
            elif ai_title:
                title = ai_title
        except:
            # AI 제목 생성 실패 시 원본 메시지 사용
            pass
        
        return JSONResponse({
            "title": title
        })
    except Exception as e:
        # 오류 발생 시 원본 메시지 사용
        first_msg = request.first_message.strip()
        title = first_msg[:50] if len(first_msg) > 50 else first_msg
        return JSONResponse({
            "title": title
        })

# Chat API 엔드포인트
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        if not model:
            raise HTTPException(
                status_code=500, 
                detail="Google AI가 초기화되지 않았습니다. GOOGLE_API_KEY 환경 변수를 설정하세요."
            )
        
        # 메시지 형식 변환 (Gemini API 형식으로)
        # 마지막 메시지는 사용자 입력이어야 함
        if not request.messages or request.messages[-1]["role"] != "user":
            raise HTTPException(status_code=400, detail="마지막 메시지는 사용자 메시지여야 합니다.")
        
        # 이전 대화 기록 구성 (마지막 사용자 메시지 제외)
        history = []
        for i in range(len(request.messages) - 1):
            msg = request.messages[i]
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})
        
        # 현재 사용자 메시지
        current_user_message = request.messages[-1]["content"]
        
        # Gemini API 호출
        try:
            if history:
                # 대화 기록이 있는 경우
                chat = model.start_chat(history=history)
                response = chat.send_message(current_user_message)
            else:
                # 첫 메시지인 경우
                response = model.generate_content(current_user_message)
            
            return JSONResponse({
                "content": response.text,
                "role": "ai"
            })
        except Exception as api_error:
            error_msg = str(api_error)
            if "API_KEY" in error_msg or "api key" in error_msg.lower():
                raise HTTPException(
                    status_code=500,
                    detail="Google AI API 키가 유효하지 않습니다. GOOGLE_API_KEY를 확인하세요."
                )
            elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                raise HTTPException(
                    status_code=500,
                    detail="API 할당량을 초과했습니다. 나중에 다시 시도하세요."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Google AI API 오류: {error_msg}"
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 응답 생성 중 오류 발생: {str(e)}")

# FastAPI 서버를 별도 스레드에서 실행
def run_api_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

# API 서버 시작 (한 번만)
if not st.session_state.api_server_started:
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    st.session_state.api_server_started = True

# 아이콘 SVG 함수들
ICONS_JS = """
const MessageSquare = (size = 24) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>`;
const ChevronDown = (size = 24) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>`;
const ChevronRight = (size = 24) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>`;
const GitBranch = (size = 24) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="3" x2="6" y2="15"></line><circle cx="18" cy="6" r="3"></circle><circle cx="6" cy="18" r="3"></circle><path d="M18 9a9 9 0 0 1-9 9"></path></svg>`;
const Plus = (size = 24) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>`;
const X = (size = 24) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
const Send = (size = 24) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>`;
const User = (size = 24) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;
const Bot = (size = 24) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="10" rx="2" ry="2"></rect><circle cx="12" cy="16" r="1"></circle><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>`;
const CornerDownRight = (size = 24) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 10 20 15 15 20"></polyline><path d="M4 4v7a4 4 0 0 0 4 4h12"></path></svg>`;
const FolderOpen = (size = 24) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 19a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h4l2 2h12a2 2 0 0 1 2 2v1M5 19h14a2 2 0 0 0 2-2v-5a2 2 0 0 0-2-2H9a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2z"></path></svg>`;
"""

# HTML 템플릿 생성 함수
def generate_html():
    projects_json = json.dumps(st.session_state.projects, ensure_ascii=False)
    current_chat_id = st.session_state.current_chat_id
    expanded_groups_json = json.dumps(st.session_state.expanded_groups, ensure_ascii=False)
    
    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Impact Chat Prototype</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked@11.1.1/marked.min.js"></script>
  <style>
    body {{
      margin: 0;
      padding: 0;
      overflow: hidden;
    }}
    .scrollbar-hide {{
      -ms-overflow-style: none;
      scrollbar-width: none;
    }}
    .scrollbar-hide::-webkit-scrollbar {{
      display: none;
    }}
    .line-clamp-1 {{
      display: -webkit-box;
      -webkit-line-clamp: 1;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    /* Markdown 스타일링 */
    .markdown-content {{
      word-wrap: break-word;
    }}
    .markdown-content h1,
    .markdown-content h2,
    .markdown-content h3,
    .markdown-content h4,
    .markdown-content h5,
    .markdown-content h6 {{
      font-weight: bold;
      margin-top: 1em;
      margin-bottom: 0.5em;
    }}
    .markdown-content h1 {{ font-size: 1.5em; }}
    .markdown-content h2 {{ font-size: 1.3em; }}
    .markdown-content h3 {{ font-size: 1.1em; }}
    .markdown-content p {{
      margin: 0.5em 0;
    }}
    .markdown-content p:first-child {{
      margin-top: 0;
    }}
    .markdown-content p:last-child {{
      margin-bottom: 0;
    }}
    .markdown-content ul,
    .markdown-content ol {{
      margin: 0.5em 0;
      padding-left: 1.5em;
    }}
    .markdown-content li {{
      margin: 0.25em 0;
    }}
    .markdown-content code {{
      background-color: rgba(0, 0, 0, 0.1);
      padding: 0.2em 0.4em;
      border-radius: 0.25em;
      font-family: 'Courier New', monospace;
      font-size: 0.9em;
    }}
    .markdown-content pre {{
      background-color: rgba(0, 0, 0, 0.1);
      padding: 0.75em;
      border-radius: 0.5em;
      overflow-x: auto;
      margin: 0.5em 0;
    }}
    .markdown-content pre code {{
      background-color: transparent;
      padding: 0;
    }}
    .markdown-content blockquote {{
      border-left: 3px solid rgba(0, 0, 0, 0.2);
      padding-left: 1em;
      margin: 0.5em 0;
      font-style: italic;
    }}
    .markdown-content a {{
      text-decoration: underline;
      opacity: 0.9;
    }}
    .markdown-content a:hover {{
      opacity: 1;
    }}
    .markdown-content table {{
      border-collapse: collapse;
      margin: 0.5em 0;
      width: 100%;
    }}
    .markdown-content th,
    .markdown-content td {{
      border: 1px solid rgba(0, 0, 0, 0.2);
      padding: 0.5em;
    }}
    .markdown-content th {{
      background-color: rgba(0, 0, 0, 0.05);
      font-weight: bold;
    }}
    /* 사용자 메시지의 마크다운 스타일 (흰색 텍스트용) */
    .markdown-content.user-msg h1,
    .markdown-content.user-msg h2,
    .markdown-content.user-msg h3,
    .markdown-content.user-msg h4,
    .markdown-content.user-msg h5,
    .markdown-content.user-msg h6 {{
      color: white;
    }}
    .markdown-content.user-msg code {{
      background-color: rgba(255, 255, 255, 0.2);
      color: white;
    }}
    .markdown-content.user-msg pre {{
      background-color: rgba(255, 255, 255, 0.2);
      color: white;
    }}
    .markdown-content.user-msg blockquote {{
      border-left-color: rgba(255, 255, 255, 0.4);
    }}
    .markdown-content.user-msg a {{
      color: rgba(255, 255, 255, 0.9);
    }}
    .markdown-content.user-msg th,
    .markdown-content.user-msg td {{
      border-color: rgba(255, 255, 255, 0.3);
    }}
    .markdown-content.user-msg th {{
      background-color: rgba(255, 255, 255, 0.1);
    }}
  </style>
</head>
<body>
  <div class="flex h-screen w-full bg-white text-gray-900 font-sans overflow-hidden">
    
    <!-- 1️⃣ 왼쪽 사이드바: 채팅방 목록 -->
    <div id="left-sidebar" class="w-[280px] bg-[#F7F7F8] border-r border-[#E5E5E5] flex flex-col flex-shrink-0">
      <!-- 동적으로 렌더링됨 -->
    </div>

    <!-- 2️⃣ 중앙: 채팅 메시지 영역 -->
    <div class="flex-1 flex flex-col h-full relative min-w-0">
      <!-- 헤더 -->
      <header id="main-header" class="h-14 border-b border-[#E5E5E5] flex items-center justify-between px-6 bg-white z-10">
        <!-- 동적으로 렌더링됨 -->
      </header>

      <!-- 메시지 리스트 -->
      <div id="messages-container" class="flex-1 overflow-y-auto p-6 space-y-6 bg-white">
        <!-- 동적으로 렌더링됨 -->
      </div>

      <!-- 입력창 -->
      <div id="input-container" class="p-4 bg-white">
        <!-- 동적으로 렌더링됨 -->
      </div>
    </div>

    <!-- 3️⃣ 우측 사이드바: 분기 목록 -->
    <div id="right-sidebar" class="border-l border-[#E5E5E5] bg-[#F9FAFB] flex flex-col transition-all duration-300 ease-in-out w-0 translate-x-full border-none">
      <!-- 동적으로 렌더링됨 -->
    </div>

    <!-- 분기 생성 모달 -->
    <div id="modal-container">
      <!-- 동적으로 렌더링됨 -->
    </div>

  </div>

  <script>
    {ICONS_JS}
    
    // 초기 데이터 (Python에서 주입)
    const INITIAL_PROJECTS = {projects_json};
    
    // 상태 관리
    const state = {{
      projects: JSON.parse(JSON.stringify(INITIAL_PROJECTS)),
      currentChatId: "{current_chat_id}",
      expandedGroups: {expanded_groups_json},
      isRightSidebarOpen: false,
      inputMessage: "",
      isBranchModalOpen: false,
      branchSourceMsg: null,
      newBranchName: ""
    }};
    
    // 유틸리티 함수
    function createElement(tag, className = '', innerHTML = '', attributes = {{}}) {{
      const element = document.createElement(tag);
      if (className) element.className = className;
      if (innerHTML) element.innerHTML = innerHTML;
      Object.keys(attributes).forEach(key => {{
        element.setAttribute(key, attributes[key]);
      }});
      return element;
    }}
    
    function Avatar(role) {{
      const avatarClass = role === 'user' 
        ? 'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-blue-100' 
        : 'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-gray-200';
      
      const icon = role === 'user' 
        ? User(16) 
        : Bot(16);
      
      const iconColor = role === 'user' 
        ? 'text-blue-600' 
        : 'text-gray-600';
      
      const div = createElement('div', avatarClass);
      const iconDiv = createElement('div', iconColor);
      iconDiv.innerHTML = icon;
      div.appendChild(iconDiv);
      return div;
    }}
    
    // 현재 프로젝트와 채팅 가져오기
    function getCurrentProject() {{
      return state.projects[0];
    }}
    
    function getCurrentChat() {{
      const currentProject = getCurrentProject();
      if (!state.currentChatId && currentProject.chats.length > 0) {{
        state.currentChatId = currentProject.chats[0].id;
      }}
      return currentProject.chats.find(c => c.id === state.currentChatId) || null;
    }}
    
    // 분기된 채팅의 부모 히스토리를 가져오는 함수
    function getParentHistory(chat) {{
      if (!chat.parentId || !chat.branchFromMessageId) {{
        return [];
      }}
      
      const currentProject = getCurrentProject();
      const parentChat = currentProject.chats.find(c => c.id === chat.parentId);
      if (!parentChat) {{
        return [];
      }}
      
      // 부모 채팅에서 분기 지점까지의 메시지만 가져오기
      const branchMessageId = chat.branchFromMessageId;
      const parentMessages = [];
      
      for (const msg of parentChat.messages) {{
        if (msg.id <= branchMessageId && msg.role !== 'system') {{
          parentMessages.push({{
            role: msg.role,
            content: msg.content
          }});
        }}
      }}
      
      // 재귀적으로 더 상위 부모도 포함
      if (parentChat.parentId) {{
        const grandParentHistory = getParentHistory(parentChat);
        return [...grandParentHistory, ...parentMessages];
      }}
      
      return parentMessages;
    }}
    
    // 채팅의 전체 메시지 히스토리 가져오기 (부모 포함)
    function getFullMessageHistory(chat, excludeLoadingMessage = false) {{
      const parentHistory = getParentHistory(chat);
      const currentMessages = chat.messages
        .filter(m => {{
          // system 메시지 제외
          if (m.role === 'system') return false;
          // 로딩 메시지 제외 (옵션)
          if (excludeLoadingMessage && m.content === '응답을 생성하는 중...') return false;
          return true;
        }})
        .map(m => ({{
          role: m.role,
          content: m.content
        }}));
      
      return [...parentHistory, ...currentMessages];
    }}
    
    // 재귀적 채팅 트리 렌더링
    function renderChatTree(parentId = null, container) {{
      const currentProject = getCurrentProject();
      const children = currentProject.chats.filter(chat => chat.parentId === parentId);
      
      if (children.length === 0) return;
      
      const treeContainer = createElement('div', `flex flex-col ${{parentId ? 'ml-4 pl-3 border-l border-gray-300' : ''}}`);
      
      children.forEach(chat => {{
        const hasChildren = currentProject.chats.some(c => c.parentId === chat.id);
        const isExpanded = state.expandedGroups[chat.id];
        const isSelected = state.currentChatId === chat.id;
        
        const chatItem = createElement('div', 'mb-1');
        
        const chatButton = createElement('div', `
          group flex items-center justify-between px-2 py-1.5 rounded cursor-pointer transition-colors duration-200
          ${{isSelected ? 'bg-blue-100 text-blue-800' : 'hover:bg-gray-100 text-gray-700'}}
        `);
        chatButton.addEventListener('click', () => handleChatSelect(chat.id));
        
        const chatContent = createElement('div', 'flex items-center gap-2 overflow-hidden');
        const chatId = createElement('span', `text-xs font-mono font-bold ${{isSelected ? 'text-blue-600' : 'text-gray-500'}}`);
        chatId.textContent = chat.id;
        const chatTitle = createElement('span', 'text-sm truncate font-medium');
        chatTitle.textContent = chat.title;
        
        chatContent.appendChild(chatId);
        chatContent.appendChild(chatTitle);
        chatButton.appendChild(chatContent);
        chatItem.appendChild(chatButton);
        
        if (hasChildren) {{
          const childrenContainer = createElement('div', 'mt-1');
          
          if (isExpanded) {{
            const nestedContainer = createElement('div');
            renderChatTree(chat.id, nestedContainer);
            childrenContainer.appendChild(nestedContainer);
          }}
          
          const toggleButton = createElement('div', 'ml-4 mt-1 flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 cursor-pointer select-none');
          toggleButton.addEventListener('click', (e) => {{
            e.stopPropagation();
            toggleGroup(chat.id);
          }});
          
          const toggleIcon = createElement('span');
          toggleIcon.innerHTML = isExpanded ? ChevronDown(12) : ChevronRight(12);
          const toggleText = createElement('span');
          toggleText.textContent = isExpanded 
            ? '[접기]' 
            : `[${{currentProject.chats.filter(c => c.parentId === chat.id).length}}개 하위 대화]`;
          
          toggleButton.appendChild(toggleIcon);
          toggleButton.appendChild(toggleText);
          childrenContainer.appendChild(toggleButton);
          chatItem.appendChild(childrenContainer);
        }}
        
        treeContainer.appendChild(chatItem);
      }});
      
      container.appendChild(treeContainer);
    }}
    
    // 왼쪽 사이드바 렌더링
    function renderLeftSidebar() {{
      const sidebar = document.getElementById('left-sidebar');
      if (!sidebar) return;
      
      sidebar.innerHTML = '';
      
      const currentProject = getCurrentProject();
      
      // 헤더
      const header = createElement('div', 'p-4 border-b border-[#E5E5E5] flex items-center gap-2');
      const folderIcon = createElement('div', 'text-gray-600');
      folderIcon.innerHTML = FolderOpen(20);
      const title = createElement('h1', 'font-bold text-gray-800');
      title.textContent = currentProject.name;
      header.appendChild(folderIcon);
      header.appendChild(title);
      
      // 채팅 트리 컨테이너
      const treeWrapper = createElement('div', 'flex-1 overflow-y-auto p-3 scrollbar-hide');
      const treeContainer = createElement('div');
      renderChatTree(null, treeContainer);
      treeWrapper.appendChild(treeContainer);
      
      // 새 대화 버튼
      const newChatSection = createElement('div', 'mt-4 pt-4 border-t border-gray-200');
      const newChatButton = createElement('button', 'flex items-center gap-2 text-sm text-gray-500 hover:text-blue-600 px-2 py-2 w-full text-left rounded hover:bg-gray-100 transition');
      const plusIcon = createElement('span');
      plusIcon.innerHTML = Plus(16);
      const newChatText = createElement('span');
      newChatText.textContent = '새 대화 시작';
      newChatButton.appendChild(plusIcon);
      newChatButton.appendChild(newChatText);
      newChatButton.addEventListener('click', handleNewChat);
      newChatSection.appendChild(newChatButton);
      treeWrapper.appendChild(newChatSection);
      
      // 푸터
      const footer = createElement('div', 'p-4 border-t border-[#E5E5E5] text-xs text-gray-400');
      footer.textContent = 'Impact Chat Prototype v0.1';
      
      sidebar.appendChild(header);
      sidebar.appendChild(treeWrapper);
      sidebar.appendChild(footer);
    }}
    
    // 메시지 렌더링
    function renderMessages() {{
      const messagesContainer = document.getElementById('messages-container');
      if (!messagesContainer) return;
      
      messagesContainer.innerHTML = '';
      
      const currentChat = getCurrentChat();
      
      if (!currentChat) {{
        const emptyState = createElement('div', 'h-full flex flex-col items-center justify-center text-gray-400 gap-4');
        const iconContainer = createElement('div', 'w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center');
        iconContainer.innerHTML = MessageSquare(32);
        const text = createElement('p');
        text.textContent = '새 대화를 시작해보세요.';
        emptyState.appendChild(iconContainer);
        emptyState.appendChild(text);
        messagesContainer.appendChild(emptyState);
        return;
      }}
      
      if (currentChat.messages.length === 0) {{
        const emptyState = createElement('div', 'h-full flex flex-col items-center justify-center text-gray-400 gap-4');
        const iconContainer = createElement('div', 'w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center');
        iconContainer.innerHTML = MessageSquare(32);
        const text = createElement('p');
        text.textContent = '대화를 시작해보세요.';
        emptyState.appendChild(iconContainer);
        emptyState.appendChild(text);
        messagesContainer.appendChild(emptyState);
      }} else {{
        currentChat.messages.forEach(msg => {{
          const messageWrapper = createElement('div', `flex w-full ${{msg.role === 'user' ? 'justify-end' : 'justify-start'}}`);
          const messageContent = createElement('div', `flex max-w-[80%] gap-3 ${{msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}}`);
          
          const avatar = Avatar(msg.role);
          messageContent.appendChild(avatar);
          
          const messageBubble = createElement('div', 'flex flex-col gap-1 items-start');
          const bubble = createElement('div', `
            px-4 py-3 text-sm leading-relaxed rounded-2xl relative group
            ${{msg.role === 'user' 
              ? 'bg-[#0066FF] text-white rounded-tr-sm' 
              : 'bg-[#F7F7F8] text-[#1F1F1F] rounded-tl-sm border border-gray-100'
            }}
          `);
          
          // 마크다운 렌더링
          const markdownContent = createElement('div', `markdown-content ${{msg.role === 'user' ? 'user-msg' : ''}}`);
          if (typeof marked !== 'undefined') {{
            // marked.js가 로드된 경우 마크다운 파싱
            markdownContent.innerHTML = marked.parse(msg.content);
          }} else {{
            // marked.js가 없는 경우 일반 텍스트로 표시
            markdownContent.textContent = msg.content;
          }}
          bubble.appendChild(markdownContent);
          
          if (msg.role === 'ai') {{
            const branchButton = createElement('div', 'absolute -right-24 bottom-0 opacity-0 group-hover:opacity-100 transition-opacity duration-200');
            const button = createElement('button', 'flex items-center gap-1.5 bg-white border border-gray-200 shadow-sm text-xs font-medium text-gray-600 px-2.5 py-1.5 rounded-full hover:text-blue-600 hover:border-blue-200 transition');
            const iconSpan = createElement('span');
            iconSpan.innerHTML = GitBranch(12);
            const textSpan = createElement('span');
            textSpan.textContent = '분기하기';
            button.appendChild(iconSpan);
            button.appendChild(textSpan);
            button.addEventListener('click', () => openBranchModal(msg));
            branchButton.appendChild(button);
            bubble.appendChild(branchButton);
          }}
          
          messageBubble.appendChild(bubble);
          messageContent.appendChild(messageBubble);
          messageWrapper.appendChild(messageContent);
          messagesContainer.appendChild(messageWrapper);
        }});
      }}
    }}
    
    // 헤더 렌더링
    function renderHeader() {{
      const header = document.getElementById('main-header');
      if (!header) return;
      
      header.innerHTML = '';
      
      const currentChat = getCurrentChat();
      
      const leftSection = createElement('div', 'flex items-center gap-3');
      if (currentChat) {{
        const chatIdBadge = createElement('span', 'bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded font-mono');
        chatIdBadge.textContent = `Chat #${{currentChat.id}}`;
        const chatTitle = createElement('h2', 'font-bold text-lg text-gray-800 truncate max-w-md');
        chatTitle.textContent = currentChat.title;
        leftSection.appendChild(chatIdBadge);
        leftSection.appendChild(chatTitle);
      }} else {{
        const chatTitle = createElement('h2', 'font-bold text-lg text-gray-800 truncate max-w-md');
        chatTitle.textContent = '새 대화';
        leftSection.appendChild(chatTitle);
      }}
      
      const rightButton = createElement('button', `p-2 rounded-md hover:bg-gray-100 transition ${{state.isRightSidebarOpen ? 'text-blue-600 bg-blue-50' : 'text-gray-500'}}`);
      rightButton.innerHTML = GitBranch(20);
      rightButton.addEventListener('click', () => {{
        state.isRightSidebarOpen = !state.isRightSidebarOpen;
        render();
      }});
      
      header.appendChild(leftSection);
      header.appendChild(rightButton);
    }}
    
    // 입력창 렌더링
    function renderInput() {{
      const inputContainer = document.getElementById('input-container');
      if (!inputContainer) return;
      
      inputContainer.innerHTML = '';
      
      const wrapper = createElement('div', 'max-w-4xl mx-auto relative');
      const form = createElement('form', 'relative');
      form.addEventListener('submit', handleSendMessage);
      
      const input = createElement('input', 'w-full bg-[#F7F7F8] border border-transparent focus:bg-white focus:border-[#0066FF] rounded-xl pl-4 pr-12 py-3.5 text-sm outline-none transition-all shadow-sm');
      input.type = 'text';
      input.placeholder = '메시지를 입력하세요...';
      input.value = state.inputMessage;
      input.addEventListener('input', (e) => {{
        state.inputMessage = e.target.value;
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {{
          submitButton.disabled = !state.inputMessage.trim();
        }}
      }});
      
      const submitButton = createElement('button', `absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition`);
      submitButton.type = 'submit';
      submitButton.disabled = !state.inputMessage.trim();
      submitButton.innerHTML = Send(16);
      
      form.appendChild(input);
      form.appendChild(submitButton);
      wrapper.appendChild(form);
      inputContainer.appendChild(wrapper);
    }}
    
    // 우측 사이드바 렌더링
    function renderRightSidebar() {{
      const sidebar = document.getElementById('right-sidebar');
      if (!sidebar) return;
      
      sidebar.className = `
        border-l border-[#E5E5E5] bg-[#F9FAFB] flex flex-col transition-all duration-300 ease-in-out
        ${{state.isRightSidebarOpen ? 'w-[300px] translate-x-0' : 'w-0 translate-x-full border-none'}}
      `;
      
      if (!state.isRightSidebarOpen) {{
        sidebar.innerHTML = '';
        return;
      }}
      
      sidebar.innerHTML = '';
      
      const header = createElement('div', 'p-4 border-b border-[#E5E5E5] flex items-center justify-between min-w-[300px]');
      const headerTitle = createElement('h3', 'font-bold text-gray-800 flex items-center gap-2');
      const branchIcon = createElement('span');
      branchIcon.innerHTML = GitBranch(18);
      const branchText = createElement('span');
      branchText.textContent = '분기 목록';
      headerTitle.appendChild(branchIcon);
      headerTitle.appendChild(branchText);
      const closeButton = createElement('button', 'text-gray-400 hover:text-gray-600');
      closeButton.innerHTML = X(18);
      closeButton.addEventListener('click', () => {{
        state.isRightSidebarOpen = false;
        render();
      }});
      header.appendChild(headerTitle);
      header.appendChild(closeButton);
      
      const content = createElement('div', 'flex-1 overflow-y-auto p-4 min-w-[300px]');
      
      // Flatten 채팅 목록
      const currentProject = getCurrentProject();
      const flattenChats = [];
      const traverse = (parentId) => {{
        const children = currentProject.chats.filter(c => c.parentId === parentId);
        children.forEach(c => {{
          flattenChats.push(c);
          traverse(c.id);
        }});
      }};
      traverse(null);
      
      flattenChats.forEach(chat => {{
        const isCurrent = chat.id === state.currentChatId;
        const indent = chat.level * 16;
        const firstUserMsg = chat.messages.find(m => m.role === 'user')?.content || "대화 시작...";
        
        const chatCard = createElement('div', `
          mb-3 p-3 rounded-lg cursor-pointer transition-all border border-transparent
          ${{isCurrent ? 'bg-white border-blue-200 shadow-sm' : 'hover:bg-white hover:border-gray-200'}}
        `);
        chatCard.style.marginLeft = `${{indent}}px`;
        chatCard.addEventListener('click', () => handleChatSelect(chat.id));
        
        const cardHeader = createElement('div', 'flex items-center gap-2 mb-1');
        const icon = createElement('span');
        icon.innerHTML = chat.parentId ? CornerDownRight(14) : MessageSquare(14);
        if (!chat.parentId) {{
          icon.className = 'text-green-600';
        }} else {{
          icon.className = 'text-gray-400';
        }}
        const title = createElement('span', `text-sm font-bold ${{isCurrent ? 'text-blue-600' : 'text-gray-800'}}`);
        title.textContent = `${{chat.level === 0 ? `${{chat.id}}.` : chat.id}} ${{chat.title}}`;
        const currentBadge = isCurrent ? createElement('span', 'text-[10px] bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded font-medium') : null;
        if (currentBadge) {{
          currentBadge.textContent = '현재';
        }}
        
        cardHeader.appendChild(icon);
        cardHeader.appendChild(title);
        if (currentBadge) cardHeader.appendChild(currentBadge);
        
        const preview = createElement('p', 'text-xs text-gray-500 line-clamp-1 pl-5');
        preview.textContent = `"${{firstUserMsg}}"`;
        
        chatCard.appendChild(cardHeader);
        chatCard.appendChild(preview);
        content.appendChild(chatCard);
      }});
      
      sidebar.appendChild(header);
      sidebar.appendChild(content);
    }}
    
    // 모달 렌더링
    function renderModal() {{
      const modalContainer = document.getElementById('modal-container');
      if (!modalContainer) return;
      
      if (!state.isBranchModalOpen) {{
        modalContainer.innerHTML = '';
        return;
      }}
      
      modalContainer.innerHTML = '';
      
      const backdrop = createElement('div', 'fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm');
      backdrop.addEventListener('click', (e) => {{
        if (e.target === backdrop) {{
          state.isBranchModalOpen = false;
          render();
        }}
      }});
      
      const modal = createElement('div', 'bg-white rounded-xl shadow-2xl w-[400px] p-6 transform transition-all scale-100');
      modal.addEventListener('click', (e) => e.stopPropagation());
      
      const modalHeader = createElement('div', 'flex items-center justify-between mb-4');
      const modalTitle = createElement('h3', 'text-lg font-bold text-gray-800');
      modalTitle.textContent = '새로운 분기 생성';
      const closeButton = createElement('button', 'text-gray-400 hover:text-gray-600');
      closeButton.innerHTML = X(20);
      closeButton.addEventListener('click', () => {{
        state.isBranchModalOpen = false;
        render();
      }});
      modalHeader.appendChild(modalTitle);
      modalHeader.appendChild(closeButton);
      
      const preview = createElement('div', 'mb-4 bg-gray-50 p-3 rounded text-sm text-gray-600 border border-gray-100 italic');
      const previewText = createElement('div');
      previewText.textContent = `"${{(state.branchSourceMsg?.content || "").substring(0, 60)}}..."`;
      const previewSubtext = createElement('div', 'mt-1 text-xs text-gray-400 font-medium not-italic');
      previewSubtext.textContent = '이 메시지로부터 분기합니다.';
      preview.appendChild(previewText);
      preview.appendChild(previewSubtext);
      
      const inputSection = createElement('div', 'mb-6');
      const label = createElement('label', 'block text-sm font-medium text-gray-700 mb-2');
      label.textContent = '분기 이름';
      const input = createElement('input', 'w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none');
      input.type = 'text';
      input.placeholder = '예: Vue와 비교, 심화 질문 등';
      input.value = state.newBranchName;
      input.autofocus = true;
      input.addEventListener('input', (e) => {{
        state.newBranchName = e.target.value;
        const createButton = modal.querySelector('button:last-child');
        if (createButton) {{
          createButton.disabled = !state.newBranchName.trim();
        }}
      }});
      input.addEventListener('keydown', (e) => {{
        if (e.key === 'Enter') {{
          handleCreateBranch();
        }}
      }});
      inputSection.appendChild(label);
      inputSection.appendChild(input);
      
      const buttonSection = createElement('div', 'flex justify-end gap-2');
      const cancelButton = createElement('button', 'px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg font-medium text-sm transition');
      cancelButton.textContent = '취소';
      cancelButton.addEventListener('click', () => {{
        state.isBranchModalOpen = false;
        render();
      }});
      const createButton = createElement('button', `px-4 py-2 bg-blue-600 text-white rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50 transition`);
      createButton.textContent = '분기 생성하기';
      createButton.disabled = !state.newBranchName.trim();
      createButton.addEventListener('click', handleCreateBranch);
      buttonSection.appendChild(cancelButton);
      buttonSection.appendChild(createButton);
      
      modal.appendChild(modalHeader);
      modal.appendChild(preview);
      modal.appendChild(inputSection);
      modal.appendChild(buttonSection);
      backdrop.appendChild(modal);
      modalContainer.appendChild(backdrop);
    }}
    
    // 이벤트 핸들러
    function handleChatSelect(chatId) {{
      state.currentChatId = chatId;
      render();
      // Streamlit에 상태 변경 알림 (선택사항)
      if (window.parent && window.parent.postMessage) {{
        window.parent.postMessage({{
          type: 'chat_selected',
          chatId: chatId
        }}, '*');
      }}
    }}
    
    function toggleGroup(chatId) {{
      state.expandedGroups[chatId] = !state.expandedGroups[chatId];
      render();
    }}
    
    async function handleSendMessage(e) {{
      e.preventDefault();
      if (!state.inputMessage.trim()) return;
      
      // 현재 채팅이 없으면 새로 생성
      let currentChat = getCurrentChat();
      if (!currentChat) {{
        handleNewChat();
        currentChat = getCurrentChat();
      }}
      
      const newMessage = {{
        id: Date.now(),
        role: 'user',
        content: state.inputMessage
      }};
      
      const currentProject = getCurrentProject();
      const chatIdx = currentProject.chats.findIndex(c => c.id === state.currentChatId);
      
      if (chatIdx > -1) {{
        const currentChat = currentProject.chats[chatIdx];
        const isFirstMessage = currentChat.messages.length === 0 || 
          (currentChat.messages.length === 1 && currentChat.messages[0].role === 'system');
        
        currentProject.chats[chatIdx].messages.push(newMessage);
        const userMessage = state.inputMessage;
        state.inputMessage = "";
        render();
        
        // 첫 메시지인 경우 제목 자동 생성
        if (isFirstMessage) {{
          updateChatTitleIfNeeded(state.currentChatId, userMessage);
        }}
        
        // 로딩 메시지 표시
        const loadingMessage = {{
          id: Date.now() + 1,
          role: 'ai',
          content: '응답을 생성하는 중...'
        }};
        const updatedProject = getCurrentProject();
        const cIdx = updatedProject.chats.findIndex(c => c.id === state.currentChatId);
        if (cIdx > -1) {{
          updatedProject.chats[cIdx].messages.push(loadingMessage);
          render();
        }}
        
        // Google AI API 호출
        try {{
          const currentChat = updatedProject.chats[cIdx];
          // 분기된 채팅의 경우 부모 히스토리 포함 (로딩 메시지 제외)
          const allMessages = getFullMessageHistory(currentChat, true);
          
          // 마지막 메시지가 사용자 메시지인지 확인
          if (allMessages.length === 0 || allMessages[allMessages.length - 1].role !== 'user') {{
            throw new Error('메시지 히스토리에 문제가 있습니다. 마지막 메시지가 사용자 메시지여야 합니다.');
          }}
          
          const response = await fetch('http://127.0.0.1:8000/api/chat', {{
            method: 'POST',
            headers: {{
              'Content-Type': 'application/json',
            }},
            body: JSON.stringify({{
              messages: allMessages
            }})
          }});
          
          if (!response.ok) {{
            // 오류 응답에서 상세 메시지 가져오기
            let errorDetail = `HTTP error! status: ${{response.status}}`;
            try {{
              const errorData = await response.json();
              if (errorData.detail) {{
                errorDetail = errorData.detail;
              }}
            }} catch (e) {{
              // JSON 파싱 실패 시 기본 메시지 사용
            }}
            throw new Error(errorDetail);
          }}
          
          const data = await response.json();
          
          // 로딩 메시지 제거하고 실제 응답 추가
          const finalProject = getCurrentProject();
          const finalIdx = finalProject.chats.findIndex(c => c.id === state.currentChatId);
          if (finalIdx > -1) {{
            const messages = finalProject.chats[finalIdx].messages;
            const loadingIdx = messages.findIndex(m => m.id === loadingMessage.id);
            if (loadingIdx > -1) {{
              messages.splice(loadingIdx, 1);
            }}
            messages.push({{
              id: Date.now() + 2,
              role: 'ai',
              content: data.content
            }});
            render();
          }}
        }} catch (error) {{
          console.error('AI 응답 오류:', error);
          // 로딩 메시지 제거하고 오류 메시지 추가
          const errorProject = getCurrentProject();
          const errorIdx = errorProject.chats.findIndex(c => c.id === state.currentChatId);
          if (errorIdx > -1) {{
            const messages = errorProject.chats[errorIdx].messages;
            const loadingIdx = messages.findIndex(m => m.id === loadingMessage.id);
            if (loadingIdx > -1) {{
              messages.splice(loadingIdx, 1);
            }}
            
            // 더 자세한 오류 메시지 생성
            let errorMessage = '죄송합니다. 응답을 생성하는 중 오류가 발생했습니다.';
            if (error.message) {{
              if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {{
                errorMessage += '\\n\\nAPI 서버에 연결할 수 없습니다. FastAPI 서버가 실행 중인지 확인하세요.';
              }} else if (error.message.includes('500')) {{
                errorMessage += '\\n\\n서버 오류가 발생했습니다. GOOGLE_API_KEY가 올바르게 설정되어 있는지 확인하세요.';
              }} else {{
                errorMessage += `\\n\\n오류: ${{error.message}}`;
              }}
            }}
            
            messages.push({{
              id: Date.now() + 2,
              role: 'ai',
              content: errorMessage
            }});
            render();
          }}
        }}
      }}
    }}
    
    function openBranchModal(message) {{
      state.branchSourceMsg = message;
      state.newBranchName = "";
      state.isBranchModalOpen = true;
      render();
    }}
    
    function handleCreateBranch() {{
      if (!state.newBranchName.trim()) return;
      
      const currentChat = getCurrentChat();
      const currentProject = getCurrentProject();
      
      const siblings = currentProject.chats.filter(c => c.parentId === currentChat.id);
      const newId = `${{currentChat.id}}-${{siblings.length + 1}}`;
      
      // 부모 채팅의 분기 지점까지의 메시지 히스토리 복사
      const branchMessageId = state.branchSourceMsg.id;
      const parentMessages = [];
      for (const msg of currentChat.messages) {{
        if (msg.id <= branchMessageId && msg.role !== 'system') {{
          parentMessages.push({{
            id: msg.id,
            role: msg.role,
            content: msg.content
          }});
        }}
      }}
      
      // 재귀적으로 더 상위 부모도 포함
      if (currentChat.parentId) {{
        const parentChat = currentProject.chats.find(c => c.id === currentChat.parentId);
        if (parentChat && parentChat.branchFromMessageId) {{
          const grandParentMessages = [];
          for (const msg of parentChat.messages) {{
            if (msg.id <= parentChat.branchFromMessageId && msg.role !== 'system') {{
              grandParentMessages.push({{
                id: msg.id,
                role: msg.role,
                content: msg.content
              }});
            }}
          }}
          parentMessages.unshift(...grandParentMessages);
        }}
      }}
      
      const newChat = {{
        id: newId,
        title: state.newBranchName,
        parentId: currentChat.id,
        level: currentChat.level + 1,
        branchFromMessageId: state.branchSourceMsg.id,
        messages: [
          {{ id: 1, role: 'system', content: `"${{currentChat.title}}" 대화에서 분기되었습니다.` }},
          ...parentMessages
        ]
      }};
      
      currentProject.chats.push(newChat);
      state.expandedGroups[currentChat.id] = true;
      state.currentChatId = newId;
      state.isBranchModalOpen = false;
      state.isRightSidebarOpen = true;
      render();
    }}
    
    function handleNewChat() {{
      const currentProject = getCurrentProject();
      const newId = (currentProject.chats.filter(c => !c.parentId).length + 1).toString();
      const newChat = {{
        id: newId,
        title: "새로운 대화",
        parentId: null,
        level: 0,
        messages: []
      }};
      currentProject.chats.push(newChat);
      state.currentChatId = newId;
      state.expandedGroups[newId] = true;
      render();
    }}
    
    // 첫 메시지로 제목 자동 생성
    async function updateChatTitleIfNeeded(chatId, firstMessage) {{
      const currentProject = getCurrentProject();
      const chat = currentProject.chats.find(c => c.id === chatId);
      if (!chat || chat.title !== "새로운 대화") {{
        return; // 이미 제목이 있으면 업데이트하지 않음
      }}
      
      try {{
        const response = await fetch('http://127.0.0.1:8000/api/generate-title', {{
          method: 'POST',
          headers: {{
            'Content-Type': 'application/json',
          }},
          body: JSON.stringify({{
            first_message: firstMessage
          }})
        }});
        
        if (response.ok) {{
          const data = await response.json();
          chat.title = data.title;
          render();
        }}
      }} catch (error) {{
        console.error('제목 생성 오류:', error);
        // 오류 발생 시 첫 메시지의 일부를 제목으로 사용
        chat.title = firstMessage.length > 50 ? firstMessage.substring(0, 47) + '...' : firstMessage;
        render();
      }}
    }}
    
    // 메인 렌더 함수
    function render() {{
      renderLeftSidebar();
      renderHeader();
      renderMessages();
      renderInput();
      renderRightSidebar();
      renderModal();
    }}
    
    // 초기화
    document.addEventListener('DOMContentLoaded', () => {{
      render();
    }});
    
    // 페이지 로드 시에도 렌더링 (이미 로드된 경우)
    if (document.readyState === 'loading') {{
      document.addEventListener('DOMContentLoaded', render);
    }} else {{
      render();
    }}
  </script>
</body>
</html>
"""
    return html_content

# Streamlit UI
st.markdown("""
<style>
    .stApp {
        padding: 0;
    }
    .main .block-container {
        padding: 0;
        max-width: 100%;
    }
    iframe {
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# HTML 렌더링
html(generate_html(), height=800, scrolling=False)

