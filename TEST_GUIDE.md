# 테스트 가이드

## 🧪 테스트 방법

### 1단계: 패키지 설치 확인

```bash
cd Agentic-News_RAG
pip install -r requirements.txt
```

필요한 패키지가 모두 설치되었는지 확인합니다.

### 1-1단계: API 키 설정 (중요!)

**GEMINI API 키 설정 (기본값으로 사용):**
- `backend/config.py` 파일에 `GEMINI_API_KEY`를 설정하거나
- 환경 변수로 설정: `export GEMINI_API_KEY="your-gemini-api-key"`
- GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY', "요기 발급받은 키를 넣으세요"EX)'dadf13x3-sd34g')

### 2단계: Backend 서버 실행

**터미널 1**을 열고:

```bash
cd Agentic-News_RAG\backend
python app.py
```

또는 배치 파일로:
```bash
cd Agentic-News_RAG\backend
run_server.bat
```

**정상 실행 시:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3단계: Backend 서버 확인

브라우저에서 다음 URL 접속:
- http://localhost:8000/health

**정상 응답:**
```json
{
  "status": "healthy",
  "agent_available": true
}
```

### 4단계: Frontend 실행

**새 터미널 2**를 열고:

```bash
cd Agentic-News_RAG\frontend
streamlit run search_app.py
```

또는 배치 파일로:
```bash
cd Agentic-News_RAG\frontend
run_app.bat
```

브라우저가 자동으로 열리고 `http://localhost:8501`에서 실행됩니다.

### 5단계: 테스트 쿼리 입력

Frontend 화면에서 다음 테스트 쿼리를 입력해보세요:

#### 테스트 1: API 검색 (뉴스 검색)
```
오늘 경제 뉴스 검색해줘
```
**예상 결과:** 
- 🔍 API 검색 배지 표시
- 뉴스 기사 카드 형태로 결과 표시

#### 테스트 2: LLM 생성 (일반 질문)
```
뉴스란 무엇인가요?
```
**예상 결과:**
- 💡 LLM 생성 배지 표시
- 텍스트 답변 표시

#### 테스트 3: 최신 뉴스 검색
```
최근 IT 뉴스 찾아줘
```
**예상 결과:**
- API 검색 실행
- IT 관련 뉴스 기사 표시

#### 테스트 4: 개념 설명
```
뉴스와 기사의 차이는?
```
**예상 결과:**
- LLM 생성 실행
- 개념 설명 답변 표시

## 🔍 문제 해결

### Backend가 시작되지 않는 경우

1. **포트 8000이 사용 중인 경우:**
   ```bash
   # 다른 포트로 실행
   uvicorn app:app --port 8001
   ```

2. **패키지 오류:**
   ```bash
   pip install --upgrade langchain-openai fastapi uvicorn
   ```

3. **OpenAI API 키 오류:**
   - `backend/config.py`에서 API 키 확인
   - OpenAI 계정에서 API 사용량 확인

### Frontend가 Backend에 연결되지 않는 경우

1. **Backend 서버가 실행 중인지 확인**
   - 터미널 1에서 Backend가 실행 중이어야 함

2. **연결 상태 확인**
   - Frontend 사이드바에서 "✅ Backend Connected" 표시 확인
   - "❌ Backend Not Connected"가 보이면 Backend 서버 확인

3. **API URL 확인**
   - Frontend 사이드바에서 "Backend API URL"이 `http://localhost:8000`인지 확인

### 에이전트 오류가 발생하는 경우

1. **GEMINI API 키 확인 (기본값):**
   ```python
   # backend/config.py 확인
   GEMINI_API_KEY = "your-gemini-api-key"
   ```
   또는 환경 변수:
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   ```

2. **OpenAI API 키 확인 (GEMINI가 없을 때 사용):**
   ```python
   # backend/config.py 확인
   OPENAI_API_KEY = "sk-proj-..."
   ```
   - `backend/config.py`에 기본값이 설정되어 있음
   - OpenAI 계정에서 API 사용량 확인

3. **에이전트 초기화 오류:**
   - Backend 터미널에서 에러 메시지 확인
   - GEMINI 키가 없으면 자동으로 OpenAI로 전환됨
   - `langchain-google-genai` 또는 `langchain-openai` 패키지 설치 확인

## ✅ 정상 작동 확인 체크리스트

- [ ] Backend 서버가 `http://localhost:8000`에서 실행 중
- [ ] `/health` 엔드포인트가 정상 응답
- [ ] Frontend가 `http://localhost:8501`에서 실행 중
- [ ] Frontend 사이드바에 "✅ Backend Connected" 표시
- [ ] API 검색 쿼리 입력 시 뉴스 기사 표시
- [ ] LLM 생성 쿼리 입력 시 텍스트 답변 표시
- [ ] 대화 기록이 유지됨

## 📝 테스트 시나리오

### 시나리오 1: 뉴스 검색 → 후속 질문
1. "오늘 경제 뉴스 검색해줘" 입력
2. 결과 확인
3. "그 중에서 부동산 관련만 알려줘" 입력
4. 이전 대화를 기반으로 답변 확인

### 시나리오 2: 개념 질문 → 구체적 검색
1. "뉴스란 무엇인가요?" 입력
2. LLM 답변 확인
3. "그럼 최근 뉴스 검색해줘" 입력
4. API 검색으로 전환 확인

## 🎯 성공 기준

- ✅ 에이전트가 쿼리 유형에 따라 자동으로 API 검색/LLM 생성 선택
- ✅ API 검색 시 실제 뉴스 기사가 카드 형태로 표시
- ✅ LLM 생성 시 자연스러운 텍스트 답변 제공
- ✅ 대화 기록이 유지되어 후속 질문 처리 가능

