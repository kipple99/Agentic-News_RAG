# Agentic News RAG

에이전트가 자동으로 뉴스 검색 vs LLM 생성을 판단하는 시스템

## 🎯 기능

- **자동 판단**: 사용자 쿼리를 분석하여 API 검색 또는 LLM 생성 자동 선택
- **뉴스 검색**: Naver API를 통한 최신 뉴스 검색
- **LLM 생성**: 무료 LLM(Ollama)을 사용한 답변 생성
- **멀티턴 대화**: 대화 기록 유지 및 후속 질문 지원

## 📋 판단 기준

### API 검색이 선택되는 경우
- "오늘 경제 뉴스 검색해줘"
- "최근 IT 뉴스 찾아줘"
- "이번 주 부동산 뉴스"

### LLM 생성이 선택되는 경우
- "뉴스란 무엇인가요?"
- "뉴스와 기사의 차이는?"
- "뉴스의 역할을 설명해줘"

## 🚀 빠른 시작

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. Backend 서버 실행

```bash
cd backend
python app.py
# 또는
run_server.bat
```

서버가 `http://localhost:8000`에서 실행됩니다.

### 3. Frontend 실행

새 터미널에서:

```bash
cd frontend
streamlit run search_app.py
# 또는
run_app.bat
```

브라우저에서 `http://localhost:8501`이 자동으로 열립니다.

## 📁 프로젝트 구조

```
Agentic-News_RAG/
├── backend/
│   ├── app.py                 # FastAPI 서버
│   ├── agent/                 # 에이전트 모듈
│   │   ├── news_agent.py     # 메인 에이전트
│   │   └── llm_factory.py    # LLM 팩토리
│   ├── external/
│   │   └── naver_client.py   # Naver API 클라이언트
│   └── config.py             # 설정
├── frontend/
│   ├── search_app.py         # Streamlit UI
│   └── run_app.bat           # Frontend 실행 배치
└── requirements.txt          # 패키지 목록
```

## 🔧 설정

### Naver API 키 (선택사항)

`backend/config.py`에 기본값이 설정되어 있거나 환경 변수로 설정:

```bash
set NAVER_CLIENT_ID=your_client_id
set NAVER_CLIENT_SECRET=your_client_secret
```

### OpenAI 모델 변경

`backend/app.py`에서 모델 이름 변경:

```python
_agent = create_news_agent(model_type="openai", model_name="gpt-4")  # 또는 gpt-3.5-turbo
```

## 💡 사용 예제

1. **뉴스 검색**: "오늘 경제 뉴스 검색해줘" → API 검색 실행
2. **일반 질문**: "뉴스란 무엇인가요?" → LLM이 답변 생성
3. **후속 질문**: 이전 대화를 기반으로 답변

## 🛠️ 문제 해결

### Backend 연결 오류
- Backend 서버가 실행 중인지 확인
- 포트 8000이 사용 가능한지 확인

### OpenAI API 오류
- `backend/config.py`에서 API 키 확인
- OpenAI 계정에서 API 사용량 확인
- 네트워크 연결 확인

### 패키지 오류
```bash
pip install --upgrade langchain langchain-community langchain-core
```

## 📝 기술 스택

- **Backend**: FastAPI, LangChain
- **Frontend**: Streamlit
- **LLM**: OpenAI GPT-3.5-turbo
- **검색 API**: Naver News API

## 📄 라이선스

교육 목적으로 제작되었습니다.
