// 아이콘 import
import {
  MessageSquare,
  ChevronDown,
  ChevronRight,
  GitBranch,
  Plus,
  X,
  Menu,
  Send,
  User,
  Bot,
  CornerDownRight,
  FolderOpen
} from './icons.js';

// 초기 샘플 데이터
const INITIAL_PROJECTS = [
  {
    id: "project-1",
    name: "프로젝트 A",
    chats: [
      {
        id: "1",
        title: "리액트 탐색 (메인)",
        parentId: null,
        level: 0,
        messages: [
          { id: 1, role: "user", content: "리액트가 뭐야?" },
          { id: 2, role: "ai", content: "리액트(React)는 페이스북에서 개발한 사용자 인터페이스를 만들기 위한 자바스크립트 라이브러리입니다. 컴포넌트 기반 아키텍처를 가지고 있습니다." },
          { id: 3, role: "user", content: "JSX 문법 알려줘" },
          { id: 4, role: "ai", content: "JSX는 자바스크립트의 확장 문법으로, HTML과 비슷하게 생겼지만 자바스크립트 내에서 UI 요소를 설명하는 데 사용됩니다." }
        ]
      },
      {
        id: "1-1",
        title: "JSX 문법 심화",
        parentId: "1",
        level: 1,
        branchFromMessageId: 4,
        messages: [
          { id: 1, role: "user", content: "JSX 더 자세히 알려줘" },
          { id: 2, role: "ai", content: "JSX의 핵심은 Babel을 통해 일반 자바스크립트 코드로 변환된다는 점입니다. React.createElement() 호출로 바뀝니다." }
        ]
      },
      {
        id: "1-2",
        title: "Vue 비교",
        parentId: "1",
        level: 1,
        branchFromMessageId: 2,
        messages: [
          { id: 1, role: "user", content: "그럼 Vue랑은 뭐가 달라?" },
          { id: 2, role: "ai", content: "Vue는 템플릿 기반이고 양방향 바인딩을 기본 지원하지만, 리액트는 단방향 데이터 흐름을 강조합니다." }
        ]
      },
      {
        id: "1-2-1",
        title: "Svelte도 보기",
        parentId: "1-2",
        level: 2,
        branchFromMessageId: 2,
        messages: [
          { id: 1, role: "user", content: "Svelte는?" },
          { id: 2, role: "ai", content: "Svelte는 런타임 라이브러리가 없는 컴파일러 방식의 프레임워크입니다." }
        ]
      },
      {
        id: "2",
        title: "독립 대화",
        parentId: null,
        level: 0,
        messages: [
          { id: 1, role: "user", content: "오늘 점심 뭐 먹지?" },
          { id: 2, role: "ai", content: "개발자라면 역시 국밥 어떠신가요?" }
        ]
      }
    ]
  }
];

// 상태 관리
const state = {
  projects: JSON.parse(JSON.stringify(INITIAL_PROJECTS)), // deep copy
  currentChatId: "1",
  expandedGroups: { "1": true, "1-2": true },
  isRightSidebarOpen: false,
  inputMessage: "",
  isBranchModalOpen: false,
  branchSourceMsg: null,
  newBranchName: ""
};

// 유틸리티 함수
function createElement(tag, className = '', innerHTML = '', attributes = {}) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (innerHTML) element.innerHTML = innerHTML;
  Object.keys(attributes).forEach(key => {
    element.setAttribute(key, attributes[key]);
  });
  return element;
}

function Avatar(role) {
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
}

// 현재 프로젝트와 채팅 가져오기
function getCurrentProject() {
  return state.projects[0];
}

function getCurrentChat() {
  const currentProject = getCurrentProject();
  return currentProject.chats.find(c => c.id === state.currentChatId) || currentProject.chats[0];
}

// 재귀적 채팅 트리 렌더링
function renderChatTree(parentId = null, container) {
  const currentProject = getCurrentProject();
  const children = currentProject.chats.filter(chat => chat.parentId === parentId);
  
  if (children.length === 0) return;
  
  const treeContainer = createElement('div', `flex flex-col ${parentId ? 'ml-4 pl-3 border-l border-gray-300' : ''}`);
  
  children.forEach(chat => {
    const hasChildren = currentProject.chats.some(c => c.parentId === chat.id);
    const isExpanded = state.expandedGroups[chat.id];
    const isSelected = state.currentChatId === chat.id;
    
    const chatItem = createElement('div', 'mb-1');
    
    const chatButton = createElement('div', `
      group flex items-center justify-between px-2 py-1.5 rounded cursor-pointer transition-colors duration-200
      ${isSelected ? 'bg-blue-100 text-blue-800' : 'hover:bg-gray-100 text-gray-700'}
    `);
    chatButton.addEventListener('click', () => handleChatSelect(chat.id));
    
    const chatContent = createElement('div', 'flex items-center gap-2 overflow-hidden');
    const chatId = createElement('span', `text-xs font-mono font-bold ${isSelected ? 'text-blue-600' : 'text-gray-500'}`);
    chatId.textContent = chat.id;
    const chatTitle = createElement('span', 'text-sm truncate font-medium');
    chatTitle.textContent = chat.title;
    
    chatContent.appendChild(chatId);
    chatContent.appendChild(chatTitle);
    chatButton.appendChild(chatContent);
    chatItem.appendChild(chatButton);
    
    if (hasChildren) {
      const childrenContainer = createElement('div', 'mt-1');
      
      if (isExpanded) {
        const nestedContainer = createElement('div');
        renderChatTree(chat.id, nestedContainer);
        childrenContainer.appendChild(nestedContainer);
      }
      
      const toggleButton = createElement('div', 'ml-4 mt-1 flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 cursor-pointer select-none');
      toggleButton.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleGroup(chat.id);
      });
      
      const toggleIcon = createElement('span');
      toggleIcon.innerHTML = isExpanded ? ChevronDown(12) : ChevronRight(12);
      const toggleText = createElement('span');
      toggleText.textContent = isExpanded 
        ? '[접기]' 
        : `[${currentProject.chats.filter(c => c.parentId === chat.id).length}개 하위 대화]`;
      
      toggleButton.appendChild(toggleIcon);
      toggleButton.appendChild(toggleText);
      childrenContainer.appendChild(toggleButton);
      chatItem.appendChild(childrenContainer);
    }
    
    treeContainer.appendChild(chatItem);
  });
  
  container.appendChild(treeContainer);
}

// 왼쪽 사이드바 렌더링
function renderLeftSidebar() {
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
}

// 메시지 렌더링
function renderMessages() {
  const messagesContainer = document.getElementById('messages-container');
  if (!messagesContainer) return;
  
  messagesContainer.innerHTML = '';
  
  const currentChat = getCurrentChat();
  
  if (currentChat.messages.length === 0) {
    const emptyState = createElement('div', 'h-full flex flex-col items-center justify-center text-gray-400 gap-4');
    const iconContainer = createElement('div', 'w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center');
    iconContainer.innerHTML = MessageSquare(32);
    const text = createElement('p');
    text.textContent = '대화를 시작해보세요.';
    emptyState.appendChild(iconContainer);
    emptyState.appendChild(text);
    messagesContainer.appendChild(emptyState);
  } else {
    currentChat.messages.forEach(msg => {
      const messageWrapper = createElement('div', `flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`);
      const messageContent = createElement('div', `flex max-w-[80%] gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`);
      
      const avatar = Avatar(msg.role);
      messageContent.appendChild(avatar);
      
      const messageBubble = createElement('div', 'flex flex-col gap-1 items-start');
      const bubble = createElement('div', `
        px-4 py-3 text-sm leading-relaxed rounded-2xl relative group
        ${msg.role === 'user' 
          ? 'bg-[#0066FF] text-white rounded-tr-sm' 
          : 'bg-[#F7F7F8] text-[#1F1F1F] rounded-tl-sm border border-gray-100'
        }
      `);
      bubble.textContent = msg.content;
      
      if (msg.role === 'ai') {
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
      }
      
      messageBubble.appendChild(bubble);
      messageContent.appendChild(messageBubble);
      messageWrapper.appendChild(messageContent);
      messagesContainer.appendChild(messageWrapper);
    });
  }
}

// 헤더 렌더링
function renderHeader() {
  const header = document.getElementById('main-header');
  if (!header) return;
  
  header.innerHTML = '';
  
  const currentChat = getCurrentChat();
  
  const leftSection = createElement('div', 'flex items-center gap-3');
  const chatIdBadge = createElement('span', 'bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded font-mono');
  chatIdBadge.textContent = `Chat #${currentChat.id}`;
  const chatTitle = createElement('h2', 'font-bold text-lg text-gray-800 truncate max-w-md');
  chatTitle.textContent = currentChat.title;
  leftSection.appendChild(chatIdBadge);
  leftSection.appendChild(chatTitle);
  
  const rightButton = createElement('button', `p-2 rounded-md hover:bg-gray-100 transition ${state.isRightSidebarOpen ? 'text-blue-600 bg-blue-50' : 'text-gray-500'}`);
  rightButton.innerHTML = GitBranch(20);
  rightButton.addEventListener('click', () => {
    state.isRightSidebarOpen = !state.isRightSidebarOpen;
    render();
  });
  
  header.appendChild(leftSection);
  header.appendChild(rightButton);
}

// 입력창 렌더링
function renderInput() {
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
  input.addEventListener('input', (e) => {
    state.inputMessage = e.target.value;
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
      submitButton.disabled = !state.inputMessage.trim();
    }
  });
  
  const submitButton = createElement('button', `absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition`);
  submitButton.type = 'submit';
  submitButton.disabled = !state.inputMessage.trim();
  submitButton.innerHTML = Send(16);
  
  form.appendChild(input);
  form.appendChild(submitButton);
  wrapper.appendChild(form);
  inputContainer.appendChild(wrapper);
}

// 우측 사이드바 렌더링
function renderRightSidebar() {
  const sidebar = document.getElementById('right-sidebar');
  if (!sidebar) return;
  
  sidebar.className = `
    border-l border-[#E5E5E5] bg-[#F9FAFB] flex flex-col transition-all duration-300 ease-in-out
    ${state.isRightSidebarOpen ? 'w-[300px] translate-x-0' : 'w-0 translate-x-full border-none'}
  `;
  
  if (!state.isRightSidebarOpen) {
    sidebar.innerHTML = '';
    return;
  }
  
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
  closeButton.addEventListener('click', () => {
    state.isRightSidebarOpen = false;
    render();
  });
  header.appendChild(headerTitle);
  header.appendChild(closeButton);
  
  const content = createElement('div', 'flex-1 overflow-y-auto p-4 min-w-[300px]');
  
  // Flatten 채팅 목록
  const currentProject = getCurrentProject();
  const flattenChats = [];
  const traverse = (parentId) => {
    const children = currentProject.chats.filter(c => c.parentId === parentId);
    children.forEach(c => {
      flattenChats.push(c);
      traverse(c.id);
    });
  };
  traverse(null);
  
  flattenChats.forEach(chat => {
    const isCurrent = chat.id === state.currentChatId;
    const indent = chat.level * 16;
    const firstUserMsg = chat.messages.find(m => m.role === 'user')?.content || "대화 시작...";
    
    const chatCard = createElement('div', `
      mb-3 p-3 rounded-lg cursor-pointer transition-all border border-transparent
      ${isCurrent ? 'bg-white border-blue-200 shadow-sm' : 'hover:bg-white hover:border-gray-200'}
    `);
    chatCard.style.marginLeft = `${indent}px`;
    chatCard.addEventListener('click', () => handleChatSelect(chat.id));
    
    const cardHeader = createElement('div', 'flex items-center gap-2 mb-1');
    const icon = createElement('span');
    icon.innerHTML = chat.parentId ? CornerDownRight(14) : MessageSquare(14);
    if (!chat.parentId) {
      icon.className = 'text-green-600';
    } else {
      icon.className = 'text-gray-400';
    }
    const title = createElement('span', `text-sm font-bold ${isCurrent ? 'text-blue-600' : 'text-gray-800'}`);
    title.textContent = `${chat.level === 0 ? `${chat.id}.` : chat.id} ${chat.title}`;
    const currentBadge = isCurrent ? createElement('span', 'text-[10px] bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded font-medium') : null;
    if (currentBadge) {
      currentBadge.textContent = '현재';
    }
    
    cardHeader.appendChild(icon);
    cardHeader.appendChild(title);
    if (currentBadge) cardHeader.appendChild(currentBadge);
    
    const preview = createElement('p', 'text-xs text-gray-500 line-clamp-1 pl-5');
    preview.textContent = `"${firstUserMsg}"`;
    
    chatCard.appendChild(cardHeader);
    chatCard.appendChild(preview);
    content.appendChild(chatCard);
  });
  
  sidebar.appendChild(header);
  sidebar.appendChild(content);
}

// 모달 렌더링
function renderModal() {
  const modalContainer = document.getElementById('modal-container');
  if (!modalContainer) return;
  
  if (!state.isBranchModalOpen) {
    modalContainer.innerHTML = '';
    return;
  }
  
  modalContainer.innerHTML = '';
  
  const backdrop = createElement('div', 'fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm');
  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) {
      state.isBranchModalOpen = false;
      render();
    }
  });
  
  const modal = createElement('div', 'bg-white rounded-xl shadow-2xl w-[400px] p-6 transform transition-all scale-100');
  modal.addEventListener('click', (e) => e.stopPropagation());
  
  const modalHeader = createElement('div', 'flex items-center justify-between mb-4');
  const modalTitle = createElement('h3', 'text-lg font-bold text-gray-800');
  modalTitle.textContent = '새로운 분기 생성';
  const closeButton = createElement('button', 'text-gray-400 hover:text-gray-600');
  closeButton.innerHTML = X(20);
  closeButton.addEventListener('click', () => {
    state.isBranchModalOpen = false;
    render();
  });
  modalHeader.appendChild(modalTitle);
  modalHeader.appendChild(closeButton);
  
  const preview = createElement('div', 'mb-4 bg-gray-50 p-3 rounded text-sm text-gray-600 border border-gray-100 italic');
  const previewText = createElement('div');
  previewText.textContent = `"${(state.branchSourceMsg?.content || "").substring(0, 60)}..."`;
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
  input.addEventListener('input', (e) => {
    state.newBranchName = e.target.value;
    const createButton = modal.querySelector('button:last-child');
    if (createButton) {
      createButton.disabled = !state.newBranchName.trim();
    }
  });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      handleCreateBranch();
    }
  });
  inputSection.appendChild(label);
  inputSection.appendChild(input);
  
  const buttonSection = createElement('div', 'flex justify-end gap-2');
  const cancelButton = createElement('button', 'px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg font-medium text-sm transition');
  cancelButton.textContent = '취소';
  cancelButton.addEventListener('click', () => {
    state.isBranchModalOpen = false;
    render();
  });
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
}

// 이벤트 핸들러
function handleChatSelect(chatId) {
  state.currentChatId = chatId;
  render();
}

function toggleGroup(chatId) {
  state.expandedGroups[chatId] = !state.expandedGroups[chatId];
  render();
}

function handleSendMessage(e) {
  e.preventDefault();
  if (!state.inputMessage.trim()) return;
  
  const newMessage = {
    id: Date.now(),
    role: 'user',
    content: state.inputMessage
  };
  
  const currentProject = getCurrentProject();
  const chatIdx = currentProject.chats.findIndex(c => c.id === state.currentChatId);
  
  if (chatIdx > -1) {
    currentProject.chats[chatIdx].messages.push(newMessage);
    state.inputMessage = "";
    render();
    
    // AI 자동 응답 시뮬레이션
    setTimeout(() => {
      const updatedProject = getCurrentProject();
      const cIdx = updatedProject.chats.findIndex(c => c.id === state.currentChatId);
      if (cIdx > -1) {
        updatedProject.chats[cIdx].messages.push({
          id: Date.now() + 1,
          role: 'ai',
          content: "이것은 프로토타입 AI 응답입니다. 이 메시지에서 분기할 수 있습니다."
        });
        render();
      }
    }, 600);
  }
}

function openBranchModal(message) {
  state.branchSourceMsg = message;
  state.newBranchName = "";
  state.isBranchModalOpen = true;
  render();
}

function handleCreateBranch() {
  if (!state.newBranchName.trim()) return;
  
  const currentChat = getCurrentChat();
  const currentProject = getCurrentProject();
  
  const siblings = currentProject.chats.filter(c => c.parentId === currentChat.id);
  const newId = `${currentChat.id}-${siblings.length + 1}`;
  
  const newChat = {
    id: newId,
    title: state.newBranchName,
    parentId: currentChat.id,
    level: currentChat.level + 1,
    branchFromMessageId: state.branchSourceMsg.id,
    messages: [
      { id: 1, role: 'system', content: `"${currentChat.title}" 대화에서 분기되었습니다.` }
    ]
  };
  
  currentProject.chats.push(newChat);
  state.expandedGroups[currentChat.id] = true;
  state.currentChatId = newId;
  state.isBranchModalOpen = false;
  state.isRightSidebarOpen = true;
  render();
}

function handleNewChat() {
  const currentProject = getCurrentProject();
  const newId = (currentProject.chats.filter(c => !c.parentId).length + 1).toString();
  const newChat = {
    id: newId,
    title: "새로운 대화",
    parentId: null,
    level: 0,
    messages: []
  };
  currentProject.chats.push(newChat);
  state.currentChatId = newId;
  render();
}

// 메인 렌더 함수
function render() {
  renderLeftSidebar();
  renderHeader();
  renderMessages();
  renderInput();
  renderRightSidebar();
  renderModal();
}

// 초기화
document.addEventListener('DOMContentLoaded', () => {
  render();
});

